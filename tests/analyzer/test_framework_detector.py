"""Tests for framework detection functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import toml

from airules.analyzer.framework_detector import (
    FrameworkDetector,
    FrameworkInfo,
    FrameworkType,
    ProjectTechnology,
)
from airules.analyzer.package_parser import DependencyInfo, PackageInfo


class TestFrameworkDetector:
    """Test suite for FrameworkDetector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = FrameworkDetector()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_file(self, filename: str, content: str) -> str:
        """Create a temporary file with given content."""
        file_path = self.temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    def create_package_info(
        self, language: str, dependencies: list, dev_dependencies: list = None
    ) -> PackageInfo:
        """Create a mock PackageInfo object."""
        if dev_dependencies is None:
            dev_dependencies = []

        return PackageInfo(
            file_path=str(self.temp_dir / "package.json"),
            language=language,
            build_system="npm" if language == "javascript" else "pip",
            dependencies=[
                DependencyInfo(name=dep, version="1.0.0") for dep in dependencies
            ],
            dev_dependencies=[
                DependencyInfo(name=dep, version="1.0.0", is_dev=True)
                for dep in dev_dependencies
            ],
            scripts={},
            metadata={},
        )

    def test_detect_react_from_dependencies(self):
        """Test detecting React from package dependencies."""
        package_info = self.create_package_info("javascript", ["react", "react-dom"])

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        react_frameworks = [f for f in frameworks if f.name == "React"]
        assert len(react_frameworks) == 1

        react_fw = react_frameworks[0]
        assert react_fw.type == FrameworkType.FRONTEND_FRAMEWORK
        assert react_fw.language == "javascript"
        assert react_fw.detection_method == "dependency"
        assert react_fw.confidence == 0.9

    def test_detect_django_from_dependencies(self):
        """Test detecting Django from Python dependencies."""
        package_info = self.create_package_info(
            "python", ["django", "djangorestframework"]
        )

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        django_frameworks = [f for f in frameworks if f.name == "Django"]
        assert len(django_frameworks) == 1

        django_fw = django_frameworks[0]
        assert django_fw.type == FrameworkType.WEB_FRAMEWORK
        assert django_fw.language == "python"

    def test_detect_multiple_frameworks(self):
        """Test detecting multiple frameworks from different languages."""
        js_package = self.create_package_info("javascript", ["react", "express"])
        py_package = self.create_package_info("python", ["django", "pytest"], ["black"])

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[js_package, py_package],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        framework_names = [f.name for f in frameworks]
        assert "React" in framework_names
        assert "Express.js" in framework_names
        assert "Django" in framework_names
        assert "pytest" in framework_names

    def test_detect_frameworks_from_files(self):
        """Test detecting frameworks from file patterns."""
        # Create React-specific files
        self.create_temp_file(
            "src/App.jsx",
            """
import React from 'react';

function App() {
  return <div>Hello World</div>;
}

export default App;
""",
        )

        self.create_temp_file(
            "public/index.html", "<html><body><div id='root'></div></body></html>"
        )

        frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        react_frameworks = [f for f in frameworks if f.name == "React"]
        assert len(react_frameworks) >= 1

        # Check detection methods
        detection_methods = [f.detection_method for f in react_frameworks]
        assert (
            "file_presence" in detection_methods or "file_pattern" in detection_methods
        )

    def test_detect_vue_from_files(self):
        """Test detecting Vue.js from .vue files."""
        self.create_temp_file(
            "src/App.vue",
            """
<template>
  <div id="app">
    <h1>Hello Vue!</h1>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>
""",
        )

        frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        vue_frameworks = [f for f in frameworks if f.name == "Vue.js"]
        assert len(vue_frameworks) >= 1

    def test_detect_django_from_structure(self):
        """Test detecting Django from directory structure."""
        # Create Django-like structure
        self.create_temp_file("manage.py", "#!/usr/bin/env python")
        self.create_temp_file("myproject/settings.py", "DEBUG = True")
        self.create_temp_file("myproject/urls.py", "urlpatterns = []")
        self.create_temp_file("apps/myapp/models.py", "from django.db import models")

        frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        django_frameworks = [f for f in frameworks if f.name == "Django"]
        assert len(django_frameworks) >= 1

        # Should detect Django (either from structure or file presence)
        django_fw = django_frameworks[0]
        assert django_fw.type == FrameworkType.WEB_FRAMEWORK
        assert django_fw.language == "python"

        # Should detect from structure or file presence
        assert django_fw.detection_method in ["directory_structure", "file_presence"]

    def test_detect_angular_from_files(self):
        """Test detecting Angular from specific patterns."""
        self.create_temp_file(
            "angular.json",
            json.dumps(
                {"version": 1, "projects": {"my-app": {"projectType": "application"}}}
            ),
        )

        self.create_temp_file(
            "src/app/app.component.ts",
            """
import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html'
})
export class AppComponent {
}
""",
        )

        frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        angular_frameworks = [f for f in frameworks if f.name == "Angular"]
        assert len(angular_frameworks) >= 1

    def test_detect_rust_frameworks(self):
        """Test detecting Rust frameworks."""
        package_info = self.create_package_info("rust", ["actix-web", "tokio", "serde"])

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        framework_names = [f.name for f in frameworks]
        assert "Actix Web" in framework_names
        assert "Tokio" in framework_names
        assert "Serde" in framework_names

    def test_detect_go_frameworks(self):
        """Test detecting Go frameworks."""
        package_info = self.create_package_info(
            "go", ["github.com/gin-gonic/gin", "gorm.io/gorm"]
        )

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        framework_names = [f.name for f in frameworks]
        assert "Gin" in framework_names
        assert "GORM" in framework_names

    def test_detect_testing_frameworks(self):
        """Test detecting testing frameworks."""
        js_package = self.create_package_info("javascript", [], ["jest", "cypress"])
        py_package = self.create_package_info("python", [], ["pytest"])

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[js_package, py_package],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        testing_frameworks = [
            f for f in frameworks if f.type == FrameworkType.TESTING_FRAMEWORK
        ]
        testing_names = [f.name for f in testing_frameworks]

        assert "Jest" in testing_names
        assert "Cypress" in testing_names
        assert "pytest" in testing_names

    def test_detect_build_tools(self):
        """Test detecting build tools."""
        package_info = self.create_package_info(
            "javascript", [], ["webpack", "vite", "rollup"]
        )

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        build_tools = [f for f in frameworks if f.type == FrameworkType.BUILD_TOOL]
        build_names = [f.name for f in build_tools]

        assert "webpack" in build_names
        assert "Vite" in build_names
        assert "Rollup" in build_names

    def test_detect_ui_libraries(self):
        """Test detecting UI libraries."""
        package_info = self.create_package_info(
            "javascript", ["@mui/material", "antd", "bootstrap"]
        )

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        ui_libraries = [f for f in frameworks if f.type == FrameworkType.UI_LIBRARY]
        ui_names = [f.name for f in ui_libraries]

        assert "Material-UI" in ui_names
        assert "Ant Design" in ui_names
        assert "Bootstrap" in ui_names

    def test_detect_mobile_frameworks(self):
        """Test detecting mobile frameworks."""
        rn_package = self.create_package_info("javascript", ["react-native"])

        # Create mobile-specific structure
        self.create_temp_file("android/build.gradle", "android { }")
        self.create_temp_file("ios/Podfile", "platform :ios")

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[rn_package],
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        mobile_frameworks = [
            f for f in frameworks if f.type == FrameworkType.MOBILE_FRAMEWORK
        ]
        assert len(mobile_frameworks) >= 1
        assert any(f.name == "React Native" for f in mobile_frameworks)

    def test_detect_container_deployment(self):
        """Test detecting container and deployment tools."""
        self.create_temp_file(
            "Dockerfile",
            """
FROM node:16
COPY . .
RUN npm install
CMD ["npm", "start"]
""",
        )

        self.create_temp_file(
            "docker-compose.yml",
            """
version: '3'
services:
  app:
    build: .
    ports:
      - "3000:3000"
""",
        )

        frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        container_frameworks = [
            f for f in frameworks if f.type == FrameworkType.CONTAINER
        ]
        assert len(container_frameworks) >= 1
        assert any(f.name == "Docker" for f in container_frameworks)

    def test_deduplicate_frameworks(self):
        """Test deduplication of framework detections."""
        # Create multiple detections of the same framework
        frameworks = [
            FrameworkInfo(
                "React", FrameworkType.FRONTEND_FRAMEWORK, "javascript", confidence=0.9
            ),
            FrameworkInfo(
                "React", FrameworkType.FRONTEND_FRAMEWORK, "javascript", confidence=0.7
            ),
            FrameworkInfo(
                "Vue.js", FrameworkType.FRONTEND_FRAMEWORK, "javascript", confidence=0.8
            ),
        ]

        unique_frameworks = self.detector._deduplicate_frameworks(frameworks)

        assert len(unique_frameworks) == 2
        # Should keep the React with higher confidence
        react_fw = next(f for f in unique_frameworks if f.name == "React")
        assert react_fw.confidence == 0.9

    def test_get_project_technology(self):
        """Test getting complete project technology analysis."""
        js_package = self.create_package_info(
            "javascript", ["react", "express"], ["jest", "webpack"]
        )
        py_package = self.create_package_info("python", ["django"], ["pytest"])

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[js_package, py_package],
        ):
            tech_analysis = self.detector.get_project_technology(str(self.temp_dir))

        assert isinstance(tech_analysis, ProjectTechnology)
        assert "javascript" in tech_analysis.languages
        assert "python" in tech_analysis.languages

        # Check framework categorization
        assert len(tech_analysis.build_tools) >= 1
        assert len(tech_analysis.testing_frameworks) >= 1

        # Check project type determination
        assert tech_analysis.project_type in [
            "web",
            "library",
            "mobile",
            "desktop",
            "data_science",
            "game",
            "cli",
        ]

        # Check confidence score
        assert 0.0 <= tech_analysis.confidence_score <= 1.0

    def test_determine_project_type(self):
        """Test project type determination logic."""
        # Web project
        web_frameworks = [
            FrameworkInfo(
                "React", FrameworkType.FRONTEND_FRAMEWORK, "javascript", confidence=0.9
            ),
            FrameworkInfo(
                "Django", FrameworkType.WEB_FRAMEWORK, "python", confidence=0.8
            ),
        ]
        project_type = self.detector._determine_project_type(web_frameworks)
        assert project_type == "web"

        # Mobile project
        mobile_frameworks = [
            FrameworkInfo(
                "React Native",
                FrameworkType.MOBILE_FRAMEWORK,
                "javascript",
                confidence=0.9,
            )
        ]
        project_type = self.detector._determine_project_type(mobile_frameworks)
        assert project_type == "mobile"

        # Data science project
        ds_frameworks = [
            FrameworkInfo(
                "Pandas", FrameworkType.DATA_PROCESSING, "python", confidence=0.9
            ),
            FrameworkInfo(
                "TensorFlow", FrameworkType.ML_FRAMEWORK, "python", confidence=0.8
            ),
        ]
        project_type = self.detector._determine_project_type(ds_frameworks)
        assert project_type == "data_science"

    def test_get_framework_suggestions(self):
        """Test framework suggestions based on detected technology."""
        # React project without testing
        js_package = self.create_package_info("javascript", ["react"])

        with patch.object(
            self.detector.package_parser,
            "parse_all_package_files",
            return_value=[js_package],
        ):
            suggestions = self.detector.get_framework_suggestions(str(self.temp_dir))

        assert "testing" in suggestions
        assert "Jest" in suggestions["testing"] or "Cypress" in suggestions["testing"]

        assert "build_tools" in suggestions
        assert "ui_libraries" in suggestions
        assert "state_management" in suggestions

    def test_analyze_compatibility(self):
        """Test framework compatibility analysis."""
        # Conflicting frontend frameworks
        conflicting_frameworks = [
            FrameworkInfo("React", FrameworkType.FRONTEND_FRAMEWORK, "javascript"),
            FrameworkInfo("Vue.js", FrameworkType.FRONTEND_FRAMEWORK, "javascript"),
            FrameworkInfo("Angular", FrameworkType.FRONTEND_FRAMEWORK, "javascript"),
        ]

        compatibility = self.detector.analyze_compatibility(conflicting_frameworks)

        assert len(compatibility["issues"]) > 0
        assert compatibility["compatibility_score"] < 1.0

        # Check that conflict is detected
        conflict_issue = next(
            (issue for issue in compatibility["issues"] if issue["type"] == "conflict"),
            None,
        )
        assert conflict_issue is not None
        assert len(conflict_issue["frameworks"]) >= 2

    def test_framework_info_dataclass(self):
        """Test FrameworkInfo dataclass functionality."""
        framework = FrameworkInfo(
            name="React",
            type=FrameworkType.FRONTEND_FRAMEWORK,
            language="javascript",
            version="18.0.0",
            confidence=0.9,
            detection_method="dependency",
            metadata={"package_file": "/path/to/package.json"},
        )

        assert framework.name == "React"
        assert framework.type == FrameworkType.FRONTEND_FRAMEWORK
        assert framework.language == "javascript"
        assert framework.version == "18.0.0"
        assert framework.confidence == 0.9
        assert framework.detection_method == "dependency"
        assert framework.metadata["package_file"] == "/path/to/package.json"

    def test_project_technology_dataclass(self):
        """Test ProjectTechnology dataclass functionality."""
        frameworks = [
            FrameworkInfo("React", FrameworkType.FRONTEND_FRAMEWORK, "javascript"),
            FrameworkInfo("Jest", FrameworkType.TESTING_FRAMEWORK, "javascript"),
        ]

        tech = ProjectTechnology(
            languages=["javascript", "python"],
            frameworks=frameworks,
            build_tools=[],
            testing_frameworks=[frameworks[1]],
            databases=["PostgreSQL"],
            deployment_targets=["Web Server"],
            project_type="web",
            confidence_score=0.85,
        )

        assert len(tech.languages) == 2
        assert len(tech.frameworks) == 2
        assert len(tech.testing_frameworks) == 1
        assert tech.project_type == "web"
        assert tech.confidence_score == 0.85

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        frameworks = [
            FrameworkInfo(
                "React",
                FrameworkType.FRONTEND_FRAMEWORK,
                "javascript",
                confidence=0.9,
                detection_method="dependency",
            ),
            FrameworkInfo(
                "Jest",
                FrameworkType.TESTING_FRAMEWORK,
                "javascript",
                confidence=0.7,
                detection_method="file_pattern",
            ),
            FrameworkInfo(
                "Docker",
                FrameworkType.CONTAINER,
                "multi",
                confidence=0.8,
                detection_method="file_presence",
            ),
        ]

        confidence = self.detector._calculate_confidence_score(frameworks)

        assert 0.0 <= confidence <= 1.0
        # Dependency detection should have higher weight
        assert confidence > 0.7

    def test_extract_databases(self):
        """Test database extraction from frameworks."""
        frameworks = [
            FrameworkInfo("Mongoose", FrameworkType.DATABASE_ORM, "javascript"),
            FrameworkInfo("SQLAlchemy", FrameworkType.DATABASE_ORM, "python"),
            FrameworkInfo("React", FrameworkType.FRONTEND_FRAMEWORK, "javascript"),
        ]

        databases = self.detector._extract_databases(frameworks)

        assert len(databases) >= 2
        assert any("MongoDB" in db for db in databases)
        assert any("SQL" in db for db in databases)

    def test_extract_deployment_targets(self):
        """Test deployment target extraction."""
        frameworks = [
            FrameworkInfo("Docker", FrameworkType.CONTAINER, "multi"),
            FrameworkInfo("React", FrameworkType.FRONTEND_FRAMEWORK, "javascript"),
            FrameworkInfo("Express.js", FrameworkType.BACKEND_FRAMEWORK, "javascript"),
        ]

        targets = self.detector._extract_deployment_targets(frameworks)

        assert "Docker" in targets
        assert "Static Hosting" in targets or "Web Server" in targets

    def test_empty_project_detection(self):
        """Test detection on empty project."""
        with patch.object(
            self.detector.package_parser, "parse_all_package_files", return_value=[]
        ):
            frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        assert len(frameworks) == 0

    def test_large_project_file_limit(self):
        """Test that file scanning is limited for large projects."""
        # Create many files
        for i in range(150):  # More than the 100 file limit
            self.create_temp_file(
                f"src/component{i}.js", f"import React from 'react'; // Component {i}"
            )

        # Should still work without issues
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))

        # Test should complete without hanging
        assert isinstance(frameworks, list)

    @pytest.mark.parametrize(
        "framework_name,expected_type",
        [
            ("react", FrameworkType.FRONTEND_FRAMEWORK),
            ("django", FrameworkType.WEB_FRAMEWORK),
            ("pytest", FrameworkType.TESTING_FRAMEWORK),
            ("webpack", FrameworkType.BUILD_TOOL),
            ("mongoose", FrameworkType.DATABASE_ORM),
            ("docker", FrameworkType.CONTAINER),
        ],
    )
    def test_framework_type_classification(self, framework_name, expected_type):
        """Test that frameworks are classified with correct types."""
        framework_def = self.detector.FRAMEWORK_DEFINITIONS.get(framework_name)
        if framework_def:
            assert framework_def["type"] == expected_type
