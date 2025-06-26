"""Tests for the core codebase analyzer."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from airules.analyzer.core import CodebaseAnalyzer
from airules.analyzer.models import (
    AnalysisResult,
    FileStats,
    LanguageInfo,
    ProjectStructure,
)
from airules.exceptions import FileOperationError


class TestCodebaseAnalyzer:
    """Test cases for CodebaseAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CodebaseAnalyzer()

    def test_init_default_parameters(self):
        """Test analyzer initialization with default parameters."""
        analyzer = CodebaseAnalyzer()
        assert analyzer.file_scanner.max_depth == 10
        assert analyzer.file_scanner.max_files == 10000

    def test_init_custom_parameters(self):
        """Test analyzer initialization with custom parameters."""
        analyzer = CodebaseAnalyzer(max_depth=5, max_files=1000)
        assert analyzer.file_scanner.max_depth == 5
        assert analyzer.file_scanner.max_files == 1000

    def test_analyze_nonexistent_path(self):
        """Test analyze with non-existent path."""
        result = self.analyzer.analyze("/nonexistent/path")

        assert isinstance(result, AnalysisResult)
        assert result.project_path == "/nonexistent/path"
        assert len(result.error_messages) > 0
        assert "does not exist" in result.error_messages[0]
        assert result.is_empty_project

    def test_analyze_file_instead_of_directory(self):
        """Test analyze with file path instead of directory."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            result = self.analyzer.analyze(tmp_file.name)

            assert isinstance(result, AnalysisResult)
            assert len(result.error_messages) > 0
            assert "not a directory" in result.error_messages[0]

    def test_analyze_empty_directory(self):
        """Test analyze with empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.analyzer.analyze(tmp_dir)

            assert isinstance(result, AnalysisResult)
            assert result.project_path == str(Path(tmp_dir).resolve())
            assert len(result.languages) == 0
            assert result.primary_language is None
            assert result.is_empty_project
            assert result.file_stats.total_files == 0

    def test_analyze_python_project(self):
        """Test analyze with a Python project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create Python files
            (tmp_path / "main.py").write_text("import os\nprint('Hello World')")
            (tmp_path / "utils.py").write_text("def helper():\n    return True")
            (tmp_path / "test_main.py").write_text(
                "import unittest\nclass TestMain(unittest.TestCase):\n    pass"
            )
            (tmp_path / "requirements.txt").write_text(
                "requests==2.28.0\npytest==7.0.0"
            )

            # Create directory structure
            src_dir = tmp_path / "src"
            src_dir.mkdir()
            (src_dir / "module.py").write_text("class MyClass:\n    pass")

            tests_dir = tmp_path / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_module.py").write_text(
                "def test_function():\n    assert True"
            )

            result = self.analyzer.analyze(str(tmp_path))

            assert isinstance(result, AnalysisResult)
            assert len(result.error_messages) == 0
            assert not result.is_empty_project
            assert len(result.languages) > 0

            # Check primary language
            assert result.primary_language is not None
            assert result.primary_language.name == "Python"

            # Check file stats
            assert result.file_stats.total_files > 0
            assert result.file_stats.code_files >= 4  # 4 Python files
            assert result.file_stats.test_files >= 2  # 2 test files
            assert result.file_stats.config_files >= 1  # requirements.txt

            # Check structure
            assert result.structure.has_src_dir
            assert result.structure.has_tests_dir
            assert result.structure.has_config_files
            assert len(result.structure.source_directories) > 0
            assert len(result.structure.test_directories) > 0

    def test_analyze_javascript_project(self):
        """Test analyze with a JavaScript project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create JavaScript files
            (tmp_path / "index.js").write_text(
                "console.log('Hello World');\nconst x = 5;"
            )
            (tmp_path / "utils.js").write_text("function helper() {\n  return true;\n}")
            (tmp_path / "index.test.js").write_text(
                "test('example', () => {\n  expect(true).toBe(true);\n});"
            )
            (tmp_path / "package.json").write_text(
                '{"name": "test", "version": "1.0.0"}'
            )

            result = self.analyzer.analyze(str(tmp_path))

            assert isinstance(result, AnalysisResult)
            assert len(result.error_messages) == 0
            assert not result.is_empty_project

            # Check primary language
            assert result.primary_language is not None
            assert result.primary_language.name == "JavaScript"

            # Check framework hints
            assert (
                "Node.js" in result.framework_hints or "npm" in result.framework_hints
            )

    def test_analyze_multilingual_project(self):
        """Test analyze with a multi-language project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create files in multiple languages
            (tmp_path / "main.py").write_text("print('Python')")
            (tmp_path / "script.js").write_text("console.log('JavaScript');")
            (tmp_path / "app.go").write_text(
                'package main\nimport "fmt"\nfunc main() {\n  fmt.Println("Go")\n}'
            )
            (tmp_path / "style.css").write_text("body { color: blue; }")
            (tmp_path / "index.html").write_text("<html><body>Hello</body></html>")

            result = self.analyzer.analyze(str(tmp_path))

            assert isinstance(result, AnalysisResult)
            assert (
                len(result.languages) >= 3
            )  # Python, JavaScript, Go (HTML/CSS might be filtered)
            assert result.is_multilingual
            assert result.primary_language is not None

    def test_detect_languages_nonexistent_path(self):
        """Test detect_languages with non-existent path."""
        with pytest.raises(FileOperationError):
            self.analyzer.detect_languages("/nonexistent/path")

    def test_detect_languages_file_path(self):
        """Test detect_languages with file path instead of directory."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            with pytest.raises(FileOperationError):
                self.analyzer.detect_languages(tmp_file.name)

    def test_detect_languages_success(self):
        """Test successful language detection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create Python files
            (tmp_path / "main.py").write_text("import os")
            (tmp_path / "utils.py").write_text("def func(): pass")

            languages = self.analyzer.detect_languages(str(tmp_path))

            assert isinstance(languages, list)
            assert len(languages) > 0
            assert all(isinstance(lang, LanguageInfo) for lang in languages)
            assert languages[0].name == "Python"
            assert languages[0].file_count == 2

    def test_get_project_summary_empty_project(self):
        """Test project summary for empty project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            summary = self.analyzer.get_project_summary(str(tmp_dir))

            assert isinstance(summary, str)
            assert "Total files: 0" in summary
            assert "No programming languages detected" in summary

    def test_get_project_summary_python_project(self):
        """Test project summary for Python project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create Python files
            (tmp_path / "main.py").write_text("print('Hello')")
            (tmp_path / "test_main.py").write_text("def test(): pass")
            (tmp_path / "README.md").write_text("# Test Project")

            summary = self.analyzer.get_project_summary(str(tmp_path))

            assert isinstance(summary, str)
            assert "Python" in summary
            assert "Total files:" in summary
            assert "Code files:" in summary
            assert "Primary Language: Python" in summary

    def test_get_project_summary_error_handling(self):
        """Test project summary error handling."""
        summary = self.analyzer.get_project_summary("/nonexistent/path")

        assert isinstance(summary, str)
        assert "Analysis failed" in summary

    def test_is_valid_project_nonexistent(self):
        """Test is_valid_project with non-existent path."""
        assert not self.analyzer.is_valid_project("/nonexistent/path")

    def test_is_valid_project_file(self):
        """Test is_valid_project with file path."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            assert not self.analyzer.is_valid_project(tmp_file.name)

    def test_is_valid_project_empty_directory(self):
        """Test is_valid_project with empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            assert not self.analyzer.is_valid_project(str(tmp_dir))

    def test_is_valid_project_with_code(self):
        """Test is_valid_project with code files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "main.py").write_text("print('Hello')")

            assert self.analyzer.is_valid_project(str(tmp_path))

    def test_is_valid_project_with_config(self):
        """Test is_valid_project with config files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "package.json").write_text('{"name": "test"}')

            assert self.analyzer.is_valid_project(str(tmp_path))

    def test_is_valid_project_with_docs(self):
        """Test is_valid_project with documentation files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "README.md").write_text("# Test Project")

            assert self.analyzer.is_valid_project(str(tmp_path))

    def test_get_language_confidence_threshold(self):
        """Test language confidence threshold."""
        threshold = self.analyzer.get_language_confidence_threshold()
        assert isinstance(threshold, float)
        assert 0.0 <= threshold <= 1.0

    def test_filter_significant_languages(self):
        """Test filtering languages by significance."""
        languages = [
            LanguageInfo("Python", 0.8, 10, {".py"}, ".py", ["main.py"]),
            LanguageInfo("JavaScript", 0.15, 2, {".js"}, ".js", ["script.js"]),
            LanguageInfo(
                "CSS", 0.02, 1, {".css"}, ".css", ["style.css"]
            ),  # Below threshold
        ]

        significant = self.analyzer.filter_significant_languages(languages)

        assert len(significant) == 2
        assert significant[0].name == "Python"
        assert significant[1].name == "JavaScript"

    def test_get_recommended_tags_python(self):
        """Test recommended tags for Python project."""
        result = AnalysisResult(
            project_path="/test",
            languages=[LanguageInfo("Python", 0.9, 5, {".py"}, ".py", [])],
            primary_language=LanguageInfo("Python", 0.9, 5, {".py"}, ".py", []),
            structure=ProjectStructure(has_tests_dir=True),
            file_stats=FileStats(test_files=2),
            framework_hints=["pip", "Git"],
        )

        tags = self.analyzer.get_recommended_tags(result)

        assert isinstance(tags, list)
        assert "security" in tags
        assert "best-practices" in tags
        assert "python" in tags
        assert "testing" in tags
        assert "version-control" in tags

    def test_get_recommended_tags_javascript(self):
        """Test recommended tags for JavaScript project."""
        result = AnalysisResult(
            project_path="/test",
            languages=[LanguageInfo("JavaScript", 0.8, 5, {".js"}, ".js", [])],
            primary_language=LanguageInfo("JavaScript", 0.8, 5, {".js"}, ".js", []),
            structure=ProjectStructure(),
            file_stats=FileStats(),
            framework_hints=["Node.js", "Docker"],
        )

        tags = self.analyzer.get_recommended_tags(result)

        assert "javascript" in tags
        assert "node" in tags
        assert "docker" in tags

    def test_get_recommended_tags_multilingual(self):
        """Test recommended tags for multilingual project."""
        result = AnalysisResult(
            project_path="/test",
            languages=[
                LanguageInfo("Python", 0.6, 3, {".py"}, ".py", []),
                LanguageInfo("JavaScript", 0.4, 2, {".js"}, ".js", []),
            ],
            primary_language=LanguageInfo("Python", 0.6, 3, {".py"}, ".py", []),
            structure=ProjectStructure(has_docs_dir=True),
            file_stats=FileStats(),
            framework_hints=[],
        )

        tags = self.analyzer.get_recommended_tags(result)

        assert "polyglot" in tags
        assert "documentation" in tags

    def test_get_recommended_tags_limits_count(self):
        """Test that recommended tags are limited to reasonable count."""
        result = AnalysisResult(
            project_path="/test",
            languages=[LanguageInfo("Python", 0.9, 5, {".py"}, ".py", [])],
            primary_language=LanguageInfo("Python", 0.9, 5, {".py"}, ".py", []),
            structure=ProjectStructure(),
            file_stats=FileStats(),
            framework_hints=[
                "Git",
                "Docker",
                "Node.js",
                "Maven",
                "Gradle",
                "Webpack",
                "Babel",
                "ESLint",
            ],
        )

        tags = self.analyzer.get_recommended_tags(result)

        assert len(tags) <= 10  # Should be limited to 10 tags

    @patch("airules.analyzer.core.logger")
    def test_analyze_with_logging(self, mock_logger):
        """Test that analysis includes proper logging."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "main.py").write_text("print('Hello')")

            self.analyzer.analyze(str(tmp_path))

            # Check that info logs were called
            mock_logger.info.assert_called()

            # Check log content
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Starting analysis" in log for log in log_calls)
            assert any("Analysis complete" in log for log in log_calls)

    @patch("airules.analyzer.core.logger")
    def test_analyze_error_logging(self, mock_logger):
        """Test that analysis errors are properly logged."""
        # Force an error by mocking the file scanner to raise an exception
        with patch.object(self.analyzer.file_scanner, "scan_directory") as mock_scan:
            mock_scan.side_effect = Exception("Test error")

            result = self.analyzer.analyze("/some/path")

            assert len(result.error_messages) > 0
            mock_logger.error.assert_called()

    def test_path_resolution(self):
        """Test that paths are properly resolved to absolute paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Use relative path
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                tmp_path = Path(".")
                (tmp_path / "main.py").write_text("print('Hello')")

                result = self.analyzer.analyze(".")

                # Should resolve to absolute path
                assert os.path.isabs(result.project_path)
                assert Path(result.project_path).resolve() == Path(tmp_dir).resolve()
            finally:
                os.chdir(original_cwd)
