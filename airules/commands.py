"""Command handlers for the CLI."""

from typing import Optional, Protocol

import typer

from .config import create_default_config, get_config, get_config_path
from .file_operations import FileManager
from .models import format_models_list
from .services import GenerationPipelineService
from .ui import ConsoleManager
from .venv_check import require_virtualenv


class CommandHandlerProtocol(Protocol):
    """Protocol for command handlers."""

    def execute(self, *args, **kwargs) -> None:
        """Execute the command."""
        ...


class InitCommandHandler:
    """Handler for the init command."""

    def __init__(self, console: ConsoleManager):
        self.console = console

    def execute(self) -> None:
        """Initialize a new .rules4rc configuration file."""
        try:
            require_virtualenv()

            if get_config_path().exists():
                self.console.print_warning("✓ .rules4rc already exists.")
                return

            create_default_config()
            self.console.print_success("✓ Created default .rules4rc.")

        except Exception as e:
            self.console.print_error(f"✗ {e}")
            raise typer.Exit(code=1)


class ListModelsCommandHandler:
    """Handler for the list-models command."""

    def __init__(self, console: ConsoleManager):
        self.console = console

    def execute(self) -> None:
        """List all available models."""
        try:
            require_virtualenv()

            self.console.print_info("Available Models for AI Rules Generation\n")
            self.console.print(
                "[dim]Both --primary and --review flags support OpenAI and Anthropic models.[/dim]"
            )
            self.console.print(format_models_list())
            self.console.print_warning(
                "\nNote: Research uses Perplexity's sonar-pro model by default."
            )

        except Exception as e:
            self.console.print_error(f"✗ {e}")
            raise typer.Exit(code=1)


class ToolCommandHandler:
    """Handler for tool-specific commands."""

    def __init__(self, console: ConsoleManager, file_manager: FileManager):
        self.console = console
        self.pipeline_service = GenerationPipelineService(console, file_manager)

    def execute(
        self,
        tool: str,
        primary: str,
        review: Optional[str],
        research: bool,
        lang: Optional[str],
        tags: Optional[str],
        dry_run: bool,
        yes: bool,
        project_path: str,
    ) -> None:
        """Execute tool-specific rule generation."""
        try:
            self.pipeline_service.run_pipeline(
                tool=tool,
                primary_model=primary,
                research=research,
                review_model=review,
                dry_run=dry_run,
                yes=yes,
                project_path=project_path,
                lang=lang,
                tags=tags,
            )

        except Exception as e:
            self.console.print_error(f"✗ {e}")
            raise typer.Exit(code=1)


class GenerateCommandHandler:
    """Handler for the generate command."""

    def __init__(self, console: ConsoleManager, file_manager: FileManager):
        self.console = console
        self.pipeline_service = GenerationPipelineService(console, file_manager)

    def execute(
        self,
        primary: str,
        review: Optional[str],
        research: bool,
        lang: Optional[str],
        tags: Optional[str],
        dry_run: bool,
        yes: bool,
        project_path: str,
    ) -> None:
        """Generate rules for all configured tools."""
        try:
            require_virtualenv()

            config = get_config()
            tools_str = config.get("settings", "tools", fallback="roo")
            tools = [tool.strip() for tool in tools_str.split(",")]

            self.console.print_info(
                f"Generating rules for {len(tools)} tool(s): {', '.join(tools)}"
            )

            supported_tools = {"cursor", "cline", "roo", "copilot", "claude"}

            for tool in tools:
                if tool not in supported_tools:
                    self.console.print_warning(
                        f"Warning: Unsupported tool '{tool}' in config. Skipping."
                    )
                    continue

                self.console.print(f"\nProcessing {tool.upper()}", style="bold")
                self.pipeline_service.run_pipeline(
                    tool=tool,
                    primary_model=primary,
                    research=research,
                    review_model=review,
                    dry_run=dry_run,
                    yes=yes,
                    project_path=project_path,
                    lang=lang,
                    tags=tags,
                )

        except FileNotFoundError:
            self.console.print_error(
                "✗ No .rules4rc file found. Please run 'rules4 init' first."
            )
            raise typer.Exit(code=1)
        except Exception as e:
            self.console.print_error(f"✗ {e}")
            raise typer.Exit(code=1)
