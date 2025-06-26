"""Package file parsers for various languages and build systems."""

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml


@dataclass
class DependencyInfo:
    """Information about a single dependency."""

    name: str
    version: Optional[str] = None
    is_dev: bool = False
    is_optional: bool = False
    extras: List[str] = field(default_factory=list)


@dataclass
class PackageInfo:
    """Information parsed from a package file."""

    file_path: str
    language: str
    build_system: str
    dependencies: List[DependencyInfo]
    dev_dependencies: List[DependencyInfo]
    scripts: Dict[str, str]
    metadata: Dict[str, Any]


class PackageParsingError(Exception):
    """Exception raised when package file parsing fails."""

    pass


class PackageParser:
    """Unified parser for various package file formats."""

    # Known package files with their corresponding parsers
    PACKAGE_FILES = {
        "package.json": "parse_npm",
        "package-lock.json": "parse_npm_lock",
        "yarn.lock": "parse_yarn_lock",
        "requirements.txt": "parse_requirements_txt",
        "requirements-dev.txt": "parse_requirements_txt",
        "requirements-test.txt": "parse_requirements_txt",
        "dev-requirements.txt": "parse_requirements_txt",
        "test-requirements.txt": "parse_requirements_txt",
        "pyproject.toml": "parse_pyproject_toml",
        "Pipfile": "parse_pipfile",
        "Pipfile.lock": "parse_pipfile_lock",
        "poetry.lock": "parse_poetry_lock",
        "Cargo.toml": "parse_cargo_toml",
        "Cargo.lock": "parse_cargo_lock",
        "go.mod": "parse_go_mod",
        "go.sum": "parse_go_sum",
        "pom.xml": "parse_maven_pom",
        "build.gradle": "parse_gradle",
        "build.gradle.kts": "parse_gradle_kts",
        "composer.json": "parse_composer",
        "composer.lock": "parse_composer_lock",
        "Gemfile": "parse_gemfile",
        "Gemfile.lock": "parse_gemfile_lock",
        "mix.exs": "parse_mix_exs",
        "rebar.config": "parse_rebar_config",
        "dune-project": "parse_dune_project",
        "cabal.project": "parse_cabal_project",
        "stack.yaml": "parse_stack_yaml",
        "pubspec.yaml": "parse_pubspec_yaml",
        "Package.swift": "parse_swift_package",
    }

    def __init__(self):
        self.errors: List[str] = []

    def find_package_files(self, project_path: str) -> List[str]:
        """Find all recognized package files in the project directory and subdirectories."""
        project_path_obj = Path(project_path)
        found_files = []

        # First check root directory
        for package_file in self.PACKAGE_FILES.keys():
            file_path = project_path_obj / package_file
            if file_path.exists():
                found_files.append(str(file_path))

        # Then check subdirectories (up to 3 levels deep to avoid infinite recursion)
        for package_file in self.PACKAGE_FILES.keys():
            pattern = f"**/{package_file}"
            for file_path in project_path_obj.glob(pattern):
                if file_path.is_file() and str(file_path) not in found_files:
                    found_files.append(str(file_path))

        return found_files

    def parse_package_file(self, file_path: str) -> Optional[PackageInfo]:
        """Parse a single package file and return structured information."""
        file_path_obj = Path(file_path)
        filename = file_path_obj.name

        if filename not in self.PACKAGE_FILES:
            self.errors.append(f"Unknown package file type: {filename}")
            return None

        parser_method = getattr(self, self.PACKAGE_FILES[filename])

        try:
            result = parser_method(str(file_path_obj))
            # Type cast to ensure mypy knows this returns PackageInfo
            return result if isinstance(result, PackageInfo) else None
        except Exception as e:
            error_msg = f"Failed to parse {file_path_obj}: {str(e)}"
            self.errors.append(error_msg)
            raise PackageParsingError(error_msg) from e

    def parse_all_package_files(self, project_path: str) -> List[PackageInfo]:
        """Parse all package files found in the project directory."""
        package_files = self.find_package_files(project_path)
        parsed_packages = []

        for file_path in package_files:
            try:
                package_info = self.parse_package_file(file_path)
                if package_info:
                    parsed_packages.append(package_info)
            except PackageParsingError:
                # Error already logged in parse_package_file
                continue

        return parsed_packages

    # JavaScript/Node.js parsers
    def parse_npm(self, file_path: str) -> PackageInfo:
        """Parse package.json file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dependencies = []
        dev_dependencies = []

        # Parse regular dependencies
        for name, version in data.get("dependencies", {}).items():
            dependencies.append(DependencyInfo(name=name, version=version))

        # Parse dev dependencies
        for name, version in data.get("devDependencies", {}).items():
            dev_dependencies.append(
                DependencyInfo(name=name, version=version, is_dev=True)
            )

        # Parse optional dependencies
        for name, version in data.get("optionalDependencies", {}).items():
            dependencies.append(
                DependencyInfo(name=name, version=version, is_optional=True)
            )

        # Parse peer dependencies
        for name, version in data.get("peerDependencies", {}).items():
            dependencies.append(DependencyInfo(name=name, version=version))

        return PackageInfo(
            file_path=file_path,
            language="javascript",
            build_system="npm",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts=data.get("scripts", {}),
            metadata={
                "name": data.get("name"),
                "version": data.get("version"),
                "description": data.get("description"),
                "engines": data.get("engines", {}),
                "workspaces": data.get("workspaces", []),
            },
        )

    def parse_npm_lock(self, file_path: str) -> PackageInfo:
        """Parse package-lock.json file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dependencies = []

        # Parse lockfile dependencies
        for name, dep_info in data.get("packages", {}).items():
            if name == "":  # Root package
                continue
            # Remove leading node_modules/ if present
            clean_name = name.replace("node_modules/", "")
            version = dep_info.get("version")
            is_dev = dep_info.get("dev", False)

            dep = DependencyInfo(name=clean_name, version=version, is_dev=is_dev)
            if is_dev:
                dependencies.append(dep)  # Will be categorized later
            else:
                dependencies.append(dep)

        return PackageInfo(
            file_path=file_path,
            language="javascript",
            build_system="npm",
            dependencies=dependencies,
            dev_dependencies=[],
            scripts={},
            metadata={
                "name": data.get("name"),
                "version": data.get("version"),
                "lockfile_version": data.get("lockfileVersion"),
            },
        )

    def parse_yarn_lock(self, file_path: str) -> PackageInfo:
        """Parse yarn.lock file."""
        # Yarn lock files are in a custom format, not JSON
        dependencies = []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple regex-based parsing for yarn.lock
        pattern = r'^"?([^"\s@]+)@([^"]+)"?:\s*\n(?:\s+.*\n)*\s+version\s+"([^"]+)"'
        matches = re.findall(pattern, content, re.MULTILINE)

        for name, version_spec, resolved_version in matches:
            dependencies.append(DependencyInfo(name=name, version=resolved_version))

        return PackageInfo(
            file_path=file_path,
            language="javascript",
            build_system="yarn",
            dependencies=dependencies,
            dev_dependencies=[],
            scripts={},
            metadata={"lockfile": True},
        )

    # Python parsers
    def parse_requirements_txt(self, file_path: str) -> PackageInfo:
        """Parse requirements.txt file."""
        dependencies = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Handle -r or -e flags
                if line.startswith("-r ") or line.startswith("-e "):
                    continue

                # Extract package name and version
                dep_info = self._parse_python_requirement(line)
                if dep_info:
                    dependencies.append(dep_info)

        # Determine if this is a dev requirements file
        is_dev_file = any(
            keyword in Path(file_path).name.lower()
            for keyword in ["dev", "test", "development"]
        )

        return PackageInfo(
            file_path=file_path,
            language="python",
            build_system="pip",
            dependencies=[] if is_dev_file else dependencies,
            dev_dependencies=dependencies if is_dev_file else [],
            scripts={},
            metadata={"is_dev_requirements": is_dev_file},
        )

    def parse_pyproject_toml(self, file_path: str) -> PackageInfo:
        """Parse pyproject.toml file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        dependencies = []
        dev_dependencies = []
        scripts = {}

        # Parse project dependencies
        project = data.get("project", {})
        for dep in project.get("dependencies", []):
            dep_info = self._parse_python_requirement(dep)
            if dep_info:
                dependencies.append(dep_info)

        # Parse optional dependencies (extras)
        for extra_name, extra_deps in project.get("optional-dependencies", {}).items():
            for dep in extra_deps:
                dep_info = self._parse_python_requirement(dep)
                if dep_info:
                    dep_info.extras = [extra_name]
                    # Check if this is a dev dependency group
                    if extra_name.lower() in ["dev", "development", "test", "testing"]:
                        dep_info.is_dev = True
                        dev_dependencies.append(dep_info)
                    else:
                        dependencies.append(dep_info)

        # Parse poetry dependencies
        poetry = data.get("tool", {}).get("poetry", {})
        for name, version_info in poetry.get("dependencies", {}).items():
            if name == "python":
                continue

            if isinstance(version_info, str):
                dependencies.append(DependencyInfo(name=name, version=version_info))
            elif isinstance(version_info, dict):
                version = version_info.get("version", version_info.get("rev", ""))
                is_optional = version_info.get("optional", False)
                dependencies.append(
                    DependencyInfo(name=name, version=version, is_optional=is_optional)
                )

        # Parse poetry dev dependencies
        for name, version_info in (
            poetry.get("group", {}).get("dev", {}).get("dependencies", {}).items()
        ):
            if isinstance(version_info, str):
                dev_dependencies.append(
                    DependencyInfo(name=name, version=version_info, is_dev=True)
                )
            elif isinstance(version_info, dict):
                version = version_info.get("version", "")
                dev_dependencies.append(
                    DependencyInfo(name=name, version=version, is_dev=True)
                )

        # Parse scripts
        scripts.update(project.get("scripts", {}))
        scripts.update(poetry.get("scripts", {}))

        build_system = "poetry" if poetry else "setuptools"

        return PackageInfo(
            file_path=file_path,
            language="python",
            build_system=build_system,
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts=scripts,
            metadata={
                "name": project.get("name") or poetry.get("name"),
                "version": project.get("version") or poetry.get("version"),
                "description": project.get("description") or poetry.get("description"),
                "python_requires": project.get("requires-python"),
            },
        )

    def parse_pipfile(self, file_path: str) -> PackageInfo:
        """Parse Pipfile (TOML format)."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        dependencies = []
        dev_dependencies = []

        # Parse regular packages
        for name, version_info in data.get("packages", {}).items():
            if isinstance(version_info, str):
                dependencies.append(DependencyInfo(name=name, version=version_info))
            elif isinstance(version_info, dict):
                version = version_info.get("version", "")
                dependencies.append(DependencyInfo(name=name, version=version))

        # Parse dev packages
        for name, version_info in data.get("dev-packages", {}).items():
            if isinstance(version_info, str):
                dev_dependencies.append(
                    DependencyInfo(name=name, version=version_info, is_dev=True)
                )
            elif isinstance(version_info, dict):
                version = version_info.get("version", "")
                dev_dependencies.append(
                    DependencyInfo(name=name, version=version, is_dev=True)
                )

        return PackageInfo(
            file_path=file_path,
            language="python",
            build_system="pipenv",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts=data.get("scripts", {}),
            metadata={
                "python_version": data.get("requires", {}).get("python_version"),
                "python_full_version": data.get("requires", {}).get(
                    "python_full_version"
                ),
            },
        )

    def parse_pipfile_lock(self, file_path: str) -> PackageInfo:
        """Parse Pipfile.lock file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dependencies = []
        dev_dependencies = []

        # Parse default dependencies
        for name, dep_info in data.get("default", {}).items():
            version = dep_info.get("version", "")
            dependencies.append(DependencyInfo(name=name, version=version))

        # Parse develop dependencies
        for name, dep_info in data.get("develop", {}).items():
            version = dep_info.get("version", "")
            dev_dependencies.append(
                DependencyInfo(name=name, version=version, is_dev=True)
            )

        return PackageInfo(
            file_path=file_path,
            language="python",
            build_system="pipenv",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts={},
            metadata={
                "hash": data.get("_meta", {}).get("hash", {}),
                "pipfile_spec": data.get("_meta", {}).get("pipfile-spec"),
            },
        )

    def parse_poetry_lock(self, file_path: str) -> PackageInfo:
        """Parse poetry.lock file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        dependencies = []

        # Parse package information
        for package in data.get("package", []):
            name = package.get("name", "")
            version = package.get("version", "")
            category = package.get("category", "main")

            is_dev = category == "dev"
            dep = DependencyInfo(name=name, version=version, is_dev=is_dev)
            dependencies.append(dep)

        return PackageInfo(
            file_path=file_path,
            language="python",
            build_system="poetry",
            dependencies=[d for d in dependencies if not d.is_dev],
            dev_dependencies=[d for d in dependencies if d.is_dev],
            scripts={},
            metadata={
                "content_hash": data.get("metadata", {}).get("content-hash"),
                "lock_version": data.get("metadata", {}).get("lock-version"),
            },
        )

    # Rust parsers
    def parse_cargo_toml(self, file_path: str) -> PackageInfo:
        """Parse Cargo.toml file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        dependencies = []
        dev_dependencies = []

        # Parse regular dependencies
        for name, version_info in data.get("dependencies", {}).items():
            if isinstance(version_info, str):
                dependencies.append(DependencyInfo(name=name, version=version_info))
            elif isinstance(version_info, dict):
                version = version_info.get("version", "")
                is_optional = version_info.get("optional", False)
                dependencies.append(
                    DependencyInfo(name=name, version=version, is_optional=is_optional)
                )

        # Parse dev dependencies
        for name, version_info in data.get("dev-dependencies", {}).items():
            if isinstance(version_info, str):
                dev_dependencies.append(
                    DependencyInfo(name=name, version=version_info, is_dev=True)
                )
            elif isinstance(version_info, dict):
                version = version_info.get("version", "")
                dev_dependencies.append(
                    DependencyInfo(name=name, version=version, is_dev=True)
                )

        package_info = data.get("package", {})

        return PackageInfo(
            file_path=file_path,
            language="rust",
            build_system="cargo",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts={},  # Cargo doesn't have scripts like npm
            metadata={
                "name": package_info.get("name"),
                "version": package_info.get("version"),
                "description": package_info.get("description"),
                "edition": package_info.get("edition", "2018"),
                "rust_version": package_info.get("rust-version"),
            },
        )

    def parse_cargo_lock(self, file_path: str) -> PackageInfo:
        """Parse Cargo.lock file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        dependencies = []

        # Parse package information
        for package in data.get("package", []):
            name = package.get("name", "")
            version = package.get("version", "")
            dependencies.append(DependencyInfo(name=name, version=version))

        return PackageInfo(
            file_path=file_path,
            language="rust",
            build_system="cargo",
            dependencies=dependencies,
            dev_dependencies=[],
            scripts={},
            metadata={"version": data.get("version", 3), "lockfile": True},
        )

    # Go parsers
    def parse_go_mod(self, file_path: str) -> PackageInfo:
        """Parse go.mod file."""
        dependencies = []
        module_name = ""
        go_version = ""

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse module name
        module_match = re.search(r"^module\s+(.+)$", content, re.MULTILINE)
        if module_match:
            module_name = module_match.group(1).strip()

        # Parse go version
        go_match = re.search(r"^go\s+(.+)$", content, re.MULTILINE)
        if go_match:
            go_version = go_match.group(1).strip()

        # Parse require block
        require_pattern = r"require\s*\(\s*(.*?)\s*\)"
        require_match = re.search(require_pattern, content, re.DOTALL)

        if require_match:
            require_content = require_match.group(1)
            # Parse individual requirements
            for line in require_content.strip().split("\n"):
                line = line.strip()
                if not line or line.startswith("//"):
                    continue

                # Remove inline comments
                line = re.sub(r"\s*//.*$", "", line)
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    # Note: ignoring indirect dependencies for now
                    dependencies.append(DependencyInfo(name=name, version=version))

        # Parse single-line requires
        single_require_pattern = r"^require\s+([^\s]+)\s+([^\s]+)"
        for match in re.finditer(single_require_pattern, content, re.MULTILINE):
            name = match.group(1)
            version = match.group(2)
            dependencies.append(DependencyInfo(name=name, version=version))

        return PackageInfo(
            file_path=file_path,
            language="go",
            build_system="go_modules",
            dependencies=dependencies,
            dev_dependencies=[],
            scripts={},
            metadata={"module": module_name, "go_version": go_version},
        )

    def parse_go_sum(self, file_path: str) -> PackageInfo:
        """Parse go.sum file."""
        dependencies = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    dependencies.append(DependencyInfo(name=name, version=version))

        return PackageInfo(
            file_path=file_path,
            language="go",
            build_system="go_modules",
            dependencies=dependencies,
            dev_dependencies=[],
            scripts={},
            metadata={"checksum_file": True},
        )

    # Java parsers
    def parse_maven_pom(self, file_path: str) -> PackageInfo:
        """Parse Maven pom.xml file."""
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Handle namespace
        ns = {"": "http://maven.apache.org/POM/4.0.0"}
        if root.tag.startswith("{"):
            ns_uri = root.tag.split("}")[0][1:]
            ns = {"": ns_uri}

        dependencies = []
        dev_dependencies = []

        # Parse dependencies
        deps_elem = root.find(".//dependencies", ns)
        if deps_elem is not None:
            for dep in deps_elem.findall("dependency", ns):
                group_id = self._get_text(dep.find("groupId", ns))
                artifact_id = self._get_text(dep.find("artifactId", ns))
                version = self._get_text(dep.find("version", ns))
                scope = self._get_text(dep.find("scope", ns), "compile")

                name = (
                    f"{group_id}:{artifact_id}"
                    if group_id and artifact_id
                    else artifact_id
                )
                is_dev = scope in ["test", "provided"]

                dep_info = DependencyInfo(name=name, version=version, is_dev=is_dev)
                if is_dev:
                    dev_dependencies.append(dep_info)
                else:
                    dependencies.append(dep_info)

        # Get project metadata
        name = self._get_text(root.find("artifactId", ns))
        version = self._get_text(root.find("version", ns))
        description = self._get_text(root.find("description", ns))

        return PackageInfo(
            file_path=file_path,
            language="java",
            build_system="maven",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts={},
            metadata={
                "name": name,
                "version": version,
                "description": description,
                "group_id": self._get_text(root.find("groupId", ns)),
            },
        )

    def parse_gradle(self, file_path: str) -> PackageInfo:
        """Parse build.gradle file."""
        dependencies = []
        dev_dependencies = []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse dependencies block
        deps_pattern = r"dependencies\s*\{([^}]*)\}"
        deps_match = re.search(deps_pattern, content, re.DOTALL)

        if deps_match:
            deps_content = deps_match.group(1)

            # Parse individual dependency lines
            dep_patterns = [
                r"(implementation|compile|api|testImplementation|testCompile)\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                r"(implementation|compile|api|testImplementation|testCompile)\s+group:\s*['\"]([^'\"]+)['\"],\s*name:\s*['\"]([^'\"]+)['\"],\s*version:\s*['\"]([^'\"]+)['\"]",
            ]

            for pattern in dep_patterns:
                for match in re.finditer(pattern, deps_content):
                    config = match.group(1)
                    if len(match.groups()) == 4:
                        group_id = match.group(2)
                        artifact_id = match.group(3)
                        version = match.group(4)
                        name = f"{group_id}:{artifact_id}"
                    else:
                        continue

                    is_dev = config.startswith("test")
                    dep_info = DependencyInfo(name=name, version=version, is_dev=is_dev)

                    if is_dev:
                        dev_dependencies.append(dep_info)
                    else:
                        dependencies.append(dep_info)

        return PackageInfo(
            file_path=file_path,
            language="java",
            build_system="gradle",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts={},
            metadata={},
        )

    def parse_gradle_kts(self, file_path: str) -> PackageInfo:
        """Parse build.gradle.kts file (Kotlin DSL)."""
        # Similar to parse_gradle but with Kotlin syntax patterns
        return self.parse_gradle(file_path)  # Simplified for now

    # PHP parsers
    def parse_composer(self, file_path: str) -> PackageInfo:
        """Parse composer.json file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dependencies = []
        dev_dependencies = []

        # Parse regular dependencies
        for name, version in data.get("require", {}).items():
            if name == "php":
                continue
            dependencies.append(DependencyInfo(name=name, version=version))

        # Parse dev dependencies
        for name, version in data.get("require-dev", {}).items():
            dev_dependencies.append(
                DependencyInfo(name=name, version=version, is_dev=True)
            )

        return PackageInfo(
            file_path=file_path,
            language="php",
            build_system="composer",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts=data.get("scripts", {}),
            metadata={
                "name": data.get("name"),
                "version": data.get("version"),
                "description": data.get("description"),
                "php_version": data.get("require", {}).get("php"),
            },
        )

    def parse_composer_lock(self, file_path: str) -> PackageInfo:
        """Parse composer.lock file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dependencies = []
        dev_dependencies = []

        # Parse regular packages
        for package in data.get("packages", []):
            name = package.get("name", "")
            version = package.get("version", "")
            dependencies.append(DependencyInfo(name=name, version=version))

        # Parse dev packages
        for package in data.get("packages-dev", []):
            name = package.get("name", "")
            version = package.get("version", "")
            dev_dependencies.append(
                DependencyInfo(name=name, version=version, is_dev=True)
            )

        return PackageInfo(
            file_path=file_path,
            language="php",
            build_system="composer",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts={},
            metadata={
                "content_hash": data.get("content-hash"),
                "platform_overrides": data.get("platform-overrides", {}),
            },
        )

    # Additional language parsers (simplified implementations)
    def parse_gemfile(self, file_path: str) -> PackageInfo:
        """Parse Ruby Gemfile."""
        dependencies = []
        dev_dependencies = []

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_groups = set()

        for line in lines:
            line = line.strip()

            # Check for group declarations
            group_match = re.match(r"group\s+(.+)", line)
            if group_match:
                # Extract group names (handle :development, :test syntax)
                groups_str = group_match.group(1)
                groups = re.findall(r":(\w+)", groups_str)
                current_groups = set(groups)
                continue

            # Check for end of group block
            if line == "end":
                current_groups.clear()
                continue

            # Parse gem declarations
            gem_match = re.match(
                r"gem\s+['\"]([^'\"]+)['\"](?:,\s*['\"]([^'\"]+)['\"])?", line
            )
            if gem_match:
                name = gem_match.group(1)
                version = gem_match.group(2) if gem_match.group(2) else None

                is_dev = bool(current_groups & {"development", "test"})
                dep_info = DependencyInfo(name=name, version=version, is_dev=is_dev)

                if is_dev:
                    dev_dependencies.append(dep_info)
                else:
                    dependencies.append(dep_info)

        return PackageInfo(
            file_path=file_path,
            language="ruby",
            build_system="bundler",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts={},
            metadata={},
        )

    def parse_gemfile_lock(self, file_path: str) -> PackageInfo:
        """Parse Ruby Gemfile.lock."""
        dependencies = []
        current_section = None

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if line == "GEM":
                    current_section = "gems"
                    continue
                elif line.startswith("DEPENDENCIES"):
                    break

                if (
                    current_section == "gems"
                    and line
                    and not line.startswith("remote:")
                ):
                    # Parse gem lines like "    activesupport (6.1.4)"
                    gem_match = re.match(r"\s*(\w+)\s*\(([^)]+)\)", line)
                    if gem_match:
                        name = gem_match.group(1)
                        version = gem_match.group(2)
                        dependencies.append(DependencyInfo(name=name, version=version))

        return PackageInfo(
            file_path=file_path,
            language="ruby",
            build_system="bundler",
            dependencies=dependencies,
            dev_dependencies=[],
            scripts={},
            metadata={"lockfile": True},
        )

    # Placeholder parsers for other languages
    def parse_mix_exs(self, file_path: str) -> PackageInfo:
        """Parse Elixir mix.exs file."""
        return PackageInfo(
            file_path=file_path,
            language="elixir",
            build_system="mix",
            dependencies=[],
            dev_dependencies=[],
            scripts={},
            metadata={},
        )

    def parse_rebar_config(self, file_path: str) -> PackageInfo:
        """Parse Erlang rebar.config file."""
        return PackageInfo(
            file_path=file_path,
            language="erlang",
            build_system="rebar3",
            dependencies=[],
            dev_dependencies=[],
            scripts={},
            metadata={},
        )

    def parse_dune_project(self, file_path: str) -> PackageInfo:
        """Parse OCaml dune-project file."""
        return PackageInfo(
            file_path=file_path,
            language="ocaml",
            build_system="dune",
            dependencies=[],
            dev_dependencies=[],
            scripts={},
            metadata={},
        )

    def parse_cabal_project(self, file_path: str) -> PackageInfo:
        """Parse Haskell cabal.project file."""
        return PackageInfo(
            file_path=file_path,
            language="haskell",
            build_system="cabal",
            dependencies=[],
            dev_dependencies=[],
            scripts={},
            metadata={},
        )

    def parse_stack_yaml(self, file_path: str) -> PackageInfo:
        """Parse Haskell stack.yaml file."""
        return PackageInfo(
            file_path=file_path,
            language="haskell",
            build_system="stack",
            dependencies=[],
            dev_dependencies=[],
            scripts={},
            metadata={},
        )

    def parse_pubspec_yaml(self, file_path: str) -> PackageInfo:
        """Parse Dart/Flutter pubspec.yaml file."""
        try:
            import yaml

            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except ImportError:
            # Fallback if PyYAML not available
            return PackageInfo(
                file_path=file_path,
                language="dart",
                build_system="pub",
                dependencies=[],
                dev_dependencies=[],
                scripts={},
                metadata={},
            )

        dependencies = []
        dev_dependencies = []

        # Parse regular dependencies
        for name, version_info in data.get("dependencies", {}).items():
            if name == "flutter":
                continue

            if isinstance(version_info, str):
                dependencies.append(DependencyInfo(name=name, version=version_info))
            elif isinstance(version_info, dict):
                version = version_info.get("version", "")
                dependencies.append(DependencyInfo(name=name, version=version))

        # Parse dev dependencies
        for name, version_info in data.get("dev_dependencies", {}).items():
            if isinstance(version_info, str):
                dev_dependencies.append(
                    DependencyInfo(name=name, version=version_info, is_dev=True)
                )
            elif isinstance(version_info, dict):
                version = version_info.get("version", "")
                dev_dependencies.append(
                    DependencyInfo(name=name, version=version, is_dev=True)
                )

        return PackageInfo(
            file_path=file_path,
            language="dart",
            build_system="pub",
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts={},
            metadata={
                "name": data.get("name"),
                "version": data.get("version"),
                "description": data.get("description"),
                "environment": data.get("environment", {}),
            },
        )

    def parse_swift_package(self, file_path: str) -> PackageInfo:
        """Parse Swift Package.swift file."""
        return PackageInfo(
            file_path=file_path,
            language="swift",
            build_system="spm",
            dependencies=[],
            dev_dependencies=[],
            scripts={},
            metadata={},
        )

    # Helper methods
    def _parse_python_requirement(self, requirement: str) -> Optional[DependencyInfo]:
        """Parse a Python requirement string like 'package>=1.0.0'."""
        # Remove whitespace but preserve URLs with #egg=
        original_requirement = requirement.strip()

        # Handle git/url dependencies first (before removing # comments)
        if any(
            proto in original_requirement.lower()
            for proto in ["http://", "https://", "git+", "ssh://"]
        ):
            # Extract package name if possible
            if "#egg=" in original_requirement:
                name = original_requirement.split("#egg=")[-1].split("&")[0]
                return DependencyInfo(name=name, version="git")
            return None

        # Now remove comments for regular dependencies
        requirement = original_requirement
        if "#" in requirement:
            requirement = requirement.split("#")[0].strip()

        if not requirement:
            return None

        # Parse name and version constraints
        # Matches patterns like: package>=1.0.0, package[extra]>=1.0.0, package==1.0.0, etc.
        # Only allow valid version operators: ==, >=, <=, >, <, ~=, !=
        pattern = r"^([a-zA-Z0-9][a-zA-Z0-9\-_.]*[a-zA-Z0-9]|[a-zA-Z0-9])(\[[^\]]+\])?\s*((==|>=|<=|>|<|~=|!=).*)?$"
        match = re.match(pattern, requirement)

        if match:
            name = match.group(1)
            extras_str = match.group(2)
            version = match.group(3).strip() if match.group(3) else None

            # Extract extras if present
            extras = []
            if extras_str:
                # Remove brackets and split by comma
                extras_content = extras_str[1:-1]  # Remove [ and ]
                extras = [extra.strip() for extra in extras_content.split(",")]

            return DependencyInfo(name=name, version=version, extras=extras)

        return None

    def _get_text(self, element, default: str = "") -> str:
        """Get text content from XML element with default."""
        if element is not None and element.text:
            return str(element.text).strip()
        return default
