#!/usr/bin/env python3
"""Comprehensive test runner for airules auto feature."""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


def run_command(command: List[str], description: str) -> Dict[str, Any]:
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")

    start_time = time.time()
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, cwd=Path(__file__).parent
        )
        end_time = time.time()
        duration = end_time - start_time

        print(f"Exit Code: {result.returncode}")
        print(f"Duration: {duration:.2f} seconds")

        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")

        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")

        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except Exception as e:
        print(f"Error running command: {e}")
        return {
            "success": False,
            "duration": 0,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
        }


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for airules"
    )
    parser.add_argument(
        "--suite",
        choices=["all", "unit", "integration", "performance", "error"],
        default="all",
        help="Test suite to run",
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Run performance benchmarks"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--parallel", "-j", type=int, help="Number of parallel test workers"
    )

    args = parser.parse_args()

    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    if not (project_root / "airules").exists():
        print("Error: Must be run from project root directory")
        sys.exit(1)

    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]

    if args.verbose:
        base_cmd.append("-v")

    if args.parallel:
        base_cmd.extend(["-n", str(args.parallel)])

    # Test configurations
    test_configs = {
        "unit": {
            "description": "Unit Tests",
            "command": base_cmd
            + [
                "tests/test_airules.py",
                "tests/test_file_creation.py",
                "tests/test_venv_check.py",
            ],
            "required": True,
        },
        "integration": {
            "description": "Integration Tests",
            "command": base_cmd
            + ["tests/test_auto_integration.py", "-m", "integration"],
            "required": True,
        },
        "performance": {
            "description": "Performance Tests",
            "command": base_cmd
            + ["tests/test_performance.py", "-m", "performance"]
            + (["--benchmark-only"] if args.benchmark else ["--benchmark-skip"]),
            "required": False,
        },
        "error": {
            "description": "Error Handling Tests",
            "command": base_cmd
            + ["tests/test_error_handling.py", "-m", "error_handling"],
            "required": True,
        },
    }

    # Coverage configuration
    coverage_config = {
        "description": "Coverage Report",
        "command": base_cmd
        + [
            "--cov=airules",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=90",
        ]
        + (["tests/"] if args.suite == "all" else []),
        "required": args.coverage,
    }

    # Results tracking
    results = {}
    total_duration = 0

    print("Airules Auto Feature Test Runner")
    print("=" * 60)
    print(f"Test Suite: {args.suite}")
    print(f"Coverage: {args.coverage}")
    print(f"Benchmarks: {args.benchmark}")
    print(f"Verbose: {args.verbose}")
    if args.parallel:
        print(f"Parallel Workers: {args.parallel}")

    # Run selected tests
    if args.suite == "all":
        # Run all test suites
        for suite_name, config in test_configs.items():
            result = run_command(config["command"], config["description"])
            results[suite_name] = result
            total_duration += result["duration"]

            if not result["success"] and config["required"]:
                print(f"\n❌ {config['description']} FAILED - Stopping execution")
                break
    else:
        # Run specific test suite
        if args.suite in test_configs:
            config = test_configs[args.suite]
            result = run_command(config["command"], config["description"])
            results[args.suite] = result
            total_duration += result["duration"]

    # Run coverage if requested
    if args.coverage:
        coverage_result = run_command(
            coverage_config["command"], coverage_config["description"]
        )
        results["coverage"] = coverage_result
        total_duration += coverage_result["duration"]

    # Summary report
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = 0
    failed = 0

    for test_name, result in results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        duration = result["duration"]
        print(f"{test_name.upper():15} {status:10} ({duration:.2f}s)")

        if result["success"]:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal Duration: {total_duration:.2f} seconds")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    # Coverage summary
    if args.coverage and "coverage" in results:
        coverage_output = results["coverage"]["stdout"]
        if "TOTAL" in coverage_output:
            # Extract coverage percentage
            lines = coverage_output.split("\n")
            for line in lines:
                if "TOTAL" in line:
                    print(f"Coverage: {line}")
                    break

    # Exit with appropriate code
    if failed > 0:
        print(f"\n❌ {failed} test suite(s) failed")
        sys.exit(1)
    else:
        print(f"\n✅ All {passed} test suite(s) passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
