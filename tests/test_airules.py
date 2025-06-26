from pathlib import Path
from unittest.mock import ANY, patch

import pytest
from typer.testing import CliRunner

from airules import config
from airules.cli import app, clean_rules_content

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_venv_check(monkeypatch):
    """Mock venv check for all tests."""
    monkeypatch.setattr("airules.cli.in_virtualenv", lambda: True)


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


@patch("airules.cli.run_generation_pipeline")
def test_tool_subcommand_invokes_pipeline(mock_run_pipeline):
    """Test that invoking a tool subcommand (e.g., 'cursor') calls the main pipeline."""
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"], catch_exceptions=False)
        result = runner.invoke(
            app,
            ["cursor", "--primary", "test-model", "--project-path", "/fake"],
            catch_exceptions=False,
        )

    assert result.exit_code == 0, result.output
    mock_run_pipeline.assert_called_once_with(
        tool="cursor",
        primary_model="test-model",
        research=False,
        review_model=None,
        dry_run=False,
        yes=False,
        project_path="/fake",
        lang=None,
        tags=None,
    )


@patch("airules.cli.write_rules_file")
@patch(
    "airules.cli.validate_rules",
    side_effect=lambda content, model: f"{content}\\n- Validated",
)
@patch("airules.cli.generate_rules", return_value="RULES")
@patch("airules.cli.research_with_perplexity", return_value="RESEARCH SUMMARY")
def test_full_pipeline(
    mock_research,
    mock_get_rules,
    mock_validate,
    mock_write_rules,
    isolated_fs_with_config,
    monkeypatch,
):
    """Test the full pipeline with --research and --review flags."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
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
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    mock_research.assert_called()
    mock_get_rules.assert_called_with(
        ANY, "cursor", ANY, ANY, research_summary="RESEARCH SUMMARY"
    )
    mock_validate.assert_called()
    mock_write_rules.assert_called()

    final_content = mock_write_rules.call_args.args[1]
    assert "- Validated" in final_content


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
    assert "Missing OpenAI API Key" in result.output


@patch("airules.cli.in_virtualenv", return_value=False)
def test_cli_fails_outside_venv(mock_in_virtualenv, isolated_fs_with_config):
    """Test that the CLI fails if not run inside a virtual environment."""
    result = runner.invoke(app, ["cursor"])
    assert result.exit_code == 1
    assert "This command must be run in a virtual environment" in result.output


@patch("airules.cli.generate_rules", return_value="RULES")
def test_pipeline_review_no_anthropic_key(
    mock_get_rules, isolated_fs_with_config, monkeypatch
):
    """Test that the CLI exits if --review is used without ANTHROPIC_API_KEY."""
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
    assert "Missing Anthropic API Key" in result.output


@patch("airules.cli.generate_rules", return_value="NEW RULES")
def test_overwrite_prompt_no(mock_get_rules, isolated_fs_with_config):
    """Test that the file is not overwritten when the user inputs 'n'."""
    filepath = isolated_fs_with_config / ".cursor/rules/security.mdc"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text("OLD RULES")

    result = runner.invoke(app, ["cursor"], input="n\n", catch_exceptions=True)

    assert "already exists. Overwrite?" in result.output
    assert "Skipping file" in result.output
    assert filepath.read_text() == "OLD RULES"


@patch("airules.cli.generate_rules", return_value="NEW RULES")
def test_overwrite_prompt_yes(mock_get_rules, isolated_fs_with_config):
    """Test that the file is overwritten when the user inputs 'y'."""
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


@patch("airules.cli.generate_rules", return_value="CLAUDE RULES")
def test_claude_model_as_primary(mock_get_rules, isolated_fs_with_config, monkeypatch):
    """Test that Claude models can be used as primary generation model."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    project_path = str(isolated_fs_with_config)
    result = runner.invoke(
        app,
        [
            "cursor",
            "--primary",
            "claude-3-sonnet-20240229",
            "--project-path",
            project_path,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    mock_get_rules.assert_called_with(
        "python",
        "cursor",
        "security",
        "claude-3-sonnet-20240229",
        research_summary=None,
    )
