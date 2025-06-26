"""Airules analyzer module for codebase analysis and framework detection."""

# Core analysis engine
from .core import CodebaseAnalyzer
from .data_models import AnalysisResult as TagAnalysisResult
from .data_models import (
    DeploymentInfo,
    DirectoryInfo,
    FrameworkCategory,
    FrameworkInfo,
    ProjectType,
    SecurityInfo,
    TestingInfo,
)
from .file_scanner import FileScanner
from .language_detector import LanguageDetector

# Data models
from .models import AnalysisResult, FileStats, LanguageInfo, ProjectStructure

# Tag generation system
from .tag_generator import TagGenerator
from .tag_validator import TagValidator

# Legacy imports for backward compatibility (if they exist)
try:
    from .dependency_analyzer import DependencyAnalyzer
    from .framework_detector import FrameworkDetector
    from .package_parser import PackageParser

    _legacy_imports = ["DependencyAnalyzer", "FrameworkDetector", "PackageParser"]
except ImportError:
    _legacy_imports = []

__all__ = [
    "CodebaseAnalyzer",
    "LanguageDetector",
    "FileScanner",
    "AnalysisResult",
    "LanguageInfo",
    "ProjectStructure",
    "FileStats",
    "TagGenerator",
    "TagValidator",
    "TagAnalysisResult",
    "FrameworkInfo",
    "ProjectType",
    "FrameworkCategory",
    "DirectoryInfo",
    "TestingInfo",
    "SecurityInfo",
    "DeploymentInfo",
] + _legacy_imports
