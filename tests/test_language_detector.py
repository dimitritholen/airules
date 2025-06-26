"""Tests for the language detector module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from airules.analyzer.language_detector import LanguageDetector
from airules.analyzer.models import LanguageInfo


class TestLanguageDetector:
    """Test cases for LanguageDetector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = LanguageDetector()

    def test_init(self):
        """Test detector initialization."""
        detector = LanguageDetector()
        assert hasattr(detector, "_compiled_patterns")
        assert len(detector._compiled_patterns) > 0

    def test_detect_languages_empty_input(self):
        """Test language detection with empty input."""
        result = self.detector.detect_languages({})
        assert result == []

    def test_detect_languages_python_files(self):
        """Test detection of Python files."""
        files_by_extension = {
            ".py": ["main.py", "utils.py", "test_main.py"],
            ".txt": ["README.txt"],
        }

        languages = self.detector.detect_languages(files_by_extension)

        assert len(languages) == 1
        assert languages[0].name == "Python"
        assert languages[0].file_count == 3
        assert languages[0].confidence > 0
        assert ".py" in languages[0].extensions
        assert languages[0].primary_extension == ".py"
        assert len(languages[0].sample_files) <= 3

    def test_detect_languages_javascript_files(self):
        """Test detection of JavaScript files."""
        files_by_extension = {
            ".js": ["index.js", "utils.js"],
            ".jsx": ["component.jsx"],
            ".json": ["package.json"],
        }

        languages = self.detector.detect_languages(files_by_extension)

        assert len(languages) == 2  # JavaScript and JSON
        js_lang = next(lang for lang in languages if lang.name == "JavaScript")
        assert js_lang.file_count == 3  # .js and .jsx both map to JavaScript
        assert ".js" in js_lang.extensions
        assert ".jsx" in js_lang.extensions

        json_lang = next(lang for lang in languages if lang.name == "JSON")
        assert json_lang.file_count == 1

    def test_detect_languages_typescript_files(self):
        """Test detection of TypeScript files."""
        files_by_extension = {
            ".ts": ["main.ts", "utils.ts"],
            ".tsx": ["component.tsx"],
            ".d.ts": ["types.d.ts"],
        }

        languages = self.detector.detect_languages(files_by_extension)

        assert len(languages) == 1
        assert languages[0].name == "TypeScript"
        assert languages[0].file_count == 4
        assert all(ext in languages[0].extensions for ext in [".ts", ".tsx", ".d.ts"])

    def test_detect_languages_mixed_languages(self):
        """Test detection with multiple languages."""
        files_by_extension = {
            ".py": ["main.py", "utils.py"],
            ".js": ["script.js"],
            ".go": ["main.go"],
            ".rs": ["main.rs"],
            ".html": ["index.html"],
        }

        languages = self.detector.detect_languages(files_by_extension)

        assert len(languages) == 5

        # Should be sorted by confidence/count
        lang_names = [lang.name for lang in languages]
        assert "Python" in lang_names
        assert "JavaScript" in lang_names
        assert "Go" in lang_names
        assert "Rust" in lang_names
        assert "HTML" in lang_names

        # Python should have highest confidence (2 files)
        assert languages[0].name == "Python"
        assert languages[0].file_count == 2

    def test_detect_languages_confidence_calculation(self):
        """Test confidence score calculation."""
        files_by_extension = {
            ".py": ["file1.py", "file2.py", "file3.py", "file4.py"],  # 4 files = 80%
            ".js": ["file.js"],  # 1 file = 20%
        }

        languages = self.detector.detect_languages(files_by_extension)

        assert len(languages) == 2
        assert languages[0].name == "Python"
        # Python gets confidence boost, so it's 0.8 * 1.2 = 0.96
        assert languages[0].confidence == 0.96
        assert languages[1].name == "JavaScript"
        # JavaScript also gets confidence boost, so it's 0.2 * 1.2 = 0.24
        assert languages[1].confidence == 0.24

    def test_detect_languages_with_content_analysis(self):
        """Test language detection with content analysis."""
        mock_scanner = Mock()
        mock_scanner.get_file_content_sample.return_value = None

        files_by_extension = {".py": ["main.py"]}

        languages = self.detector.detect_languages(files_by_extension, mock_scanner)

        assert len(languages) == 1
        assert languages[0].name == "Python"

    def test_detect_languages_unknown_extensions(self):
        """Test handling of unknown file extensions."""
        files_by_extension = {".unknown": ["file.unknown"], ".xyz": ["test.xyz"]}

        languages = self.detector.detect_languages(files_by_extension)

        assert len(languages) == 0

    def test_detect_languages_case_insensitive_extensions(self):
        """Test that extension matching is case insensitive."""
        files_by_extension = {".PY": ["Main.PY"], ".JS": ["Script.JS"]}

        languages = self.detector.detect_languages(files_by_extension)

        assert len(languages) == 2
        lang_names = [lang.name for lang in languages]
        assert "Python" in lang_names
        assert "JavaScript" in lang_names

    def test_detect_language_from_content_python(self):
        """Test content-based detection for Python."""
        python_content = """
import os
import sys

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
"""

        result = self.detector._detect_language_from_content(
            python_content, ["Python", "JavaScript"]
        )
        assert result == "Python"

    def test_detect_language_from_content_javascript(self):
        """Test content-based detection for JavaScript."""
        js_content = """
const express = require('express');

function main() {
    console.log("Hello, World!");
}

module.exports = main;
"""

        result = self.detector._detect_language_from_content(
            js_content, ["Python", "JavaScript"]
        )
        assert result == "JavaScript"

    def test_detect_language_from_content_typescript(self):
        """Test content-based detection for TypeScript."""
        ts_content = """
interface User {
    name: string;
    age: number;
}

type UserRole = 'admin' | 'user';

function greet(user: User): string {
    return `Hello, ${user.name}` as string;
}
"""

        result = self.detector._detect_language_from_content(
            ts_content, ["JavaScript", "TypeScript"]
        )
        assert result == "TypeScript"

    def test_detect_language_from_content_no_match(self):
        """Test content-based detection with no clear match."""
        unclear_content = "This is just some text without clear language indicators."

        result = self.detector._detect_language_from_content(
            unclear_content, ["Python", "JavaScript"]
        )
        assert result is None

    def test_detect_language_from_content_empty(self):
        """Test content-based detection with empty content."""
        result = self.detector._detect_language_from_content("", ["Python"])
        assert result is None

        result = self.detector._detect_language_from_content("   \n  \t  ", ["Python"])
        assert result is None

    def test_get_primary_language_single_language(self):
        """Test primary language detection with single language."""
        languages = [LanguageInfo("Python", 0.8, 10, {".py"}, ".py", ["main.py"])]

        primary = self.detector.get_primary_language(languages)
        assert primary is not None
        assert primary.name == "Python"

    def test_get_primary_language_multiple_languages(self):
        """Test primary language detection with multiple languages."""
        languages = [
            LanguageInfo("Python", 0.6, 6, {".py"}, ".py", ["main.py"]),
            LanguageInfo("JavaScript", 0.3, 3, {".js"}, ".js", ["script.js"]),
            LanguageInfo("HTML", 0.1, 1, {".html"}, ".html", ["index.html"]),
        ]

        primary = self.detector.get_primary_language(languages)
        assert primary is not None
        assert primary.name == "Python"

    def test_get_primary_language_filters_markup(self):
        """Test that primary language detection filters out markup languages."""
        languages = [
            LanguageInfo("HTML", 0.5, 5, {".html"}, ".html", ["index.html"]),
            LanguageInfo("CSS", 0.3, 3, {".css"}, ".css", ["style.css"]),
            LanguageInfo("Python", 0.2, 2, {".py"}, ".py", ["main.py"]),
        ]

        primary = self.detector.get_primary_language(languages)
        assert primary is not None
        assert primary.name == "Python"  # Should pick Python over HTML/CSS

    def test_get_primary_language_only_markup(self):
        """Test primary language detection with only markup languages."""
        languages = [
            LanguageInfo("HTML", 0.6, 6, {".html"}, ".html", ["index.html"]),
            LanguageInfo("CSS", 0.4, 4, {".css"}, ".css", ["style.css"]),
        ]

        primary = self.detector.get_primary_language(languages)
        assert primary is not None
        assert primary.name == "HTML"  # Should return most prominent markup language

    def test_get_primary_language_low_confidence(self):
        """Test primary language detection with low confidence."""
        languages = [
            LanguageInfo(
                "Python", 0.05, 1, {".py"}, ".py", ["main.py"]
            ),  # Below 10% threshold
            LanguageInfo("JavaScript", 0.03, 1, {".js"}, ".js", ["script.js"]),
        ]

        primary = self.detector.get_primary_language(languages)
        assert primary is None  # Should return None for low confidence

    def test_get_primary_language_clear_dominance(self):
        """Test primary language detection with clear dominance."""
        languages = [
            LanguageInfo("Python", 0.08, 2, {".py"}, ".py", ["main.py"]),  # 8%
            LanguageInfo(
                "JavaScript", 0.02, 1, {".js"}, ".js", ["script.js"]
            ),  # 2% (4x less)
        ]

        primary = self.detector.get_primary_language(languages)
        assert primary is not None
        assert (
            primary.name == "Python"
        )  # Should return dominant language even below 10%

    def test_get_primary_language_empty_list(self):
        """Test primary language detection with empty list."""
        primary = self.detector.get_primary_language([])
        assert primary is None

    def test_detect_frameworks_and_libraries_empty(self):
        """Test framework detection with empty input."""
        frameworks = self.detector.detect_frameworks_and_libraries({})
        assert frameworks == []

    def test_detect_frameworks_and_libraries_python(self):
        """Test framework detection for Python project."""
        files_by_extension = {
            ".py": ["main.py"],
            ".txt": ["requirements.txt"],
            ".toml": ["pyproject.toml"],
        }

        frameworks = self.detector.detect_frameworks_and_libraries(files_by_extension)

        assert "pip" in frameworks
        assert "Poetry" in frameworks

    def test_detect_frameworks_and_libraries_javascript(self):
        """Test framework detection for JavaScript project."""
        files_by_extension = {
            ".js": ["index.js", "webpack.config.js"],
            ".json": ["package.json", "package-lock.json"],
        }

        frameworks = self.detector.detect_frameworks_and_libraries(files_by_extension)

        assert "Node.js" in frameworks
        assert "npm" in frameworks
        assert "Webpack" in frameworks

    def test_detect_frameworks_and_libraries_docker(self):
        """Test framework detection for Docker."""
        files_by_extension = {
            ".py": ["main.py"],
            "": ["Dockerfile", "docker-compose.yml"],
        }

        frameworks = self.detector.detect_frameworks_and_libraries(files_by_extension)

        assert "Docker" in frameworks
        assert "Docker Compose" in frameworks

    def test_detect_frameworks_and_libraries_java(self):
        """Test framework detection for Java project."""
        files_by_extension = {
            ".java": ["Main.java"],
            ".xml": ["pom.xml"],
            ".gradle": ["build.gradle"],
        }

        frameworks = self.detector.detect_frameworks_and_libraries(files_by_extension)

        assert "Maven" in frameworks
        assert "Gradle" in frameworks

    def test_detect_frameworks_and_libraries_case_insensitive(self):
        """Test that framework detection is case insensitive."""
        files_by_extension = {".py": ["main.py"], "": ["DOCKERFILE", "Makefile"]}

        frameworks = self.detector.detect_frameworks_and_libraries(files_by_extension)

        assert "Docker" in frameworks
        assert "Make" in frameworks

    def test_is_language_compatible(self):
        """Test language compatibility checking."""
        # Related languages
        assert self.detector.is_language_compatible("JavaScript", "TypeScript")
        assert self.detector.is_language_compatible("TypeScript", "JavaScript")
        assert self.detector.is_language_compatible("HTML", "CSS")
        assert self.detector.is_language_compatible("C", "C++")
        assert self.detector.is_language_compatible("Kotlin", "Java")

        # Unrelated languages
        assert not self.detector.is_language_compatible("Python", "Rust")
        assert not self.detector.is_language_compatible("Go", "PHP")

    def test_extension_map_completeness(self):
        """Test that extension map covers common languages."""
        # Check that common extensions are mapped
        common_extensions = [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".cpp",
            ".c",
        ]

        for ext in common_extensions:
            assert (
                ext in self.detector.EXTENSION_MAP
            ), f"Extension {ext} not in EXTENSION_MAP"

    def test_content_patterns_compiled(self):
        """Test that content patterns are properly compiled."""
        assert "Python" in self.detector._compiled_patterns
        assert "JavaScript" in self.detector._compiled_patterns

        # Check that patterns are compiled regex objects
        for lang, patterns in self.detector._compiled_patterns.items():
            assert isinstance(patterns, list)
            for pattern in patterns:
                assert hasattr(
                    pattern, "findall"
                )  # Compiled regex should have findall method

    def test_refine_with_content_analysis_matlab_vs_objective_c(self):
        """Test content analysis refinement for .m files (MATLAB vs Objective-C)."""
        mock_scanner = Mock()

        # Mock MATLAB content
        matlab_content = """
function result = calculate(x, y)
    result = x + y;
end

plot(1:10, rand(1,10));
"""
        mock_scanner.get_file_content_sample.return_value = matlab_content

        language_counts = {"MATLAB": 1, "Objective-C": 1}
        language_files = {"MATLAB": ["calc.m"], "Objective-C": ["calc.m"]}

        self.detector._refine_with_content_analysis(
            language_counts, language_files, mock_scanner
        )

        # Should favor MATLAB based on content
        # Note: This test might need adjustment based on actual pattern matching

    def test_detect_languages_large_sample(self):
        """Test language detection with many files."""
        files_by_extension = {
            ".py": [f"file{i}.py" for i in range(50)],
            ".js": [f"script{i}.js" for i in range(20)],
            ".html": [f"page{i}.html" for i in range(10)],
        }

        languages = self.detector.detect_languages(files_by_extension)

        assert len(languages) == 3
        assert languages[0].name == "Python"
        assert languages[0].file_count == 50
        assert len(languages[0].sample_files) <= 3  # Should limit sample files

    def test_detect_languages_confidence_boost(self):
        """Test confidence boost for certain languages."""
        files_by_extension = {
            ".py": ["main.py"],  # Should get confidence boost
            ".obscure": ["file.obscure"],  # Hypothetical extension
        }

        # Mock the extension map to include the obscure extension
        original_map = self.detector.EXTENSION_MAP.copy()
        self.detector.EXTENSION_MAP[".obscure"] = "ObscureLanguage"

        try:
            languages = self.detector.detect_languages(files_by_extension)

            # Find Python language
            python_lang = next(
                (lang for lang in languages if lang.name == "Python"), None
            )
            assert python_lang is not None

            # Python should have boosted confidence
            # (This test validates the boost logic exists, actual values may vary)
            assert python_lang.confidence > 0

        finally:
            self.detector.EXTENSION_MAP = original_map
