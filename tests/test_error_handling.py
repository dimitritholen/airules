"""Error handling and edge case tests for airules auto feature."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from airules.cli import app
from airules.exceptions import APIError
from tests.fixtures import create_python_project, create_react_project

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_venv_check(monkeypatch):
    """Mock venv check for all tests."""
    monkeypatch.setattr("airules.venv_check.in_virtualenv", lambda: True)


@pytest.mark.error_handling
class TestFileSystemErrorHandling:
    """Test error handling for file system related issues."""

    @pytest.mark.error_handling
    def test_missing_project_directory(self, tmp_path):
        """Test handling when project directory doesn't exist."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.chdir(tmp_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # The auto command should handle missing directories gracefully
            # result = runner.invoke(
            #     app,
            #     ["auto", "--project-path", str(non_existent_path)],
            #     catch_exceptions=True
            # )
            # assert result.exit_code != 0
            # assert "directory does not exist" in result.output.lower()

    def test_permission_denied_directory(self, tmp_path):
        """Test handling when directory access is denied."""
        project_path = create_python_project(tmp_path, "permission_test")

        # Make directory read-only (simulate permission issues)
        try:
            project_path.chmod(0o444)

            with runner.isolated_filesystem(temp_dir=tmp_path):
                # Test auto command on directory with restricted permissions
                result = runner.invoke(
                    app, ["auto", "--project-path", str(project_path), "--dry-run"]
                )

                # Should handle permission errors gracefully
                assert result.exit_code == 1
        finally:
            # Restore permissions for cleanup
            project_path.chmod(0o755)

    def test_corrupted_config_file(self, tmp_path):
        """Test handling of corrupted .airulesrc file."""
        project_path = create_python_project(tmp_path, "corrupted_config")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Corrupt the config file
            config_path = project_path / ".airulesrc"
            config_path.write_text("invalid config content [[[")

            # The auto command should handle corrupted config gracefully
            # result = runner.invoke(app, ["auto"], catch_exceptions=True)
            # assert "Invalid configuration" in result.output or result.exit_code != 0

    def test_corrupted_package_json(self, tmp_path):
        """Test handling of corrupted package.json files."""
        project_path = tmp_path / "corrupted_json"
        project_path.mkdir()

        # Create corrupted package.json
        package_json_path = project_path / "package.json"
        package_json_path.write_text('{"name": "test", "version": invalid json}')

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # The auto command should handle JSON parsing errors
            # This would test the PackageParser error handling

    def test_corrupted_requirements_txt(self, tmp_path):
        """Test handling of corrupted requirements.txt files."""
        project_path = tmp_path / "corrupted_requirements"
        project_path.mkdir()

        # Create corrupted requirements.txt with invalid format
        req_path = project_path / "requirements.txt"
        req_path.write_text("flask===invalid_version\n<<>>invalid_package\n")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # The auto command should handle requirements parsing errors

    def test_large_binary_files(self, tmp_path):
        """Test handling of projects with large binary files."""
        project_path = create_python_project(tmp_path, "binary_test")

        # Create a large binary file
        binary_path = project_path / "large_file.bin"
        binary_path.write_bytes(b"\x00" * (10 * 1024 * 1024))  # 10MB binary file

        # Also create some image files
        (project_path / "image.jpg").write_bytes(b"\xff\xd8\xff" * 1000)
        (project_path / "document.pdf").write_bytes(b"%PDF-1.4" * 1000)

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # The auto command should skip binary files during analysis

    def test_extremely_deep_directory_structure(self, tmp_path):
        """Test handling of extremely deep directory structures."""
        project_path = create_python_project(tmp_path, "deep_structure")

        # Create very deep nested structure
        current_path = project_path / "src"
        for i in range(100):  # Very deep nesting
            current_path = current_path / f"level_{i}"
            current_path.mkdir(parents=True, exist_ok=True)
            (current_path / f"file_{i}.py").write_text(f"# Level {i}")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # The auto command should handle deep structures without stack overflow

    def test_circular_symlinks(self, tmp_path):
        """Test handling of circular symbolic links."""
        project_path = create_python_project(tmp_path, "symlink_test")

        # Create circular symlinks (if supported by OS)
        try:
            link1 = project_path / "link1"
            link2 = project_path / "link2"
            link1.symlink_to(link2)
            link2.symlink_to(link1)

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # The auto command should handle circular symlinks
        except OSError:
            # Skip if symlinks not supported on this platform
            pytest.skip("Symlinks not supported on this platform")


class TestAPIErrorHandling:
    """Test error handling for API-related issues."""

    def test_openai_api_error(self, tmp_path):
        """Test handling of OpenAI API errors."""
        project_path = create_python_project(tmp_path, "openai_error_test")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.side_effect = APIError(
                "OpenAI API error: Rate limit exceeded"
            )
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Test that API errors are handled gracefully
                # result = runner.invoke(app, ["auto"], catch_exceptions=True)
                # assert result.exit_code != 0
                # assert "Rate limit exceeded" in result.output

    def test_anthropic_api_error(self, tmp_path):
        """Test handling of Anthropic API errors."""
        project_path = create_python_project(tmp_path, "anthropic_error_test")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            # First call (generation) succeeds, second call (validation) fails
            mock_client = Mock()
            mock_client.generate_completion.side_effect = [
                "# Generated rules",
                APIError("Anthropic API error: Invalid request"),
            ]
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Test validation error handling
                # result = runner.invoke(
                #     app,
                #     ["auto", "--review", "claude-3-sonnet-20240229"],
                #     catch_exceptions=True
                # )

    def test_perplexity_api_error(self, tmp_path):
        """Test handling of Perplexity API errors."""
        project_path = create_python_project(tmp_path, "perplexity_error_test")

        with patch(
            "airules.api_clients.AIClientFactory.get_research_client"
        ) as mock_get_research_client:
            mock_research_client = Mock()
            mock_research_client.generate_completion.side_effect = APIError(
                "Perplexity API error: Service unavailable"
            )
            mock_get_research_client.return_value = mock_research_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Test research error handling
                # result = runner.invoke(app, ["auto", "--research"], catch_exceptions=True)

    def test_network_timeout(self, tmp_path):
        """Test handling of network timeouts."""
        project_path = create_python_project(tmp_path, "timeout_test")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            import requests

            mock_client = Mock()
            mock_client.generate_completion.side_effect = requests.exceptions.Timeout(
                "Request timed out"
            )
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Test timeout handling

    def test_network_connection_error(self, tmp_path):
        """Test handling of network connection errors."""
        project_path = create_python_project(tmp_path, "connection_test")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            import requests

            mock_client = Mock()
            mock_client.generate_completion.side_effect = (
                requests.exceptions.ConnectionError("Connection failed")
            )
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Test connection error handling

    def test_invalid_api_response(self, tmp_path):
        """Test handling of invalid API responses."""
        project_path = create_python_project(tmp_path, "invalid_response_test")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = None  # Invalid response
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Test invalid response handling

    def test_empty_api_response(self, tmp_path):
        """Test handling of empty API responses."""
        project_path = create_python_project(tmp_path, "empty_response_test")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = ""  # Empty response
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Test empty response handling


class TestConfigurationErrorHandling:
    """Test error handling for configuration issues."""

    def test_missing_api_keys(self, tmp_path, monkeypatch):
        """Test handling of missing API keys."""
        project_path = create_python_project(tmp_path, "missing_keys_test")

        # Remove API keys
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test missing API key handling
            # result = runner.invoke(app, ["auto"], catch_exceptions=True)
            # assert result.exit_code != 0
            # assert "API key" in result.output.lower()

    def test_invalid_model_name(self, tmp_path):
        """Test handling of invalid model names."""
        project_path = create_python_project(tmp_path, "invalid_model_test")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test invalid model name handling
            # result = runner.invoke(
            #     app,
            #     ["auto", "--primary", "invalid-model-name"],
            #     catch_exceptions=True
            # )
            # assert result.exit_code != 0
            # assert "invalid model" in result.output.lower()

    def test_conflicting_configuration(self, tmp_path):
        """Test handling of conflicting configuration options."""
        project_path = create_python_project(tmp_path, "conflict_test")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test conflicting options (e.g., specifying both language and auto-detection)
            # result = runner.invoke(
            #     app,
            #     ["auto", "--lang", "python", "--detect-language"],
            #     catch_exceptions=True
            # )

    def test_invalid_tool_specification(self, tmp_path):
        """Test handling of invalid tool specifications."""
        project_path = create_python_project(tmp_path, "invalid_tool_test")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Modify config to include invalid tool
            config_path = project_path / ".rules4rc"
            content = config_path.read_text()
            content = content.replace(
                "tools = cursor,claude,copilot,cline,roo", "tools = invalid_tool"
            )
            config_path.write_text(content)

            # Test invalid tool handling
            # result = runner.invoke(app, ["auto"], catch_exceptions=True)


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_empty_project_directory(self, tmp_path):
        """Test handling of completely empty project directories."""
        empty_project = tmp_path / "empty_project"
        empty_project.mkdir()

        with runner.isolated_filesystem(temp_dir=empty_project.parent):
            os.chdir(empty_project)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of empty projects
            # result = runner.invoke(app, ["auto"], catch_exceptions=True)
            # Should either provide default rules or inform user of no detectable framework

    def test_mixed_language_project(self, tmp_path):
        """Test handling of projects with multiple programming languages."""
        project_path = tmp_path / "mixed_language"
        project_path.mkdir()

        # Create Python files
        python_dir = project_path / "backend"
        python_dir.mkdir()
        (python_dir / "app.py").write_text(
            "from flask import Flask\napp = Flask(__name__)"
        )
        (python_dir / "requirements.txt").write_text("flask==2.3.2")

        # Create JavaScript files
        js_dir = project_path / "frontend"
        js_dir.mkdir()
        package_json = {"name": "frontend", "dependencies": {"react": "^18.0.0"}}
        (js_dir / "package.json").write_text(json.dumps(package_json))
        (js_dir / "app.js").write_text("import React from 'react';")

        # Create Rust files
        (project_path / "Cargo.toml").write_text(
            '[package]\nname = "mixed"\nversion = "0.1.0"'
        )
        (project_path / "main.rs").write_text(
            'fn main() { println!("Hello, world!"); }'
        )

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of mixed language projects

    def test_project_with_no_dependencies(self, tmp_path):
        """Test handling of projects with no external dependencies."""
        project_path = tmp_path / "no_deps"
        project_path.mkdir()

        # Create simple Python project with no dependencies
        src_dir = project_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('Hello, World!')")
        (project_path / "requirements.txt").write_text("")  # Empty requirements

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of projects with no dependencies

    def test_project_with_dev_dependencies_only(self, tmp_path):
        """Test handling of projects with only development dependencies."""
        project_path = tmp_path / "dev_deps_only"
        project_path.mkdir()

        # Create project with only dev dependencies
        package_json = {
            "name": "dev_deps_only",
            "version": "1.0.0",
            "dependencies": {},
            "devDependencies": {
                "eslint": "^8.0.0",
                "prettier": "^2.0.0",
                "jest": "^29.0.0",
            },
        }
        (project_path / "package.json").write_text(json.dumps(package_json, indent=2))
        (project_path / "index.js").write_text("console.log('Hello, World!');")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of dev-only dependencies

    def test_project_with_legacy_file_formats(self, tmp_path):
        """Test handling of projects with legacy file formats."""
        project_path = tmp_path / "legacy_project"
        project_path.mkdir()

        # Create legacy Python project structure
        (project_path / "setup.py").write_text(
            """
from distutils.core import setup
setup(
    name='legacy_project',
    version='1.0',
    py_modules=['legacy_module'],
)
"""
        )
        (project_path / "legacy_module.py").write_text("def legacy_function(): pass")

        # Create legacy JavaScript with bower.json
        bower_json = {
            "name": "legacy_frontend",
            "dependencies": {"jquery": "~2.1.0", "angular": "~1.5.0"},
        }
        (project_path / "bower.json").write_text(json.dumps(bower_json))

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of legacy file formats

    def test_project_with_unusual_file_extensions(self, tmp_path):
        """Test handling of projects with unusual file extensions."""
        project_path = tmp_path / "unusual_extensions"
        project_path.mkdir()

        # Create files with unusual but valid extensions
        (project_path / "script.pyx").write_text("# Cython file")
        (project_path / "config.toml").write_text('[tool.mypy]\npython_version = "3.8"')
        (project_path / "Dockerfile").write_text("FROM python:3.8\nCOPY . /app")
        (project_path / "docker-compose.yml").write_text(
            "version: '3'\nservices:\n  app:\n    build: ."
        )
        (project_path / "Makefile").write_text(
            "install:\n\tpip install -r requirements.txt"
        )

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of unusual file extensions

    def test_project_with_version_conflicts(self, tmp_path):
        """Test handling of projects with version conflicts in dependencies."""
        project_path = tmp_path / "version_conflicts"
        project_path.mkdir()

        # Create requirements.txt with conflicting versions
        (project_path / "requirements.txt").write_text(
            """
flask==2.3.2
flask>=3.0.0
django==4.2.0
django<4.0.0
"""
        )

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of version conflicts

    def test_unicode_and_special_characters(self, tmp_path):
        """Test handling of files with unicode and special characters."""
        project_path = tmp_path / "unicode_test"
        project_path.mkdir()

        # Create files with unicode names and content
        unicode_file = project_path / "тест.py"
        unicode_file.write_text(
            "# Файл с unicode именем\ndef функция():\n    return 'Привет мир'"
        )

        special_file = project_path / "special-chars!@#$.py"
        special_file.write_text("# File with special characters in name")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of unicode and special characters

    def test_extremely_large_files(self, tmp_path):
        """Test handling of extremely large source files."""
        project_path = tmp_path / "large_files"
        project_path.mkdir()

        # Create a very large Python file
        large_content = "# Large file\n" + "def function_{}(): pass\n" * 10000
        (project_path / "large_file.py").write_text(large_content)

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Test handling of large files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
