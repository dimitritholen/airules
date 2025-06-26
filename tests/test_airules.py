from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest
from typer.testing import CliRunner

from airules import config
from airules.cli import app, clean_rules_content

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_venv_check(monkeypatch):
    """Mock venv check for all tests."""
    monkeypatch.setattr("airules.venv_check.in_virtualenv", lambda: True)


@pytest.fixture
def isolated_fs_with_config(tmp_path):
    """
    Provides an isolated filesystem with a default .rules4rc file,
    modified to contain only a single tag to simplify overwrite tests.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(app, ["init"], catch_exceptions=False)
        config_path = Path(td) / config.CONFIG_FILENAME
        cfg = config.get_config()
        cfg.set("settings", "tags", "security")  # Use a single tag
        with open(config_path, "w") as f:
            cfg.write(f)
        yield Path(td)


def test_init_command(isolated_fs_with_config):
    """Test that the init command runs successfully within an isolated fs."""
    config_path = isolated_fs_with_config / config.CONFIG_FILENAME
    assert config_path.exists()


@patch("airules.api_clients.AIClientFactory.get_client")
def test_tool_subcommand_invokes_pipeline(mock_get_client):
    """Test that invoking a tool subcommand (e.g., 'cursor') calls the pipeline and creates an API client."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.return_value = "# Test Rules\n\nSample rule content"
    mock_get_client.return_value = mock_client

    with runner.isolated_filesystem():
        runner.invoke(app, ["init"], catch_exceptions=False)
        result = runner.invoke(
            app,
            ["cursor", "--primary", "gpt-4o", "--project-path", "/fake", "--dry-run"],
            catch_exceptions=False,
        )

    assert result.exit_code == 0, result.output
    # Verify the API client was created for the correct model
    mock_get_client.assert_called()
    # Verify the client was used to generate content
    mock_client.generate_completion.assert_called()


@patch("airules.api_clients.AIClientFactory.get_client")
@patch("airules.api_clients.AIClientFactory.get_research_client")
def test_full_pipeline(
    mock_get_research_client,
    mock_get_client,
    isolated_fs_with_config,
    monkeypatch,
):
    """Test the full pipeline with --research and --review flags."""
    # Mock research client
    mock_research_client = Mock()
    mock_research_client.generate_completion.return_value = "RESEARCH SUMMARY"
    mock_get_research_client.return_value = mock_research_client

    # Mock generation and validation clients
    mock_client = Mock()
    mock_client.generate_completion.side_effect = ["RULES", "RULES\n- Validated"]
    mock_get_client.return_value = mock_client

    project_path = str(isolated_fs_with_config)
    result = runner.invoke(
        app,
        [
            "cursor",
            "--research",
            "--review",
            "claude-3-sonnet-20240229",
            "--project-path",
            project_path,
            "--dry-run",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    # Verify research was called
    mock_get_research_client.assert_called()
    mock_research_client.generate_completion.assert_called()
    # Verify generation and validation were called
    assert mock_client.generate_completion.call_count == 2  # generation + validation


def test_pipeline_no_config_fails(tmp_path):
    """Test that the pipeline fails gracefully if no config file exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["cursor"])
        assert result.exit_code == 1
        assert "No .rules4rc file found" in result.output


@pytest.mark.parametrize(
    "content, expected",
    [
        ("```markdown\\nHello World\\n```", "Hello World"),
        ("Hello World", "Hello World"),
        ("```\\nHello World\\n```", "Hello World"),
        ("\\n```python\\nimport os\\n```\\n", "import os"),
    ],
)
def test_clean_rules_content(content, expected):
    """Test that clean_rules_content removes markdown fences correctly."""
    assert clean_rules_content(content) == expected


def test_generate_missing_perplexity_key(monkeypatch, isolated_fs_with_config):
    """Test that the CLI exits if --research is used without PERPLEXITY_API_KEY."""
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    result = runner.invoke(app, ["cursor", "--research"])
    assert result.exit_code == 1
    assert "Missing Perplexity API Key" in result.output


def test_generate_missing_openai_key(monkeypatch, isolated_fs_with_config):
    """Test that the CLI exits if OPENAI_API_KEY is not set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = runner.invoke(app, ["cursor"])
    assert result.exit_code == 1
    assert "Missing OpenAI API" in result.output and "Key" in result.output


@patch("airules.services.in_virtualenv", return_value=False)
def test_cli_fails_outside_venv(mock_in_virtualenv, isolated_fs_with_config):
    """Test that the CLI fails if not run inside a virtual environment."""
    result = runner.invoke(app, ["cursor"])
    assert result.exit_code == 1
    assert "This command must be run in a virtual environment" in result.output


@patch("airules.api_clients.AIClientFactory.get_client")
def test_pipeline_review_no_anthropic_key(
    mock_get_client, isolated_fs_with_config, monkeypatch
):
    """Test that the CLI exits if --review is used without ANTHROPIC_API_KEY."""
    # First call (generation) succeeds, second call (validation) fails due to
    # missing key
    mock_client = Mock()
    mock_client.generate_completion.return_value = "RULES"

    def side_effect(model):
        # Mock generation client works
        if model == "gpt-4-turbo":  # Default primary model
            return mock_client
        # Mock validation client fails
        elif model == "claude-3-sonnet-20240229":
            from airules.exceptions import APIError

            raise APIError(
                "Missing Anthropic API Key. Set ANTHROPIC_API_KEY environment variable."
            )
        return mock_client

    mock_get_client.side_effect = side_effect
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    project_path = str(isolated_fs_with_config)
    result = runner.invoke(
        app,
        [
            "cursor",
            "--review",
            "claude-3-sonnet-20240229",
            "--project-path",
            project_path,
        ],
    )
    assert result.exit_code == 1
    assert (
        "Missing Anthropic" in result.output
        and "API" in result.output
        and "Key" in result.output
    )


@patch("airules.api_clients.AIClientFactory.get_client")
def test_overwrite_prompt_no(mock_get_client, isolated_fs_with_config):
    """Test that the file is not overwritten when the user inputs 'n'."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.return_value = "NEW RULES"
    mock_get_client.return_value = mock_client

    filepath = isolated_fs_with_config / ".cursor/rules/security.mdc"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text("OLD RULES")

    result = runner.invoke(app, ["cursor"], input="n\n", catch_exceptions=True)

    assert "already exists. Overwrite?" in result.output
    assert "Skipping file" in result.output
    assert filepath.read_text() == "OLD RULES"


@patch("airules.api_clients.AIClientFactory.get_client")
def test_overwrite_prompt_yes(mock_get_client, isolated_fs_with_config):
    """Test that the file is overwritten when the user inputs 'y'."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.return_value = "NEW RULES"
    mock_get_client.return_value = mock_client

    filepath = isolated_fs_with_config / ".cursor/rules/security.mdc"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text("OLD RULES")

    result = runner.invoke(app, ["cursor"], input="y\n", catch_exceptions=True)

    assert "already exists. Overwrite?" in result.output
    assert filepath.read_text() == "NEW RULES"


def test_list_models_command():
    """Test the list-models command shows available models."""
    result = runner.invoke(app, ["list-models"])
    assert result.exit_code == 0
    assert "Available Models for AI Rules Generation" in result.output
    assert "OPENAI Models:" in result.output
    assert "ANTHROPIC Models:" in result.output
    assert "PERPLEXITY Models:" in result.output
    assert "gpt-4-turbo" in result.output
    assert "claude-3-sonnet-20240229" in result.output


@patch("airules.api_clients.AIClientFactory.get_client")
def test_claude_model_as_primary(mock_get_client, isolated_fs_with_config, monkeypatch):
    """Test that Claude models can be used as primary generation model."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.return_value = "CLAUDE RULES"
    mock_get_client.return_value = mock_client

    project_path = str(isolated_fs_with_config)
    result = runner.invoke(
        app,
        [
            "cursor",
            "--primary",
            "claude-3-sonnet-20240229",
            "--project-path",
            project_path,
            "--dry-run",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    # Verify the client was created for Claude model
    mock_get_client.assert_called()
    mock_client.generate_completion.assert_called()
