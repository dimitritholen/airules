# Makefile for airules CLI

.PHONY: venv install test test-integration test-performance test-error-handling test-coverage test-all lint lint-check lint-fix format type-check publish publish-test clean

venv:
	python3 -m venv .venv

install: venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && pip install pytest-benchmark

# Run all tests with coverage requirement
test:
	. .venv/bin/activate && PYTHONPATH=. pytest

# Run only integration tests
test-integration:
	. .venv/bin/activate && PYTHONPATH=. pytest tests/test_auto_integration.py -v -m integration

# Run only performance tests
test-performance:
	. .venv/bin/activate && PYTHONPATH=. pytest tests/test_performance.py -v -m performance --benchmark-only

# Run only error handling tests
test-error-handling:
	. .venv/bin/activate && PYTHONPATH=. pytest tests/test_error_handling.py -v -m error_handling

# Generate detailed coverage report
test-coverage:
	. .venv/bin/activate && PYTHONPATH=. pytest --cov=airules --cov-report=html --cov-report=term-missing --cov-fail-under=90
	@echo "Coverage report generated in htmlcov/index.html"

# Run all test suites including performance benchmarks
test-all:
	. .venv/bin/activate && PYTHONPATH=. pytest --cov=airules --cov-report=html --cov-report=term-missing --cov-fail-under=90 --benchmark-skip

# Comprehensive linting
lint: lint-check type-check
	@echo "✅ All linting checks passed!"

# Check code style without fixing
lint-check:
	@echo "🔍 Running flake8..."
	. .venv/bin/activate && flake8 airules tests
	@echo "🔍 Checking import order..."
	. .venv/bin/activate && isort --check-only --diff airules tests
	@echo "🔍 Checking code formatting..."
	. .venv/bin/activate && black --check --diff airules tests

# Fix code style issues
lint-fix: format
	@echo "🔧 Fixing import order..."
	. .venv/bin/activate && isort airules tests

# Format code with black
format:
	@echo "🎨 Formatting code with black..."
	. .venv/bin/activate && black airules tests

# Type checking
type-check:
	@echo "🔍 Running type checks..."
	. .venv/bin/activate && mypy airules

# Publishing
publish:
	@echo "📦 Publishing to PyPI..."
	./publish.sh

publish-test:
	@echo "📦 Publishing to TestPyPI..."
	./publish.sh --test

clean:
	rm -rf .venv __pycache__ .pytest_cache .coverage .mypy_cache dist build *.egg-info
