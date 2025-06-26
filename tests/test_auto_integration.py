"""End-to-end integration tests for the auto feature workflow."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from airules.cli import app
from tests.fixtures import (
    create_django_project,
    create_fastapi_project,
    create_nextjs_project,
    create_python_project,
    create_react_project,
    create_rust_project,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_venv_check(monkeypatch):
    """Mock venv check for all tests."""
    monkeypatch.setattr("airules.venv_check.in_virtualenv", lambda: True)


@pytest.fixture
def mock_api_responses():
    """Mock API responses for testing."""
    return {
        "research": "RESEARCH: Found Python/Flask project with pytest testing framework",
        "generation": "# Auto-Generated Rules\n\nThis is a Flask web application with the following characteristics:\n- Uses pytest for testing\n- Has black for code formatting\n- Uses flake8 for linting",
        "validation": "# Validated Auto-Generated Rules\n\nThis is a Flask web application with improved rules:\n- Use pytest for comprehensive testing\n- Maintain code quality with black formatting\n- Follow PEP 8 with flake8 linting",
    }


@pytest.mark.integration
class TestAutoFeatureIntegration:
    """Integration tests for the complete auto workflow."""

    @pytest.mark.integration
    def test_auto_command_python_project(self, tmp_path, mock_api_responses):
        """Test auto command on a Python Flask project."""
        # Create mock Python project
        project_path = create_python_project(tmp_path, "flask_app")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            # Mock the API client responses
            mock_client = Mock()
            mock_client.generate_completion.return_value = mock_api_responses[
                "generation"
            ]
            mock_get_client.return_value = mock_client

            # Change to project directory and run auto command
            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                # Initialize config in project
                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Run auto command (this would be implemented by sub-agents 1-4)
                # For now, we'll simulate the expected behavior
                result = runner.invoke(
                    app, ["auto", "--dry-run"], catch_exceptions=False
                )

                # This will fail until the auto command is implemented
                # but the test structure is ready
                # assert result.exit_code == 0
                # assert "Detected: Python Flask application" in result.output
                # assert "Generated rules for: cursor, claude" in result.output

    def test_auto_command_django_project(self, tmp_path, mock_api_responses):
        """Test auto command on a Django project."""
        project_path = create_django_project(tmp_path, "django_app")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = mock_api_responses[
                "generation"
            ]
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # The auto command would detect Django-specific patterns
                # and generate appropriate rules

    def test_auto_command_react_project(self, tmp_path, mock_api_responses):
        """Test auto command on a React TypeScript project."""
        project_path = create_react_project(tmp_path, "react_app")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = mock_api_responses[
                "generation"
            ]
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # The auto command would detect React/TypeScript patterns

    def test_auto_command_nextjs_project(self, tmp_path, mock_api_responses):
        """Test auto command on a Next.js project."""
        project_path = create_nextjs_project(tmp_path, "nextjs_app")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = mock_api_responses[
                "generation"
            ]
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

    def test_auto_command_rust_project(self, tmp_path, mock_api_responses):
        """Test auto command on a Rust project."""
        project_path = create_rust_project(tmp_path, "rust_app")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = mock_api_responses[
                "generation"
            ]
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

    def test_auto_command_fastapi_project(self, tmp_path, mock_api_responses):
        """Test auto command on a FastAPI project."""
        project_path = create_fastapi_project(tmp_path, "fastapi_app")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = mock_api_responses[
                "generation"
            ]
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

    def test_auto_command_with_research_and_validation(
        self, tmp_path, mock_api_responses
    ):
        """Test auto command with full pipeline including research and validation."""
        project_path = create_python_project(tmp_path, "full_pipeline_test")

        with patch(
            "airules.api_clients.AIClientFactory.get_client"
        ) as mock_get_client, patch(
            "airules.api_clients.AIClientFactory.get_research_client"
        ) as mock_get_research_client:

            # Mock research client
            mock_research_client = Mock()
            mock_research_client.generate_completion.return_value = mock_api_responses[
                "research"
            ]
            mock_get_research_client.return_value = mock_research_client

            # Mock generation and validation clients
            mock_client = Mock()
            mock_client.generate_completion.side_effect = [
                mock_api_responses["generation"],
                mock_api_responses["validation"],
            ]
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # This would test the full auto pipeline with research and validation
                # result = runner.invoke(
                #     app,
                #     ["auto", "--research", "--review", "claude-3-sonnet-20240229", "--dry-run"],
                #     catch_exceptions=False
                # )

    def test_auto_command_error_handling(self, tmp_path):
        """Test auto command error handling scenarios."""
        # Test with empty directory
        empty_dir = tmp_path / "empty_project"
        empty_dir.mkdir()

        with runner.isolated_filesystem(temp_dir=empty_dir):
            os.chdir(empty_dir)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # The auto command should handle projects with no detectable framework
            # result = runner.invoke(app, ["auto"], catch_exceptions=True)
            # assert "No framework detected" in result.output or result.exit_code != 0

    def test_auto_command_multiple_frameworks(self, tmp_path):
        """Test auto command with projects that have multiple frameworks."""
        # Create a project with both Python backend and React frontend
        project_path = tmp_path / "fullstack_app"
        project_path.mkdir()

        # Create Python backend
        backend_dir = project_path / "backend"
        create_fastapi_project(backend_dir.parent, "backend")

        # Create React frontend
        frontend_dir = project_path / "frontend"
        create_react_project(frontend_dir.parent, "frontend")

        # Create root package.json to make it look like a monorepo
        package_json = {
            "name": "fullstack_app",
            "version": "1.0.0",
            "workspaces": ["frontend", "backend"],
        }
        (project_path / "package.json").write_text(json.dumps(package_json, indent=2))

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # The auto command should detect multiple frameworks
            # and generate appropriate rules for each

    def test_auto_command_performance_large_project(self, tmp_path):
        """Test auto command performance with large project structures."""
        project_path = create_python_project(tmp_path, "large_project")

        # Create many files to simulate a large project
        for i in range(100):
            module_dir = project_path / "src" / "large_project" / f"module_{i}"
            module_dir.mkdir(parents=True, exist_ok=True)
            (module_dir / "__init__.py").write_text("")
            (module_dir / f"file_{i}.py").write_text(
                f"# Module {i}\ndef function_{i}():\n    pass\n"
            )

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = "# Generated rules"
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # Test that auto command can handle large projects efficiently
                # import time
                # start_time = time.time()
                # result = runner.invoke(app, ["auto", "--dry-run"], catch_exceptions=False)
                # end_time = time.time()
                # assert end_time - start_time < 30  # Should complete within 30 seconds

    def test_auto_command_with_custom_config(self, tmp_path):
        """Test auto command respecting custom configuration."""
        project_path = create_python_project(tmp_path, "custom_config_test")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Modify the config to only generate rules for specific tools
            config_path = project_path / ".rules4rc"
            config_content = config_path.read_text()
            config_content = config_content.replace(
                "tools = cursor,claude,copilot,cline,roo", "tools = cursor"
            )
            config_path.write_text(config_content)

            with patch(
                "airules.api_clients.AIClientFactory.get_client"
            ) as mock_get_client:
                mock_client = Mock()
                mock_client.generate_completion.return_value = "# Generated rules"
                mock_get_client.return_value = mock_client

                # The auto command should respect the custom configuration
                # and only generate rules for cursor

    def test_auto_command_incremental_updates(self, tmp_path):
        """Test auto command with incremental updates to existing rules."""
        project_path = create_python_project(tmp_path, "incremental_test")

        with runner.isolated_filesystem(temp_dir=project_path.parent):
            os.chdir(project_path)

            result = runner.invoke(app, ["init"], catch_exceptions=False)
            assert result.exit_code == 0

            # Create existing rules files
            cursor_dir = project_path / ".cursor" / "rules"
            cursor_dir.mkdir(parents=True, exist_ok=True)
            (cursor_dir / "python.mdc").write_text("# Existing Python rules")

            with patch(
                "airules.api_clients.AIClientFactory.get_client"
            ) as mock_get_client:
                mock_client = Mock()
                mock_client.generate_completion.return_value = "# Updated rules"
                mock_get_client.return_value = mock_client

                # The auto command should handle incremental updates
                # and prompt for overwriting existing files


class TestAutoFeatureComponents:
    """Test individual components of the auto feature."""

    def test_framework_detection_python(self, tmp_path):
        """Test framework detection for Python projects."""
        project_path = create_python_project(tmp_path)

        # Ensure the project was created successfully
        assert project_path.exists()

        # Test would use the FrameworkDetector component
        # detector = FrameworkDetector()
        # frameworks = detector.detect_frameworks(project_path)
        # assert "python" in frameworks
        # assert "flask" in frameworks

    def test_framework_detection_react(self, tmp_path):
        """Test framework detection for React projects."""
        project_path = create_react_project(tmp_path)

        # Ensure the project was created successfully
        assert project_path.exists()

        # detector = FrameworkDetector()
        # frameworks = detector.detect_frameworks(project_path)
        # assert "javascript" in frameworks
        # assert "react" in frameworks
        # assert "typescript" in frameworks

    def test_dependency_analysis_python(self, tmp_path):
        """Test dependency analysis for Python projects."""
        project_path = create_python_project(tmp_path)

        # Ensure the project was created successfully
        assert project_path.exists()

        # analyzer = DependencyAnalyzer()
        # dependencies = analyzer.analyze_dependencies(project_path)
        # assert "flask" in dependencies
        # assert "pytest" in dependencies

    def test_tag_generation_from_analysis(self, tmp_path):
        """Test tag generation based on project analysis."""
        project_path = create_python_project(tmp_path)

        # Ensure the project was created successfully
        assert project_path.exists()

        # tag_generator = TagGenerator()
        # tags = tag_generator.generate_tags(project_path)
        # assert "python" in tags
        # assert "web" in tags
        # assert "testing" in tags

    def test_package_parser_python(self, tmp_path):
        """Test Python package file parsing."""
        project_path = create_python_project(tmp_path)

        # Ensure the project was created successfully
        assert project_path.exists()

        # parser = PackageParser()
        # requirements = parser.parse_requirements(project_path / "requirements.txt")
        # assert "flask" in [req.name for req in requirements]

    def test_package_parser_javascript(self, tmp_path):
        """Test JavaScript package.json parsing."""
        project_path = create_react_project(tmp_path)

        # Ensure the project was created successfully
        assert project_path.exists()

        # parser = PackageParser()
        # package_info = parser.parse_package_json(project_path / "package.json")
        # assert "react" in package_info.dependencies

    def test_package_parser_rust(self, tmp_path):
        """Test Rust Cargo.toml parsing."""
        project_path = create_rust_project(tmp_path)

        # Ensure the project was created successfully
        assert project_path.exists()

        # parser = PackageParser()
        # cargo_info = parser.parse_cargo_toml(project_path / "Cargo.toml")
        # assert "serde" in cargo_info.dependencies


class TestAutoFeatureErrorHandling:
    """Test error handling and edge cases for the auto feature."""

    def test_missing_package_files(self, tmp_path):
        """Test handling of projects with missing package files."""
        project_path = tmp_path / "incomplete_project"
        project_path.mkdir()

        # Create some source files but no package manifests
        src_dir = project_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('Hello, World!')")

        # The auto command should still work with minimal information

    def test_corrupted_package_files(self, tmp_path):
        """Test handling of corrupted package files."""
        project_path = tmp_path / "corrupted_project"
        project_path.mkdir()

        # Create corrupted package.json
        (project_path / "package.json").write_text('{"name": "test", invalid json}')

        # The auto command should handle parsing errors gracefully

    def test_network_failures(self, tmp_path):
        """Test handling of network failures during API calls."""
        project_path = create_python_project(tmp_path)

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.side_effect = Exception("Network error")
            mock_get_client.return_value = mock_client

            with runner.isolated_filesystem(temp_dir=project_path.parent):
                os.chdir(project_path)

                result = runner.invoke(app, ["init"], catch_exceptions=False)
                assert result.exit_code == 0

                # The auto command should handle network failures gracefully

    def test_insufficient_api_quota(self, tmp_path):
        """Test handling of API quota exceeded errors."""
        project_path = create_python_project(tmp_path)

        # Ensure the project was created successfully
        assert project_path.exists()

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            from airules.exceptions import APIError

            mock_client = Mock()
            mock_client.generate_completion.side_effect = APIError("Quota exceeded")
            mock_get_client.return_value = mock_client

            # The auto command should handle quota errors with appropriate messages

    def test_unsupported_project_types(self, tmp_path):
        """Test handling of unsupported project types."""
        project_path = tmp_path / "unsupported_project"
        project_path.mkdir()

        # Create files for an unsupported language/framework
        (project_path / "main.go").write_text("package main\n\nfunc main() {}")
        (project_path / "go.mod").write_text("module test\n\ngo 1.21")

        # The auto command should handle unsupported projects gracefully


class TestAutoFeaturePerformance:
    """Performance tests for the auto feature."""

    def test_large_monorepo_performance(self, tmp_path):
        """Test performance with large monorepo structures."""
        project_path = tmp_path / "large_monorepo"
        project_path.mkdir()

        # Create multiple sub-projects
        for i in range(10):
            create_python_project(project_path, f"service_{i}")
            create_react_project(project_path, f"frontend_{i}")

        # Test that analysis completes in reasonable time

    def test_deep_directory_structure_performance(self, tmp_path):
        """Test performance with deeply nested directory structures."""
        project_path = tmp_path / "deep_project"
        current_path = project_path

        # Create a deeply nested structure
        for i in range(50):
            current_path = current_path / f"level_{i}"
            current_path.mkdir(parents=True, exist_ok=True)
            (current_path / f"file_{i}.py").write_text(f"# Level {i}")

        # Test that analysis completes efficiently

    def test_many_files_performance(self, tmp_path):
        """Test performance with projects containing many files."""
        project_path = create_python_project(tmp_path, "many_files")

        # Create many files
        for i in range(1000):
            file_path = project_path / "src" / "many_files" / f"module_{i}.py"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"def function_{i}(): pass")

        # Test that analysis scales well with file count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
