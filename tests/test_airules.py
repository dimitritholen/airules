import sys
import os
import pytest
import subprocess
import sys
import os
import pytest
import subprocess
from unittest.mock import patch
from airules.cli import get_perplexity_rules, write_rules_file, main as cli_main
from airules.venv_check import in_virtualenv, main as venv_main

def test_get_perplexity_rules_mock():
    out = get_perplexity_rules('python', 'cursor', ['langgraph', 'pytest'])
    assert 'python' in out and 'cursor' in out and 'langgraph' in out and 'pytest' in out

def test_dry_run(tmp_path):
    # Simulate writing rules file with dry-run
    test_file = tmp_path / '.cursor' / 'rules'
    os.makedirs(test_file.parent, exist_ok=True)
    from airules.cli import write_rules_file
    write_rules_file(str(test_file), 'RULES', dry_run=True, yes=True)
    assert not test_file.exists()

def test_overwrite_prompt_yes(monkeypatch, tmp_path):
    test_file = tmp_path / 'CLAUDE.md'
    test_file.write_text('OLD')
    from airules.cli import write_rules_file
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    write_rules_file(str(test_file), 'NEW', dry_run=False, yes=False)
    assert test_file.read_text() == 'NEW'

def test_overwrite_prompt_no(monkeypatch, tmp_path):
    test_file = tmp_path / 'CLAUDE.md'
    test_file.write_text('OLD')
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    write_rules_file(str(test_file), 'NEW', dry_run=False, yes=False)
    assert test_file.read_text() == 'OLD'

def test_tool_to_file_mapping(tmp_path):
    # Test that different tool names map to correct files
    test_cases = {
        'roo': tmp_path / '.roo' / 'rules',
        'claude': tmp_path / 'CLAUDE.md',
        'unknown': tmp_path / 'unknown.rules',
    }
    for tool, expected_file in test_cases.items():
        if not expected_file.parent.exists():
            os.makedirs(expected_file.parent, exist_ok=True)
        write_rules_file(str(expected_file), f'{tool}-rules', dry_run=False, yes=True)
        assert expected_file.exists()

def test_venv_check_in_venv(monkeypatch):
    # Simulate being in a virtual environment
    monkeypatch.setattr(sys, 'real_prefix', '/usr', raising=False)
    assert in_virtualenv() is True

def test_venv_check_not_in_venv(monkeypatch):
    # Simulate not being in a virtual environment
    monkeypatch.delattr(sys, 'real_prefix', raising=False)
    monkeypatch.setattr(sys, 'base_prefix', sys.prefix)
    assert in_virtualenv() is False

@patch('airules.cli.get_perplexity_rules')
@patch('airules.cli.write_rules_file')
def test_cli_main(mock_write_rules, mock_get_rules, monkeypatch):
    # Test the main CLI function with mock arguments
    mock_get_rules.return_value = "RULES"
    monkeypatch.setattr(sys, 'argv', ['airules', '--lang', 'python', '--tool', 'cursor', '--tags', 'pytest'])
    cli_main()
    mock_write_rules.assert_called_once()

def test_cli_help():
    result = subprocess.run([sys.executable, '-m', 'airules.cli', '--help'], capture_output=True, text=True)
    assert 'usage:' in result.stdout.lower()
    assert '--lang' in result.stdout
    assert '--tool' in result.stdout
    assert '--tags' in result.stdout
    assert result.returncode == 0
