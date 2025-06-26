"""File operations for rules generation."""

import re
from pathlib import Path
from typing import Protocol

import typer

from .exceptions import FileOperationError
from .ui import ConsoleManager


def sanitize_filename(tag: str) -> str:
    """Convert a tag to a safe filename.

    Examples:
        'C# 9' -> 'csharp-9'
        'best practices' -> 'best-practices'
        'Vue.js 3.x' -> 'vuejs-3x'
        'security & performance' -> 'security-performance'
    """
    if not tag:
        return "default"

    # Replace common language/framework names
    replacements = {
        "c#": "csharp",
        "c++": "cpp",
        "f#": "fsharp",
        ".net": "dotnet",
        "node.js": "nodejs",
        "vue.js": "vuejs",
        "angular.js": "angularjs",
        "react.js": "reactjs",
    }

    # Convert to lowercase for processing
    filename = tag.lower()

    # Apply replacements
    for old, new in replacements.items():
        filename = filename.replace(old, new)

    # Replace spaces and special characters with hyphens
    filename = re.sub(r"[^a-z0-9]+", "-", filename)

    # Remove leading/trailing hyphens and collapse multiple hyphens
    filename = re.sub(r"^-+|-+$", "", filename)
    filename = re.sub(r"-+", "-", filename)

    # Ensure we have a valid filename
    if not filename:
        return "default"

    return filename


class FileManagerProtocol(Protocol):
    """Protocol for file manager implementations."""

    def get_rules_filepath(
        self, tool: str, lang: str, tag: str, project_path: str
    ) -> Path:
        """Get the file path for rules."""
        ...

    def write_rules_file(
        self, filepath: Path, content: str, dry_run: bool, yes: bool, tool: str
    ) -> None:
        """Write rules content to file."""
        ...


class FileManager:
    """Manages file operations for rules generation."""

    def __init__(self, console: ConsoleManager):
        self.console = console

    def get_rules_filepath(
        self, tool: str, lang: str, tag: str, project_path: str
    ) -> Path:
        """Determine the appropriate file path for the generated rules."""
        project_root = Path(project_path)

        if tool == "claude":
            return project_root / "CLAUDE.md"
        elif tool == "copilot":
            rules_dir = project_root / ".github"
            safe_lang = sanitize_filename(lang)
            safe_tag = sanitize_filename(tag)
            return rules_dir / f"copilot-{safe_lang}-{safe_tag}.md"

        extension = "mdc" if tool == "cursor" else "md"
        folder = f".{tool}"
        safe_tag = sanitize_filename(tag)

        rules_dir = project_root / folder / "rules"
        return rules_dir / f"{safe_tag}.{extension}"

    def write_rules_file(
        self, filepath: Path, content: str, dry_run: bool, yes: bool, tool: str
    ) -> None:
        """Write the rules content to the specified file path."""
        if dry_run:
            self._preview_file_write(filepath, content)
            return

        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)

            file_existed = filepath.exists()
            write_mode = "a" if tool == "claude" else "w"

            if write_mode == "w" and file_existed and not yes:
                if not self._confirm_overwrite(filepath):
                    self.console.print_warning("Skipping file.")
                    return

            with open(filepath, write_mode, encoding="utf-8") as f:
                if write_mode == "a" and file_existed:
                    f.write("\n\n---\n\n")
                f.write(content)

            action = (
                "appended to" if write_mode == "a" and file_existed else "written to"
            )
            self.console.print_success(f"✓ Rules {action} {filepath}")

        except Exception as e:
            raise FileOperationError(f"Failed to write file {filepath}: {e}")

    def _preview_file_write(self, filepath: Path, content: str) -> None:
        """Preview what would be written to the file."""
        self.console.print(
            f"[bold yellow]--DRY RUN--[/bold yellow] Would write {len(content)} chars to {filepath}"
        )
        self.console.print("--BEGIN PREVIEW--")
        self.console.print(content)
        self.console.print("--END PREVIEW--")

    def _confirm_overwrite(self, filepath: Path) -> bool:
        """Confirm file overwrite with user."""
        try:
            return typer.confirm(f"File {filepath} already exists. Overwrite?")
        except Exception:
            # Handle test environments where stdin/stdout might be redirected
            return False


class ContentProcessor:
    """Processes and cleans rule content."""

    @staticmethod
    def clean_rules_content(content: str) -> str:
        """Clean markdown code blocks from the content."""
        # Replace escaped newlines with actual newlines for proper parsing
        content = content.replace("\\n", "\n").strip()

        # Handle markdown code blocks
        if content.startswith("```") and content.endswith("```"):
            lines = content.split("\n")
            # Skip first line (which might have language name) and last line
            cleaned_content = "\n".join(lines[1:-1])
            return cleaned_content.strip()

        return content
