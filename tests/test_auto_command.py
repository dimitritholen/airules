"""Tests for the auto command functionality."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from airules.analyzer import CodebaseAnalyzer
from airules.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_venv_check(monkeypatch):
    """Mock venv check for all tests."""
    monkeypatch.setattr("airules.venv_check.in_virtualenv", lambda: True)


@pytest.fixture
def mock_api_clients():
    """Mock API clients for testing."""
    mock_client = Mock()
    mock_client.generate_completion.return_value = "# Test Rules\n\nSample rule content"

    with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def python_project_structure(tmp_path):
    """Create a mock Python project structure."""
    # Create Python files
    (tmp_path / "main.py").write_text("print('Hello, World!')")
    (tmp_path / "__init__.py").write_text("")
    (tmp_path / "requirements.txt").write_text("pytest==7.0.0\nflask==2.0.0")

    # Create test directory and files
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_main.py").write_text("def test_something(): pass")
    (test_dir / "__init__.py").write_text("")

    # Create package.json (should not affect Python detection)
    (tmp_path / "package.json").write_text('{"name": "test", "dependencies": {}}')

    return tmp_path


@pytest.fixture
def javascript_project_structure(tmp_path):
    """Create a mock JavaScript project structure."""
    # Create JavaScript files
    (tmp_path / "index.js").write_text("console.log('Hello, World!');")
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "test-project",
                "dependencies": {"express": "^4.18.0", "jest": "^28.0.0"},
                "devDependencies": {"webpack": "^5.0.0"},
            }
        )
    )

    # Create test files
    test_dir = tmp_path / "__tests__"
    test_dir.mkdir()
    (test_dir / "index.test.js").write_text("test('example', () => {});")

    # Create src directory
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.js").write_text("const express = require('express');")

    return tmp_path


@pytest.fixture
def go_project_structure(tmp_path):
    """Create a mock Go project structure."""
    # Create Go files
    (tmp_path / "main.go").write_text(
        'package main\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}'
    )
    (tmp_path / "go.mod").write_text(
        "module example.com/test\n\ngo 1.19\n\nrequire (\n    github.com/gin-gonic/gin v1.9.0\n)"
    )
    (tmp_path / "go.sum").write_text("github.com/gin-gonic/gin v1.9.0 h1:...")

    # Create test files
    (tmp_path / "main_test.go").write_text(
        "package main\n\nfunc TestMain(t *testing.T) {}"
    )

    return tmp_path


class TestCodebaseAnalyzer:
    """Test the CodebaseAnalyzer class."""

    def test_analyze_python_project(self, python_project_structure):
        """Test analysis of a Python project."""
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(str(python_project_structure))

        assert result.primary_language is not None
        assert result.primary_language.name == "Python"

        tags = analyzer.get_recommended_tags(result)
        assert "python" in tags
        assert "testing" in tags  # pytest in requirements.txt

    def test_analyze_javascript_project(self, javascript_project_structure):
        """Test analysis of a JavaScript project."""
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(str(javascript_project_structure))

        assert result.primary_language is not None
        assert result.primary_language.name == "JavaScript"

        tags = analyzer.get_recommended_tags(result)
        assert "javascript" in tags
        assert "testing" in tags  # jest in package.json

    def test_analyze_go_project(self, go_project_structure):
        """Test analysis of a Go project."""
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(str(go_project_structure))

        assert result.primary_language is not None
        assert result.primary_language.name == "Go"

        tags = analyzer.get_recommended_tags(result)
        assert "go" in tags

    def test_analyze_unknown_project(self, tmp_path):
        """Test analysis of project with no detectable characteristics."""
        # Create a directory with no recognizable files
        (tmp_path / "README.txt").write_text("Some readme")
        (tmp_path / "data.csv").write_text("name,value\ntest,123")

        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(str(tmp_path))

        assert result.primary_language is None
        tags = analyzer.get_recommended_tags(result)
        assert "security" in tags  # Always includes security
        assert "best-practices" in tags  # Always includes best-practices

    def test_analyze_nonexistent_path(self):
        """Test analysis of non-existent path."""
        analyzer = CodebaseAnalyzer()

        # The existing analyzer handles errors gracefully and returns a result with errors
        result = analyzer.analyze("/nonexistent/path")
        assert result.error_messages  # Should have error messages
        assert result.primary_language is None

    def test_get_project_summary(self, python_project_structure):
        """Test project summary generation."""
        analyzer = CodebaseAnalyzer()

        summary = analyzer.get_project_summary(str(python_project_structure))
        assert "Project Analysis:" in summary
        assert "Python" in summary


class TestAutoCommand:
    """Test the auto command CLI integration."""

    def test_auto_command_basic_python(
        self, python_project_structure, mock_api_clients
    ):
        """Test basic auto command on Python project."""
        with runner.isolated_filesystem(temp_dir=python_project_structure.parent):
            # Change to the project directory
            import os

            os.chdir(str(python_project_structure))

            result = runner.invoke(app, ["auto", "--dry-run"], catch_exceptions=False)

            assert result.exit_code == 0
            assert "Analyzing project structure" in result.stdout
            assert "Detected language: Python" in result.stdout
            assert "testing" in result.stdout.lower()

    def test_auto_command_specific_tool(
        self, python_project_structure, mock_api_clients
    ):
        """Test auto command with specific tool."""
        with runner.isolated_filesystem(temp_dir=python_project_structure.parent):
            import os

            os.chdir(str(python_project_structure))

            result = runner.invoke(
                app, ["auto", "cursor", "--dry-run"], catch_exceptions=False
            )

            assert result.exit_code == 0
            assert "Processing CURSOR with auto-detected settings" in result.stdout

    def test_auto_command_with_overrides(
        self, python_project_structure, mock_api_clients
    ):
        """Test auto command with manual overrides."""
        with runner.isolated_filesystem(temp_dir=python_project_structure.parent):
            import os

            os.chdir(str(python_project_structure))

            result = runner.invoke(
                app,
                [
                    "auto",
                    "--lang",
                    "go",  # Override detected Python
                    "--tags",
                    "performance,security",  # Override detected tags
                    "--dry-run",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "language=go" in result.stdout
            assert "tags=performance,security" in result.stdout

    def test_auto_command_with_research(
        self, python_project_structure, mock_api_clients
    ):
        """Test auto command with research enabled."""
        # Mock research client
        mock_research_client = Mock()
        mock_research_client.generate_completion.return_value = (
            "Research summary content"
        )

        with patch(
            "airules.api_clients.AIClientFactory.get_research_client"
        ) as mock_research:
            mock_research.return_value = mock_research_client

            with runner.isolated_filesystem(temp_dir=python_project_structure.parent):
                import os

                os.chdir(str(python_project_structure))

                result = runner.invoke(
                    app, ["auto", "--research", "--dry-run"], catch_exceptions=False
                )

                assert result.exit_code == 0
                # Should have called research client
                mock_research_client.generate_completion.assert_called()

    def test_auto_command_with_review(self, python_project_structure, mock_api_clients):
        """Test auto command with review model."""
        with runner.isolated_filesystem(temp_dir=python_project_structure.parent):
            import os

            os.chdir(str(python_project_structure))

            result = runner.invoke(
                app,
                ["auto", "--review", "claude-3-sonnet-20240229", "--dry-run"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            # API client should be called twice (generation + review)
            assert mock_api_clients.generate_completion.call_count >= 2

    def test_auto_command_no_detection_fails(self, tmp_path, mock_api_clients):
        """Test auto command fails gracefully when no language detected."""
        # Create directory with no recognizable files
        (tmp_path / "unknown.xyz").write_text("unknown content")

        with runner.isolated_filesystem(temp_dir=tmp_path.parent):
            import os

            os.chdir(str(tmp_path))

            result = runner.invoke(app, ["auto", "--dry-run"])

            assert result.exit_code == 1
            assert "Unable to detect" in result.stdout

    def test_auto_command_unsupported_tool(
        self, python_project_structure, mock_api_clients
    ):
        """Test auto command with unsupported tool."""
        with runner.isolated_filesystem(temp_dir=python_project_structure.parent):
            import os

            os.chdir(str(python_project_structure))

            result = runner.invoke(app, ["auto", "unsupported-tool", "--dry-run"])

            assert result.exit_code == 1
            assert "Unsupported tool: unsupported-tool" in result.stderr

    def test_auto_command_javascript_project(
        self, javascript_project_structure, mock_api_clients
    ):
        """Test auto command on JavaScript project."""
        with runner.isolated_filesystem(temp_dir=javascript_project_structure.parent):
            import os

            os.chdir(str(javascript_project_structure))

            result = runner.invoke(app, ["auto", "--dry-run"], catch_exceptions=False)

            assert result.exit_code == 0
            assert "Detected language: JavaScript" in result.stdout
            assert "testing" in result.stdout.lower()

    def test_auto_command_go_project(self, go_project_structure, mock_api_clients):
        """Test auto command on Go project."""
        with runner.isolated_filesystem(temp_dir=go_project_structure.parent):
            import os

            os.chdir(str(go_project_structure))

            result = runner.invoke(app, ["auto", "--dry-run"], catch_exceptions=False)

            assert result.exit_code == 0
            assert "Detected language: Go" in result.stdout

    def test_auto_command_with_config_file(
        self, python_project_structure, mock_api_clients
    ):
        """Test auto command with existing config file."""
        with runner.isolated_filesystem(temp_dir=python_project_structure.parent):
            import os

            os.chdir(str(python_project_structure))

            # First create a config file
            runner.invoke(app, ["init"], catch_exceptions=False)

            result = runner.invoke(app, ["auto", "--dry-run"], catch_exceptions=False)

            assert result.exit_code == 0
            assert "Generating auto-detected rules" in result.stdout

    def test_auto_command_no_config_uses_defaults(
        self, python_project_structure, mock_api_clients
    ):
        """Test auto command without config file uses sensible defaults."""
        with runner.isolated_filesystem(temp_dir=python_project_structure.parent):
            import os

            os.chdir(str(python_project_structure))

            result = runner.invoke(app, ["auto", "--dry-run"], catch_exceptions=False)

            assert result.exit_code == 0
            assert "No .rules4rc file found" in result.stdout
            assert "Using default tools: cursor, claude" in result.stdout


class TestAutoCommandEdgeCases:
    """Test edge cases for the auto command."""

    def test_mixed_language_project_detection(self, tmp_path, mock_api_clients):
        """Test project with multiple languages - should detect primary one."""
        # Create files for multiple languages
        (tmp_path / "main.py").write_text("print('Python')")
        (tmp_path / "requirements.txt").write_text("flask==2.0.0")
        (tmp_path / "index.js").write_text("console.log('JavaScript');")
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"express": "^4.0.0"}}'
        )

        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(str(tmp_path))

        # Should detect one primary language
        assert result.primary_language is not None
        assert result.primary_language.name in ["Python", "JavaScript"]

        tags = analyzer.get_recommended_tags(result)
        assert len(tags) > 0

    def test_large_project_depth_limit(self, tmp_path, mock_api_clients):
        """Test that analyzer respects depth limits for large projects."""
        # Create deeply nested structure
        current = tmp_path
        for i in range(10):  # Create 10 levels deep
            current = current / f"level_{i}"
            current.mkdir()
            (current / f"file_{i}.py").write_text(f"# Level {i}")

        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(str(tmp_path))

        # Should still detect Python despite deep nesting
        assert result.primary_language is not None
        assert result.primary_language.name == "Python"

    def test_symlink_handling(self, tmp_path, mock_api_clients):
        """Test handling of symbolic links in project structure."""
        # Create a Python file
        (tmp_path / "main.py").write_text("print('Hello')")

        # Create a symlink (if supported by the system)
        try:
            (tmp_path / "link_to_main.py").symlink_to("main.py")
        except OSError:
            # Skip test if symlinks not supported (e.g., Windows)
            pytest.skip("Symlinks not supported on this system")

        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(str(tmp_path))

        assert result.primary_language is not None
        assert result.primary_language.name == "Python"

    def test_permission_error_handling(self, tmp_path, mock_api_clients):
        """Test graceful handling of permission errors."""
        # Create a directory we can't read (on Unix systems)
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()
        (restricted_dir / "secret.py").write_text("secret_code = 42")

        # Make a regular Python file too
        (tmp_path / "main.py").write_text("print('Hello')")

        try:
            restricted_dir.chmod(0o000)  # Remove all permissions

            analyzer = CodebaseAnalyzer()
            result = analyzer.analyze(str(tmp_path))

            # Should still detect Python from accessible files
            assert result.primary_language is not None
            assert result.primary_language.name == "Python"

        finally:
            # Restore permissions for cleanup
            restricted_dir.chmod(0o755)

    def test_empty_project_directory(self, tmp_path, mock_api_clients):
        """Test handling of completely empty project directory."""
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(str(tmp_path))

        assert result.primary_language is None
        tags = analyzer.get_recommended_tags(result)
        assert "security" in tags  # Always includes security
        assert "best-practices" in tags  # Always includes best-practices
