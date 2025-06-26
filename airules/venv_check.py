"""Virtual environment validation utilities."""

import sys

from .exceptions import VirtualEnvironmentError


def in_virtualenv() -> bool:
    """Check if running in a virtual environment."""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def require_virtualenv() -> None:
    """Require that the code is running in a virtual environment."""
    if not in_virtualenv():
        raise VirtualEnvironmentError(
            "This command must be run in a virtual environment. "
            "Please activate a virtual environment before running airules."
        )


def main() -> None:
    """Main entry point for venv check."""
    try:
        require_virtualenv()
        print("[airules] Virtual environment detected.")
    except VirtualEnvironmentError as e:
        print(f"[airules] ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
