"""Command handlers for the CLI."""

from typing import Optional, Protocol

import typer

from .analyzer import CodebaseAnalyzer
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


class AutoCommandHandler:
    """Handler for the auto command that auto-detects project characteristics."""

    def __init__(self, console: ConsoleManager, file_manager: FileManager):
        self.console = console
        self.pipeline_service = GenerationPipelineService(console, file_manager)
        self.analyzer = CodebaseAnalyzer()

    def execute(
        self,
        tool: Optional[str],
        primary: str,
        review: Optional[str],
        research: bool,
        lang: Optional[str],
        tags: Optional[str],
        dry_run: bool,
        yes: bool,
        project_path: str,
    ) -> None:
        """Execute auto command with project analysis."""
        try:
            require_virtualenv()

            # Auto-detect project characteristics
            self.console.print_info("Analyzing project structure...")
            analysis_result = self.analyzer.analyze(project_path)

            # Extract detected language and tags
            detected_lang = (
                analysis_result.primary_language.name
                if analysis_result.primary_language
                else None
            )
            detected_tags = self.analyzer.get_recommended_tags(analysis_result)

            # Show analysis results
            summary_parts = []
            if detected_lang:
                summary_parts.append(f"Detected language: {detected_lang}")
            else:
                summary_parts.append("Language: Unable to detect")

            if detected_tags:
                summary_parts.append(f"Detected tags: {', '.join(detected_tags)}")
            else:
                summary_parts.append("Tags: None detected")

            analysis_summary = " | ".join(summary_parts)
            self.console.print_info(f"Analysis: {analysis_summary}")

            # Merge detected characteristics with user overrides
            final_lang = lang or detected_lang
            final_tags = tags or ",".join(detected_tags) if detected_tags else None

            if not final_lang:
                raise Exception(
                    "Unable to detect project language. Please specify with --lang option."
                )

            if not final_tags:
                final_tags = "general"
                self.console.print_warning("No specific tags detected, using 'general'")

            # Show what will be generated
            self.console.print_info(
                f"Generating with: language={final_lang}, tags={final_tags}"
            )

            # Determine tools to process
            if tool:
                # Single tool specified
                self._process_single_tool(
                    tool,
                    primary,
                    review,
                    research,
                    final_lang,
                    final_tags,
                    dry_run,
                    yes,
                    project_path,
                )
            else:
                # Process all configured tools
                self._process_all_tools(
                    primary,
                    review,
                    research,
                    final_lang,
                    final_tags,
                    dry_run,
                    yes,
                    project_path,
                )

        except Exception as e:
            self.console.print_error(f"✗ {e}")
            raise typer.Exit(code=1)

    def _process_single_tool(
        self,
        tool: str,
        primary: str,
        review: Optional[str],
        research: bool,
        lang: str,
        tags: str,
        dry_run: bool,
        yes: bool,
        project_path: str,
    ) -> None:
        """Process a single tool with auto-detected characteristics."""
        supported_tools = {"cursor", "cline", "roo", "copilot", "claude"}

        if tool not in supported_tools:
            raise Exception(
                f"Unsupported tool: {tool}. Supported tools: {', '.join(supported_tools)}"
            )

        self.console.print(
            f"Processing {tool.upper()} with auto-detected settings", style="bold"
        )

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

    def _process_all_tools(
        self,
        primary: str,
        review: Optional[str],
        research: bool,
        lang: str,
        tags: str,
        dry_run: bool,
        yes: bool,
        project_path: str,
    ) -> None:
        """Process all configured tools with auto-detected characteristics."""
        try:
            config = get_config()
            tools_str = config.get("settings", "tools", fallback="roo")
            tools = [tool.strip() for tool in tools_str.split(",")]
        except FileNotFoundError:
            # Default to common tools if no config
            tools = ["cursor", "claude"]
            self.console.print_warning(
                "No .rules4rc file found. Using default tools: cursor, claude. "
                "Run 'rules4 init' to create configuration."
            )

        self.console.print_info(
            f"Generating auto-detected rules for {len(tools)} tool(s): {', '.join(tools)}"
        )

        supported_tools = {"cursor", "cline", "roo", "copilot", "claude"}

        for tool in tools:
            if tool not in supported_tools:
                self.console.print_warning(
                    f"Warning: Unsupported tool '{tool}' in config. Skipping."
                )
                continue

            self.console.print(
                f"\nProcessing {tool.upper()} with auto-detected settings", style="bold"
            )
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
