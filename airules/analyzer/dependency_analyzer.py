"""Dependency analysis and security scanning for project dependencies."""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from .framework_detector import FrameworkDetector
from .package_parser import DependencyInfo, PackageInfo, PackageParser


class SecurityRisk(Enum):
    """Security risk levels for dependencies."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DependencyHealth(Enum):
    """Health status of dependencies."""

    HEALTHY = "healthy"
    OUTDATED = "outdated"
    DEPRECATED = "deprecated"
    VULNERABLE = "vulnerable"
    ABANDONED = "abandoned"


@dataclass
class VulnerabilityInfo:
    """Information about a security vulnerability."""

    id: str
    severity: SecurityRisk
    title: str
    description: str
    affected_versions: str
    patched_versions: Optional[str] = None
    published_date: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass
class DependencyReport:
    """Comprehensive dependency analysis report."""

    name: str
    version: str
    language: str
    license: Optional[str] = None
    health: DependencyHealth = DependencyHealth.HEALTHY
    vulnerabilities: List[VulnerabilityInfo] = field(default_factory=list)
    is_dev_dependency: bool = False
    is_direct_dependency: bool = True
    size_mb: Optional[float] = None
    last_updated: Optional[str] = None
    maintainers: List[str] = field(default_factory=list)
    repository_url: Optional[str] = None
    dependencies_count: int = 0
    dependents_count: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProjectDependencyAnalysis:
    """Complete project dependency analysis."""

    total_dependencies: int
    direct_dependencies: int
    dev_dependencies: int
    security_vulnerabilities: int
    outdated_dependencies: int
    license_issues: int
    health_score: float
    dependency_reports: List[DependencyReport]
    framework_analysis: Optional[Dict] = None
    recommendations: List[str] = field(default_factory=list)
    scan_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DependencyAnalyzer:
    """Main dependency analyzer with security and health checks."""

    # Known vulnerable packages (simplified database)
    KNOWN_VULNERABILITIES = {
        "lodash": [
            {
                "id": "CVE-2019-10744",
                "severity": SecurityRisk.HIGH,
                "title": "Prototype Pollution",
                "description": "Prototype pollution vulnerability",
                "affected_versions": "<4.17.12",
                "patched_versions": ">=4.17.12",
            }
        ],
        "moment": [
            {
                "id": "DEPRECATED",
                "severity": SecurityRisk.MEDIUM,
                "title": "Deprecated Package",
                "description": "Package is deprecated, consider using date-fns or dayjs",
                "affected_versions": "*",
                "patched_versions": None,
            }
        ],
        "django": [
            {
                "id": "CVE-2021-35042",
                "severity": SecurityRisk.HIGH,
                "title": "SQL Injection",
                "description": "SQL injection vulnerability in Django",
                "affected_versions": "<3.2.6",
                "patched_versions": ">=3.2.6",
            }
        ],
        "requests": [
            {
                "id": "CVE-2018-18074",
                "severity": SecurityRisk.MEDIUM,
                "title": "Unsafe Redirect",
                "description": "Unsafe redirect vulnerability",
                "affected_versions": "<2.20.0",
                "patched_versions": ">=2.20.0",
            }
        ],
        "express": [
            {
                "id": "CVE-2022-24999",
                "severity": SecurityRisk.HIGH,
                "title": "Open Redirect",
                "description": "Open redirect vulnerability",
                "affected_versions": "<4.18.0",
                "patched_versions": ">=4.18.0",
            }
        ],
    }

    # Deprecated packages
    DEPRECATED_PACKAGES = {
        "moment": "Use date-fns or dayjs instead",
        "request": "Use axios or node-fetch instead",
        "bower": "Use npm or yarn instead",
        "gulp": "Consider using npm scripts or other build tools",
        "grunt": "Consider using npm scripts or other build tools",
        "babel-core": "Use @babel/core instead",
        "babel-preset-es2015": "Use @babel/preset-env instead",
        "node-sass": "Use sass (Dart Sass) instead",
        "tslint": "Use ESLint with TypeScript support instead",
        "protractor": "Use Cypress or Playwright instead",
        "karma": "Use Jest or Vitest instead",
        "istanbul": "Use nyc or c8 instead",
    }

    # License compatibility matrix
    LICENSE_COMPATIBILITY = {
        "MIT": ["MIT", "BSD", "Apache-2.0", "ISC", "Unlicense"],
        "Apache-2.0": ["MIT", "BSD", "Apache-2.0", "ISC"],
        "GPL-3.0": ["GPL-3.0", "LGPL-3.0"],
        "GPL-2.0": ["GPL-2.0", "LGPL-2.0"],
        "BSD": ["MIT", "BSD", "Apache-2.0", "ISC"],
        "ISC": ["MIT", "BSD", "Apache-2.0", "ISC"],
    }

    def __init__(self):
        self.package_parser = PackageParser()
        self.framework_detector = FrameworkDetector()

    def analyze_project_dependencies(
        self, project_path: str
    ) -> ProjectDependencyAnalysis:
        """Perform comprehensive dependency analysis on a project."""
        # Parse all package files
        package_infos = self.package_parser.parse_all_package_files(project_path)

        if not package_infos:
            return ProjectDependencyAnalysis(
                total_dependencies=0,
                direct_dependencies=0,
                dev_dependencies=0,
                security_vulnerabilities=0,
                outdated_dependencies=0,
                license_issues=0,
                health_score=1.0,
                dependency_reports=[],
                recommendations=["No package files found in project"],
            )

        # Analyze each dependency
        all_dependency_reports = []
        total_vulnerabilities = 0
        total_outdated = 0
        total_license_issues = 0

        for package_info in package_infos:
            # Analyze direct dependencies
            for dep in package_info.dependencies:
                report = self._analyze_single_dependency(
                    dep, package_info.language, False
                )
                all_dependency_reports.append(report)
                total_vulnerabilities += len(report.vulnerabilities)
                if report.health in [
                    DependencyHealth.OUTDATED,
                    DependencyHealth.DEPRECATED,
                ]:
                    total_outdated += 1

            # Analyze dev dependencies
            for dep in package_info.dev_dependencies:
                report = self._analyze_single_dependency(
                    dep, package_info.language, True
                )
                all_dependency_reports.append(report)
                total_vulnerabilities += len(report.vulnerabilities)
                if report.health in [
                    DependencyHealth.OUTDATED,
                    DependencyHealth.DEPRECATED,
                ]:
                    total_outdated += 1

        # Remove duplicates
        unique_reports = self._deduplicate_dependency_reports(all_dependency_reports)

        # Calculate metrics
        total_deps = len(unique_reports)
        direct_deps = len([r for r in unique_reports if not r.is_dev_dependency])
        dev_deps = len([r for r in unique_reports if r.is_dev_dependency])

        # Calculate health score
        health_score = self._calculate_health_score(unique_reports)

        # Generate recommendations
        recommendations = self._generate_recommendations(unique_reports, package_infos)

        # Analyze frameworks
        framework_analysis = self._analyze_frameworks(project_path, unique_reports)

        return ProjectDependencyAnalysis(
            total_dependencies=total_deps,
            direct_dependencies=direct_deps,
            dev_dependencies=dev_deps,
            security_vulnerabilities=total_vulnerabilities,
            outdated_dependencies=total_outdated,
            license_issues=total_license_issues,
            health_score=health_score,
            dependency_reports=unique_reports,
            framework_analysis=framework_analysis,
            recommendations=recommendations,
        )

    def _analyze_single_dependency(
        self, dep: DependencyInfo, language: str, is_dev: bool
    ) -> DependencyReport:
        """Analyze a single dependency for security, health, and metadata."""
        # Check for vulnerabilities
        vulnerabilities = self._check_vulnerabilities(dep.name, dep.version)

        # Determine health status
        health = self._determine_health_status(dep.name, dep.version, language)

        # Get license information (simplified)
        license_info = self._get_license_info(dep.name, language)

        # Get metadata
        metadata = self._get_dependency_metadata(dep.name, language)

        return DependencyReport(
            name=dep.name,
            version=dep.version or "unknown",
            language=language,
            license=license_info,
            health=health,
            vulnerabilities=vulnerabilities,
            is_dev_dependency=is_dev,
            is_direct_dependency=True,
            size_mb=metadata.get("size_mb"),
            last_updated=metadata.get("last_updated"),
            maintainers=metadata.get("maintainers", []),
            repository_url=metadata.get("repository_url"),
            dependencies_count=metadata.get("dependencies_count", 0),
            dependents_count=metadata.get("dependents_count", 0),
            metadata=metadata,
        )

    def _check_vulnerabilities(
        self, package_name: str, version: Optional[str]
    ) -> List[VulnerabilityInfo]:
        """Check for known vulnerabilities in a package."""
        vulnerabilities = []

        # Check against known vulnerabilities database
        if package_name.lower() in self.KNOWN_VULNERABILITIES:
            for vuln_data in self.KNOWN_VULNERABILITIES[package_name.lower()]:
                # Check if version is affected
                if self._is_version_affected(
                    version, str(vuln_data["affected_versions"])
                ):
                    vulnerability = VulnerabilityInfo(
                        id=str(vuln_data["id"]),
                        severity=(
                            vuln_data["severity"]
                            if isinstance(vuln_data["severity"], SecurityRisk)
                            else SecurityRisk.MEDIUM
                        ),
                        title=str(vuln_data["title"]),
                        description=str(vuln_data["description"]),
                        affected_versions=str(vuln_data["affected_versions"]),
                        patched_versions=(
                            str(vuln_data.get("patched_versions"))
                            if vuln_data.get("patched_versions") is not None
                            else None
                        ),
                    )
                    vulnerabilities.append(vulnerability)

        return vulnerabilities

    def _determine_health_status(
        self, package_name: str, version: Optional[str], language: str
    ) -> DependencyHealth:
        """Determine the health status of a dependency."""
        # Check if deprecated
        if package_name.lower() in self.DEPRECATED_PACKAGES:
            return DependencyHealth.DEPRECATED

        # Check for vulnerabilities
        if self._check_vulnerabilities(package_name, version):
            return DependencyHealth.VULNERABLE

        # Check if outdated (simplified heuristic)
        if self._is_likely_outdated(package_name, version, language):
            return DependencyHealth.OUTDATED

        return DependencyHealth.HEALTHY

    def _is_version_affected(
        self, current_version: Optional[str], affected_range: str
    ) -> bool:
        """Check if current version is affected by vulnerability."""
        if not current_version or current_version == "unknown":
            return True  # Assume vulnerable if version unknown

        if affected_range == "*":
            return True

        # Simple pattern matching for common version patterns
        if affected_range.startswith("<"):
            # e.g., "<4.17.12"
            threshold = affected_range[1:]
            return self._compare_versions(current_version, threshold) < 0
        elif affected_range.startswith("<="):
            threshold = affected_range[2:]
            return self._compare_versions(current_version, threshold) <= 0
        elif affected_range.startswith(">="):
            threshold = affected_range[2:]
            return self._compare_versions(current_version, threshold) >= 0
        elif affected_range.startswith(">"):
            threshold = affected_range[1:]
            return self._compare_versions(current_version, threshold) > 0

        return False

    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""

        # Simplified version comparison
        def normalize_version(v):
            # Remove non-numeric prefixes (^, ~, etc.)
            v = re.sub(r"^[^\d]*", "", v)
            # Split by dots and convert to integers
            parts = []
            for part in v.split("."):
                # Extract numeric part
                num_part = re.match(r"(\d+)", part)
                if num_part:
                    parts.append(int(num_part.group(1)))
                else:
                    parts.append(0)
            return parts

        try:
            v1_parts = normalize_version(version1)
            v2_parts = normalize_version(version2)

            # Pad with zeros to make same length
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            for i in range(max_len):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1

            return 0
        except Exception:
            # Fallback to string comparison
            return -1 if version1 < version2 else (1 if version1 > version2 else 0)

    def _is_likely_outdated(
        self, package_name: str, version: Optional[str], language: str
    ) -> bool:
        """Heuristic to determine if a package is likely outdated."""
        # This is a simplified heuristic
        # In a real implementation, you'd check against package registries

        # Check for very old version patterns
        if version:
            # Remove non-numeric prefixes
            clean_version = re.sub(r"^[^\d]*", "", version)
            if clean_version:
                try:
                    major_version = int(clean_version.split(".")[0])
                    # Heuristic: major version 0 or 1 might be outdated for popular packages
                    popular_packages = [
                        "react",
                        "vue",
                        "angular",
                        "django",
                        "flask",
                        "express",
                    ]
                    if package_name.lower() in popular_packages and major_version <= 1:
                        return True
                except Exception:
                    pass

        return False

    def _get_license_info(self, package_name: str, language: str) -> Optional[str]:
        """Get license information for a package (simplified)."""
        # This would typically query package registries
        # For now, return common licenses based on popular packages
        common_licenses = {
            "react": "MIT",
            "vue": "MIT",
            "angular": "MIT",
            "django": "BSD-3-Clause",
            "flask": "BSD-3-Clause",
            "express": "MIT",
            "lodash": "MIT",
            "moment": "MIT",
            "axios": "MIT",
            "pytest": "MIT",
            "requests": "Apache-2.0",
        }

        return common_licenses.get(package_name.lower())

    def _get_dependency_metadata(self, package_name: str, language: str) -> Dict:
        """Get additional metadata for a dependency."""
        # This would typically query package registries (npm, PyPI, etc.)
        # For now, return mock data
        return {
            "size_mb": 0.5,  # Mock size
            "last_updated": "2023-01-01",
            "maintainers": ["maintainer1"],
            "repository_url": f"https://github.com/example/{package_name}",
            "dependencies_count": 5,
            "dependents_count": 1000,
        }

    def _deduplicate_dependency_reports(
        self, reports: List[DependencyReport]
    ) -> List[DependencyReport]:
        """Remove duplicate dependency reports."""
        seen = {}
        for report in reports:
            key = (report.name, report.language)
            if key not in seen:
                seen[key] = report
            elif seen[key].is_dev_dependency and not report.is_dev_dependency:
                # Prefer non-dev dependency over dev dependency
                seen[key] = report
        return list(seen.values())

    def _calculate_health_score(self, reports: List[DependencyReport]) -> float:
        """Calculate overall health score for dependencies."""
        if not reports:
            return 1.0

        total_score = 0.0
        total_weight = 0.0

        for report in reports:
            # Weight based on dependency type
            weight = 0.5 if report.is_dev_dependency else 1.0

            # Score based on health status
            health_scores = {
                DependencyHealth.HEALTHY: 1.0,
                DependencyHealth.OUTDATED: 0.7,
                DependencyHealth.DEPRECATED: 0.4,
                DependencyHealth.VULNERABLE: 0.2,
                DependencyHealth.ABANDONED: 0.0,
            }

            base_score = health_scores[report.health]

            # Reduce score for vulnerabilities
            vuln_penalty = len(report.vulnerabilities) * 0.1
            final_score = max(0.0, base_score - vuln_penalty)

            total_score += final_score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 1.0

    def _generate_recommendations(
        self, reports: List[DependencyReport], package_infos: List[PackageInfo]
    ) -> List[str]:
        """Generate recommendations based on dependency analysis."""
        recommendations = []

        # Check for vulnerable dependencies
        vulnerable_deps = [r for r in reports if r.vulnerabilities]
        if vulnerable_deps:
            recommendations.append(
                f"Update {len(vulnerable_deps)} vulnerable dependencies"
            )

        # Check for deprecated dependencies
        deprecated_deps = [
            r for r in reports if r.health == DependencyHealth.DEPRECATED
        ]
        if deprecated_deps:
            recommendations.append(
                f"Replace {len(deprecated_deps)} deprecated dependencies"
            )
            for dep in deprecated_deps[:3]:  # Show top 3
                replacement = self.DEPRECATED_PACKAGES.get(dep.name)
                if replacement:
                    recommendations.append(
                        f"  - Replace '{dep.name}' with {replacement}"
                    )

        # Check for outdated dependencies
        outdated_deps = [r for r in reports if r.health == DependencyHealth.OUTDATED]
        if outdated_deps:
            recommendations.append(f"Update {len(outdated_deps)} outdated dependencies")

        # Check for missing security practices
        has_security_linter = any(
            "eslint" in r.name.lower()
            or "bandit" in r.name.lower()
            or "safety" in r.name.lower()
            for r in reports
        )
        if not has_security_linter:
            recommendations.append(
                "Add security linting tools (ESLint, Bandit, Safety)"
            )

        # Check for missing testing frameworks
        has_testing = any(
            r.name.lower() in ["jest", "mocha", "pytest", "junit"] for r in reports
        )
        if not has_testing:
            recommendations.append("Add testing framework for better code quality")

        # Check for dependency count
        if len(reports) > 100:
            recommendations.append(
                "Consider reducing dependency count to improve maintainability"
            )

        return recommendations

    def _analyze_frameworks(
        self, project_path: str, dependency_reports: List[DependencyReport]
    ) -> Dict:
        """Analyze frameworks in context of dependencies."""
        frameworks = self.framework_detector.detect_frameworks(project_path)

        # Check framework-specific security concerns
        framework_security = []
        for framework in frameworks:
            if framework.name.lower() in ["django", "flask", "express", "react"]:
                # Check for framework-specific security packages
                security_packages = {
                    "django": ["django-security", "django-csp"],
                    "flask": ["flask-security", "flask-cors"],
                    "express": ["helmet", "cors"],
                    "react": ["react-helmet", "dompurify"],
                }

                framework_packages = security_packages.get(framework.name.lower(), [])
                missing_packages = []
                for pkg in framework_packages:
                    if not any(pkg in r.name.lower() for r in dependency_reports):
                        missing_packages.append(pkg)

                if missing_packages:
                    framework_security.append(
                        {
                            "framework": framework.name,
                            "missing_security_packages": missing_packages,
                        }
                    )

        return {
            "detected_frameworks": [f.name for f in frameworks],
            "framework_security_recommendations": framework_security,
            "framework_count": len(frameworks),
        }

    def generate_dependency_graph(self, project_path: str) -> Dict:
        """Generate dependency graph for visualization."""
        package_infos = self.package_parser.parse_all_package_files(project_path)

        nodes = []
        edges = []

        for package_info in package_infos:
            # Add package file as root node
            root_node = {
                "id": package_info.file_path,
                "name": Path(package_info.file_path).name,
                "type": "package_file",
                "language": package_info.language,
            }
            nodes.append(root_node)

            # Add dependencies as nodes and edges
            for dep in package_info.dependencies + package_info.dev_dependencies:
                dep_node: Dict[str, str] = {
                    "id": f"{dep.name}@{dep.version or 'unknown'}",
                    "name": dep.name,
                    "type": "dependency",
                    "version": dep.version or "unknown",
                    "is_dev": str(dep.is_dev),
                }
                nodes.append(dep_node)

                edge = {
                    "from": package_info.file_path,
                    "to": f"{dep.name}@{dep.version or 'unknown'}",
                    "type": "depends_on",
                }
                edges.append(edge)

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "package_files": len(package_infos),
            },
        }

    def check_license_compatibility(
        self, reports: List[DependencyReport], project_license: str = "MIT"
    ) -> Dict:
        """Check license compatibility across dependencies."""
        license_issues = []
        license_distribution: Dict[str, int] = {}

        for report in reports:
            if report.license:
                # Count license distribution
                license_distribution[report.license] = (
                    license_distribution.get(report.license, 0) + 1
                )

                # Check compatibility
                compatible_licenses = self.LICENSE_COMPATIBILITY.get(
                    project_license, []
                )
                if report.license not in compatible_licenses:
                    license_issues.append(
                        {
                            "dependency": report.name,
                            "license": report.license,
                            "issue": f"License {report.license} may not be compatible with {project_license}",
                        }
                    )

        return {
            "license_distribution": license_distribution,
            "compatibility_issues": license_issues,
            "total_licenses": len(license_distribution),
            "compatibility_score": 1.0 - (len(license_issues) / max(1, len(reports))),
        }

    def export_report(
        self, analysis: ProjectDependencyAnalysis, format: str = "json"
    ) -> str:
        """Export dependency analysis report in specified format."""
        if format.lower() == "json":
            # Convert dataclasses to dict for JSON serialization
            report_dict = {
                "summary": {
                    "total_dependencies": analysis.total_dependencies,
                    "direct_dependencies": analysis.direct_dependencies,
                    "dev_dependencies": analysis.dev_dependencies,
                    "security_vulnerabilities": analysis.security_vulnerabilities,
                    "outdated_dependencies": analysis.outdated_dependencies,
                    "health_score": analysis.health_score,
                    "scan_timestamp": analysis.scan_timestamp,
                },
                "dependencies": [
                    {
                        "name": dep.name,
                        "version": dep.version,
                        "language": dep.language,
                        "license": dep.license,
                        "health": dep.health.value,
                        "vulnerabilities": [
                            {
                                "id": vuln.id,
                                "severity": vuln.severity.value,
                                "title": vuln.title,
                                "description": vuln.description,
                            }
                            for vuln in dep.vulnerabilities
                        ],
                        "is_dev_dependency": dep.is_dev_dependency,
                    }
                    for dep in analysis.dependency_reports
                ],
                "recommendations": analysis.recommendations,
                "framework_analysis": analysis.framework_analysis,
            }
            return json.dumps(report_dict, indent=2)

        elif format.lower() == "markdown":
            # Generate markdown report
            md_lines = [
                "# Dependency Analysis Report",
                f"Generated: {analysis.scan_timestamp}",
                "",
                "## Summary",
                f"- **Total Dependencies**: {analysis.total_dependencies}",
                f"- **Direct Dependencies**: {analysis.direct_dependencies}",
                f"- **Dev Dependencies**: {analysis.dev_dependencies}",
                f"- **Security Vulnerabilities**: {analysis.security_vulnerabilities}",
                f"- **Outdated Dependencies**: {analysis.outdated_dependencies}",
                f"- **Health Score**: {analysis.health_score:.2f}/1.0",
                "",
            ]

            if analysis.security_vulnerabilities > 0:
                md_lines.extend(["## Security Vulnerabilities", ""])
                for dep in analysis.dependency_reports:
                    if dep.vulnerabilities:
                        md_lines.append(f"### {dep.name} ({dep.version})")
                        for vuln in dep.vulnerabilities:
                            md_lines.extend(
                                [
                                    f"- **{vuln.severity.value.upper()}**: {vuln.title}",
                                    f"  - {vuln.description}",
                                    f"  - Affected: {vuln.affected_versions}",
                                    "",
                                ]
                            )

            if analysis.recommendations:
                md_lines.extend(["## Recommendations", ""])
                for rec in analysis.recommendations:
                    md_lines.append(f"- {rec}")
                md_lines.append("")

            return "\n".join(md_lines)

        else:
            raise ValueError(f"Unsupported format: {format}")
