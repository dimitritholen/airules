"""Integration tests for the analyzer module components."""

import json
import tempfile
from pathlib import Path

import pytest
import toml

from airules.analyzer import DependencyAnalyzer, FrameworkDetector, PackageParser
from airules.analyzer.dependency_analyzer import DependencyHealth, SecurityRisk
from airules.analyzer.framework_detector import FrameworkType


class TestAnalyzerIntegration:
    """Integration tests for analyzer components working together."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.parser = PackageParser()
        self.detector = FrameworkDetector()
        self.analyzer = DependencyAnalyzer()

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

    def test_react_project_full_analysis(self):
        """Test complete analysis of a React project."""
        # Create React project structure
        package_json = {
            "name": "my-react-app",
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "lodash": "4.17.11",  # Vulnerable version
                "axios": "^1.0.0",
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "eslint": "^8.0.0",
                "webpack": "^5.0.0",
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "jest",
            },
        }

        self.create_temp_file("package.json", json.dumps(package_json))
        self.create_temp_file(
            "src/App.jsx",
            """
import React from 'react';
import lodash from 'lodash';

function App() {
  return (
    <div className="App">
      <h1>Hello React!</h1>
    </div>
  );
}

export default App;
""",
        )
        self.create_temp_file(
            "src/index.js",
            """
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
""",
        )
        self.create_temp_file(
            "public/index.html",
            """
<!DOCTYPE html>
<html>
<head><title>React App</title></head>
<body><div id="root"></div></body>
</html>
""",
        )

        # Test package parsing
        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))
        assert len(package_infos) == 1

        package_info = package_infos[0]
        assert package_info.language == "javascript"
        assert package_info.build_system == "npm"
        assert len(package_info.dependencies) == 4  # react, react-dom, lodash, axios
        assert len(package_info.dev_dependencies) == 3  # jest, eslint, webpack

        # Test framework detection
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))
        framework_names = [f.name for f in frameworks]

        assert "React" in framework_names
        assert "Jest" in framework_names
        assert "webpack" in framework_names

        # Check React detection details
        react_fw = next(f for f in frameworks if f.name == "React")
        assert react_fw.type == FrameworkType.FRONTEND_FRAMEWORK
        assert react_fw.language == "javascript"

        # Test project technology analysis
        tech_analysis = self.detector.get_project_technology(str(self.temp_dir))
        assert "javascript" in tech_analysis.languages
        assert tech_analysis.project_type == "web"
        assert len(tech_analysis.testing_frameworks) >= 1
        assert len(tech_analysis.build_tools) >= 1

        # Test dependency analysis
        dep_analysis = self.analyzer.analyze_project_dependencies(str(self.temp_dir))

        assert dep_analysis.total_dependencies == 7  # All dependencies
        assert dep_analysis.direct_dependencies == 4
        assert dep_analysis.dev_dependencies == 3
        assert dep_analysis.security_vulnerabilities >= 1  # lodash vulnerability

        # Check for lodash vulnerability
        lodash_report = next(
            (r for r in dep_analysis.dependency_reports if r.name == "lodash"), None
        )
        assert lodash_report is not None
        assert lodash_report.health == DependencyHealth.VULNERABLE
        assert len(lodash_report.vulnerabilities) >= 1

        # Check recommendations
        assert len(dep_analysis.recommendations) > 0
        rec_text = " ".join(dep_analysis.recommendations).lower()
        assert "vulnerable" in rec_text or "update" in rec_text

    def test_django_project_full_analysis(self):
        """Test complete analysis of a Django project."""
        # Create Django project structure
        pyproject_toml = {
            "project": {
                "name": "my-django-app",
                "version": "1.0.0",
                "dependencies": [
                    "django>=3.2.0",
                    "djangorestframework>=3.12.0",
                    "requests>=2.25.0",
                    "psycopg2-binary>=2.8.0",
                ],
                "optional-dependencies": {
                    "dev": ["pytest>=6.0.0", "black>=21.0.0", "flake8>=3.9.0"]
                },
            },
            "tool": {"poetry": {"dependencies": {"python": "^3.8"}}},
        }

        self.create_temp_file("pyproject.toml", toml.dumps(pyproject_toml))
        self.create_temp_file(
            "manage.py",
            """
#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
""",
        )
        self.create_temp_file(
            "myproject/settings.py",
            """
from django.conf import settings

DEBUG = True
INSTALLED_APPS = [
    'django.contrib.admin',
    'rest_framework',
]
""",
        )
        self.create_temp_file(
            "myproject/urls.py",
            """
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
""",
        )
        self.create_temp_file(
            "apps/myapp/models.py",
            """
from django.db import models

class MyModel(models.Model):
    name = models.CharField(max_length=100)
""",
        )

        # Test package parsing
        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))
        assert len(package_infos) == 1

        package_info = package_infos[0]
        assert package_info.language == "python"
        assert "poetry" in package_info.build_system

        # Test framework detection
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))
        framework_names = [f.name for f in frameworks]

        assert "Django" in framework_names
        assert "pytest" in framework_names

        # Check Django detection
        django_fw = next(f for f in frameworks if f.name == "Django")
        assert django_fw.type == FrameworkType.WEB_FRAMEWORK
        assert django_fw.language == "python"

        # Test project technology analysis
        tech_analysis = self.detector.get_project_technology(str(self.temp_dir))
        assert "python" in tech_analysis.languages
        assert tech_analysis.project_type == "web"

        # Test dependency analysis
        dep_analysis = self.analyzer.analyze_project_dependencies(str(self.temp_dir))

        assert dep_analysis.total_dependencies >= 4
        assert dep_analysis.health_score > 0.5  # Should be healthy

        # Check framework analysis integration
        assert dep_analysis.framework_analysis is not None
        assert "Django" in dep_analysis.framework_analysis["detected_frameworks"]

    def test_rust_project_full_analysis(self):
        """Test complete analysis of a Rust project."""
        # Create Rust project structure
        cargo_toml = {
            "package": {"name": "my-rust-app", "version": "0.1.0", "edition": "2021"},
            "dependencies": {
                "actix-web": "4.0",
                "tokio": {"version": "1.0", "features": ["full"]},
                "serde": {"version": "1.0", "features": ["derive"]},
                "serde_json": "1.0",
            },
            "dev-dependencies": {"proptest": "1.0"},
        }

        self.create_temp_file("Cargo.toml", toml.dumps(cargo_toml))
        self.create_temp_file(
            "src/main.rs",
            """
use actix_web::{web, App, HttpServer, HttpResponse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct User {
    name: String,
    age: u32,
}

async fn hello() -> HttpResponse {
    HttpResponse::Ok().json(User {
        name: "Hello".to_string(),
        age: 25,
    })
}

#[tokio::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/hello", web::get().to(hello))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
""",
        )

        # Test package parsing
        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))
        assert len(package_infos) == 1

        package_info = package_infos[0]
        assert package_info.language == "rust"
        assert package_info.build_system == "cargo"
        assert len(package_info.dependencies) == 4
        assert len(package_info.dev_dependencies) == 1

        # Test framework detection
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))
        framework_names = [f.name for f in frameworks]

        assert "Actix Web" in framework_names
        assert "Tokio" in framework_names
        assert "Serde" in framework_names

        # Test project technology analysis
        tech_analysis = self.detector.get_project_technology(str(self.temp_dir))
        assert "rust" in tech_analysis.languages
        assert tech_analysis.project_type in ["web", "library"]

    def test_multi_language_project(self):
        """Test analysis of a project with multiple languages."""
        # Create a full-stack project with Node.js backend and Python ML service

        # Node.js backend
        backend_package = {
            "name": "fullstack-backend",
            "dependencies": {
                "express": "^4.18.0",
                "mongoose": "^6.0.0",
                "cors": "^2.8.0",
            },
            "devDependencies": {"jest": "^29.0.0", "supertest": "^6.0.0"},
        }
        self.create_temp_file("backend/package.json", json.dumps(backend_package))

        # Python ML service
        requirements_txt = """
fastapi>=0.68.0
uvicorn>=0.15.0
pandas>=1.3.0
scikit-learn>=1.0.0
pytest>=6.0.0
"""
        self.create_temp_file("ml-service/requirements.txt", requirements_txt)

        # React frontend
        frontend_package = {
            "name": "fullstack-frontend",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
                "axios": "^1.0.0",
            },
            "devDependencies": {"vite": "^4.0.0", "eslint": "^8.0.0"},
        }
        self.create_temp_file("frontend/package.json", json.dumps(frontend_package))

        # Test parsing finds all package files
        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))
        assert len(package_infos) == 3

        languages = {pkg.language for pkg in package_infos}
        assert "javascript" in languages
        assert "python" in languages

        # Test framework detection across languages
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))
        framework_names = [f.name for f in frameworks]

        # Should detect frameworks from all languages
        assert "React" in framework_names
        assert "Express.js" in framework_names
        assert "FastAPI" in framework_names
        assert "Pandas" in framework_names

        # Test project technology analysis
        tech_analysis = self.detector.get_project_technology(str(self.temp_dir))
        assert len(tech_analysis.languages) >= 2
        assert tech_analysis.project_type == "web"  # Should detect as web project

        # Test dependency analysis
        dep_analysis = self.analyzer.analyze_project_dependencies(str(self.temp_dir))
        assert dep_analysis.total_dependencies >= 8  # Dependencies from all packages

        # Should have framework analysis
        assert dep_analysis.framework_analysis is not None
        detected_frameworks = dep_analysis.framework_analysis["detected_frameworks"]
        assert len(detected_frameworks) >= 4

    def test_mobile_project_analysis(self):
        """Test analysis of a React Native mobile project."""
        # Create React Native project
        package_json = {
            "name": "my-mobile-app",
            "dependencies": {
                "react": "18.0.0",
                "react-native": "0.70.0",
                "@react-navigation/native": "^6.0.0",
                "react-native-vector-icons": "^9.0.0",
            },
            "devDependencies": {
                "metro": "^0.70.0",
                "jest": "^29.0.0",
                "detox": "^19.0.0",
            },
        }

        self.create_temp_file("package.json", json.dumps(package_json))
        self.create_temp_file("metro.config.js", "module.exports = {};")
        self.create_temp_file("android/build.gradle", "// Android build file")
        self.create_temp_file("ios/Podfile", "# iOS Podfile")
        self.create_temp_file(
            "App.tsx",
            """
import React from 'react';
import {View, Text} from 'react-native';

const App = () => {
  return (
    <View>
      <Text>Hello React Native!</Text>
    </View>
  );
};

export default App;
""",
        )

        # Test framework detection
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))
        framework_names = [f.name for f in frameworks]

        assert "React Native" in framework_names
        assert "React" in framework_names

        # Test project type detection
        tech_analysis = self.detector.get_project_technology(str(self.temp_dir))
        assert tech_analysis.project_type == "mobile"

        # Check deployment targets
        assert "Mobile App Store" in tech_analysis.deployment_targets

    def test_containerized_project_analysis(self):
        """Test analysis of a containerized project."""
        # Create project with Docker
        package_json = {
            "name": "containerized-app",
            "dependencies": {"express": "^4.18.0"},
        }

        self.create_temp_file("package.json", json.dumps(package_json))
        self.create_temp_file(
            "Dockerfile",
            """
FROM node:16
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
""",
        )
        self.create_temp_file(
            "docker-compose.yml",
            """
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: myapp
""",
        )
        self.create_temp_file(
            ".dockerignore",
            """
node_modules
.git
""",
        )

        # Test framework detection
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))
        framework_names = [f.name for f in frameworks]

        assert "Express.js" in framework_names
        assert "Docker" in framework_names

        # Test project technology analysis
        tech_analysis = self.detector.get_project_technology(str(self.temp_dir))
        assert "Docker" in tech_analysis.deployment_targets

    def test_end_to_end_analysis_workflow(self):
        """Test complete end-to-end analysis workflow."""
        # Create a complex project
        package_json = {
            "name": "complex-project",
            "dependencies": {
                "react": "^18.0.0",
                "express": "^4.18.0",
                "lodash": "4.17.11",  # Vulnerable
                "moment": "^2.29.0",  # Deprecated
                "mongoose": "^6.0.0",
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "webpack": "^5.0.0",
                "eslint": "^8.0.0",
            },
        }

        self.create_temp_file("package.json", json.dumps(package_json))
        self.create_temp_file("src/App.jsx", "import React from 'react';")
        self.create_temp_file("server.js", "const express = require('express');")

        # Step 1: Parse packages
        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))
        assert len(package_infos) == 1

        # Step 2: Detect frameworks
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))
        assert len(frameworks) >= 5  # React, Express, Jest, webpack, Mongoose

        # Step 3: Analyze dependencies
        dep_analysis = self.analyzer.analyze_project_dependencies(str(self.temp_dir))

        # Step 4: Verify comprehensive analysis
        assert dep_analysis.total_dependencies == 8
        assert dep_analysis.security_vulnerabilities >= 1  # lodash
        assert (
            dep_analysis.health_score < 1.0
        )  # Due to vulnerabilities and deprecated packages

        # Step 5: Check recommendations
        recommendations = dep_analysis.recommendations
        assert len(recommendations) > 0

        rec_text = " ".join(recommendations).lower()
        assert "vulnerable" in rec_text or "update" in rec_text
        assert "deprecated" in rec_text or "replace" in rec_text

        # Step 6: Check framework suggestions
        suggestions = self.detector.get_framework_suggestions(str(self.temp_dir))
        assert isinstance(suggestions, dict)

        # Step 7: Check compatibility analysis
        compatibility = self.detector.analyze_compatibility(frameworks)
        assert "issues" in compatibility
        assert "recommendations" in compatibility
        assert "compatibility_score" in compatibility

        # Step 8: Generate dependency graph
        graph = self.analyzer.generate_dependency_graph(str(self.temp_dir))
        assert len(graph["nodes"]) >= 9  # 1 package file + 8 dependencies
        assert len(graph["edges"]) >= 8

        # Step 9: Check license compatibility
        license_compat = self.analyzer.check_license_compatibility(
            dep_analysis.dependency_reports
        )
        assert "license_distribution" in license_compat
        assert "compatibility_score" in license_compat

        # Step 10: Export reports
        json_report = self.analyzer.export_report(dep_analysis, "json")
        assert isinstance(json_report, str)
        assert len(json_report) > 100

        md_report = self.analyzer.export_report(dep_analysis, "markdown")
        assert isinstance(md_report, str)
        assert "# Dependency Analysis Report" in md_report

    def test_error_handling_integration(self):
        """Test error handling across integrated components."""
        # Create malformed files
        self.create_temp_file("package.json", "{invalid json")
        self.create_temp_file("requirements.txt", "")

        # Should handle errors gracefully
        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))
        # Should parse requirements.txt but fail on package.json
        assert len(package_infos) <= 1
        assert len(self.parser.errors) > 0

        # Framework detection should still work
        frameworks = self.detector.detect_frameworks(str(self.temp_dir))
        assert isinstance(frameworks, list)

        # Dependency analysis should handle empty results
        dep_analysis = self.analyzer.analyze_project_dependencies(str(self.temp_dir))
        assert dep_analysis.total_dependencies >= 0
        assert isinstance(dep_analysis.recommendations, list)

    def test_performance_with_large_project(self):
        """Test performance with a simulated large project."""
        # Create many package files and source files
        for i in range(10):
            small_package = {
                "name": f"module-{i}",
                "dependencies": {"lodash": "^4.17.0", "axios": "^1.0.0"},
            }
            self.create_temp_file(
                f"modules/module-{i}/package.json", json.dumps(small_package)
            )

        # Create many source files
        for i in range(50):
            self.create_temp_file(
                f"src/component-{i}.js", f"import React from 'react'; // Component {i}"
            )

        # Should complete analysis without hanging
        import time

        start_time = time.time()

        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))
        self.detector.detect_frameworks(str(self.temp_dir))
        dep_analysis = self.analyzer.analyze_project_dependencies(str(self.temp_dir))

        end_time = time.time()

        # Should complete in reasonable time (less than 10 seconds for this test)
        assert (end_time - start_time) < 10.0

        # Should still produce meaningful results
        assert len(package_infos) == 10
        assert dep_analysis.total_dependencies > 0
