import sys
from unittest.mock import patch

import pytest

from airules.venv_check import in_virtualenv, main


def test_in_virtualenv_real_prefix(monkeypatch):
    """Test in_virtualenv returns True when sys.real_prefix is set."""
    # Use monkeypatch.setitem on sys.__dict__ to handle modules where
    # setattr can be problematic for attributes that may not exist.
    monkeypatch.setitem(sys.__dict__, "real_prefix", "/usr")
    assert in_virtualenv() is True


def test_in_virtualenv_base_prefix(monkeypatch):
    """Test in_virtualenv returns True when base_prefix differs from prefix."""
    monkeypatch.delattr(sys, "real_prefix", raising=False)
    monkeypatch.setattr(sys, "base_prefix", "/usr")
    monkeypatch.setattr(sys, "prefix", "/home/user/project/.venv")
    assert in_virtualenv() is True


def test_not_in_virtualenv(monkeypatch):
    """Test in_virtualenv returns False when not in a virtual environment."""
    monkeypatch.delattr(sys, "real_prefix", raising=False)
    monkeypatch.setattr(sys, "base_prefix", sys.prefix)
    assert in_virtualenv() is False


@patch("airules.venv_check.in_virtualenv", return_value=True)
def test_main_in_venv(mock_in_venv, capsys):
    """Test main function prints success message when in a venv."""
    main()
    captured = capsys.readouterr()
    assert "[airules] Virtual environment detected." in captured.out


@patch("airules.venv_check.in_virtualenv", return_value=False)
def test_main_not_in_venv_exits_and_prints_error(mock_in_venv, capsys):
    """Test main function prints error and exits when not in a venv."""
    with pytest.raises(SystemExit) as e:
        main()
    assert e.type == SystemExit
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert (
        "[airules] ERROR: This command must be run in a virtual environment"
        in captured.out
    )
