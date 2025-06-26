"""Tests for the file scanner module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from airules.analyzer.file_scanner import FileScanner
from airules.analyzer.models import FileStats, ProjectStructure


class TestFileScanner:
    """Test cases for FileScanner class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scanner = FileScanner()

    def test_init_default_parameters(self):
        """Test scanner initialization with default parameters."""
        scanner = FileScanner()
        assert scanner.max_depth == 10
        assert scanner.max_files == 10000

    def test_init_custom_parameters(self):
        """Test scanner initialization with custom parameters."""
        scanner = FileScanner(max_depth=5, max_files=1000)
        assert scanner.max_depth == 5
        assert scanner.max_files == 1000

    def test_scan_directory_nonexistent(self):
        """Test scanning non-existent directory."""
        with pytest.raises(ValueError, match="Invalid project path"):
            self.scanner.scan_directory("/nonexistent/path")

    def test_scan_directory_file_instead_of_dir(self):
        """Test scanning file instead of directory."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            with pytest.raises(ValueError, match="Invalid project path"):
                self.scanner.scan_directory(tmp_file.name)

    def test_scan_directory_empty(self):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            files_by_ext, structure, stats = self.scanner.scan_directory(tmp_dir)

            assert isinstance(files_by_ext, dict)
            assert len(files_by_ext) == 0
            assert isinstance(structure, ProjectStructure)
            assert isinstance(stats, FileStats)
            assert stats.total_files == 0

    def test_scan_directory_python_project(self):
        """Test scanning Python project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create Python files
            (tmp_path / "main.py").write_text("print('Hello')")
            (tmp_path / "utils.py").write_text("def helper(): pass")
            (tmp_path / "test_main.py").write_text("def test(): pass")

            # Create config files
            (tmp_path / "requirements.txt").write_text("requests==2.28.0")
            (tmp_path / "pyproject.toml").write_text("[tool.poetry]")

            # Create directories
            src_dir = tmp_path / "src"
            src_dir.mkdir()
            (src_dir / "module.py").write_text("class MyClass: pass")

            tests_dir = tmp_path / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_module.py").write_text("def test_func(): pass")

            # Create docs
            (tmp_path / "README.md").write_text("# Project")

            files_by_ext, structure, stats = self.scanner.scan_directory(tmp_dir)

            # Check files by extension
            assert ".py" in files_by_ext
            assert len(files_by_ext[".py"]) == 5  # 5 Python files
            assert ".txt" in files_by_ext
            assert ".toml" in files_by_ext
            assert ".md" in files_by_ext

            # Check structure
            assert structure.has_src_dir
            assert structure.has_tests_dir
            assert structure.has_config_files
            assert len(structure.source_directories) > 0
            assert len(structure.test_directories) > 0
            assert len(structure.config_files) >= 2

            # Check stats
            assert stats.total_files >= 8
            assert stats.code_files >= 5
            assert stats.test_files >= 2
            assert stats.config_files >= 2
            assert stats.documentation_files >= 1

    def test_scan_directory_javascript_project(self):
        """Test scanning JavaScript project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create JavaScript files
            (tmp_path / "index.js").write_text("console.log('Hello');")
            (tmp_path / "utils.js").write_text("function helper() {}")
            (tmp_path / "index.test.js").write_text("test('example', () => {});")

            # Create config files
            (tmp_path / "package.json").write_text('{"name": "test"}')
            (tmp_path / "webpack.config.js").write_text("module.exports = {};")

            # Create node_modules (should be ignored)
            node_modules = tmp_path / "node_modules"
            node_modules.mkdir()
            (node_modules / "some-package").mkdir()
            (node_modules / "some-package" / "index.js").write_text("// ignored")

            files_by_ext, structure, stats = self.scanner.scan_directory(tmp_dir)

            # Check that node_modules was ignored
            js_files = files_by_ext.get(".js", [])
            assert not any("node_modules" in path for path in js_files)

            # Should find the main JS files
            assert len(js_files) >= 3

    def test_scan_directory_with_ignored_directories(self):
        """Test that ignored directories are properly skipped."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create files in ignored directories
            for ignored_dir in [".git", "__pycache__", ".venv", "node_modules"]:
                ignored_path = tmp_path / ignored_dir
                ignored_path.mkdir()
                (ignored_path / "file.py").write_text("# ignored")

            # Create regular file
            (tmp_path / "main.py").write_text("print('Hello')")

            files_by_ext, structure, stats = self.scanner.scan_directory(tmp_dir)

            # Should only find the main file
            assert ".py" in files_by_ext
            assert len(files_by_ext[".py"]) == 1
            assert files_by_ext[".py"][0].endswith("main.py")

    def test_scan_directory_with_ignored_files(self):
        """Test that ignored files are properly skipped."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create ignored files
            (tmp_path / "file.pyc").write_text("# ignored")
            (tmp_path / "file.log").write_text("# ignored")
            (tmp_path / ".hidden").write_text("# ignored")
            (tmp_path / "file.min.js").write_text("# ignored")

            # Create regular files
            (tmp_path / "main.py").write_text("print('Hello')")
            (tmp_path / "script.js").write_text("console.log('Hello');")

            files_by_ext, structure, stats = self.scanner.scan_directory(tmp_dir)

            # Should only find regular files
            assert ".py" in files_by_ext
            assert ".js" in files_by_ext
            assert ".pyc" not in files_by_ext
            assert ".log" not in files_by_ext

    def test_scan_directory_depth_limit(self):
        """Test that depth limit is respected."""
        scanner = FileScanner(max_depth=2)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create nested directories
            deep_path = tmp_path / "level1" / "level2" / "level3" / "level4"
            deep_path.mkdir(parents=True)
            (deep_path / "deep.py").write_text("# deep file")

            # Create file at acceptable depth
            shallow_path = tmp_path / "level1" / "level2"
            (shallow_path / "shallow.py").write_text("# shallow file")

            files_by_ext, structure, stats = scanner.scan_directory(tmp_dir)

            # Should find shallow file but not deep file
            py_files = files_by_ext.get(".py", [])
            assert any("shallow.py" in path for path in py_files)
            assert not any("deep.py" in path for path in py_files)

    def test_scan_directory_file_limit(self):
        """Test that file limit is respected."""
        scanner = FileScanner(max_files=5)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create more files than the limit
            for i in range(10):
                (tmp_path / f"file{i}.py").write_text(f"# file {i}")

            files_by_ext, structure, stats = scanner.scan_directory(tmp_dir)

            # Should respect file limit
            py_files = files_by_ext.get(".py", [])
            assert len(py_files) <= 5

    def test_is_test_file(self):
        """Test test file detection."""
        test_cases = [
            ("test_main.py", True),
            ("main_test.py", True),
            ("test_utils.py", True),
            ("utils.test.js", True),
            ("component.spec.ts", True),
            ("main.py", False),
            ("utils.js", False),
            ("data.txt", False),  # Not a test file
        ]

        for filename, expected in test_cases:
            path = Path(f"/tmp/{filename}")
            result = self.scanner._is_test_file(path)
            assert (
                result == expected
            ), f"Failed for {filename}: expected {expected}, got {result}"

    def test_is_test_file_by_directory(self):
        """Test test file detection by directory."""
        test_path = Path("/project/tests/utils.py")
        regular_path = Path("/project/src/utils.py")

        assert self.scanner._is_test_file(test_path)
        assert not self.scanner._is_test_file(regular_path)

    def test_is_config_file(self):
        """Test config file detection."""
        test_cases = [
            ("package.json", True),
            ("pyproject.toml", True),
            ("requirements.txt", True),
            ("Dockerfile", True),
            ("webpack.config.js", True),
            (".eslintrc.json", True),
            ("main.py", False),
            ("README.md", False),
        ]

        for filename, expected in test_cases:
            path = Path(f"/tmp/{filename}")
            result = self.scanner._is_config_file(path)
            assert (
                result == expected
            ), f"Failed for {filename}: expected {expected}, got {result}"

    def test_is_doc_file(self):
        """Test documentation file detection."""
        test_cases = [
            ("README.md", True),
            ("CHANGELOG.md", True),
            ("LICENSE", True),
            ("AUTHORS.txt", True),
            ("docs.rst", True),
            ("main.py", False),
            ("script.js", False),
        ]

        for filename, expected in test_cases:
            path = Path(f"/tmp/{filename}")
            result = self.scanner._is_doc_file(path)
            assert (
                result == expected
            ), f"Failed for {filename}: expected {expected}, got {result}"

    def test_is_code_file(self):
        """Test code file detection."""
        test_cases = [
            ("main.py", True),
            ("script.js", True),
            ("app.go", True),
            ("program.cpp", True),
            ("README.md", False),
            ("data.json", False),
            ("image.png", False),
        ]

        for filename, expected in test_cases:
            path = Path(f"/tmp/{filename}")
            result = self.scanner._is_code_file(path)
            assert (
                result == expected
            ), f"Failed for {filename}: expected {expected}, got {result}"

    def test_is_text_file(self):
        """Test text file detection."""
        test_cases = [
            ("main.py", True),
            ("script.js", True),
            ("style.css", True),
            ("data.json", True),
            ("config.yaml", True),
            ("Dockerfile", True),
            ("Makefile", True),
            ("README", True),
            ("image.png", False),
            ("binary.exe", False),
        ]

        for filename, expected in test_cases:
            path = Path(f"/tmp/{filename}")
            result = self.scanner._is_text_file(path)
            assert (
                result == expected
            ), f"Failed for {filename}: expected {expected}, got {result}"

    def test_should_ignore_dir(self):
        """Test directory ignore logic."""
        test_cases = [
            (".git", True),
            ("__pycache__", True),
            ("node_modules", True),
            (".venv", True),
            ("build", True),
            (".hidden", True),  # Starts with dot
            ("src", False),
            ("tests", False),
            ("docs", False),
        ]

        for dirname, expected in test_cases:
            path = Path(f"/tmp/{dirname}")
            result = self.scanner._should_ignore_dir(path)
            assert (
                result == expected
            ), f"Failed for {dirname}: expected {expected}, got {result}"

    def test_should_ignore_file(self):
        """Test file ignore logic."""
        test_cases = [
            ("file.pyc", True),
            ("file.log", True),
            (".hidden", True),
            ("file.min.js", True),
            ("main.py", False),
            ("script.js", False),
            (".gitignore", False),  # Config file exception
        ]

        for filename, expected in test_cases:
            path = Path(f"/tmp/{filename}")
            result = self.scanner._should_ignore_file(path)
            assert (
                result == expected
            ), f"Failed for {filename}: expected {expected}, got {result}"

    def test_get_file_content_sample_success(self):
        """Test successful file content sampling."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as tmp_file:
            tmp_file.write("line 1\nline 2\nline 3\n")
            tmp_file.flush()

            try:
                content = self.scanner.get_file_content_sample(
                    tmp_file.name, max_lines=2
                )
                assert content == "line 1\nline 2"
            finally:
                os.unlink(tmp_file.name)

    def test_get_file_content_sample_nonexistent(self):
        """Test file content sampling with non-existent file."""
        content = self.scanner.get_file_content_sample("/nonexistent/file.py")
        assert content is None

    def test_get_file_content_sample_binary_file(self):
        """Test file content sampling with binary file."""
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp_file:
            tmp_file.write(b"\x00\x01\x02\x03")
            tmp_file.flush()

            try:
                content = self.scanner.get_file_content_sample(tmp_file.name)
                assert content is None  # Should return None for binary files
            finally:
                os.unlink(tmp_file.name)

    def test_get_file_content_sample_max_lines(self):
        """Test file content sampling with line limit."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as tmp_file:
            for i in range(100):
                tmp_file.write(f"line {i}\n")
            tmp_file.flush()

            try:
                content = self.scanner.get_file_content_sample(
                    tmp_file.name, max_lines=5
                )
                lines = content.split("\n")
                assert len(lines) == 5
                assert lines[0] == "line 0"
                assert lines[4] == "line 4"
            finally:
                os.unlink(tmp_file.name)

    def test_analyze_structure_empty_project(self):
        """Test structure analysis for empty project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            structure = self.scanner._analyze_structure(Path(tmp_dir), [], [], [])

            assert not structure.has_src_dir
            assert not structure.has_tests_dir
            assert not structure.has_docs_dir
            assert not structure.has_config_files
            assert len(structure.source_directories) == 0
            assert len(structure.test_directories) == 0

    def test_analyze_structure_typical_project(self):
        """Test structure analysis for typical project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create directory structure
            (tmp_path / "src").mkdir()
            (tmp_path / "tests").mkdir()
            (tmp_path / "docs").mkdir()

            # Create files (directories are only detected if they contain files)
            src_file = tmp_path / "src" / "main.py"
            src_file.write_text("print('hello')")
            test_file = tmp_path / "tests" / "test_main.py"
            test_file.write_text("def test(): pass")
            doc_file = tmp_path / "docs" / "README.md"
            doc_file.write_text("# Documentation")
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("[tool.poetry]")

            all_files = [src_file, test_file, doc_file, config_file]
            test_files = [str(test_file)]
            config_files = [str(config_file)]

            structure = self.scanner._analyze_structure(
                tmp_path, all_files, test_files, config_files
            )

            assert structure.has_src_dir
            assert structure.has_tests_dir
            assert structure.has_docs_dir
            assert structure.has_config_files
            assert len(structure.source_directories) > 0
            assert len(structure.test_directories) > 0
            assert len(structure.config_files) > 0

    def test_calculate_stats_comprehensive(self):
        """Test comprehensive file statistics calculation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create various file types
            code_file = tmp_path / "main.py"
            code_file.write_text("print('hello')")

            test_file = tmp_path / "test_main.py"
            test_file.write_text("def test(): pass")

            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("[tool.poetry]")

            doc_file = tmp_path / "README.md"
            doc_file.write_text("# Project")

            all_files = [code_file, test_file, config_file, doc_file]
            test_files = [str(test_file)]
            config_files = [str(config_file)]
            doc_files = [str(doc_file)]

            stats = self.scanner._calculate_stats(
                all_files, test_files, config_files, doc_files
            )

            assert stats.total_files == 4
            assert stats.code_files >= 2  # main.py and test_main.py
            assert stats.test_files == 1
            assert stats.config_files == 1
            assert stats.documentation_files == 1
            assert stats.other_files == 0  # All files are categorized
            assert len(stats.largest_files) <= 5

    def test_walk_directory_permission_error(self):
        """Test directory walking with permission errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a regular file
            (tmp_path / "accessible.py").write_text("print('hello')")

            # Mock a permission error for directory traversal
            original_iterdir = Path.iterdir

            def mock_iterdir(self):
                if "inaccessible" in str(self):
                    raise PermissionError("Access denied")
                return original_iterdir(self)

            with patch.object(Path, "iterdir", mock_iterdir):
                # Create inaccessible directory
                inaccessible_dir = tmp_path / "inaccessible"
                inaccessible_dir.mkdir()

                files_by_ext, structure, stats = self.scanner.scan_directory(tmp_dir)

                # Should continue despite permission error
                assert ".py" in files_by_ext
                assert len(files_by_ext[".py"]) == 1

    def test_reset_file_count_between_scans(self):
        """Test that file count is reset between scans."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "file1.py").write_text("print('1')")

            # First scan
            self.scanner.scan_directory(tmp_dir)
            first_count = self.scanner._file_count

            # Second scan
            self.scanner.scan_directory(tmp_dir)
            second_count = self.scanner._file_count

            # File count should be reset, so both counts should be the same
            assert first_count == second_count

    def test_scanner_constants(self):
        """Test that scanner constants are properly defined."""
        # Check that ignore sets are not empty
        assert len(self.scanner.IGNORE_DIRS) > 0
        assert len(self.scanner.IGNORE_PATTERNS) > 0
        assert len(self.scanner.CODE_EXTENSIONS) > 0
        assert len(self.scanner.CONFIG_PATTERNS) > 0
        assert len(self.scanner.DOC_PATTERNS) > 0

        # Check specific important entries
        assert ".git" in self.scanner.IGNORE_DIRS
        assert "__pycache__" in self.scanner.IGNORE_DIRS
        assert "node_modules" in self.scanner.IGNORE_DIRS

        assert ".py" in self.scanner.CODE_EXTENSIONS
        assert ".js" in self.scanner.CODE_EXTENSIONS
        assert ".ts" in self.scanner.CODE_EXTENSIONS

        assert "*.pyc" in self.scanner.IGNORE_PATTERNS
        assert "*.log" in self.scanner.IGNORE_PATTERNS
