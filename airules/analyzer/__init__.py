"""Airules analyzer module for codebase analysis and framework detection."""

# Core analysis engine
from .core import CodebaseAnalyzer
from .language_detector import LanguageDetector  
from .file_scanner import FileScanner

# Data models
from .models import AnalysisResult, LanguageInfo, ProjectStructure, FileStats

# Tag generation system
from .tag_generator import TagGenerator
from .tag_validator import TagValidator
from .data_models import (
    AnalysisResult as TagAnalysisResult,
    FrameworkInfo,
    ProjectType,
    FrameworkCategory,
    DirectoryInfo,
    TestingInfo,
    SecurityInfo,
    DeploymentInfo,
)

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