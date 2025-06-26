"""Pytest configuration and shared fixtures for airules tests."""

import os
import tempfile
from pathlib import Path
from typing import Iterator
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner


@pytest.fixture(autouse=True)
def mock_venv_check(monkeypatch):
    """Mock venv check for all tests."""
    monkeypatch.setattr("airules.venv_check.in_virtualenv", lambda: True)


@pytest.fixture
def runner():
    """Provide a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_project_dir() -> Iterator[Path]:
    """Provide a temporary directory for test projects."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI API client."""
    mock_client = Mock()
    mock_client.generate_completion.return_value = "# Generated rules content"
    return mock_client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client."""
    mock_client = Mock()
    mock_client.generate_completion.return_value = "# Validated rules content"
    return mock_client


@pytest.fixture
def mock_perplexity_client():
    """Mock Perplexity research client."""
    mock_client = Mock()
    mock_client.generate_completion.return_value = "Research summary content"
    return mock_client


@pytest.fixture
def mock_api_responses():
    """Standard mock API responses for testing."""
    return {
        "research": "RESEARCH: Comprehensive analysis of the project structure and dependencies",
        "generation": "# Auto-Generated Rules\n\nThis project uses the following technologies:\n- Language: Python\n- Framework: Flask\n- Testing: pytest",
        "validation": "# Validated Auto-Generated Rules\n\nImproved rules based on analysis:\n- Use Python 3.8+ features\n- Follow Flask best practices\n- Implement comprehensive testing with pytest",
    }


@pytest.fixture
def mock_all_api_clients(
    mock_openai_client, mock_anthropic_client, mock_perplexity_client
):
    """Mock all API clients."""
    return {
        "openai": mock_openai_client,
        "anthropic": mock_anthropic_client,
        "perplexity": mock_perplexity_client,
    }


@pytest.fixture
def sample_env_vars():
    """Provide sample environment variables for testing."""
    return {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "PERPLEXITY_API_KEY": "test-perplexity-key",
    }


@pytest.fixture
def mock_env_vars(monkeypatch, sample_env_vars):
    """Mock environment variables for testing."""
    for key, value in sample_env_vars.items():
        monkeypatch.setenv(key, value)


# Pytest markers for organizing tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: Integration tests that test the complete workflow"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and benchmarking tests"
    )
    config.addinivalue_line(
        "markers", "error_handling: Error handling and edge case tests"
    )
    config.addinivalue_line("markers", "slow: Tests that take longer to run")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to integration test files
        if "test_auto_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Add performance marker to performance test files
        if "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)

        # Add error_handling marker to error handling test files
        if "test_error_handling" in item.nodeid:
            item.add_marker(pytest.mark.error_handling)

        # Add slow marker to performance tests
        if "test_performance" in item.nodeid or "benchmark" in item.name:
            item.add_marker(pytest.mark.slow)


# Test environment setup
def pytest_sessionstart(session):
    """Set up test environment."""
    # Ensure test directory exists
    test_dir = Path(__file__).parent
    fixtures_dir = test_dir / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    # Set up any global test configuration
    os.environ.setdefault("TESTING", "1")


def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session."""
    # Clean up any temporary files or resources
    pass
