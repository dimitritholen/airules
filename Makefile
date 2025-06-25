# Makefile for airules CLI

.PHONY: venv install test lint clean

venv:
	python3 -m venv .venv

install: venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

test:
	. .venv/bin/activate && PYTHONPATH=. pytest --maxfail=1 --disable-warnings --cov=airules --cov-report=term-missing

lint:
	. .venv/bin/activate && flake8 airules tests

clean:
	rm -rf .venv __pycache__ .pytest_cache .coverage .mypy_cache
