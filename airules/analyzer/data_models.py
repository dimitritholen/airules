"""Data models for project analysis and tag generation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class ProjectType(Enum):
    """Enumeration of project types."""

    WEB_FRONTEND = "web_frontend"
    WEB_BACKEND = "web_backend"
    FULLSTACK = "fullstack"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    CLI = "cli"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    MONOLITH = "monolith"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    DEVOPS = "devops"
    GAME = "game"
    UNKNOWN = "unknown"


class FrameworkCategory(Enum):
    """Categories of frameworks and technologies."""

    WEB_FRAMEWORK = "web_framework"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    BUILD_TOOL = "build_tool"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    AUTHENTICATION = "authentication"
    API = "api"
    UI_FRAMEWORK = "ui_framework"
    STATE_MANAGEMENT = "state_management"
    STYLING = "styling"
    BUNDLER = "bundler"
    LINTER = "linter"
    FORMATTER = "formatter"
    TASK_RUNNER = "task_runner"
    CONTAINER = "container"
    CLOUD = "cloud"
    MESSAGE_QUEUE = "message_queue"
    CACHE = "cache"
    SEARCH = "search"
    ANALYTICS = "analytics"
    LOGGING = "logging"
    DOCUMENTATION = "documentation"
    VERSION_CONTROL = "version_control"
    CI_CD = "ci_cd"


@dataclass
class FrameworkInfo:
    """Information about a detected framework or technology."""

    name: str
    category: FrameworkCategory
    version: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0
    package_name: Optional[str] = None
    config_files: List[str] = field(default_factory=list)
    indicators: List[str] = field(
        default_factory=list
    )  # Files/patterns that indicate this framework
    tags: List[str] = field(default_factory=list)  # Pre-associated tags
    is_dev_dependency: bool = False


@dataclass
class DirectoryInfo:
    """Information about project directory structure."""

    has_src_dir: bool = False
    has_lib_dir: bool = False
    has_tests_dir: bool = False
    has_docs_dir: bool = False
    has_scripts_dir: bool = False
    has_config_dir: bool = False
    has_assets_dir: bool = False
    has_static_dir: bool = False
    has_templates_dir: bool = False
    has_migrations_dir: bool = False
    nested_projects: List[str] = field(
        default_factory=list
    )  # Subdirectories with their own package files
    monorepo_packages: List[str] = field(default_factory=list)


@dataclass
class LanguageInfo:
    """Information about programming languages used in the project."""

    primary_language: str
    languages: Dict[str, float] = field(default_factory=dict)  # language -> percentage
    file_extensions: Set[str] = field(default_factory=set)
    total_files: int = 0


@dataclass
class TestingInfo:
    """Information about testing setup and patterns."""

    has_unit_tests: bool = False
    has_integration_tests: bool = False
    has_e2e_tests: bool = False
    test_frameworks: List[str] = field(default_factory=list)
    test_coverage_tools: List[str] = field(default_factory=list)
    test_file_patterns: List[str] = field(default_factory=list)
    test_directories: List[str] = field(default_factory=list)


@dataclass
class SecurityInfo:
    """Information about security-related configurations and tools."""

    has_security_tools: bool = False
    security_frameworks: List[str] = field(default_factory=list)
    has_env_files: bool = False
    has_secrets_config: bool = False
    has_security_headers: bool = False
    authentication_methods: List[str] = field(default_factory=list)


@dataclass
class DeploymentInfo:
    """Information about deployment and infrastructure setup."""

    containerized: bool = False
    container_tools: List[str] = field(default_factory=list)
    cloud_platforms: List[str] = field(default_factory=list)
    ci_cd_tools: List[str] = field(default_factory=list)
    infrastructure_as_code: List[str] = field(default_factory=list)
    deployment_configs: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete analysis result for a project."""

    project_path: str
    project_type: ProjectType = ProjectType.UNKNOWN
    languages: LanguageInfo = field(
        default_factory=lambda: LanguageInfo(primary_language="unknown")
    )
    frameworks: List[FrameworkInfo] = field(default_factory=list)
    directory_info: DirectoryInfo = field(default_factory=DirectoryInfo)
    testing_info: TestingInfo = field(default_factory=TestingInfo)
    security_info: SecurityInfo = field(default_factory=SecurityInfo)
    deployment_info: DeploymentInfo = field(default_factory=DeploymentInfo)
    package_files: List[str] = field(
        default_factory=list
    )  # package.json, requirements.txt, etc.
    config_files: List[str] = field(default_factory=list)  # Various config files found
    readme_files: List[str] = field(default_factory=list)
    license_files: List[str] = field(default_factory=list)
    confidence_score: float = 0.0  # Overall confidence in the analysis
    analysis_timestamp: Optional[str] = None

    @property
    def is_microservice(self) -> bool:
        """Determine if this appears to be a microservice."""
        return (
            len(self.directory_info.nested_projects) == 0
            and any(
                fw.category == FrameworkCategory.WEB_FRAMEWORK for fw in self.frameworks
            )
            and self.deployment_info.containerized
        )

    @property
    def is_monorepo(self) -> bool:
        """Determine if this appears to be a monorepo."""
        return len(self.directory_info.monorepo_packages) > 1

    @property
    def framework_names(self) -> List[str]:
        """Get list of framework names."""
        return [fw.name for fw in self.frameworks]

    @property
    def primary_frameworks(self) -> List[FrameworkInfo]:
        """Get frameworks with high confidence that aren't dev dependencies."""
        return [
            fw
            for fw in self.frameworks
            if fw.confidence > 0.7 and not fw.is_dev_dependency
        ]
