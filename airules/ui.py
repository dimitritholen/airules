"""UI components for airules CLI."""

import sys
import threading
import time
from typing import Protocol

from rich.console import Console


class SpinnerProtocol(Protocol):
    """Protocol for spinner implementations."""

    def __enter__(self):
        """Start the spinner."""
        ...

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop the spinner."""
        ...


class Spinner:
    """Enhanced terminal spinner with color support."""

    def __init__(self, message: str = "Loading..."):
        self.message = message
        self.stop_running = threading.Event()
        self.spinner_thread = threading.Thread(target=self._spin)
        self.spinner_thread.daemon = True

        # ANSI color and formatting codes
        self._colors = {
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "magenta": "\033[95m",
            "dim": "\033[2m",
            "bold": "\033[1m",
            "reset": "\033[0m",
            "hide_cursor": "\033[?25l",
            "show_cursor": "\033[?25h",
        }

        # Spinner frames
        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._frame_delay = 0.08

    def _spin(self) -> None:
        """Spinner animation loop."""
        i = 0
        sys.stdout.write(self._colors["hide_cursor"])
        sys.stdout.flush()

        while not self.stop_running.is_set():
            frame = self._frames[i % len(self._frames)]
            output = (
                f"\r{self._colors['cyan']}{frame}{self._colors['reset']} "
                f"{self._colors['bold']}{self.message}{self._colors['reset']}"
            )

            sys.stdout.write("\r\033[K" + output)
            sys.stdout.flush()

            time.sleep(self._frame_delay)
            i += 1

    def __enter__(self):
        """Start the spinner."""
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        self.spinner_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop the spinner."""
        self.stop_running.set()
        self.spinner_thread.join()
        sys.stdout.write("\r\033[K")
        sys.stdout.write(self._colors["show_cursor"])
        sys.stdout.flush()
        time.sleep(0.05)


class ConsoleManager:
    """Manages console output for the application."""

    def __init__(self):
        self.console = Console()
        self.error_console = Console(stderr=True)

    def print(self, message: str, style: str = "") -> None:
        """Print a message to the console."""
        self.console.print(message, style=style)

    def print_error(self, message: str, style: str = "bold red") -> None:
        """Print an error message to stderr."""
        self.error_console.print(message, style=style)

    def print_success(self, message: str) -> None:
        """Print a success message."""
        self.console.print(message, style="bold green")

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        self.console.print(message, style="yellow")

    def print_info(self, message: str) -> None:
        """Print an info message."""
        self.console.print(message, style="blue")
