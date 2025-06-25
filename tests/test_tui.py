import pytest
import configparser
from pathlib import Path
from typer.testing import CliRunner
import os

from airules.cli import app as cli_app
from airules.tui import ConfigTUI, Input, Static
from airules import config

# The Textual test harness is not compatible with the trio backend.
# This fixture skips all tests in this file if the backend is trio.
@pytest.fixture(autouse=True)
def skip_trio_backend(anyio_backend):
    if anyio_backend == 'trio':
        pytest.skip('Skipping TUI tests for trio backend.')

runner = CliRunner()

@pytest.fixture
def isolated_fs_with_config(tmp_path):
    """Provides an isolated filesystem with a default .airulesrc file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        runner.invoke(cli_app, ["init"], catch_exceptions=False)
        yield tmp_path
    finally:
        os.chdir(original_cwd)

@pytest.fixture
def isolated_fs_no_config(tmp_path):
    """Provides an isolated filesystem with no config file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(original_cwd)

@pytest.mark.anyio
async def test_tui_loads_config_correctly(isolated_fs_with_config):
    """Test that the TUI loads and displays config values correctly."""
    app = ConfigTUI()
    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.pause()
        lang_input = app.query_one("#settings_language", expect_type=Input)
        assert lang_input.value == "python"

@pytest.mark.anyio
async def test_tui_save_config(isolated_fs_with_config):
    """Test that changing a value and saving updates the config file."""
    app = ConfigTUI()
    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.pause()
        
        lang_input = app.query_one("#settings_language", expect_type=Input)
        lang_input.value = "javascript"
        
        await pilot.click("#save")
        await pilot.pause()
        
        last_static = app.query_one("Static:last-of-type")
        assert "✓ Configuration saved!" in str(last_static.renderable)

        cfg = configparser.ConfigParser()
        cfg.read(isolated_fs_with_config / config.CONFIG_FILENAME)
        assert cfg.get("settings", "language") == "javascript"

@pytest.mark.anyio
async def test_tui_no_config_found(isolated_fs_no_config):
    """Test that the TUI shows an error if no config file is found."""
    app = ConfigTUI()
    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.pause()
        static_widgets = app.query(Static)
        all_text = " ".join([str(widget.renderable) for widget in static_widgets])
        assert "ERROR: .airulesrc not found." in all_text
        assert "Please run [b]airules init[/b] to create one." in all_text
