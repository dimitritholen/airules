import pytest
from typer.testing import CliRunner
from unittest.mock import patch, ANY
from pathlib import Path

from airules.cli import app
from airules import config

runner = CliRunner()

@pytest.fixture(autouse=True)
def mock_venv_and_config(monkeypatch):
    """Mock venv check and config path for all tests."""
    monkeypatch.setattr('airules.cli.in_virtualenv', lambda: True)
    monkeypatch.setattr('airules.cli.CONFIG_PATH', Path('/tmp/fake_config.nonexistent'))

@pytest.fixture
def isolated_fs_with_config(tmp_path):
    """Provides an isolated filesystem with a default .airulesrc file."""
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Convert string path from runner to a Path object
        temp_dir_path = Path(td)
        config_path = temp_dir_path / config.CONFIG_FILENAME
        with patch('airules.cli.CONFIG_PATH', config_path), \
             patch('airules.config.CONFIG_PATH', config_path):
            runner.invoke(app, ["init"], catch_exceptions=False)
            yield temp_dir_path

def test_init_command(isolated_fs_with_config):
    """Test that the init command runs successfully within an isolated fs."""
    config_path = isolated_fs_with_config / config.CONFIG_FILENAME
    assert config_path.exists()

@patch('airules.cli.run_generation_pipeline')
def test_tool_subcommand_invokes_pipeline(mock_run_pipeline):
    """Test that invoking a tool subcommand (e.g., 'cursor') calls the main pipeline."""
    result = runner.invoke(app, ["cursor", "--primary", "test-model", "--project-path", "/fake"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    mock_run_pipeline.assert_called_once_with(
        tool='cursor',
        primary_model='test-model',
        research=False,
        review_model=None,
        dry_run=False,
        yes=False,
        project_path='/fake'
    )

@patch('airules.cli.write_rules_file')
@patch('airules.cli.validate_with_claude', side_effect=lambda content, model: f"{content}\n- Validated")
@patch('airules.cli.get_openai_rules', return_value="RULES")
@patch('airules.cli.research_with_perplexity', return_value="RESEARCH SUMMARY")
def test_full_pipeline(
    mock_research, mock_get_rules, mock_validate, mock_write_rules, isolated_fs_with_config
):
    """Test the full pipeline with --research and --review flags."""
    project_path = str(isolated_fs_with_config)
    result = runner.invoke(
        app, 
        [
            "cursor", 
            "--research", 
            "--review", "claude-model", 
            "--project-path", project_path
        ],
        catch_exceptions=False
    )

    assert result.exit_code == 0, result.output
    mock_research.assert_called()
    # The research summary is now passed as a keyword argument
    mock_get_rules.assert_called_with(ANY, 'cursor', ANY, ANY, research_summary="RESEARCH SUMMARY")
    mock_validate.assert_called()
    mock_write_rules.assert_called()

    final_content = mock_write_rules.call_args.args[1]
    assert "- Validated" in final_content

def test_pipeline_no_config_fails(tmp_path):
    """Test that the pipeline fails gracefully if no config file exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Don't call init
        result = runner.invoke(app, ["cursor"])
        assert result.exit_code == 1
        assert "No .airulesrc file found" in result.stdout
