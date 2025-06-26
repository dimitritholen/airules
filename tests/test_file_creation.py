import configparser
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from airules import config
from airules.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_venv_check(monkeypatch):
    monkeypatch.setattr("airules.services.in_virtualenv", lambda: True)


@pytest.fixture
def isolated_fs_with_config(tmp_path):
    """Provides an isolated filesystem with a default .rules4rc file with a single tag."""
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(app, ["init"], catch_exceptions=False)

        # Modify config to only have one tag for all tests in this module
        config_path = Path(td) / config.CONFIG_FILENAME
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
        cfg.set("settings", "tags", "security")  # Use only one tag
        with open(config_path, "w") as f:
            cfg.write(f)

        yield Path(td)


@patch("airules.api_clients.AIClientFactory.get_client")
def test_claude_file_creation_and_append(mock_get_client, isolated_fs_with_config):
    """Test that 'airules claude' creates and appends to CLAUDE.md."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.side_effect = ["Generated Rules", "More Rules"]
    mock_get_client.return_value = mock_client

    project_path = isolated_fs_with_config
    # First run creates the file
    result1 = runner.invoke(
        app, ["claude", "--project-path", str(project_path)], catch_exceptions=False
    )
    assert result1.exit_code == 0, result1.output
    claude_md_path = project_path / "CLAUDE.md"
    assert claude_md_path.exists()
    assert "Generated Rules" in claude_md_path.read_text()
    assert "---" not in claude_md_path.read_text()  # No separator on first write

    # Second run appends to the file
    result2 = runner.invoke(
        app, ["claude", "--project-path", str(project_path)], catch_exceptions=False
    )
    assert result2.exit_code == 0, result2.output
    final_content = claude_md_path.read_text()
    assert "Generated Rules" in final_content
    assert "More Rules" in final_content
    assert "---" in final_content  # Separator should now exist


@patch("airules.api_clients.AIClientFactory.get_client")
def test_cursor_file_creation(mock_get_client, isolated_fs_with_config):
    """Test that 'airules cursor' creates .cursor/rules/ with a .mdc file."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.return_value = "Generated Rules"
    mock_get_client.return_value = mock_client

    project_path = isolated_fs_with_config
    result = runner.invoke(
        app, ["cursor", "--project-path", str(project_path)], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output
    cursor_file_path = project_path / ".cursor" / "rules" / "security.mdc"
    assert cursor_file_path.exists()
    assert cursor_file_path.read_text() == "Generated Rules"


@patch("airules.api_clients.AIClientFactory.get_client")
def test_cline_file_creation(mock_get_client, isolated_fs_with_config):
    """Test that 'airules cline' creates .cline/rules/ with a .md file."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.return_value = "Generated Rules"
    mock_get_client.return_value = mock_client

    project_path = isolated_fs_with_config
    result = runner.invoke(
        app, ["cline", "--project-path", str(project_path)], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output
    cline_file_path = project_path / ".cline" / "rules" / "security.md"
    assert cline_file_path.exists()
    assert cline_file_path.read_text() == "Generated Rules"


@patch("airules.api_clients.AIClientFactory.get_client")
def test_roo_file_creation(mock_get_client, isolated_fs_with_config):
    """Test that 'airules roo' creates .roo/rules/ with a .md file."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.return_value = "Generated Rules"
    mock_get_client.return_value = mock_client

    project_path = isolated_fs_with_config
    result = runner.invoke(
        app, ["roo", "--project-path", str(project_path)], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output
    roo_file_path = project_path / ".roo" / "rules" / "security.md"
    assert roo_file_path.exists()
    assert roo_file_path.read_text() == "Generated Rules"


@patch("airules.api_clients.AIClientFactory.get_client")
def test_copilot_file_creation(mock_get_client, isolated_fs_with_config):
    """Test that 'airules copilot' creates .github/copilot-python-security.md."""
    # Mock the API client
    mock_client = Mock()
    mock_client.generate_completion.return_value = "Generated Rules"
    mock_get_client.return_value = mock_client

    project_path = isolated_fs_with_config
    result = runner.invoke(
        app, ["copilot", "--project-path", str(project_path)], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output
    # Default lang is 'python', default tag is 'security'
    copilot_file_path = project_path / ".github" / "copilot-python-security.md"
    assert copilot_file_path.exists()
    assert copilot_file_path.read_text() == "Generated Rules"
