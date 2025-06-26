"""Custom exceptions for airules."""


class AirulesError(Exception):
    """Base exception for airules."""

    pass


class ConfigurationError(AirulesError):
    """Raised when there's an issue with configuration."""

    pass


class VirtualEnvironmentError(AirulesError):
    """Raised when virtual environment is not active."""

    pass


class APIError(AirulesError):
    """Raised when API operations fail."""

    pass


class ModelNotFoundError(AirulesError):
    """Raised when a model is not found."""

    pass


class FileOperationError(AirulesError):
    """Raised when file operations fail."""

    pass
