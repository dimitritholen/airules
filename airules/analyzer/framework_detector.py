"""Framework and technology detection for various languages and ecosystems."""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from .package_parser import PackageInfo, PackageParser


class FrameworkType(Enum):
    """Types of frameworks that can be detected."""

    WEB_FRAMEWORK = "web_framework"
    FRONTEND_FRAMEWORK = "frontend_framework"
    BACKEND_FRAMEWORK = "backend_framework"
    TESTING_FRAMEWORK = "testing_framework"
    BUILD_TOOL = "build_tool"
    DATABASE_ORM = "database_orm"
    UI_LIBRARY = "ui_library"
    STATE_MANAGEMENT = "state_management"
    HTTP_CLIENT = "http_client"
    AUTHENTICATION = "authentication"
    LOGGING = "logging"
    DEPLOYMENT = "deployment"
    MOBILE_FRAMEWORK = "mobile_framework"
    DESKTOP_FRAMEWORK = "desktop_framework"
    GAME_ENGINE = "game_engine"
    ML_FRAMEWORK = "ml_framework"
    DATA_PROCESSING = "data_processing"
    MICROSERVICE = "microservice"
    SERVERLESS = "serverless"
    CONTAINER = "container"


@dataclass
class FrameworkInfo:
    """Information about a detected framework."""

    name: str
    type: FrameworkType
    language: str
    version: Optional[str] = None
    confidence: float = 1.0
    detection_method: str = "dependency"
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProjectTechnology:
    """Complete technology stack information for a project."""

    languages: List[str]
    frameworks: List[FrameworkInfo]
    build_tools: List[FrameworkInfo]
    testing_frameworks: List[FrameworkInfo]
    databases: List[str]
    deployment_targets: List[str]
    project_type: str  # 'web', 'mobile', 'desktop', 'library', etc.
    confidence_score: float


class FrameworkDetector:
    """Main framework detection engine."""

    # Framework definitions with detection patterns
    FRAMEWORK_DEFINITIONS = {
        # JavaScript/TypeScript Frameworks
        "react": {
            "name": "React",
            "type": FrameworkType.FRONTEND_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["react", "@types/react"],
            "files": ["src/App.jsx", "src/App.tsx", "public/index.html"],
            "file_patterns": [r"import.*React", r'from ["\']react["\']', r"\.jsx?$"],
            "package_scripts": ["start", "build"],
        },
        "vue": {
            "name": "Vue.js",
            "type": FrameworkType.FRONTEND_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["vue", "@vue/cli"],
            "files": ["src/App.vue", "src/main.js"],
            "file_patterns": [r"<template>", r"import.*Vue", r"\.vue$"],
        },
        "angular": {
            "name": "Angular",
            "type": FrameworkType.FRONTEND_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["@angular/core", "@angular/cli"],
            "files": ["src/app/app.component.ts", "angular.json"],
            "file_patterns": [r"@Component", r"@NgModule", r"@Injectable"],
        },
        "svelte": {
            "name": "Svelte",
            "type": FrameworkType.FRONTEND_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["svelte", "@sveltejs/kit"],
            "files": ["src/App.svelte"],
            "file_patterns": [r"<script>", r"\.svelte$"],
        },
        "nextjs": {
            "name": "Next.js",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["next"],
            "files": ["pages/_app.js", "pages/index.js", "next.config.js"],
            "file_patterns": [r'from ["\']next["\']'],
        },
        "nuxtjs": {
            "name": "Nuxt.js",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["nuxt"],
            "files": ["nuxt.config.js", "pages/index.vue"],
        },
        "express": {
            "name": "Express.js",
            "type": FrameworkType.BACKEND_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["express"],
            "file_patterns": [
                r'require\(["\']express["\']\)',
                r'from ["\']express["\']',
            ],
        },
        "nestjs": {
            "name": "NestJS",
            "type": FrameworkType.BACKEND_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["@nestjs/core", "@nestjs/common"],
            "file_patterns": [r"@Controller", r"@Injectable", r"@Module"],
        },
        "fastify": {
            "name": "Fastify",
            "type": FrameworkType.BACKEND_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["fastify"],
        },
        # Python Frameworks
        "django": {
            "name": "Django",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "python",
            "dependencies": ["django", "Django"],
            "files": ["manage.py", "settings.py", "urls.py"],
            "file_patterns": [r"from django", r"import django"],
        },
        "flask": {
            "name": "Flask",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "python",
            "dependencies": ["flask", "Flask"],
            "file_patterns": [r"from flask", r"import flask", r"@app\.route"],
        },
        "fastapi": {
            "name": "FastAPI",
            "type": FrameworkType.BACKEND_FRAMEWORK,
            "language": "python",
            "dependencies": ["fastapi"],
            "file_patterns": [
                r"from fastapi",
                r"import fastapi",
                r"@app\.(get|post|put|delete)",
            ],
        },
        "tornado": {
            "name": "Tornado",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "python",
            "dependencies": ["tornado"],
            "file_patterns": [r"import tornado", r"from tornado"],
        },
        "pyramid": {
            "name": "Pyramid",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "python",
            "dependencies": ["pyramid"],
        },
        "sanic": {
            "name": "Sanic",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "python",
            "dependencies": ["sanic"],
        },
        "celery": {
            "name": "Celery",
            "type": FrameworkType.MICROSERVICE,
            "language": "python",
            "dependencies": ["celery"],
        },
        # Python Data/ML Frameworks
        "pandas": {
            "name": "Pandas",
            "type": FrameworkType.DATA_PROCESSING,
            "language": "python",
            "dependencies": ["pandas"],
        },
        "numpy": {
            "name": "NumPy",
            "type": FrameworkType.DATA_PROCESSING,
            "language": "python",
            "dependencies": ["numpy"],
        },
        "scikit-learn": {
            "name": "Scikit-learn",
            "type": FrameworkType.ML_FRAMEWORK,
            "language": "python",
            "dependencies": ["scikit-learn", "sklearn"],
        },
        "tensorflow": {
            "name": "TensorFlow",
            "type": FrameworkType.ML_FRAMEWORK,
            "language": "python",
            "dependencies": ["tensorflow", "tensorflow-gpu"],
        },
        "pytorch": {
            "name": "PyTorch",
            "type": FrameworkType.ML_FRAMEWORK,
            "language": "python",
            "dependencies": ["torch", "pytorch"],
        },
        "keras": {
            "name": "Keras",
            "type": FrameworkType.ML_FRAMEWORK,
            "language": "python",
            "dependencies": ["keras"],
        },
        # Java Frameworks
        "spring": {
            "name": "Spring Framework",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "java",
            "dependencies": [
                "org.springframework:spring-core",
                "org.springframework:spring-web",
            ],
            "file_patterns": [r"@RestController", r"@Component", r"@Autowired"],
        },
        "spring-boot": {
            "name": "Spring Boot",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "java",
            "dependencies": ["org.springframework.boot:spring-boot-starter"],
            "files": ["application.properties", "application.yml"],
            "file_patterns": [r"@SpringBootApplication"],
        },
        "hibernate": {
            "name": "Hibernate",
            "type": FrameworkType.DATABASE_ORM,
            "language": "java",
            "dependencies": ["org.hibernate:hibernate-core"],
        },
        "junit": {
            "name": "JUnit",
            "type": FrameworkType.TESTING_FRAMEWORK,
            "language": "java",
            "dependencies": ["junit:junit", "org.junit.jupiter:junit-jupiter"],
        },
        # Rust Frameworks
        "actix-web": {
            "name": "Actix Web",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "rust",
            "dependencies": ["actix-web"],
        },
        "warp": {
            "name": "Warp",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "rust",
            "dependencies": ["warp"],
        },
        "rocket": {
            "name": "Rocket",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "rust",
            "dependencies": ["rocket"],
        },
        "axum": {
            "name": "Axum",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "rust",
            "dependencies": ["axum"],
        },
        "tokio": {
            "name": "Tokio",
            "type": FrameworkType.BACKEND_FRAMEWORK,
            "language": "rust",
            "dependencies": ["tokio"],
        },
        "serde": {
            "name": "Serde",
            "type": FrameworkType.DATA_PROCESSING,
            "language": "rust",
            "dependencies": ["serde"],
        },
        # Go Frameworks
        "gin": {
            "name": "Gin",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "go",
            "dependencies": ["github.com/gin-gonic/gin"],
        },
        "echo": {
            "name": "Echo",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "go",
            "dependencies": ["github.com/labstack/echo"],
        },
        "fiber": {
            "name": "Fiber",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "go",
            "dependencies": ["github.com/gofiber/fiber"],
        },
        "gorilla": {
            "name": "Gorilla",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "go",
            "dependencies": ["github.com/gorilla/mux"],
        },
        "gorm": {
            "name": "GORM",
            "type": FrameworkType.DATABASE_ORM,
            "language": "go",
            "dependencies": ["gorm.io/gorm"],
        },
        # PHP Frameworks
        "laravel": {
            "name": "Laravel",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "php",
            "dependencies": ["laravel/framework"],
            "files": ["artisan", "config/app.php"],
        },
        "symfony": {
            "name": "Symfony",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "php",
            "dependencies": ["symfony/framework-bundle"],
        },
        "codeigniter": {
            "name": "CodeIgniter",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "php",
            "dependencies": ["codeigniter/framework"],
        },
        # Ruby Frameworks
        "rails": {
            "name": "Ruby on Rails",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "ruby",
            "dependencies": ["rails"],
            "files": ["config/application.rb", "Rakefile"],
        },
        "sinatra": {
            "name": "Sinatra",
            "type": FrameworkType.WEB_FRAMEWORK,
            "language": "ruby",
            "dependencies": ["sinatra"],
        },
        # Testing Frameworks
        "jest": {
            "name": "Jest",
            "type": FrameworkType.TESTING_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["jest"],
            "files": ["jest.config.js"],
        },
        "mocha": {
            "name": "Mocha",
            "type": FrameworkType.TESTING_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["mocha"],
        },
        "cypress": {
            "name": "Cypress",
            "type": FrameworkType.TESTING_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["cypress"],
            "files": ["cypress.config.js"],
        },
        "playwright": {
            "name": "Playwright",
            "type": FrameworkType.TESTING_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["@playwright/test"],
        },
        "pytest": {
            "name": "pytest",
            "type": FrameworkType.TESTING_FRAMEWORK,
            "language": "python",
            "dependencies": ["pytest"],
            "files": ["pytest.ini", "pyproject.toml"],
        },
        "unittest": {
            "name": "unittest",
            "type": FrameworkType.TESTING_FRAMEWORK,
            "language": "python",
            "file_patterns": [r"import unittest", r"from unittest"],
        },
        # Build Tools
        "webpack": {
            "name": "webpack",
            "type": FrameworkType.BUILD_TOOL,
            "language": "javascript",
            "dependencies": ["webpack"],
            "files": ["webpack.config.js"],
        },
        "vite": {
            "name": "Vite",
            "type": FrameworkType.BUILD_TOOL,
            "language": "javascript",
            "dependencies": ["vite"],
            "files": ["vite.config.js", "vite.config.ts"],
        },
        "rollup": {
            "name": "Rollup",
            "type": FrameworkType.BUILD_TOOL,
            "language": "javascript",
            "dependencies": ["rollup"],
            "files": ["rollup.config.js"],
        },
        "parcel": {
            "name": "Parcel",
            "type": FrameworkType.BUILD_TOOL,
            "language": "javascript",
            "dependencies": ["parcel"],
        },
        "esbuild": {
            "name": "esbuild",
            "type": FrameworkType.BUILD_TOOL,
            "language": "javascript",
            "dependencies": ["esbuild"],
        },
        # Mobile Frameworks
        "react-native": {
            "name": "React Native",
            "type": FrameworkType.MOBILE_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["react-native"],
            "files": ["metro.config.js", "android/", "ios/"],
        },
        "flutter": {
            "name": "Flutter",
            "type": FrameworkType.MOBILE_FRAMEWORK,
            "language": "dart",
            "dependencies": ["flutter"],
            "files": ["pubspec.yaml", "lib/main.dart"],
        },
        "ionic": {
            "name": "Ionic",
            "type": FrameworkType.MOBILE_FRAMEWORK,
            "language": "javascript",
            "dependencies": ["@ionic/angular", "@ionic/react", "@ionic/vue"],
        },
        # State Management
        "redux": {
            "name": "Redux",
            "type": FrameworkType.STATE_MANAGEMENT,
            "language": "javascript",
            "dependencies": ["redux", "@reduxjs/toolkit"],
        },
        "mobx": {
            "name": "MobX",
            "type": FrameworkType.STATE_MANAGEMENT,
            "language": "javascript",
            "dependencies": ["mobx"],
        },
        "zustand": {
            "name": "Zustand",
            "type": FrameworkType.STATE_MANAGEMENT,
            "language": "javascript",
            "dependencies": ["zustand"],
        },
        "vuex": {
            "name": "Vuex",
            "type": FrameworkType.STATE_MANAGEMENT,
            "language": "javascript",
            "dependencies": ["vuex"],
        },
        # UI Libraries
        "mui": {
            "name": "Material-UI",
            "type": FrameworkType.UI_LIBRARY,
            "language": "javascript",
            "dependencies": ["@mui/material", "@material-ui/core"],
        },
        "antd": {
            "name": "Ant Design",
            "type": FrameworkType.UI_LIBRARY,
            "language": "javascript",
            "dependencies": ["antd"],
        },
        "chakra-ui": {
            "name": "Chakra UI",
            "type": FrameworkType.UI_LIBRARY,
            "language": "javascript",
            "dependencies": ["@chakra-ui/react"],
        },
        "bootstrap": {
            "name": "Bootstrap",
            "type": FrameworkType.UI_LIBRARY,
            "language": "javascript",
            "dependencies": ["bootstrap"],
        },
        "tailwindcss": {
            "name": "Tailwind CSS",
            "type": FrameworkType.UI_LIBRARY,
            "language": "javascript",
            "dependencies": ["tailwindcss"],
            "files": ["tailwind.config.js"],
        },
        # Databases & ORMs
        "mongoose": {
            "name": "Mongoose",
            "type": FrameworkType.DATABASE_ORM,
            "language": "javascript",
            "dependencies": ["mongoose"],
        },
        "prisma": {
            "name": "Prisma",
            "type": FrameworkType.DATABASE_ORM,
            "language": "javascript",
            "dependencies": ["prisma", "@prisma/client"],
            "files": ["prisma/schema.prisma"],
        },
        "typeorm": {
            "name": "TypeORM",
            "type": FrameworkType.DATABASE_ORM,
            "language": "javascript",
            "dependencies": ["typeorm"],
        },
        "sequelize": {
            "name": "Sequelize",
            "type": FrameworkType.DATABASE_ORM,
            "language": "javascript",
            "dependencies": ["sequelize"],
        },
        "sqlalchemy": {
            "name": "SQLAlchemy",
            "type": FrameworkType.DATABASE_ORM,
            "language": "python",
            "dependencies": ["sqlalchemy", "SQLAlchemy"],
        },
        "django-orm": {
            "name": "Django ORM",
            "type": FrameworkType.DATABASE_ORM,
            "language": "python",
            "dependencies": ["django"],
            "file_patterns": [r"from django\.db import models"],
        },
        # Container & Deployment
        "docker": {
            "name": "Docker",
            "type": FrameworkType.CONTAINER,
            "language": "multi",
            "files": ["Dockerfile", "docker-compose.yml", ".dockerignore"],
        },
        "kubernetes": {
            "name": "Kubernetes",
            "type": FrameworkType.DEPLOYMENT,
            "language": "multi",
            "files": ["k8s/", "kubernetes/", "*.yaml"],
        },
        "serverless": {
            "name": "Serverless Framework",
            "type": FrameworkType.SERVERLESS,
            "language": "multi",
            "dependencies": ["serverless"],
            "files": ["serverless.yml"],
        },
    }

    def __init__(self):
        self.package_parser = PackageParser()
        self.detected_frameworks: List[FrameworkInfo] = []
        self.project_languages = set()

    def detect_frameworks(self, project_path: str) -> List[FrameworkInfo]:
        """Detect all frameworks in a project."""
        project_path_obj = Path(project_path)
        detected_frameworks = []

        # Parse package files
        package_infos = self.package_parser.parse_all_package_files(
            str(project_path_obj)
        )

        # Detect frameworks from dependencies
        for package_info in package_infos:
            frameworks = self._detect_from_dependencies(package_info)
            detected_frameworks.extend(frameworks)
            self.project_languages.add(package_info.language)

        # Detect frameworks from file patterns
        file_frameworks = self._detect_from_files(project_path_obj)
        detected_frameworks.extend(file_frameworks)

        # Detect frameworks from directory structure
        structure_frameworks = self._detect_from_structure(project_path_obj)
        detected_frameworks.extend(structure_frameworks)

        # Remove duplicates and sort by confidence
        unique_frameworks = self._deduplicate_frameworks(detected_frameworks)
        unique_frameworks.sort(key=lambda x: x.confidence, reverse=True)

        self.detected_frameworks = unique_frameworks
        return unique_frameworks

    def get_project_technology(self, project_path: str) -> ProjectTechnology:
        """Get complete technology stack analysis."""
        frameworks = self.detect_frameworks(project_path)

        # Categorize frameworks
        build_tools = [f for f in frameworks if f.type == FrameworkType.BUILD_TOOL]
        testing_frameworks = [
            f for f in frameworks if f.type == FrameworkType.TESTING_FRAMEWORK
        ]

        # Determine project type
        project_type = self._determine_project_type(frameworks)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(frameworks)

        # Extract database information
        databases = self._extract_databases(frameworks)

        # Extract deployment targets
        deployment_targets = self._extract_deployment_targets(frameworks)

        return ProjectTechnology(
            languages=list(self.project_languages),
            frameworks=frameworks,
            build_tools=build_tools,
            testing_frameworks=testing_frameworks,
            databases=databases,
            deployment_targets=deployment_targets,
            project_type=project_type,
            confidence_score=confidence_score,
        )

    def _detect_from_dependencies(
        self, package_info: PackageInfo
    ) -> List[FrameworkInfo]:
        """Detect frameworks from package dependencies."""
        detected = []
        all_deps = package_info.dependencies + package_info.dev_dependencies

        for framework_key, framework_def in self.FRAMEWORK_DEFINITIONS.items():
            framework_deps = framework_def.get("dependencies", [])
            if not framework_deps:
                continue

            # Check if any framework dependency is present
            for dep in all_deps:
                if any(
                    fw_dep.lower() in dep.name.lower()
                    for fw_dep in cast(List[str], framework_deps)
                ):
                    framework_info = FrameworkInfo(
                        name=str(framework_def["name"]),
                        type=FrameworkType(framework_def["type"]),
                        language=str(framework_def["language"]),
                        version=dep.version,
                        confidence=0.9,
                        detection_method="dependency",
                        metadata={
                            "package_file": package_info.file_path,
                            "dependency_name": dep.name,
                            "is_dev_dependency": dep.is_dev,
                        },
                    )
                    detected.append(framework_info)
                    break

        return detected

    def _detect_from_files(self, project_path: Path) -> List[FrameworkInfo]:
        """Detect frameworks from file patterns and specific files."""
        detected = []

        # Get all source files
        source_files: List[Path] = []
        for ext in [
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".py",
            ".java",
            ".rs",
            ".go",
            ".php",
            ".rb",
            ".vue",
            ".svelte",
        ]:
            source_files.extend(project_path.rglob(f"*{ext}"))

        # Limit to reasonable number of files to scan
        source_files = source_files[:100]

        for framework_key, framework_def in self.FRAMEWORK_DEFINITIONS.items():
            # Check for specific files
            framework_files = framework_def.get("files", [])
            for file_path in cast(List[str], framework_files):
                if (project_path / file_path).exists():
                    framework_info = FrameworkInfo(
                        name=str(framework_def["name"]),
                        type=FrameworkType(framework_def["type"]),
                        language=str(framework_def["language"]),
                        confidence=0.8,
                        detection_method="file_presence",
                        metadata={"detected_file": file_path},
                    )
                    detected.append(framework_info)
                    break

            # Check file patterns
            file_patterns = framework_def.get("file_patterns", [])
            if file_patterns:
                for source_file in source_files:
                    try:
                        with source_file.open(
                            "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read(8192)  # Read first 8KB only

                        for pattern in cast(List[str], file_patterns):
                            if re.search(pattern, content, re.IGNORECASE):
                                framework_info = FrameworkInfo(
                                    name=str(framework_def["name"]),
                                    type=FrameworkType(framework_def["type"]),
                                    language=str(framework_def["language"]),
                                    confidence=0.7,
                                    detection_method="file_pattern",
                                    metadata={
                                        "detected_file": str(source_file),
                                        "pattern": pattern,
                                    },
                                )
                                detected.append(framework_info)
                                break
                    except (OSError, UnicodeDecodeError):
                        continue

        return detected

    def _detect_from_structure(self, project_path: Path) -> List[FrameworkInfo]:
        """Detect frameworks from directory structure."""
        detected = []

        # Common directory patterns
        structure_patterns = {
            "django": ["manage.py", "apps/", "templates/", "static/"],
            "rails": ["app/", "config/", "db/", "Gemfile"],
            "laravel": ["app/", "config/", "database/", "resources/", "artisan"],
            "spring-boot": ["src/main/java/", "src/main/resources/", "pom.xml"],
            "react": ["src/", "public/", "package.json"],
            "angular": ["src/app/", "angular.json"],
            "vue": ["src/", "public/", "vue.config.js"],
            "flutter": ["lib/", "android/", "ios/", "pubspec.yaml"],
            "react-native": ["android/", "ios/", "metro.config.js"],
        }

        for framework_key, required_items in structure_patterns.items():
            matches = 0
            total = len(required_items)

            for item in required_items:
                item_path = project_path / item
                # Check if it's a directory (ends with /) or file
                if item.endswith("/"):
                    # Remove trailing slash for directory check
                    dir_path = project_path / item.rstrip("/")
                    if dir_path.is_dir():
                        matches += 1
                else:
                    if item_path.is_file():
                        matches += 1

            confidence = matches / total
            if confidence >= 0.5:  # At least 50% of structure matches
                if framework_key in self.FRAMEWORK_DEFINITIONS:
                    framework_def = self.FRAMEWORK_DEFINITIONS[framework_key]
                    framework_info = FrameworkInfo(
                        name=str(framework_def["name"]),
                        type=FrameworkType(framework_def["type"]),
                        language=str(framework_def["language"]),
                        confidence=confidence
                        * 0.6,  # Lower confidence for structure-based detection
                        detection_method="directory_structure",
                        metadata={"structure_match_ratio": confidence},
                    )
                    detected.append(framework_info)

        return detected

    def _deduplicate_frameworks(
        self, frameworks: List[FrameworkInfo]
    ) -> List[FrameworkInfo]:
        """Remove duplicate frameworks, keeping the one with highest confidence."""
        seen: Dict[Tuple[str, FrameworkType, str], FrameworkInfo] = {}

        for framework in frameworks:
            key = (framework.name, framework.type, framework.language)
            if key not in seen or framework.confidence > seen[key].confidence:
                seen[key] = framework

        return list(seen.values())

    def _determine_project_type(self, frameworks: List[FrameworkInfo]) -> str:
        """Determine the primary project type based on detected frameworks."""
        type_scores: Dict[str, float] = {
            "web": 0.0,
            "mobile": 0.0,
            "desktop": 0.0,
            "library": 0.0,
            "data_science": 0.0,
            "game": 0.0,
            "cli": 0.0,
        }

        for framework in frameworks:
            if framework.type in [
                FrameworkType.WEB_FRAMEWORK,
                FrameworkType.FRONTEND_FRAMEWORK,
                FrameworkType.BACKEND_FRAMEWORK,
            ]:
                type_scores["web"] += framework.confidence
            elif framework.type == FrameworkType.MOBILE_FRAMEWORK:
                type_scores["mobile"] += framework.confidence * 2
            elif framework.type == FrameworkType.DESKTOP_FRAMEWORK:
                type_scores["desktop"] += framework.confidence * 2
            elif framework.type in [
                FrameworkType.ML_FRAMEWORK,
                FrameworkType.DATA_PROCESSING,
            ]:
                type_scores["data_science"] += framework.confidence
            elif framework.type == FrameworkType.GAME_ENGINE:
                type_scores["game"] += framework.confidence * 2

        # Return the type with the highest score
        max_type = max(type_scores.keys(), key=lambda k: type_scores[k])
        return max_type if type_scores[max_type] > 0 else "library"

    def _calculate_confidence_score(self, frameworks: List[FrameworkInfo]) -> float:
        """Calculate overall confidence score for the detection."""
        if not frameworks:
            return 0.0

        # Weight by detection method
        method_weights = {
            "dependency": 1.0,
            "file_presence": 0.8,
            "file_pattern": 0.6,
            "directory_structure": 0.4,
        }

        total_score = 0.0
        total_weight = 0.0

        for framework in frameworks:
            weight = method_weights.get(framework.detection_method, 0.5)
            total_score += framework.confidence * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _extract_databases(self, frameworks: List[FrameworkInfo]) -> List[str]:
        """Extract database technologies from frameworks."""
        databases = set()

        database_mapping = {
            "mongoose": "MongoDB",
            "prisma": "PostgreSQL/MySQL/SQLite",
            "typeorm": "Multiple SQL databases",
            "sequelize": "PostgreSQL/MySQL/SQLite",
            "sqlalchemy": "Multiple SQL databases",
            "django-orm": "PostgreSQL/MySQL/SQLite",
            "hibernate": "Multiple SQL databases",
            "gorm": "Multiple SQL databases",
        }

        for framework in frameworks:
            if framework.type == FrameworkType.DATABASE_ORM:
                db_name = database_mapping.get(framework.name.lower(), "Unknown")
                databases.add(db_name)

        return list(databases)

    def _extract_deployment_targets(self, frameworks: List[FrameworkInfo]) -> List[str]:
        """Extract deployment targets from frameworks."""
        targets = set()

        for framework in frameworks:
            if framework.type == FrameworkType.CONTAINER:
                targets.add("Docker")
            elif framework.type == FrameworkType.SERVERLESS:
                targets.add("Serverless")
            elif framework.type == FrameworkType.DEPLOYMENT:
                targets.add("Kubernetes")
            elif framework.name == "React" or framework.name == "Vue.js":
                targets.add("Static Hosting")
            elif framework.type in [
                FrameworkType.WEB_FRAMEWORK,
                FrameworkType.BACKEND_FRAMEWORK,
            ]:
                targets.add("Web Server")
            elif framework.type == FrameworkType.MOBILE_FRAMEWORK:
                targets.add("Mobile App Store")

        return list(targets) if targets else ["Unknown"]

    def get_framework_suggestions(self, project_path: str) -> Dict[str, List[str]]:
        """Suggest complementary frameworks based on detected technology."""
        frameworks = self.detect_frameworks(project_path)
        suggestions: Dict[str, List[str]] = {
            "testing": [],
            "build_tools": [],
            "ui_libraries": [],
            "state_management": [],
            "databases": [],
            "deployment": [],
        }

        detected_names = {f.name.lower() for f in frameworks}
        languages = {f.language for f in frameworks}

        # Testing framework suggestions
        if "javascript" in languages and not any(
            "jest" in name or "mocha" in name for name in detected_names
        ):
            suggestions["testing"].extend(["Jest", "Cypress", "Playwright"])
        if "python" in languages and "pytest" not in detected_names:
            suggestions["testing"].append("pytest")

        # Build tool suggestions
        if "javascript" in languages and not any(
            tool in detected_names for tool in ["webpack", "vite", "rollup"]
        ):
            suggestions["build_tools"].extend(["Vite", "webpack"])

        # UI library suggestions for React projects
        if any("react" in name for name in detected_names):
            if not any(
                ui in detected_names for ui in ["material-ui", "antd", "chakra"]
            ):
                suggestions["ui_libraries"].extend(
                    ["Material-UI", "Ant Design", "Chakra UI"]
                )
            if not any(
                state in detected_names for state in ["redux", "mobx", "zustand"]
            ):
                suggestions["state_management"].extend(["Redux Toolkit", "Zustand"])

        # Database suggestions
        if any(
            fw.type in [FrameworkType.WEB_FRAMEWORK, FrameworkType.BACKEND_FRAMEWORK]
            for fw in frameworks
        ):
            if not any(fw.type == FrameworkType.DATABASE_ORM for fw in frameworks):
                if "javascript" in languages:
                    suggestions["databases"].extend(["Prisma", "TypeORM"])
                if "python" in languages:
                    suggestions["databases"].extend(["SQLAlchemy", "Django ORM"])

        # Deployment suggestions
        if not any(
            fw.type in [FrameworkType.CONTAINER, FrameworkType.DEPLOYMENT]
            for fw in frameworks
        ):
            suggestions["deployment"].extend(["Docker", "Kubernetes"])

        return {k: v for k, v in suggestions.items() if v}

    def analyze_compatibility(self, frameworks: List[FrameworkInfo]) -> Dict[str, Any]:
        """Analyze compatibility between detected frameworks."""
        compatibility_issues = []
        recommendations = []

        # Check for conflicting frameworks
        conflicts = [
            (["React", "Vue.js", "Angular"], "Multiple frontend frameworks detected"),
            (["Django", "Flask", "FastAPI"], "Multiple Python web frameworks detected"),
            (
                ["Express.js", "Fastify", "NestJS"],
                "Multiple Node.js frameworks detected",
            ),
        ]

        framework_names = [f.name for f in frameworks]

        for conflict_group, message in conflicts:
            detected_in_group = [
                name for name in framework_names if name in conflict_group
            ]
            if len(detected_in_group) > 1:
                compatibility_issues.append(
                    {
                        "type": "conflict",
                        "frameworks": detected_in_group,
                        "message": message,
                    }
                )

        # Check for missing complementary frameworks
        if any(f.name == "React" for f in frameworks):
            if not any(f.type == FrameworkType.BUILD_TOOL for f in frameworks):
                recommendations.append(
                    "Consider adding a build tool like Vite or webpack"
                )
            if not any(f.type == FrameworkType.TESTING_FRAMEWORK for f in frameworks):
                recommendations.append("Consider adding Jest for testing")

        return {
            "issues": compatibility_issues,
            "recommendations": recommendations,
            "compatibility_score": 1.0 - (len(compatibility_issues) * 0.2),
        }
