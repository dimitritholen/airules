"""Language detection from file extensions and content analysis."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional

from .models import LanguageInfo


class LanguageDetector:
    """Utility class for detecting programming languages in a project."""

    # Mapping of file extensions to languages
    EXTENSION_MAP = {
        # Python
        ".py": "Python",
        ".pyx": "Python",
        ".pyi": "Python",
        ".pyw": "Python",
        # JavaScript/TypeScript
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".mjs": "JavaScript",
        ".cjs": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".d.ts": "TypeScript",
        # Java/JVM
        ".java": "Java",
        ".kt": "Kotlin",
        ".kts": "Kotlin",
        ".scala": "Scala",
        ".sc": "Scala",
        ".groovy": "Groovy",
        ".gradle": "Groovy",
        ".clj": "Clojure",
        ".cljs": "Clojure",
        ".cljc": "Clojure",
        # C/C++
        ".c": "C",
        ".h": "C",
        ".cpp": "C++",
        ".cxx": "C++",
        ".cc": "C++",
        ".c++": "C++",
        ".hpp": "C++",
        ".hxx": "C++",
        ".h++": "C++",
        ".hh": "C++",
        # C#/.NET
        ".cs": "C#",
        ".vb": "Visual Basic",
        ".fs": "F#",
        ".fsx": "F#",
        ".fsi": "F#",
        # Web
        ".html": "HTML",
        ".htm": "HTML",
        ".xhtml": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sass": "Sass",
        ".less": "Less",
        ".php": "PHP",
        # Systems
        ".go": "Go",
        ".rs": "Rust",
        ".zig": "Zig",
        ".v": "V",
        ".odin": "Odin",
        ".nim": "Nim",
        ".cr": "Crystal",
        # Scripting
        ".rb": "Ruby",
        ".pl": "Perl",
        ".pm": "Perl",
        ".lua": "Lua",
        ".tcl": "Tcl",
        ".fish": "Fish",
        ".zsh": "Zsh",
        ".bash": "Bash",
        ".sh": "Shell",
        ".ps1": "PowerShell",
        ".psm1": "PowerShell",
        ".psd1": "PowerShell",
        # Mobile
        ".swift": "Swift",
        ".m": "Objective-C",  # Note: can also be MATLAB, resolved by content analysis
        ".mm": "Objective-C++",
        ".dart": "Dart",
        # Functional
        ".hs": "Haskell",
        ".lhs": "Haskell",
        ".elm": "Elm",
        ".ml": "OCaml",
        ".mli": "OCaml",
        ".re": "Reason",
        ".rei": "Reason",
        ".erl": "Erlang",
        ".hrl": "Erlang",
        ".ex": "Elixir",
        ".exs": "Elixir",
        # Data & Scientific
        ".r": "R",
        ".R": "R",
        ".jl": "Julia",
        ".sql": "SQL",
        ".json": "JSON",
        ".xml": "XML",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        # Config/Markup
        ".dockerfile": "Dockerfile",
        ".md": "Markdown",
        ".rst": "reStructuredText",
        ".tex": "LaTeX",
        ".vim": "Vim script",
    }

    # Content-based language detection patterns
    CONTENT_PATTERNS = {
        "Python": [
            r"^\s*import\s+\w+",
            r"^\s*from\s+\w+\s+import",
            r"^\s*def\s+\w+\s*\(",
            r"^\s*class\s+\w+\s*[\(:]",
            r'^\s*if\s+__name__\s*==\s*[\'"]__main__[\'"]',
            r"print\s*\(",
        ],
        "JavaScript": [
            r"^\s*function\s+\w+\s*\(",
            r"^\s*const\s+\w+\s*=",
            r"^\s*let\s+\w+\s*=",
            r"^\s*var\s+\w+\s*=",
            r"console\.log\s*\(",
            r'require\s*\([\'"]',
            r"module\.exports\s*=",
        ],
        "TypeScript": [
            r"^\s*interface\s+\w+",
            r"^\s*type\s+\w+\s*=",
            r":\s*\w+(\[\]|\|)",
            r"<\w+>",
            r"as\s+\w+",
        ],
        "Java": [
            r"^\s*public\s+class\s+\w+",
            r"^\s*public\s+static\s+void\s+main",
            r"^\s*package\s+[\w\.]+;",
            r"^\s*import\s+[\w\.]+;",
            r"System\.out\.print",
        ],
        "C++": [
            r"#include\s*<[\w\/\.]+>",
            r"^\s*using\s+namespace\s+\w+;",
            r"^\s*class\s+\w+\s*{",
            r"std::\w+",
            r"cout\s*<<",
        ],
        "C": [
            r"#include\s*<[\w\/\.]+\.h>",
            r"^\s*int\s+main\s*\(",
            r"printf\s*\(",
            r"malloc\s*\(",
        ],
        "Go": [
            r"^\s*package\s+\w+",
            r'^\s*import\s+[\'"]',
            r"^\s*func\s+\w+\s*\(",
            r"fmt\.Print",
            r":\s*=",
        ],
        "Rust": [
            r"^\s*fn\s+\w+\s*\(",
            r"^\s*use\s+\w+",
            r"^\s*mod\s+\w+",
            r"println!\s*\(",
            r"let\s+mut\s+\w+",
        ],
        "Ruby": [
            r"^\s*def\s+\w+",
            r"^\s*class\s+\w+",
            r"^\s*module\s+\w+",
            r"puts\s+",
            r'require\s+[\'"]',
        ],
        "PHP": [
            r"<\?php",
            r"^\s*function\s+\w+\s*\(",
            r"^\s*class\s+\w+",
            r"\$\w+",
            r"echo\s+",
        ],
        "Swift": [
            r"^\s*func\s+\w+\s*\(",
            r"^\s*class\s+\w+",
            r"^\s*import\s+\w+",
            r"var\s+\w+:",
            r"let\s+\w+:",
        ],
    }

    # Languages that commonly appear together
    RELATED_LANGUAGES = {
        "JavaScript": ["TypeScript", "HTML", "CSS"],
        "TypeScript": ["JavaScript", "HTML", "CSS"],
        "HTML": ["CSS", "JavaScript", "TypeScript"],
        "CSS": ["HTML", "JavaScript", "SCSS", "Sass"],
        "Python": ["Cython"],
        "C": ["C++"],
        "C++": ["C"],
        "Objective-C": ["Objective-C++", "Swift"],
        "Kotlin": ["Java"],
        "Scala": ["Java"],
    }

    def __init__(self):
        """Initialize the language detector."""
        self._compiled_patterns = {}
        for lang, patterns in self.CONTENT_PATTERNS.items():
            self._compiled_patterns[lang] = [
                re.compile(pattern, re.MULTILINE) for pattern in patterns
            ]

    def detect_languages(
        self, files_by_extension: Dict[str, List[str]], file_scanner=None
    ) -> List[LanguageInfo]:
        """
        Detect programming languages from file extensions and content.

        Args:
            files_by_extension: Dictionary mapping extensions to file lists
            file_scanner: Optional FileScanner instance for content analysis

        Returns:
            List of LanguageInfo objects sorted by confidence
        """
        if not files_by_extension:
            return []

        # Count files by language based on extensions
        language_counts: DefaultDict[str, int] = defaultdict(int)
        language_extensions = defaultdict(set)
        language_files = defaultdict(list)

        total_files = 0
        for ext, files in files_by_extension.items():
            if ext.lower() in self.EXTENSION_MAP:
                lang = self.EXTENSION_MAP[ext.lower()]
                file_count = len(files)
                language_counts[lang] += file_count
                language_extensions[lang].add(ext)
                language_files[lang].extend(files[:5])  # Keep sample files
                total_files += file_count

        if total_files == 0:
            return []

        # Perform content-based analysis for ambiguous cases
        if file_scanner:
            self._refine_with_content_analysis(
                language_counts, language_files, file_scanner
            )

        # Create LanguageInfo objects
        languages = []
        for lang, count in language_counts.items():
            confidence = min(count / total_files, 1.0)

            # Boost confidence for certain patterns
            if lang in ["Python", "JavaScript", "TypeScript"] and confidence > 0.1:
                confidence = min(confidence * 1.2, 1.0)

            # Find primary extension (most common)
            ext_counter: Counter[str] = Counter()
            for file_path in language_files[lang]:
                ext = Path(file_path).suffix.lower()
                if ext:
                    ext_counter[ext] += 1

            primary_ext = ext_counter.most_common(1)[0][0] if ext_counter else ""

            lang_info = LanguageInfo(
                name=lang,
                confidence=confidence,
                file_count=count,
                extensions=language_extensions[lang],
                primary_extension=primary_ext,
                sample_files=language_files[lang][:3],  # Keep top 3 samples
            )
            languages.append(lang_info)

        # Sort by confidence (descending) and file count
        languages.sort(key=lambda x: (x.confidence, x.file_count), reverse=True)

        return languages

    def _refine_with_content_analysis(
        self,
        language_counts: Dict[str, int],
        language_files: Dict[str, List[str]],
        file_scanner,
    ) -> None:
        """Refine language detection using content analysis."""

        # Handle ambiguous cases
        ambiguous_files = []

        # Check for .m files (MATLAB vs Objective-C)
        if "MATLAB" in language_counts and "Objective-C" in language_counts:
            m_files = language_files.get("MATLAB", []) + language_files.get(
                "Objective-C", []
            )
            ambiguous_files.extend([(f, ["MATLAB", "Objective-C"]) for f in m_files])

        # Analyze content for ambiguous files
        for file_path, candidate_langs in ambiguous_files:
            content = file_scanner.get_file_content_sample(file_path, max_lines=100)
            if content:
                detected_lang = self._detect_language_from_content(
                    content, candidate_langs
                )
                if detected_lang:
                    # Adjust counts
                    for lang in candidate_langs:
                        if lang != detected_lang and lang in language_counts:
                            language_counts[lang] -= 1
                            if file_path in language_files.get(lang, []):
                                language_files[lang].remove(file_path)

                    # Boost the detected language
                    if detected_lang not in language_counts:
                        language_counts[detected_lang] = 0
                        language_files[detected_lang] = []
                    language_counts[detected_lang] += 1
                    language_files[detected_lang].append(file_path)

    def _detect_language_from_content(
        self, content: str, candidate_languages: List[str]
    ) -> Optional[str]:
        """
        Detect language from file content.

        Args:
            content: File content sample
            candidate_languages: List of possible languages to check

        Returns:
            Detected language name or None
        """
        if not content.strip():
            return None

        scores = {}

        for lang in candidate_languages:
            if lang in self._compiled_patterns:
                score = 0
                patterns = self._compiled_patterns[lang]

                for pattern in patterns:
                    matches = pattern.findall(content)
                    score += len(matches)

                scores[lang] = score

        # Return language with highest score
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            return best_lang[0] if best_lang[1] > 0 else None

        return None

    def get_primary_language(
        self, languages: List[LanguageInfo]
    ) -> Optional[LanguageInfo]:
        """
        Determine the primary language of a project.

        Args:
            languages: List of detected languages

        Returns:
            Primary language or None if no clear primary language
        """
        if not languages:
            return None

        # Filter out markup/config languages for primary language detection
        code_languages = [
            lang
            for lang in languages
            if lang.name
            not in {
                "HTML",
                "CSS",
                "JSON",
                "YAML",
                "XML",
                "Markdown",
                "TOML",
                "Dockerfile",
                "reStructuredText",
                "LaTeX",
            }
        ]

        if not code_languages:
            # If only markup languages, return the most prominent one
            return languages[0]

        # Primary language should have significant presence
        primary = code_languages[0]

        # Must have at least 10% of files or be clearly dominant
        if primary.confidence >= 0.1 or (
            len(code_languages) > 1
            and primary.confidence > code_languages[1].confidence * 2
        ):
            return primary

        return None

    def detect_frameworks_and_libraries(
        self, files_by_extension: Dict[str, List[str]], file_scanner=None
    ) -> List[str]:
        """
        Detect frameworks and libraries based on file patterns and content.

        Args:
            files_by_extension: Dictionary mapping extensions to file lists
            file_scanner: Optional FileScanner for content analysis

        Returns:
            List of detected framework/library names
        """
        frameworks = set()

        # File-based detection
        all_files = []
        for file_list in files_by_extension.values():
            all_files.extend(file_list)

        file_names = [Path(f).name.lower() for f in all_files]

        # Common framework indicators
        framework_indicators = {
            "package.json": ["Node.js", "npm"],
            "requirements.txt": ["pip"],
            "pyproject.toml": ["Poetry", "pip"],
            "cargo.toml": ["Cargo"],
            "go.mod": ["Go modules"],
            "pom.xml": ["Maven"],
            "build.gradle": ["Gradle"],
            "composer.json": ["Composer"],
            "gemfile": ["Bundler"],
            "pipfile": ["Pipenv"],
            "poetry.lock": ["Poetry"],
            "yarn.lock": ["Yarn"],
            "package-lock.json": ["npm"],
            "dockerfile": ["Docker"],
            "docker-compose.yml": ["Docker Compose"],
            "makefile": ["Make"],
            "cmakelists.txt": ["CMake"],
            "webpack.config.js": ["Webpack"],
            "rollup.config.js": ["Rollup"],
            "vite.config.js": ["Vite"],
            "tsconfig.json": ["TypeScript"],
            ".eslintrc.js": ["ESLint"],
            ".babelrc": ["Babel"],
        }

        for file_name in file_names:
            if file_name in framework_indicators:
                frameworks.update(framework_indicators[file_name])

        # Directory-based detection
        all_paths = [Path(f) for f in all_files]
        dir_names = set()
        for path in all_paths:
            for parent in path.parents:
                dir_names.add(parent.name.lower())

        directory_indicators = {
            "node_modules": ["Node.js"],
            ".git": ["Git"],
            ".svn": ["Subversion"],
            "venv": ["Python venv"],
            ".venv": ["Python venv"],
            "__pycache__": ["Python"],
            "target": ["Maven", "Cargo"],
            "build": ["Build system"],
            "dist": ["Distribution"],
        }

        for dir_name in dir_names:
            if dir_name in directory_indicators:
                frameworks.update(directory_indicators[dir_name])

        return sorted(list(frameworks))

    def is_language_compatible(self, lang1: str, lang2: str) -> bool:
        """
        Check if two languages commonly appear together in projects.

        Args:
            lang1: First language name
            lang2: Second language name

        Returns:
            True if languages are commonly used together
        """
        return lang2 in self.RELATED_LANGUAGES.get(
            lang1, []
        ) or lang1 in self.RELATED_LANGUAGES.get(lang2, [])
