"""Data models for codebase analysis results."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from pathlib import Path


@dataclass
class LanguageInfo:
    """Information about a detected programming language."""
    
    name: str
    confidence: float  # 0.0 to 1.0
    file_count: int
    extensions: Set[str]
    primary_extension: str
    sample_files: List[str]  # Sample file paths for this language


@dataclass
class ProjectStructure:
    """Information about project directory structure."""
    
    has_src_dir: bool = False
    has_tests_dir: bool = False  
    has_docs_dir: bool = False
    has_config_files: bool = False
    test_directories: List[str] = None
    source_directories: List[str] = None
    config_files: List[str] = None
    
    def __post_init__(self):
        if self.test_directories is None:
            self.test_directories = []
        if self.source_directories is None:
            self.source_directories = []
        if self.config_files is None:
            self.config_files = []


@dataclass 
class FileStats:
    """Statistics about project files."""
    
    total_files: int = 0
    code_files: int = 0
    test_files: int = 0
    config_files: int = 0
    documentation_files: int = 0
    other_files: int = 0
    largest_files: List[str] = None  # Paths to largest files
    
    def __post_init__(self):
        if self.largest_files is None:
            self.largest_files = []


@dataclass
class AnalysisResult:
    """Complete result of codebase analysis."""
    
    project_path: str
    languages: List[LanguageInfo]
    primary_language: Optional[LanguageInfo]
    structure: ProjectStructure
    file_stats: FileStats
    framework_hints: List[str]  # Detected frameworks/libraries
    error_messages: List[str] = None  # Any errors encountered during analysis
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []
    
    @property
    def is_empty_project(self) -> bool:
        """Check if this appears to be an empty or minimal project."""
        return self.file_stats.code_files == 0 or len(self.languages) == 0
    
    @property
    def is_multilingual(self) -> bool:
        """Check if project uses multiple programming languages."""
        return len([lang for lang in self.languages if lang.confidence > 0.1]) > 1