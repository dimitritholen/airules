"""Project structure scanning utilities for recursive directory analysis."""

import fnmatch
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import FileStats, ProjectStructure


class FileScanner:
    """Utility class for scanning project directory structure."""

    # Common directories to ignore during scanning
    IGNORE_DIRS = {
        ".git",
        ".svn",
        ".hg",
        ".bzr",  # Version control
        "__pycache__",
        ".pytest_cache",
        ".coverage",  # Python
        "node_modules",
        ".npm",
        ".yarn",  # JavaScript/Node
        ".venv",
        "venv",
        "env",
        ".env",  # Virtual environments
        "dist",
        "build",
        "target",
        "out",  # Build outputs
        ".idea",
        ".vscode",
        ".vs",  # IDEs
        ".DS_Store",
        "Thumbs.db",  # OS files
        ".tox",
        ".mypy_cache",
        ".ruff_cache",  # Python tools
    }

    # Common file patterns to ignore
    IGNORE_PATTERNS = {
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",  # Python bytecode
        "*.so",
        "*.dylib",
        "*.dll",  # Shared libraries
        "*.o",
        "*.obj",
        "*.a",
        "*.lib",  # Object files
        "*.log",
        "*.tmp",
        "*.temp",  # Temporary files
        ".DS_Store",
        "Thumbs.db",  # OS files
        "*.min.js",
        "*.min.css",  # Minified files
        "*.bundle.js",
        "*.chunk.js",  # Bundled files
    }

    # File extensions that indicate code files
    CODE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".kt",
        ".scala",
        ".c",
        ".cpp",
        ".cc",
        ".cxx",
        ".h",
        ".hpp",
        ".hxx",
        ".cs",
        ".vb",
        ".fs",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".m",
        ".mm",
        ".pl",
        ".pm",
        ".sh",
        ".ps1",
        ".r",
        ".R",
        ".jl",
        ".lua",
        ".dart",
        ".elm",
        ".clj",
        ".hs",
        ".ml",
        ".nim",
        ".cr",
        ".zig",
        ".v",
        ".odin",
    }

    # File extensions for test files
    TEST_EXTENSIONS = {
        ".test.js",
        ".test.ts",
        ".spec.js",
        ".spec.ts",
        "_test.py",
        "_test.go",
    }
    TEST_PATTERNS = {"test_*.py", "*_test.py", "*_test.go", "*.test.*", "*.spec.*"}

    # Configuration file patterns
    CONFIG_PATTERNS = {
        "package.json",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Cargo.toml",
        "go.mod",
        "build.gradle",
        "pom.xml",
        "composer.json",
        "Gemfile",
        "Podfile",
        "pubspec.yaml",
        "mix.exs",
        "stack.yaml",
        "*.config.js",
        "*.config.ts",
        ".babelrc",
        ".eslintrc*",
        "tsconfig.json",
        "webpack.config.*",
        "rollup.config.*",
        "vite.config.*",
        "Dockerfile",
        "docker-compose.*",
        ".dockerignore",
        "Makefile",
        "CMakeLists.txt",
        "meson.build",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        "*.yml",
        "*.yaml",
        "*.toml",
        "*.ini",
        "*.cfg",
        "*.conf",
    }

    # Documentation file patterns
    DOC_PATTERNS = {
        "README.*",
        "CHANGELOG.*",
        "HISTORY.*",
        "NEWS.*",
        "AUTHORS.*",
        "CONTRIBUTORS.*",
        "LICENSE*",
        "COPYING*",
        "*.md",
        "*.rst",
        "*.txt",
        "*.adoc",
        "*.org",
    }

    def __init__(self, max_depth: int = 10, max_files: int = 10000):
        """
        Initialize file scanner.

        Args:
            max_depth: Maximum directory depth to scan
            max_files: Maximum number of files to process
        """
        self.max_depth = max_depth
        self.max_files = max_files
        self._file_count = 0

    def scan_directory(
        self, project_path: str
    ) -> Tuple[Dict[str, List[str]], ProjectStructure, FileStats]:
        """
        Scan directory structure and categorize files.

        Args:
            project_path: Path to project root directory

        Returns:
            Tuple of (files_by_extension, project_structure, file_stats)
        """
        project_path_obj = Path(project_path).resolve()
        if not project_path_obj.exists() or not project_path_obj.is_dir():
            raise ValueError(f"Invalid project path: {project_path_obj}")

        # Reset file count for each scan
        self._file_count = 0

        files_by_extension: Dict[str, List[str]] = defaultdict(list)
        all_files: List[Path] = []
        test_files: List[str] = []
        config_files: List[str] = []
        doc_files: List[str] = []

        # Scan files recursively
        for file_path in self._walk_directory(project_path_obj, 0):
            if self._file_count >= self.max_files:
                break

            if self._should_ignore_file(file_path):
                continue

            all_files.append(file_path)
            self._file_count += 1

            # Categorize by extension
            extension = file_path.suffix.lower()
            if extension:
                files_by_extension[extension].append(str(file_path))

            # Categorize by file type
            if self._is_test_file(file_path):
                test_files.append(str(file_path))
            elif self._is_config_file(file_path):
                config_files.append(str(file_path))
            elif self._is_doc_file(file_path):
                doc_files.append(str(file_path))

        # Analyze project structure
        structure = self._analyze_structure(
            project_path_obj, all_files, test_files, config_files
        )

        # Calculate file statistics
        stats = self._calculate_stats(all_files, test_files, config_files, doc_files)

        return dict(files_by_extension), structure, stats

    def _walk_directory(self, directory: Path, depth: int):
        """Recursively walk directory with depth limit."""
        if depth > self.max_depth:
            return

        try:
            for item in directory.iterdir():
                if item.is_file():
                    yield item
                elif item.is_dir() and not self._should_ignore_dir(item):
                    yield from self._walk_directory(item, depth + 1)
        except (PermissionError, OSError):
            # Skip directories we can't read
            pass

    def _should_ignore_dir(self, dir_path: Path) -> bool:
        """Check if directory should be ignored."""
        dir_name = dir_path.name
        return dir_name in self.IGNORE_DIRS or dir_name.startswith(".")

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        file_name = file_path.name

        # Check ignore patterns
        for pattern in self.IGNORE_PATTERNS:
            if fnmatch.fnmatch(file_name, pattern):
                return True

        # Ignore hidden files (except common config files)
        if file_name.startswith(".") and not self._is_config_file(file_path):
            return True

        return False

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file."""
        file_name = file_path.name.lower()

        # Check test-specific extensions
        for ext in self.TEST_EXTENSIONS:
            if file_name.endswith(ext):
                return True

        # Check test patterns
        for pattern in self.TEST_PATTERNS:
            if fnmatch.fnmatch(file_name, pattern):
                return True

        # Check if in test directory
        path_parts = [p.lower() for p in file_path.parts]
        return any("test" in part for part in path_parts)

    def _is_config_file(self, file_path: Path) -> bool:
        """Check if file is a configuration file."""
        file_name = file_path.name

        for pattern in self.CONFIG_PATTERNS:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        return False

    def _is_doc_file(self, file_path: Path) -> bool:
        """Check if file is a documentation file."""
        file_name = file_path.name

        for pattern in self.DOC_PATTERNS:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        return False

    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file."""
        return file_path.suffix.lower() in self.CODE_EXTENSIONS

    def _analyze_structure(
        self,
        project_path: Path,
        all_files: List[Path],
        test_files: List[str],
        config_files: List[str],
    ) -> ProjectStructure:
        """Analyze project directory structure."""
        structure = ProjectStructure()

        # Find all directories
        directories = set()
        for file_path in all_files:
            for parent in file_path.parents:
                if parent != project_path:
                    try:
                        rel_path = parent.relative_to(project_path)
                        directories.add(str(rel_path))
                    except ValueError:
                        # parent is not within project_path, skip it
                        break

        # Check for common directory patterns
        dir_names = [d.lower() for d in directories]

        structure.has_src_dir = any("src" in name for name in dir_names)
        structure.has_tests_dir = any("test" in name for name in dir_names)
        structure.has_docs_dir = any("doc" in name for name in dir_names)
        structure.has_config_files = len(config_files) > 0

        # Categorize directories
        for dir_name in directories:
            dir_lower = dir_name.lower()
            if "test" in dir_lower:
                structure.test_directories.append(dir_name)
            elif any(src in dir_lower for src in ["src", "lib", "source"]):
                structure.source_directories.append(dir_name)

        structure.config_files = config_files

        return structure

    def _calculate_stats(
        self,
        all_files: List[Path],
        test_files: List[str],
        config_files: List[str],
        doc_files: List[str],
    ) -> FileStats:
        """Calculate file statistics."""
        stats = FileStats()

        stats.total_files = len(all_files)
        stats.test_files = len(test_files)
        stats.config_files = len(config_files)
        stats.documentation_files = len(doc_files)

        # Count code files
        code_files = [f for f in all_files if self._is_code_file(f)]
        stats.code_files = len(code_files)

        # Other files
        categorized = set(
            test_files + config_files + doc_files + [str(f) for f in code_files]
        )
        stats.other_files = stats.total_files - len(categorized)

        # Find largest files (by line count for text files, by size for others)
        file_sizes = []
        for file_path in all_files[:100]:  # Limit to avoid performance issues
            try:
                if self._is_code_file(file_path) or self._is_doc_file(file_path):
                    # Count lines for text files
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                    file_sizes.append((line_count, str(file_path)))
                else:
                    # Use file size for binary files
                    size = file_path.stat().st_size
                    file_sizes.append((size, str(file_path)))
            except (OSError, UnicodeDecodeError):
                continue

        # Get top 5 largest files
        file_sizes.sort(reverse=True)
        stats.largest_files = [path for _, path in file_sizes[:5]]

        return stats

    def get_file_content_sample(
        self, file_path: str, max_lines: int = 50
    ) -> Optional[str]:
        """
        Get a sample of file content for analysis.

        Args:
            file_path: Path to the file
            max_lines: Maximum number of lines to read

        Returns:
            File content sample or None if file can't be read
        """
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return None

            # Only read text files
            if not self._is_text_file(path):
                return None

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())
                return "\n".join(lines)
        except (OSError, UnicodeDecodeError):
            return None

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file."""
        text_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".kt",
            ".scala",
            ".c",
            ".cpp",
            ".cc",
            ".cxx",
            ".h",
            ".hpp",
            ".hxx",
            ".cs",
            ".vb",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".swift",
            ".m",
            ".mm",
            ".pl",
            ".pm",
            ".sh",
            ".ps1",
            ".r",
            ".R",
            ".jl",
            ".lua",
            ".dart",
            ".elm",
            ".clj",
            ".hs",
            ".ml",
            ".nim",
            ".cr",
            ".zig",
            ".v",
            ".odin",
            ".html",
            ".htm",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".xml",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".md",
            ".rst",
            ".txt",
            ".sql",
            ".dockerfile",
            ".makefile",
            ".gitignore",
            ".editorconfig",
        }

        extension = file_path.suffix.lower()
        return extension in text_extensions or file_path.name.lower() in {
            "dockerfile",
            "makefile",
            "readme",
            "license",
            "changelog",
        }
