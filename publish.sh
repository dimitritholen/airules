#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Cleaning up old builds..."
rm -rf dist/ build/ *.egg-info

echo "Building distribution packages..."
python3 -m build

echo "Uploading to PyPI..."
# Assumes PYPI_API_TOKEN environment variable is set
python3 -m twine upload --repository pypi dist/*

echo "Successfully published to PyPI!"
