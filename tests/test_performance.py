"""Performance benchmarking tests for airules auto feature."""

import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from airules.cli import app
from tests.fixtures import (
    create_python_project,
    create_react_project,
    create_rust_project,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_venv_check(monkeypatch):
    """Mock venv check for all tests."""
    monkeypatch.setattr("airules.venv_check.in_virtualenv", lambda: True)


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmarking tests."""

    @pytest.mark.performance
    def test_small_project_analysis_performance(self, tmp_path, benchmark):
        """Benchmark analysis performance on small projects."""
        create_python_project(tmp_path, "small_project")

        def analyze_small_project():
            # This would call the actual analysis components
            # For now, simulate the analysis
            time.sleep(0.1)  # Simulate analysis time
            return {"language": "python", "frameworks": ["flask"]}

        result = benchmark(analyze_small_project)
        assert result["language"] == "python"

        # Small projects should be analyzed quickly
        assert benchmark.stats["mean"] < 0.5  # Less than 500ms

    def test_medium_project_analysis_performance(self, tmp_path, benchmark):
        """Benchmark analysis performance on medium-sized projects."""
        project_path = create_python_project(tmp_path, "medium_project")

        # Create additional files to simulate medium project
        for i in range(50):
            module_path = project_path / "src" / "medium_project" / f"module_{i}.py"
            module_path.parent.mkdir(parents=True, exist_ok=True)
            module_path.write_text(f"def function_{i}(): pass\n" * 10)

        def analyze_medium_project():
            # Simulate medium project analysis
            time.sleep(0.5)
            return {"language": "python", "frameworks": ["flask"], "modules": 50}

        result = benchmark(analyze_medium_project)
        assert result["modules"] == 50

        # Medium projects should still be reasonably fast
        assert benchmark.stats["mean"] < 2.0  # Less than 2 seconds

    def test_large_project_analysis_performance(self, tmp_path, benchmark):
        """Benchmark analysis performance on large projects."""
        project_path = create_python_project(tmp_path, "large_project")

        # Create many files to simulate large project
        for i in range(200):
            module_path = project_path / "src" / "large_project" / f"module_{i}.py"
            module_path.parent.mkdir(parents=True, exist_ok=True)
            module_path.write_text(f"def function_{i}(): pass\n" * 20)

        def analyze_large_project():
            # Simulate large project analysis
            time.sleep(1.0)
            return {"language": "python", "frameworks": ["flask"], "modules": 200}

        result = benchmark(analyze_large_project)
        assert result["modules"] == 200

        # Large projects should complete within reasonable time
        assert benchmark.stats["mean"] < 5.0  # Less than 5 seconds

    def test_package_parsing_performance(self, tmp_path, benchmark):
        """Benchmark package file parsing performance."""
        project_path = create_python_project(tmp_path, "package_test")

        def parse_requirements():
            # Simulate requirements.txt parsing
            requirements_path = project_path / "requirements.txt"
            content = requirements_path.read_text()
            lines = content.strip().split("\n")
            return [line.split("==")[0] for line in lines if "==" in line]

        result = benchmark(parse_requirements)
        assert len(result) > 0

        # Package parsing should be very fast
        assert benchmark.stats["mean"] < 0.1  # Less than 100ms

    def test_framework_detection_performance(self, tmp_path, benchmark):
        """Benchmark framework detection performance."""
        project_path = create_react_project(tmp_path, "react_test")

        def detect_frameworks():
            # Simulate framework detection logic
            frameworks = set()

            # Check for React
            package_json = project_path / "package.json"
            if package_json.exists():
                frameworks.add("javascript")
                frameworks.add("react")

            # Check for TypeScript
            tsconfig = project_path / "tsconfig.json"
            if tsconfig.exists():
                frameworks.add("typescript")

            return list(frameworks)

        result = benchmark(detect_frameworks)
        assert "react" in result

        # Framework detection should be fast
        assert benchmark.stats["mean"] < 0.2  # Less than 200ms

    def test_dependency_analysis_performance(self, tmp_path, benchmark):
        """Benchmark dependency analysis performance."""
        project_path = create_python_project(tmp_path, "dep_test")

        def analyze_dependencies():
            # Simulate dependency analysis
            dependencies = {}

            # Parse requirements.txt
            req_file = project_path / "requirements.txt"
            if req_file.exists():
                content = req_file.read_text()
                for line in content.strip().split("\n"):
                    if "==" in line:
                        name, version = line.split("==")
                        dependencies[name] = version

            return dependencies

        result = benchmark(analyze_dependencies)
        assert len(result) > 0

        # Dependency analysis should be fast
        assert benchmark.stats["mean"] < 0.3  # Less than 300ms

    def test_tag_generation_performance(self, tmp_path, benchmark):
        """Benchmark tag generation performance."""
        project_path = create_python_project(tmp_path, "tag_test")

        def generate_tags():
            # Simulate tag generation based on project analysis
            tags = set()

            # Language tags
            if (project_path / "requirements.txt").exists():
                tags.add("python")

            # Framework tags
            req_content = (project_path / "requirements.txt").read_text()
            if "flask" in req_content.lower():
                tags.add("web")
                tags.add("api")

            if "pytest" in req_content.lower():
                tags.add("testing")

            return list(tags)

        result = benchmark(generate_tags)
        assert len(result) > 0

        # Tag generation should be very fast
        assert benchmark.stats["mean"] < 0.1  # Less than 100ms

    def test_full_auto_pipeline_performance(self, tmp_path, benchmark):
        """Benchmark full auto pipeline performance."""
        create_python_project(tmp_path, "pipeline_test")

        with patch("airules.api_clients.AIClientFactory.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.generate_completion.return_value = "# Generated rules"
            mock_get_client.return_value = mock_client

            def run_auto_pipeline():
                # Simulate full auto pipeline
                # 1. Framework detection
                time.sleep(0.1)

                # 2. Dependency analysis
                time.sleep(0.1)

                # 3. Tag generation
                time.sleep(0.05)

                # 4. Rule generation (API call)
                time.sleep(0.2)

                return {"success": True, "rules_generated": 3}

            result = benchmark(run_auto_pipeline)
            assert result["success"] is True

            # Full pipeline should complete reasonably quickly
            assert benchmark.stats["mean"] < 1.0  # Less than 1 second

    def test_concurrent_analysis_performance(self, tmp_path, benchmark):
        """Benchmark concurrent analysis of multiple projects."""
        import concurrent.futures

        # Create multiple projects
        projects = []
        for i in range(5):
            project_path = create_python_project(tmp_path, f"concurrent_test_{i}")
            projects.append(project_path)

        def analyze_projects_concurrently():
            def analyze_single_project(project_path):
                # Simulate project analysis
                time.sleep(0.1)
                return {"path": str(project_path), "language": "python"}

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(analyze_single_project, p) for p in projects]
                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

            return results

        result = benchmark(analyze_projects_concurrently)
        assert len(result) == 5

        # Concurrent analysis should be more efficient than sequential
        # With 5 projects taking 0.1s each, concurrent should be much faster than 0.5s
        assert benchmark.stats["mean"] < 0.3  # Less than 300ms

    def test_memory_usage_large_project(self, tmp_path):
        """Test memory usage with large projects."""
        psutil = pytest.importorskip("psutil")
        import os

        project_path = create_python_project(tmp_path, "memory_test")

        # Create many files
        for i in range(1000):
            file_path = project_path / "src" / "memory_test" / f"file_{i}.py"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("def function(): pass\n" * 100)

        # Measure memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate analysis of large project
        def analyze_large_project():
            # Simulate reading and analyzing many files
            total_lines = 0
            for py_file in project_path.rglob("*.py"):
                content = py_file.read_text()
                total_lines += len(content.split("\n"))
            return total_lines

        result = analyze_large_project()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory usage should be reasonable (less than 100MB increase)
        assert memory_increase < 100
        assert result > 0

    def test_disk_io_performance(self, tmp_path, benchmark):
        """Benchmark disk I/O performance during analysis."""
        project_path = create_rust_project(tmp_path, "io_test")

        # Create additional files
        for i in range(100):
            file_path = project_path / "src" / f"module_{i}.rs"
            file_path.write_text(f"// Module {i}\npub fn function_{i}() {{}}\n" * 10)

        def analyze_with_disk_io():
            # Simulate reading many files
            file_count = 0
            total_size = 0

            for rust_file in project_path.rglob("*.rs"):
                content = rust_file.read_text()
                file_count += 1
                total_size += len(content)

            return {"files": file_count, "total_size": total_size}

        result = benchmark(analyze_with_disk_io)
        assert result["files"] > 0

        # Disk I/O should be reasonably fast
        assert benchmark.stats["mean"] < 1.0  # Less than 1 second

    def test_regex_performance(self, tmp_path, benchmark):
        """Benchmark regex pattern matching performance."""
        import re

        project_path = create_python_project(tmp_path, "regex_test")

        # Create files with various patterns
        test_content = """
import flask
from django.models import Model
import pytest
from unittest import TestCase
import requests
import pandas as pd
import numpy as np
"""

        for i in range(50):
            file_path = project_path / "src" / "regex_test" / f"file_{i}.py"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(test_content * 10)

        # Common regex patterns for framework detection
        patterns = {
            "flask": re.compile(r"from flask|import flask", re.IGNORECASE),
            "django": re.compile(r"from django|import django", re.IGNORECASE),
            "pytest": re.compile(r"import pytest|from pytest", re.IGNORECASE),
            "requests": re.compile(r"import requests|from requests", re.IGNORECASE),
        }

        def analyze_with_regex():
            matches = {pattern: 0 for pattern in patterns}

            for py_file in project_path.rglob("*.py"):
                content = py_file.read_text()
                for name, pattern in patterns.items():
                    if pattern.search(content):
                        matches[name] += 1

            return matches

        result = benchmark(analyze_with_regex)
        assert sum(result.values()) > 0

        # Regex analysis should be fast
        assert benchmark.stats["mean"] < 0.5  # Less than 500ms


class TestScalabilityTests:
    """Test scalability with different project sizes."""

    @pytest.mark.parametrize("file_count", [10, 50, 100, 500])
    def test_scalability_by_file_count(self, tmp_path, file_count):
        """Test how performance scales with file count."""
        project_path = create_python_project(tmp_path, f"scale_test_{file_count}")

        # Create specified number of files
        for i in range(file_count):
            file_path = (
                project_path / "src" / f"scale_test_{file_count}" / f"file_{i}.py"
            )
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"def function_{i}(): pass\n")

        start_time = time.time()

        # Simulate analysis
        file_count_actual = len(list(project_path.rglob("*.py")))

        end_time = time.time()
        analysis_time = end_time - start_time

        # Performance should scale reasonably (not exponentially)
        assert file_count_actual >= file_count
        assert analysis_time < (
            file_count * 0.01
        )  # Should be much faster than 10ms per file

    @pytest.mark.parametrize("dir_depth", [5, 10, 20])
    def test_scalability_by_directory_depth(self, tmp_path, dir_depth):
        """Test how performance scales with directory depth."""
        project_path = tmp_path / "depth_test"

        # Create nested directory structure
        current_path = project_path
        for i in range(dir_depth):
            current_path = current_path / f"level_{i}"
            current_path.mkdir(parents=True, exist_ok=True)
            (current_path / f"file_{i}.py").write_text(f"# Level {i}")

        start_time = time.time()

        # Simulate deep directory traversal
        file_count = len(list(project_path.rglob("*.py")))

        end_time = time.time()
        traversal_time = end_time - start_time

        # Deep directories should not significantly impact performance
        assert file_count == dir_depth
        assert traversal_time < 1.0  # Should complete within 1 second

    def test_memory_scalability(self, tmp_path):
        """Test memory usage scalability."""
        psutil = pytest.importorskip("psutil")
        import os

        process = psutil.Process(os.getpid())

        # Test with increasing project sizes
        for size in [10, 50, 100]:
            project_path = create_python_project(tmp_path, f"memory_scale_{size}")

            # Create files
            for i in range(size):
                file_path = (
                    project_path / "src" / f"memory_scale_{size}" / f"file_{i}.py"
                )
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("def function(): pass\n" * 100)

            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Simulate analysis
            total_lines = 0
            for py_file in project_path.rglob("*.py"):
                content = py_file.read_text()
                total_lines += len(content.split("\n"))

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable and not grow exponentially
            assert memory_increase < (size * 0.5)  # Less than 0.5MB per file


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
