"""Main analysis engine class for codebase analysis."""

import logging
from pathlib import Path
from typing import List

from ..exceptions import FileOperationError
from .file_scanner import FileScanner
from .language_detector import LanguageDetector
from .models import AnalysisResult, FileStats, LanguageInfo, ProjectStructure

logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """Main analysis engine for analyzing project codebases."""

    def __init__(self, max_depth: int = 10, max_files: int = 10000):
        """
        Initialize the codebase analyzer.

        Args:
            max_depth: Maximum directory depth to scan
            max_files: Maximum number of files to process
        """
        self.file_scanner = FileScanner(max_depth=max_depth, max_files=max_files)
        self.language_detector = LanguageDetector()

    def analyze(self, project_path: str) -> AnalysisResult:
        """
        Perform complete analysis of a project codebase.

        Args:
            project_path: Path to the project root directory

        Returns:
            AnalysisResult containing complete analysis

        Raises:
            FileOperationError: If project path is invalid or inaccessible
        """
        try:
            project_path = str(Path(project_path).resolve())
            logger.info(f"Starting analysis of project: {project_path}")

            # Validate project path
            path_obj = Path(project_path)
            if not path_obj.exists():
                raise FileOperationError(f"Project path does not exist: {project_path}")
            if not path_obj.is_dir():
                raise FileOperationError(
                    f"Project path is not a directory: {project_path}"
                )

            # Scan directory structure
            files_by_extension, structure, file_stats = (
                self.file_scanner.scan_directory(project_path)
            )

            # Detect languages
            languages = self.language_detector.detect_languages(
                files_by_extension, file_scanner=self.file_scanner
            )

            # Determine primary language
            primary_language = self.language_detector.get_primary_language(languages)

            # Detect frameworks and libraries
            framework_hints = self.language_detector.detect_frameworks_and_libraries(
                files_by_extension, file_scanner=self.file_scanner
            )

            # Create analysis result
            result = AnalysisResult(
                project_path=project_path,
                languages=languages,
                primary_language=primary_language,
                structure=structure,
                file_stats=file_stats,
                framework_hints=framework_hints,
            )

            logger.info(
                f"Analysis complete. Found {len(languages)} languages, "
                f"{file_stats.total_files} total files"
            )

            # Log warning for empty projects
            if result.is_empty_project:
                logger.warning("Project appears to be empty or contains no code files")

            return result

        except Exception as e:
            error_msg = f"Analysis failed for {project_path}: {str(e)}"
            logger.error(error_msg)

            # Return partial result with error information
            return AnalysisResult(
                project_path=project_path,
                languages=[],
                primary_language=None,
                structure=ProjectStructure(),
                file_stats=FileStats(),
                framework_hints=[],
                error_messages=[error_msg],
            )

    def detect_languages(self, project_path: str) -> List[LanguageInfo]:
        """
        Detect programming languages in a project.

        Args:
            project_path: Path to the project root directory

        Returns:
            List of LanguageInfo objects sorted by confidence

        Raises:
            FileOperationError: If project path is invalid or inaccessible
        """
        try:
            project_path = str(Path(project_path).resolve())

            # Validate project path
            path_obj = Path(project_path)
            if not path_obj.exists():
                raise FileOperationError(f"Project path does not exist: {project_path}")
            if not path_obj.is_dir():
                raise FileOperationError(
                    f"Project path is not a directory: {project_path}"
                )

            # Scan for files
            files_by_extension, _, _ = self.file_scanner.scan_directory(project_path)

            # Detect languages
            languages = self.language_detector.detect_languages(
                files_by_extension, file_scanner=self.file_scanner
            )

            logger.info(f"Detected {len(languages)} languages in {project_path}")
            return languages

        except Exception as e:
            error_msg = f"Language detection failed for {project_path}: {str(e)}"
            logger.error(error_msg)
            raise FileOperationError(error_msg) from e

    def get_project_summary(self, project_path: str) -> str:
        """
        Get a human-readable summary of the project.

        Args:
            project_path: Path to the project root directory

        Returns:
            Formatted summary string
        """
        try:
            result = self.analyze(project_path)

            if result.error_messages:
                return f"Analysis failed: {'; '.join(result.error_messages)}"

            lines = [f"Project Analysis: {Path(project_path).name}"]
            lines.append("=" * 50)

            # File statistics
            stats = result.file_stats
            lines.append(f"Total files: {stats.total_files}")
            lines.append(f"Code files: {stats.code_files}")
            lines.append(f"Test files: {stats.test_files}")
            lines.append(f"Config files: {stats.config_files}")
            lines.append(f"Documentation files: {stats.documentation_files}")
            lines.append("")

            # Languages
            if result.languages:
                lines.append("Programming Languages:")
                for lang in result.languages[:5]:  # Top 5 languages
                    percentage = lang.confidence * 100
                    lines.append(
                        f"  • {lang.name}: {lang.file_count} files "
                        f"({percentage:.1f}%)"
                    )

                if result.primary_language:
                    lines.append(f"\nPrimary Language: {result.primary_language.name}")
                lines.append("")
            else:
                lines.append("No programming languages detected.\n")

            # Project structure
            structure = result.structure
            lines.append("Project Structure:")
            if structure.has_src_dir:
                lines.append("  • Has source directory")
            if structure.has_tests_dir:
                lines.append("  • Has test directory")
            if structure.has_docs_dir:
                lines.append("  • Has documentation directory")
            if structure.has_config_files:
                lines.append("  • Has configuration files")

            if structure.source_directories:
                lines.append(
                    f"  • Source dirs: {', '.join(structure.source_directories[:3])}"
                )
            if structure.test_directories:
                lines.append(
                    f"  • Test dirs: {', '.join(structure.test_directories[:3])}"
                )
            lines.append("")

            # Frameworks and libraries
            if result.framework_hints:
                lines.append("Detected Frameworks/Tools:")
                for framework in result.framework_hints[:10]:  # Top 10
                    lines.append(f"  • {framework}")
                lines.append("")

            # Project characteristics
            characteristics = []
            if result.is_empty_project:
                characteristics.append("Empty/minimal project")
            if result.is_multilingual:
                characteristics.append("Multi-language project")
            if len(result.languages) == 1:
                characteristics.append("Single-language project")

            if characteristics:
                lines.append("Characteristics:")
                for char in characteristics:
                    lines.append(f"  • {char}")

            return "\n".join(lines)

        except Exception as e:
            return f"Failed to generate project summary: {str(e)}"

    def is_valid_project(self, project_path: str) -> bool:
        """
        Check if the path points to a valid project directory.

        Args:
            project_path: Path to check

        Returns:
            True if path is a valid project directory
        """
        try:
            path_obj = Path(project_path)
            if not path_obj.exists() or not path_obj.is_dir():
                return False

            # Quick scan to see if there are any code files
            files_by_extension, _, stats = self.file_scanner.scan_directory(
                project_path
            )

            # Consider it valid if it has any code files or common project files
            return (
                stats.code_files > 0
                or stats.config_files > 0
                or any(
                    ext in [".md", ".txt", ".rst"] for ext in files_by_extension.keys()
                )
            )

        except Exception:
            return False

    def get_language_confidence_threshold(self) -> float:
        """
        Get the confidence threshold for considering a language significant.

        Returns:
            Confidence threshold (0.0 to 1.0)
        """
        return 0.05  # 5% threshold for significant languages

    def filter_significant_languages(
        self, languages: List[LanguageInfo]
    ) -> List[LanguageInfo]:
        """
        Filter languages by significance threshold.

        Args:
            languages: List of detected languages

        Returns:
            List of significant languages only
        """
        threshold = self.get_language_confidence_threshold()
        return [lang for lang in languages if lang.confidence >= threshold]

    def get_recommended_tags(self, result: AnalysisResult) -> List[str]:
        """
        Get recommended tags for rule generation based on analysis.

        Args:
            result: Analysis result

        Returns:
            List of recommended tag strings
        """
        tags = set()

        # Always include security and best practices
        tags.update(["security", "best-practices"])

        # Language-specific tags
        if result.primary_language:
            lang_name = result.primary_language.name.lower()
            tags.add(lang_name)

            # Language-specific recommendations
            if lang_name == "python":
                tags.update(["pep8", "typing", "testing"])
            elif lang_name in ["javascript", "typescript"]:
                tags.update(["es6", "node", "testing"])
            elif lang_name == "java":
                tags.update(["spring", "junit", "maven"])
            elif lang_name in ["c", "c++"]:
                tags.update(["memory-safety", "performance"])
            elif lang_name == "go":
                tags.update(["concurrency", "performance"])
            elif lang_name == "rust":
                tags.update(["memory-safety", "performance", "cargo"])

        # Framework-specific tags
        for framework in result.framework_hints:
            framework_lower = framework.lower()
            if "docker" in framework_lower:
                tags.add("docker")
            elif framework_lower in ["node.js", "npm", "yarn"]:
                tags.add("node")
            elif framework_lower in ["maven", "gradle"]:
                tags.add("build-tools")
            elif framework_lower == "git":
                tags.add("version-control")

        # Structure-based tags
        if result.structure.has_tests_dir or result.file_stats.test_files > 0:
            tags.add("testing")

        if result.structure.has_docs_dir:
            tags.add("documentation")

        if result.is_multilingual:
            tags.add("polyglot")

        # Filter and sort tags
        recommended = sorted(list(tags))[:10]  # Limit to 10 tags
        return recommended
