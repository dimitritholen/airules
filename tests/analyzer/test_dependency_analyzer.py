"""Tests for dependency analysis functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from airules.analyzer.dependency_analyzer import (
    DependencyAnalyzer,
    DependencyHealth,
    DependencyReport,
    ProjectDependencyAnalysis,
    SecurityRisk,
    VulnerabilityInfo,
)
from airules.analyzer.package_parser import DependencyInfo, PackageInfo


class TestDependencyAnalyzer:
    """Test suite for DependencyAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

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

    def test_analyze_project_dependencies_basic(self):
        """Test basic project dependency analysis."""
        package_info = self.create_package_info(
            "javascript", ["react", "lodash"], ["jest"]
        )

        with patch.object(
            self.analyzer.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            analysis = self.analyzer.analyze_project_dependencies(str(self.temp_dir))

        assert isinstance(analysis, ProjectDependencyAnalysis)
        assert analysis.total_dependencies == 3
        assert analysis.direct_dependencies == 2
        assert analysis.dev_dependencies == 1
        assert 0.0 <= analysis.health_score <= 1.0
        assert len(analysis.dependency_reports) == 3

    def test_analyze_project_no_packages(self):
        """Test analysis of project with no package files."""
        with patch.object(
            self.analyzer.package_parser, "parse_all_package_files", return_value=[]
        ):
            analysis = self.analyzer.analyze_project_dependencies(str(self.temp_dir))

        assert analysis.total_dependencies == 0
        assert analysis.direct_dependencies == 0
        assert analysis.dev_dependencies == 0
        assert analysis.health_score == 1.0
        assert len(analysis.dependency_reports) == 0
        assert "No package files found" in analysis.recommendations[0]

    def test_vulnerability_detection(self):
        """Test detection of known vulnerabilities."""
        # Test with vulnerable lodash version
        vulnerable_dep = DependencyInfo(name="lodash", version="4.17.11")
        report = self.analyzer._analyze_single_dependency(
            vulnerable_dep, "javascript", False
        )

        assert len(report.vulnerabilities) > 0
        vuln = report.vulnerabilities[0]
        assert vuln.severity == SecurityRisk.HIGH
        assert "Prototype Pollution" in vuln.title

    def test_vulnerability_version_checking(self):
        """Test version checking for vulnerabilities."""
        # Test affected version
        assert self.analyzer._is_version_affected("4.17.11", "<4.17.12") is True
        assert self.analyzer._is_version_affected("4.17.12", "<4.17.12") is False
        assert self.analyzer._is_version_affected("4.17.13", "<4.17.12") is False

        # Test with unknown version
        assert self.analyzer._is_version_affected("unknown", "<4.17.12") is True
        assert self.analyzer._is_version_affected(None, "<4.17.12") is True

        # Test wildcard
        assert self.analyzer._is_version_affected("1.0.0", "*") is True

    def test_version_comparison(self):
        """Test version comparison functionality."""
        # Basic version comparisons
        assert self.analyzer._compare_versions("1.0.0", "2.0.0") == -1
        assert self.analyzer._compare_versions("2.0.0", "1.0.0") == 1
        assert self.analyzer._compare_versions("1.0.0", "1.0.0") == 0

        # Semantic versioning
        assert self.analyzer._compare_versions("1.0.1", "1.0.0") == 1
        assert self.analyzer._compare_versions("1.1.0", "1.0.9") == 1
        assert self.analyzer._compare_versions("2.0.0", "1.9.9") == 1

        # Version prefixes
        assert self.analyzer._compare_versions("^1.0.0", "1.0.0") == 0
        assert self.analyzer._compare_versions("~1.0.0", "1.0.1") == -1

        # Different lengths
        assert self.analyzer._compare_versions("1.0", "1.0.0") == 0
        assert self.analyzer._compare_versions("1", "1.0.0") == 0

    def test_deprecated_package_detection(self):
        """Test detection of deprecated packages."""
        deprecated_dep = DependencyInfo(name="moment", version="2.29.0")
        report = self.analyzer._analyze_single_dependency(
            deprecated_dep, "javascript", False
        )

        assert report.health == DependencyHealth.DEPRECATED
        assert len(report.vulnerabilities) > 0
        assert any(
            "deprecated" in vuln.title.lower() for vuln in report.vulnerabilities
        )

    def test_health_status_determination(self):
        """Test dependency health status determination."""
        # Healthy dependency - testing status determination
        health = self.analyzer._determine_health_status(
            "unknown-package", "1.0.0", "javascript"
        )
        assert health == DependencyHealth.HEALTHY

        # Deprecated dependency
        deprecated_health = self.analyzer._determine_health_status(
            "moment", "2.29.0", "javascript"
        )
        assert deprecated_health == DependencyHealth.DEPRECATED

        # Vulnerable dependency
        vulnerable_health = self.analyzer._determine_health_status(
            "lodash", "4.17.11", "javascript"
        )
        assert vulnerable_health == DependencyHealth.VULNERABLE

    def test_outdated_detection_heuristic(self):
        """Test heuristic for detecting outdated packages."""
        # Popular package with very old version
        assert (
            self.analyzer._is_likely_outdated("react", "0.14.0", "javascript") is True
        )
        assert self.analyzer._is_likely_outdated("react", "1.0.0", "javascript") is True
        assert (
            self.analyzer._is_likely_outdated("react", "18.0.0", "javascript") is False
        )

        # Unknown package should not be flagged as outdated
        assert (
            self.analyzer._is_likely_outdated("unknown-package", "0.1.0", "javascript")
            is False
        )

    def test_license_information(self):
        """Test license information retrieval."""
        # Known packages
        assert self.analyzer._get_license_info("react", "javascript") == "MIT"
        assert self.analyzer._get_license_info("django", "python") == "BSD-3-Clause"
        assert self.analyzer._get_license_info("requests", "python") == "Apache-2.0"

        # Unknown package
        assert self.analyzer._get_license_info("unknown-package", "javascript") is None

    def test_dependency_metadata(self):
        """Test dependency metadata retrieval."""
        metadata = self.analyzer._get_dependency_metadata("react", "javascript")

        assert isinstance(metadata, dict)
        assert "size_mb" in metadata
        assert "last_updated" in metadata
        assert "maintainers" in metadata
        assert "repository_url" in metadata
        assert "dependencies_count" in metadata
        assert "dependents_count" in metadata

    def test_deduplicate_dependency_reports(self):
        """Test deduplication of dependency reports."""
        reports = [
            DependencyReport("react", "18.0.0", "javascript", is_dev_dependency=False),
            DependencyReport("react", "17.0.0", "javascript", is_dev_dependency=True),
            DependencyReport("vue", "3.0.0", "javascript", is_dev_dependency=False),
        ]

        unique_reports = self.analyzer._deduplicate_dependency_reports(reports)

        assert len(unique_reports) == 2
        # Should prefer production dependency over dev dependency
        react_report = next(r for r in unique_reports if r.name == "react")
        assert react_report.is_dev_dependency is False

    def test_health_score_calculation(self):
        """Test health score calculation."""
        reports = [
            DependencyReport(
                "healthy", "1.0.0", "javascript", health=DependencyHealth.HEALTHY
            ),
            DependencyReport(
                "outdated", "1.0.0", "javascript", health=DependencyHealth.OUTDATED
            ),
            DependencyReport(
                "vulnerable",
                "1.0.0",
                "javascript",
                health=DependencyHealth.VULNERABLE,
                vulnerabilities=[
                    VulnerabilityInfo(
                        "CVE-123", SecurityRisk.HIGH, "Test", "Test vuln", "*"
                    )
                ],
            ),
            DependencyReport(
                "dev-tool",
                "1.0.0",
                "javascript",
                health=DependencyHealth.HEALTHY,
                is_dev_dependency=True,
            ),
        ]

        health_score = self.analyzer._calculate_health_score(reports)

        assert 0.0 <= health_score <= 1.0
        # Should be less than 1.0 due to vulnerable and outdated dependencies
        assert health_score < 0.8

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        reports = [
            DependencyReport(
                "vulnerable",
                "1.0.0",
                "javascript",
                health=DependencyHealth.VULNERABLE,
                vulnerabilities=[
                    VulnerabilityInfo("CVE-123", SecurityRisk.HIGH, "Test", "Test", "*")
                ],
            ),
            DependencyReport(
                "moment", "2.29.0", "javascript", health=DependencyHealth.DEPRECATED
            ),
            DependencyReport(
                "outdated", "1.0.0", "javascript", health=DependencyHealth.OUTDATED
            ),
        ]

        package_infos = [
            self.create_package_info("javascript", ["vulnerable", "moment", "outdated"])
        ]
        recommendations = self.analyzer._generate_recommendations(
            reports, package_infos
        )

        assert len(recommendations) > 0

        # Check for specific recommendation types
        rec_text = " ".join(recommendations).lower()
        assert "vulnerable" in rec_text or "update" in rec_text
        assert "deprecated" in rec_text or "replace" in rec_text
        assert "outdated" in rec_text

    def test_framework_analysis_integration(self):
        """Test integration with framework analysis."""
        package_info = self.create_package_info("javascript", ["react", "express"])

        with patch.object(
            self.analyzer.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            with patch.object(
                self.analyzer.framework_detector, "detect_frameworks"
            ) as mock_detect:
                from airules.analyzer.framework_detector import (
                    FrameworkInfo,
                    FrameworkType,
                )

                mock_detect.return_value = [
                    FrameworkInfo(
                        "React", FrameworkType.FRONTEND_FRAMEWORK, "javascript"
                    ),
                    FrameworkInfo(
                        "Express.js", FrameworkType.BACKEND_FRAMEWORK, "javascript"
                    ),
                ]

                analysis = self.analyzer.analyze_project_dependencies(
                    str(self.temp_dir)
                )

        assert analysis.framework_analysis is not None
        assert "detected_frameworks" in analysis.framework_analysis
        assert "React" in analysis.framework_analysis["detected_frameworks"]
        assert "Express.js" in analysis.framework_analysis["detected_frameworks"]

    def test_dependency_graph_generation(self):
        """Test dependency graph generation."""
        package_info = self.create_package_info(
            "javascript", ["react", "lodash"], ["jest"]
        )

        with patch.object(
            self.analyzer.package_parser,
            "parse_all_package_files",
            return_value=[package_info],
        ):
            graph = self.analyzer.generate_dependency_graph(str(self.temp_dir))

        assert "nodes" in graph
        assert "edges" in graph
        assert "stats" in graph

        # Check nodes
        nodes = graph["nodes"]
        assert len(nodes) >= 4  # 1 package file + 3 dependencies

        node_types = [node["type"] for node in nodes]
        assert "package_file" in node_types
        assert "dependency" in node_types

        # Check edges
        edges = graph["edges"]
        assert len(edges) >= 3  # 3 dependencies

        # Check stats
        stats = graph["stats"]
        assert stats["total_nodes"] == len(nodes)
        assert stats["total_edges"] == len(edges)
        assert stats["package_files"] == 1

    def test_license_compatibility_checking(self):
        """Test license compatibility checking."""
        reports = [
            DependencyReport("mit-package", "1.0.0", "javascript", license="MIT"),
            DependencyReport(
                "apache-package", "1.0.0", "javascript", license="Apache-2.0"
            ),
            DependencyReport("gpl-package", "1.0.0", "javascript", license="GPL-3.0"),
            DependencyReport("unlicensed", "1.0.0", "javascript", license=None),
        ]

        compatibility = self.analyzer.check_license_compatibility(reports, "MIT")

        assert "license_distribution" in compatibility
        assert "compatibility_issues" in compatibility
        assert "compatibility_score" in compatibility

        # MIT should be compatible with MIT and Apache
        # GPL should cause compatibility issues
        assert len(compatibility["compatibility_issues"]) >= 1
        assert any(
            "GPL-3.0" in issue["license"]
            for issue in compatibility["compatibility_issues"]
        )

        # Check distribution
        distribution = compatibility["license_distribution"]
        assert "MIT" in distribution
        assert "Apache-2.0" in distribution
        assert "GPL-3.0" in distribution

    def test_export_report_json(self):
        """Test exporting report as JSON."""
        analysis = ProjectDependencyAnalysis(
            total_dependencies=2,
            direct_dependencies=1,
            dev_dependencies=1,
            security_vulnerabilities=1,
            outdated_dependencies=0,
            license_issues=0,
            health_score=0.8,
            dependency_reports=[
                DependencyReport(
                    "test-package",
                    "1.0.0",
                    "javascript",
                    vulnerabilities=[
                        VulnerabilityInfo(
                            "CVE-123", SecurityRisk.MEDIUM, "Test", "Test vuln", "*"
                        )
                    ],
                )
            ],
            recommendations=["Update vulnerable dependencies"],
            framework_analysis={"detected_frameworks": ["React"]},
        )

        json_report = self.analyzer.export_report(analysis, "json")

        assert isinstance(json_report, str)

        # Parse to verify valid JSON
        parsed = json.loads(json_report)
        assert "summary" in parsed
        assert "dependencies" in parsed
        assert "recommendations" in parsed
        assert "framework_analysis" in parsed

        # Check summary
        summary = parsed["summary"]
        assert summary["total_dependencies"] == 2
        assert summary["health_score"] == 0.8

        # Check dependency details
        deps = parsed["dependencies"]
        assert len(deps) == 1
        assert deps[0]["name"] == "test-package"
        assert len(deps[0]["vulnerabilities"]) == 1

    def test_export_report_markdown(self):
        """Test exporting report as Markdown."""
        analysis = ProjectDependencyAnalysis(
            total_dependencies=2,
            direct_dependencies=1,
            dev_dependencies=1,
            security_vulnerabilities=1,
            outdated_dependencies=0,
            license_issues=0,
            health_score=0.8,
            dependency_reports=[
                DependencyReport(
                    "vulnerable-package",
                    "1.0.0",
                    "javascript",
                    vulnerabilities=[
                        VulnerabilityInfo(
                            "CVE-123",
                            SecurityRisk.HIGH,
                            "Critical Bug",
                            "Test vuln",
                            "*",
                        )
                    ],
                )
            ],
            recommendations=["Update vulnerable dependencies", "Add testing framework"],
        )

        md_report = self.analyzer.export_report(analysis, "markdown")

        assert isinstance(md_report, str)
        assert "# Dependency Analysis Report" in md_report
        assert "## Summary" in md_report
        assert "Total Dependencies**: 2" in md_report
        assert "Health Score**: 0.80" in md_report

        # Check vulnerability section
        assert "## Security Vulnerabilities" in md_report
        assert "vulnerable-package" in md_report
        assert "**HIGH**: Critical Bug" in md_report

        # Check recommendations
        assert "## Recommendations" in md_report
        assert "Update vulnerable dependencies" in md_report
        assert "Add testing framework" in md_report

    def test_export_report_unsupported_format(self):
        """Test exporting report with unsupported format."""
        analysis = ProjectDependencyAnalysis(
            total_dependencies=0,
            direct_dependencies=0,
            dev_dependencies=0,
            security_vulnerabilities=0,
            outdated_dependencies=0,
            license_issues=0,
            health_score=1.0,
            dependency_reports=[],
        )

        with pytest.raises(ValueError):
            self.analyzer.export_report(analysis, "xml")

    def test_vulnerability_info_dataclass(self):
        """Test VulnerabilityInfo dataclass."""
        vuln = VulnerabilityInfo(
            id="CVE-2021-12345",
            severity=SecurityRisk.HIGH,
            title="SQL Injection",
            description="SQL injection vulnerability in authentication",
            affected_versions="<2.0.0",
            patched_versions=">=2.0.0",
            published_date="2021-01-01",
            references=[
                "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-12345"
            ],
        )

        assert vuln.id == "CVE-2021-12345"
        assert vuln.severity == SecurityRisk.HIGH
        assert vuln.title == "SQL Injection"
        assert vuln.affected_versions == "<2.0.0"
        assert len(vuln.references) == 1

    def test_dependency_report_dataclass(self):
        """Test DependencyReport dataclass."""
        vuln = VulnerabilityInfo(
            "CVE-123", SecurityRisk.MEDIUM, "Test", "Test vuln", "*"
        )

        report = DependencyReport(
            name="test-package",
            version="1.0.0",
            language="javascript",
            license="MIT",
            health=DependencyHealth.VULNERABLE,
            vulnerabilities=[vuln],
            is_dev_dependency=True,
            size_mb=2.5,
            maintainers=["maintainer1", "maintainer2"],
            dependencies_count=5,
        )

        assert report.name == "test-package"
        assert report.version == "1.0.0"
        assert report.health == DependencyHealth.VULNERABLE
        assert len(report.vulnerabilities) == 1
        assert report.is_dev_dependency is True
        assert report.size_mb == 2.5
        assert len(report.maintainers) == 2

    def test_project_dependency_analysis_dataclass(self):
        """Test ProjectDependencyAnalysis dataclass."""
        report = DependencyReport("test", "1.0.0", "javascript")

        analysis = ProjectDependencyAnalysis(
            total_dependencies=5,
            direct_dependencies=3,
            dev_dependencies=2,
            security_vulnerabilities=1,
            outdated_dependencies=1,
            license_issues=0,
            health_score=0.75,
            dependency_reports=[report],
            framework_analysis={"frameworks": ["React"]},
            recommendations=["Update dependencies"],
        )

        assert analysis.total_dependencies == 5
        assert analysis.direct_dependencies == 3
        assert analysis.dev_dependencies == 2
        assert analysis.health_score == 0.75
        assert len(analysis.dependency_reports) == 1
        assert len(analysis.recommendations) == 1

        # Check timestamp format
        timestamp = analysis.scan_timestamp
        # Should be ISO format datetime
        datetime.fromisoformat(
            timestamp.replace("Z", "+00:00") if timestamp.endswith("Z") else timestamp
        )

    @pytest.mark.parametrize(
        "security_risk",
        [
            SecurityRisk.CRITICAL,
            SecurityRisk.HIGH,
            SecurityRisk.MEDIUM,
            SecurityRisk.LOW,
            SecurityRisk.INFO,
        ],
    )
    def test_security_risk_enum(self, security_risk):
        """Test SecurityRisk enum values."""
        assert security_risk.value in ["critical", "high", "medium", "low", "info"]

    @pytest.mark.parametrize(
        "health_status",
        [
            DependencyHealth.HEALTHY,
            DependencyHealth.OUTDATED,
            DependencyHealth.DEPRECATED,
            DependencyHealth.VULNERABLE,
            DependencyHealth.ABANDONED,
        ],
    )
    def test_dependency_health_enum(self, health_status):
        """Test DependencyHealth enum values."""
        assert health_status.value in [
            "healthy",
            "outdated",
            "deprecated",
            "vulnerable",
            "abandoned",
        ]
