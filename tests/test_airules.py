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

    rules = get_openai_rules('python', 'cursor', ['pytest'])
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
    with pytest.raises(SystemExit):
        cli_main()
    captured = capsys.readouterr()
    assert "[airules] ERROR: API Error" in captured.err

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
    # Test that the new file path logic works correctly
    test_cases = {
        ('cursor', 'python', ('fastapi',)): tmp_path / '.cursor' / 'python_fastapi.mdc',
        ('roo', 'javascript', ('react',)): tmp_path / '.roo' / 'javascript_react.md',
        ('claude', 'go', ('gin',)): tmp_path / 'CLAUDE.md', # Claude is a special case
        ('other', 'rust', ()): tmp_path / 'other' / 'rust_general.md',
    }
    from airules.cli import get_rules_filepath
    for (tool, lang, tags), expected_path in test_cases.items():
        filepath = get_rules_filepath(tool, lang, tags, str(tmp_path))
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
@patch('airules.cli.get_rules_filepath', return_value='/fake/path.md')
@patch('airules.cli.validate_with_claude', side_effect=lambda rules: rules)
@patch('airules.cli.get_openai_rules', return_value="RULES")
def test_cli_main(mock_get_openai, mock_validate_claude, mock_get_path, mock_write_rules, monkeypatch):
    # Test the main CLI function with mock arguments
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
