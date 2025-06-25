import sys
import os
import pytest
import subprocess
import openai
import anthropic
import sys
import os
import pytest
import subprocess
from unittest.mock import patch
from airules.cli import get_openai_rules, validate_with_claude, write_rules_file, main as cli_main, clean_rules_content
from airules.venv_check import in_virtualenv, main as venv_main

@patch('openai.OpenAI')
def test_get_openai_rules_success(mock_openai, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_client = mock_openai.return_value
    mock_client.chat.completions.create.return_value.choices[0].message.content = 'OpenAI rules'

    rules = get_openai_rules('python', 'cursor', 'pytest')
    assert rules == 'OpenAI rules'

@patch('anthropic.Anthropic')
def test_validate_with_claude_success(mock_anthropic, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_client = mock_anthropic.return_value
    mock_client.messages.create.return_value.content[0].text = 'Claude validated rules'

    rules = validate_with_claude('OpenAI rules')
    assert rules == 'Claude validated rules'

def test_validate_with_claude_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rules = validate_with_claude('Original rules')
    assert rules == 'Original rules'

@patch('airules.cli.get_openai_rules', side_effect=RuntimeError('API Error'))
def test_cli_main_openai_failure(mock_get_rules, monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['airules', '--lang', 'python', '--tool', 'cursor', '--tags', 'pytest'])
    cli_main()
    captured = capsys.readouterr()
    assert "[airules] ✗ ERROR processing tag 'pytest': API Error" in captured.err

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

def test_get_rules_filepath(tmp_path):
    # Test that the new file path logic works correctly for various tags
    test_cases = {
        ('cursor', 'python', 'fastapi'): tmp_path / '.cursor' / 'python_fastapi.mdc',
        ('roo', 'javascript', 'react'): tmp_path / '.roo' / 'javascript_react.md',
        ('claude', 'go', 'gin'): tmp_path / 'CLAUDE.md', # Claude is a special case
        ('other', 'rust', 'coding style'): tmp_path / 'other' / 'rust_coding_style.md',
    }
    from airules.cli import get_rules_filepath
    for (tool, lang, tag), expected_path in test_cases.items():
        filepath = get_rules_filepath(tool, lang, tag, str(tmp_path))
        assert filepath == str(expected_path)

def test_clean_rules_content():
    # Test that markdown fences are removed correctly
    content_with_fences = "```markdown\n- Rule 1\n- Rule 2\n```"
    content_without_fences = "- Rule 1\n- Rule 2"
    assert clean_rules_content(content_with_fences) == content_without_fences
    assert clean_rules_content(content_without_fences) == content_without_fences

def test_venv_check_in_venv(monkeypatch):
    # Simulate being in a virtual environment
    monkeypatch.setattr(sys, 'real_prefix', '/usr', raising=False)
    assert in_virtualenv() is True

def test_venv_check_not_in_venv(monkeypatch):
    # Simulate not being in a virtual environment
    monkeypatch.delattr(sys, 'real_prefix', raising=False)
    monkeypatch.setattr(sys, 'base_prefix', sys.prefix)
    assert in_virtualenv() is False

@patch('airules.cli.write_rules_file')
@patch('airules.cli.get_rules_filepath')
@patch('airules.cli.clean_rules_content', side_effect=lambda x: x)
@patch('airules.cli.validate_with_claude', side_effect=lambda x: x)
@patch('airules.cli.get_openai_rules', return_value="RULES")
def test_cli_main_multiple_tags(mock_get_rules, mock_validate, mock_clean, mock_get_path, mock_write, monkeypatch):
    # Test that the CLI processes multiple tags correctly
    tags = "fastapi,pytest"
    monkeypatch.setattr(sys, 'argv', ['airules', '--lang', 'python', '--tool', 'cursor', '--tags', tags])

    # Make get_rules_filepath return a different path for each tag
    mock_get_path.side_effect = lambda tool, lang, tag, path: f"/{tag}.md"

    cli_main()

    # Check that functions were called for each tag
    assert mock_get_rules.call_count == 2
    assert mock_write.call_count == 2

    # Check that get_openai_rules was called with the correct tags
    mock_get_rules.assert_any_call('python', 'cursor', 'fastapi')
    mock_get_rules.assert_any_call('python', 'cursor', 'pytest')

    # Check that write_rules_file was called with the correct paths
    mock_write.assert_any_call('/fastapi.md', "RULES", False, False)
    mock_write.assert_any_call('/pytest.md', "RULES", False, False)

def test_cli_help():
    result = subprocess.run([sys.executable, '-m', 'airules.cli', '--help'], capture_output=True, text=True)
    assert 'usage:' in result.stdout.lower()
    assert '--lang' in result.stdout
    assert '--tool' in result.stdout
    assert '--tags' in result.stdout
    assert result.returncode == 0
