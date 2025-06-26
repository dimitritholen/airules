"""Test fixtures for airules auto feature testing."""

from .mock_projects import (
    create_django_project,
    create_fastapi_project,
    create_nextjs_project,
    create_python_project,
    create_react_project,
    create_rust_project,
)

__all__ = [
    "create_python_project",
    "create_django_project",
    "create_fastapi_project",
    "create_react_project",
    "create_nextjs_project",
    "create_rust_project",
]
