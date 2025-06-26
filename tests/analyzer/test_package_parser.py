"""Tests for package parser functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import toml

from airules.analyzer.package_parser import (
    DependencyInfo,
    PackageInfo,
    PackageParser,
    PackageParsingError,
)


class TestPackageParser:
    """Test suite for PackageParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PackageParser()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_file(self, filename: str, content: str) -> str:
        """Create a temporary file with given content."""
        file_path = self.temp_dir / filename
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    def test_find_package_files(self):
        """Test finding package files in directory."""
        # Create various package files
        self.create_temp_file("package.json", "{}")
        self.create_temp_file("requirements.txt", "")
        self.create_temp_file("Cargo.toml", "")
        self.create_temp_file("random.txt", "")  # Should be ignored

        found_files = self.parser.find_package_files(str(self.temp_dir))

        assert len(found_files) == 3
        assert any("package.json" in f for f in found_files)
        assert any("requirements.txt" in f for f in found_files)
        assert any("Cargo.toml" in f for f in found_files)

    def test_parse_npm_package_json(self):
        """Test parsing npm package.json file."""
        package_json_content = {
            "name": "test-project",
            "version": "1.0.0",
            "description": "Test project",
            "dependencies": {"react": "^18.0.0", "lodash": "4.17.21"},
            "devDependencies": {"jest": "^27.0.0", "eslint": "^8.0.0"},
            "optionalDependencies": {"fsevents": "^2.3.0"},
            "scripts": {"start": "react-scripts start", "build": "react-scripts build"},
            "engines": {"node": ">=14.0.0"},
        }

        file_path = self.create_temp_file(
            "package.json", json.dumps(package_json_content)
        )
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "javascript"
        assert package_info.build_system == "npm"
        assert len(package_info.dependencies) == 3  # react, lodash, fsevents
        assert len(package_info.dev_dependencies) == 2  # jest, eslint
        assert "start" in package_info.scripts
        assert package_info.metadata["name"] == "test-project"
        assert package_info.metadata["engines"]["node"] == ">=14.0.0"

    def test_parse_requirements_txt(self):
        """Test parsing Python requirements.txt file."""
        requirements_content = """
# This is a comment
requests>=2.25.0
django==3.2.0
flask[async]>=2.0.0
pytest  # dev dependency comment
-r other-requirements.txt
# Another comment
numpy~=1.21.0
"""

        file_path = self.create_temp_file("requirements.txt", requirements_content)
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "python"
        assert package_info.build_system == "pip"
        assert (
            len(package_info.dependencies) == 5
        )  # requests, django, flask, pytest, numpy

        # Check specific dependencies
        dep_names = [dep.name for dep in package_info.dependencies]
        assert "requests" in dep_names
        assert "django" in dep_names
        assert "flask" in dep_names
        assert "numpy" in dep_names

    def test_parse_dev_requirements_txt(self):
        """Test parsing dev requirements file."""
        requirements_content = "pytest>=6.0.0\nblack>=21.0.0"

        file_path = self.create_temp_file("requirements-dev.txt", requirements_content)
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert len(package_info.dependencies) == 0
        assert len(package_info.dev_dependencies) == 2
        assert package_info.metadata["is_dev_requirements"] is True

    def test_parse_pyproject_toml(self):
        """Test parsing pyproject.toml file."""
        pyproject_content = {
            "project": {
                "name": "test-project",
                "version": "1.0.0",
                "description": "Test Python project",
                "dependencies": ["requests>=2.25.0", "click>=8.0.0"],
                "optional-dependencies": {
                    "dev": ["pytest>=6.0.0", "black>=21.0.0"],
                    "docs": ["sphinx>=4.0.0"],
                },
                "requires-python": ">=3.8",
                "scripts": {"my-script": "mypackage.cli:main"},
            },
            "tool": {
                "poetry": {
                    "name": "test-project",
                    "version": "1.0.0",
                    "dependencies": {"python": "^3.8", "fastapi": "^0.68.0"},
                    "group": {"dev": {"dependencies": {"pytest": "^6.0.0"}}},
                }
            },
        }

        file_path = self.create_temp_file(
            "pyproject.toml", toml.dumps(pyproject_content)
        )
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "python"
        assert package_info.build_system == "poetry"
        assert len(package_info.dependencies) >= 3  # requests, click, fastapi + extras
        assert len(package_info.dev_dependencies) >= 1  # pytest
        assert "my-script" in package_info.scripts

    def test_parse_cargo_toml(self):
        """Test parsing Rust Cargo.toml file."""
        cargo_content = {
            "package": {
                "name": "test-project",
                "version": "0.1.0",
                "edition": "2021",
                "description": "Test Rust project",
            },
            "dependencies": {
                "serde": "1.0",
                "tokio": {"version": "1.0", "features": ["full"]},
                "reqwest": {"version": "0.11", "optional": True},
            },
            "dev-dependencies": {"proptest": "1.0"},
        }

        file_path = self.create_temp_file("Cargo.toml", toml.dumps(cargo_content))
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "rust"
        assert package_info.build_system == "cargo"
        assert len(package_info.dependencies) == 3  # serde, tokio, reqwest
        assert len(package_info.dev_dependencies) == 1  # proptest
        assert package_info.metadata["edition"] == "2021"

    def test_parse_go_mod(self):
        """Test parsing Go go.mod file."""
        go_mod_content = """module github.com/example/test-project

go 1.19

require (
    github.com/gin-gonic/gin v1.8.1
    github.com/stretchr/testify v1.8.0 // indirect
    gorm.io/gorm v1.23.0
)

replace github.com/old/package => github.com/new/package v1.0.0
"""

        file_path = self.create_temp_file("go.mod", go_mod_content)
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "go"
        assert package_info.build_system == "go_modules"
        assert len(package_info.dependencies) >= 3
        assert package_info.metadata["module"] == "github.com/example/test-project"
        assert package_info.metadata["go_version"] == "1.19"

    def test_parse_composer_json(self):
        """Test parsing PHP composer.json file."""
        composer_content = {
            "name": "example/test-project",
            "description": "Test PHP project",
            "require": {
                "php": "^8.0",
                "laravel/framework": "^9.0",
                "guzzlehttp/guzzle": "^7.0",
            },
            "require-dev": {"phpunit/phpunit": "^9.0", "mockery/mockery": "^1.0"},
            "scripts": {"test": "phpunit"},
        }

        file_path = self.create_temp_file("composer.json", json.dumps(composer_content))
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "php"
        assert package_info.build_system == "composer"
        assert len(package_info.dependencies) == 2  # laravel, guzzle (php excluded)
        assert len(package_info.dev_dependencies) == 2  # phpunit, mockery
        assert "test" in package_info.scripts

    def test_parse_gemfile(self):
        """Test parsing Ruby Gemfile."""
        gemfile_content = """
source 'https://rubygems.org'

gem 'rails', '~> 7.0'
gem 'pg', '~> 1.1'
gem 'puma', '~> 5.0'

group :development, :test do
  gem 'byebug', platforms: [:mri, :mingw, :x64_mingw]
  gem 'rspec-rails'
end

group :development do
  gem 'web-console', '>= 4.1.0'
end
"""

        file_path = self.create_temp_file("Gemfile", gemfile_content)
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "ruby"
        assert package_info.build_system == "bundler"
        # Note: This is a simplified parser, so exact counts may vary
        assert len(package_info.dependencies) >= 2
        assert len(package_info.dev_dependencies) >= 1

    def test_parse_maven_pom_xml(self):
        """Test parsing Maven pom.xml file."""
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    <description>Test Java project</description>

    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>5.3.0</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>"""

        file_path = self.create_temp_file("pom.xml", pom_content)
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "java"
        assert package_info.build_system == "maven"
        assert len(package_info.dependencies) == 1  # spring-core
        assert len(package_info.dev_dependencies) == 1  # junit
        assert package_info.metadata["name"] == "test-project"

    def test_parse_gradle_build_file(self):
        """Test parsing Gradle build.gradle file."""
        gradle_content = """
plugins {
    id 'java'
    id 'org.springframework.boot' version '2.5.0'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web:2.5.0'
    implementation 'com.fasterxml.jackson.core:jackson-core:2.12.0'
    testImplementation 'org.springframework.boot:spring-boot-starter-test:2.5.0'
    testImplementation 'junit:junit:4.13.2'
}
"""

        file_path = self.create_temp_file("build.gradle", gradle_content)
        package_info = self.parser.parse_package_file(file_path)

        assert package_info is not None
        assert package_info.language == "java"
        assert package_info.build_system == "gradle"
        assert len(package_info.dependencies) >= 1
        assert len(package_info.dev_dependencies) >= 1

    @pytest.mark.parametrize(
        "version_input,expected_name,expected_version",
        [
            ("requests>=2.25.0", "requests", ">=2.25.0"),
            ("django==3.2.0", "django", "==3.2.0"),
            ("flask[async]>=2.0.0", "flask", ">=2.0.0"),
            ("numpy~=1.21.0", "numpy", "~=1.21.0"),
            ("pytest", "pytest", None),
            ("git+https://github.com/user/repo.git#egg=package", "package", "git"),
            ("", None, None),  # Empty string
            ("invalid_package_spec!@#", None, None),  # Invalid spec
        ],
    )
    def test_parse_python_requirement(
        self, version_input, expected_name, expected_version
    ):
        """Test parsing individual Python requirement strings."""
        result = self.parser._parse_python_requirement(version_input)

        if expected_name is None:
            assert result is None
        else:
            assert result is not None
            assert result.name == expected_name
            assert result.version == expected_version

    def test_parse_unknown_file_type(self):
        """Test handling of unknown file types."""
        file_path = self.create_temp_file("unknown.file", "content")

        result = self.parser.parse_package_file(file_path)
        assert result is None
        assert len(self.parser.errors) > 0

    def test_parse_malformed_json(self):
        """Test handling of malformed JSON files."""
        file_path = self.create_temp_file("package.json", "{invalid json}")

        with pytest.raises(PackageParsingError):
            self.parser.parse_package_file(file_path)

    def test_parse_malformed_toml(self):
        """Test handling of malformed TOML files."""
        file_path = self.create_temp_file("pyproject.toml", "[invalid toml")

        with pytest.raises(PackageParsingError):
            self.parser.parse_package_file(file_path)

    def test_parse_all_package_files(self):
        """Test parsing all package files in a directory."""
        # Create multiple package files
        self.create_temp_file(
            "package.json", '{"name": "test", "dependencies": {"react": "18.0.0"}}'
        )
        self.create_temp_file("requirements.txt", "django>=3.0.0")
        self.create_temp_file(
            "Cargo.toml",
            toml.dumps({"package": {"name": "test"}, "dependencies": {"serde": "1.0"}}),
        )

        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))

        assert len(package_infos) == 3
        languages = {pkg.language for pkg in package_infos}
        assert "javascript" in languages
        assert "python" in languages
        assert "rust" in languages

    def test_empty_directory(self):
        """Test parsing empty directory."""
        package_infos = self.parser.parse_all_package_files(str(self.temp_dir))
        assert len(package_infos) == 0

    def test_dependency_info_dataclass(self):
        """Test DependencyInfo dataclass functionality."""
        dep = DependencyInfo(name="test-package", version="1.0.0", is_dev=True)
        assert dep.name == "test-package"
        assert dep.version == "1.0.0"
        assert dep.is_dev is True
        assert dep.is_optional is False
        assert dep.extras == []

        # Test with extras
        dep_with_extras = DependencyInfo(name="test", extras=["extra1", "extra2"])
        assert len(dep_with_extras.extras) == 2

    def test_package_info_dataclass(self):
        """Test PackageInfo dataclass functionality."""
        deps = [DependencyInfo(name="dep1", version="1.0.0")]
        dev_deps = [DependencyInfo(name="dev-dep1", version="2.0.0", is_dev=True)]
        scripts = {"test": "pytest", "build": "python setup.py build"}
        metadata = {"name": "test-project", "version": "1.0.0"}

        pkg_info = PackageInfo(
            file_path="/path/to/package.json",
            language="javascript",
            build_system="npm",
            dependencies=deps,
            dev_dependencies=dev_deps,
            scripts=scripts,
            metadata=metadata,
        )

        assert pkg_info.file_path == "/path/to/package.json"
        assert pkg_info.language == "javascript"
        assert pkg_info.build_system == "npm"
        assert len(pkg_info.dependencies) == 1
        assert len(pkg_info.dev_dependencies) == 1
        assert pkg_info.scripts["test"] == "pytest"
        assert pkg_info.metadata["name"] == "test-project"

    def test_error_handling_and_logging(self):
        """Test error handling and logging functionality."""
        # Create file with permission issues (simulate)
        file_path = self.create_temp_file("package.json", '{"valid": "json"}')

        # Test with non-existent file (but known file type)
        with pytest.raises(PackageParsingError):
            self.parser.parse_package_file("/non/existent/package.json")

        # Clear errors
        self.parser.errors.clear()

        # Parse valid file
        result = self.parser.parse_package_file(file_path)
        assert result is not None
        assert len(self.parser.errors) == 0

    def test_get_text_helper(self):
        """Test XML text extraction helper method."""
        import xml.etree.ElementTree as ET

        # Test with valid element
        xml_string = "<test>Hello World</test>"
        element = ET.fromstring(xml_string)
        assert self.parser._get_text(element) == "Hello World"

        # Test with None element
        assert self.parser._get_text(None) == ""

        # Test with empty element
        empty_xml = "<test></test>"
        empty_element = ET.fromstring(empty_xml)
        assert self.parser._get_text(empty_element) == ""

        # Test with default value
        assert self.parser._get_text(None, "default") == "default"
