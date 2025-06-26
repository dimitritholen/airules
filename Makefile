# Makefile for airules CLI

.PHONY: venv install test lint lint-check lint-fix format type-check clean

venv:
	python3 -m venv .venv

install: venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

test:
	. .venv/bin/activate && PYTHONPATH=. pytest --maxfail=1 --disable-warnings --cov=airules --cov-report=term-missing

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

clean:
	rm -rf .venv __pycache__ .pytest_cache .coverage .mypy_cache
