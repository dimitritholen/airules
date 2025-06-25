# Test for airules CLI
import subprocess
import sys
import os
import pytest

def test_airules_help():
    result = subprocess.run([sys.executable, 'airules.py', '--help'], capture_output=True, text=True, cwd=os.path.dirname(__file__) or '.')
    assert 'usage:' in result.stdout.lower()
    assert '--lang' in result.stdout
    assert '--tool' in result.stdout
    assert '--tags' in result.stdout
    assert result.returncode == 0
