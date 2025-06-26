"""Refactored CLI for airules - follows industry best practices."""

from pathlib import Path
from typing import Optional

import typer

from .commands import (
    AutoCommandHandler,
    GenerateCommandHandler,
    InitCommandHandler,
    ListModelsCommandHandler,
    ToolCommandHandler,
)
from .file_operations import ContentProcessor, FileManager
from .ui import ConsoleManager

# Backwards compatibility exports for tests
clean_rules_content = ContentProcessor.clean_rules_content


__version__ = "1.0.0"

# Initialize shared dependencies
console_manager = ConsoleManager()
file_manager = FileManager(console_manager)

# Initialize command handlers
init_handler = InitCommandHandler(console_manager)
list_models_handler = ListModelsCommandHandler(console_manager)
tool_handler = ToolCommandHandler(console_manager, file_manager)
generate_handler = GenerateCommandHandler(console_manager, file_manager)
auto_handler = AutoCommandHandler(console_manager, file_manager)


def version_callback(value: bool) -> None:
    """Handle version flag."""
    if value:
        console_manager.print_info(f"rules4 version {__version__}")
        console_manager.print(
            "[dim]A CLI to generate AI coding assistant rules for your project[/dim]"
        )
        raise typer.Exit()


# Create the main application
app = typer.Typer(
    help="""Generate AI coding assistant rules for your project

[bold blue]EXAMPLES:[/bold blue]
  [dim]$[/dim] rules4 auto --research --review claude-3-5-sonnet-20241022  # Smart auto-detection
  [dim]$[/dim] rules4 auto cursor --primary gpt-4-turbo  # Auto-detect for specific tool
  [dim]$[/dim] rules4 copilot --lang python --tags "pytest" --primary gpt-4-turbo
  [dim]$[/dim] rules4 cursor --primary claude-3-5-sonnet-20241022 --review gpt-4o
  [dim]$[/dim] rules4 generate --lang go --tags "code style,testing"
  [dim]$[/dim] rules4 list-models  # See all available models

[bold blue]TIPS:[/bold blue]
  [green]•[/green] Run [bold]'rules4 init'[/bold] to create config file
  [green]•[/green] Use [bold]'rules4 auto'[/bold] for smart project analysis
  [green]•[/green] Use [bold]'--research'[/bold] for better results
  [green]•[/green] Mix models: Claude for generation, GPT-4 for review
""",
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version information.",
    ),
) -> None:
    """A CLI to generate AI coding assistant rules for your project.

    Generate customized rules for popular AI coding assistants like Cursor, Cline,
    Roo, GitHub Copilot, and Claude. Supports research-backed rule generation and
    multi-model review processes.

    [bold blue]Getting Started:[/bold blue]
    [green]1.[/green] Run [bold]'rules4 init'[/bold] to create a configuration file
    [green]2.[/green] Set your API keys in environment variables
    [green]3.[/green] Generate rules with [bold]'rules4 <tool>'[/bold] or [bold]'rules4 generate'[/bold]
    """
    if ctx.invoked_subcommand is None:
        console_manager.console.print(ctx.get_help())


@app.command()
def init() -> None:
    """Initialize a new .rules4rc configuration file.

    Creates a default configuration file in the current directory with:
    [green]•[/green] Default language and tool settings
    [green]•[/green] Customizable tags for rule generation
    [green]•[/green] Environment variable references for API keys

    [yellow]Must be run inside a virtual environment for safety.[/yellow]
    """
    init_handler.execute()


@app.command(name="list-models")
def list_models() -> None:
    """List all available models for primary and review operations.

    Shows models grouped by provider (OpenAI, Anthropic, Perplexity).
    Both --primary and --review flags support OpenAI and Anthropic models.
    """
    list_models_handler.execute()


def _create_tool_command(tool_name: str):
    """Create a command function for a specific tool."""

    def _command(
        primary: str = typer.Option(
            "gpt-4-turbo",
            "--primary",
            help="Primary model for rule generation (OpenAI or Anthropic). Use --list-models to see available options.",
        ),
        review: Optional[str] = typer.Option(
            None,
            "--review",
            help="Review model for refinement (OpenAI or Anthropic). Use --list-models to see available options.",
        ),
        research: bool = typer.Option(
            False, "--research", help="Perform research with Perplexity first."
        ),
        lang: Optional[str] = typer.Option(
            None, "--lang", help="Specify the programming language for rule generation."
        ),
        tags: Optional[str] = typer.Option(
            None,
            "--tags",
            help="Comma-separated list of tags/topics for rule generation.",
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Preview changes without writing files."
        ),
        yes: bool = typer.Option(
            False, "-y", "--yes", help="Overwrite files without prompting."
        ),
        project_path: str = typer.Option(".", help="Target project directory."),
    ) -> None:
        """Generate rules for a specific tool."""
        tool_handler.execute(
            tool=tool_name,
            primary=primary,
            review=review,
            research=research,
            lang=lang,
            tags=tags,
            dry_run=dry_run,
            yes=yes,
            project_path=project_path,
        )

    return _command


# Register tool commands
for tool in ["cursor", "cline", "roo", "copilot", "claude"]:
    app.command(name=tool, help=f"Generate rules for {tool.capitalize()}.")(
        _create_tool_command(tool)
    )


@app.command()
def generate(
    primary: str = typer.Option(
        "gpt-4-turbo",
        "--primary",
        help="Primary model for rule generation (OpenAI or Anthropic). Use --list-models to see available options.",
    ),
    review: Optional[str] = typer.Option(
        None,
        "--review",
        help="Review model for refinement (OpenAI or Anthropic). Use --list-models to see available options.",
    ),
    research: bool = typer.Option(
        False, "--research", help="Perform research with Perplexity first."
    ),
    lang: Optional[str] = typer.Option(
        None, "--lang", help="Specify the programming language for rule generation."
    ),
    tags: Optional[str] = typer.Option(
        None, "--tags", help="Comma-separated list of tags/topics for rule generation."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview changes without writing files."
    ),
    yes: bool = typer.Option(
        False, "-y", "--yes", help="Overwrite files without prompting."
    ),
    project_path: str = typer.Option(".", help="Target project directory."),
) -> None:
    """Generate rules for all tools configured in .rules4rc.

    Processes all tools specified in your configuration file and generates
    appropriate rules for each one. This is the most efficient way to set up
    rules for multiple AI coding assistants at once.

    [bold blue]Features:[/bold blue]
    [green]•[/green] Batch processing for multiple tools
    [green]•[/green] Respects .rules4rc configuration settings
    [green]•[/green] Supports research-backed generation
    [green]•[/green] Optional Claude review for quality assurance
    """
    generate_handler.execute(
        primary=primary,
        review=review,
        research=research,
        lang=lang,
        tags=tags,
        dry_run=dry_run,
        yes=yes,
        project_path=project_path,
    )


@app.command()
def auto(
    tool: Optional[str] = typer.Argument(
        None,
        help="Specific tool to generate rules for (cursor, cline, roo, copilot, claude). If not specified, generates for all configured tools.",
    ),
    primary: str = typer.Option(
        "gpt-4-turbo",
        "--primary",
        help="Primary model for rule generation (OpenAI or Anthropic). Use --list-models to see available options.",
    ),
    review: Optional[str] = typer.Option(
        None,
        "--review",
        help="Review model for refinement (OpenAI or Anthropic). Use --list-models to see available options.",
    ),
    research: bool = typer.Option(
        False, "--research", help="Perform research with Perplexity first."
    ),
    lang: Optional[str] = typer.Option(
        None, "--lang", help="Override auto-detected programming language."
    ),
    tags: Optional[str] = typer.Option(
        None, "--tags", help="Override auto-detected tags (comma-separated)."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview changes without writing files."
    ),
    yes: bool = typer.Option(
        False, "-y", "--yes", help="Overwrite files without prompting."
    ),
    project_path: str = typer.Option(".", help="Target project directory."),
) -> None:
    """Auto-detect project characteristics and generate tailored rules.

    Analyzes your project structure to automatically determine the programming
    language and relevant tags, then generates appropriate rules for AI coding
    assistants. This is the smartest way to get started with rules generation.

    [bold blue]Features:[/bold blue]
    [green]•[/green] Smart project language detection (Python, JavaScript, Go, etc.)
    [green]•[/green] Automatic tag detection (testing, web-dev, API, security, etc.)
    [green]•[/green] Manual overrides with --lang and --tags options
    [green]•[/green] Works with single tools or all configured tools
    [green]•[/green] Integrates with research and review pipeline

    [bold blue]Examples:[/bold blue]
    [dim]$[/dim] rules4 auto  # Auto-detect and generate for all tools
    [dim]$[/dim] rules4 auto cursor  # Auto-detect for Cursor only
    [dim]$[/dim] rules4 auto --research --lang python  # Override language
    [dim]$[/dim] rules4 auto --tags "testing,security"  # Override tags

    [yellow]Must be run inside a virtual environment for safety.[/yellow]
    """
    auto_handler.execute(
        tool=tool,
        primary=primary,
        review=review,
        research=research,
        lang=lang,
        tags=tags,
        dry_run=dry_run,
        yes=yes,
        project_path=project_path,
    )


if __name__ == "__main__":
    app()


# Import original implementations for backwards compatibility with tests
# This allows tests to continue working while we have the new refactored code
try:
    from .cli_old import (
        generate_rules,
        research_with_perplexity,
        run_generation_pipeline,
        validate_rules,
        write_rules_file,
    )
except ImportError:
    # Fallback implementations if old file doesn't exist
    def run_generation_pipeline(
        tool: str,
        primary_model: str,
        research: bool,
        review_model: Optional[str],
        dry_run: bool,
        yes: bool,
        project_path: str,
        lang: Optional[str] = None,
        tags: Optional[str] = None,
    ):
        """Compatibility wrapper for tests."""
        tool_handler.execute(
            tool=tool,
            primary=primary_model,
            review=review_model,
            research=research,
            lang=lang,
            tags=tags,
            dry_run=dry_run,
            yes=yes,
            project_path=project_path,
        )

    def write_rules_file(
        filepath: Path, content: str, dry_run: bool, yes: bool, tool: str
    ):
        """Compatibility wrapper for tests."""
        file_manager.write_rules_file(filepath, content, dry_run, yes, tool)

    def generate_rules(
        lang: str,
        tool: str,
        tag: str,
        model: str,
        research_summary: Optional[str] = None,
    ) -> str:
        """Compatibility wrapper for tests."""
        from .services import RulesGeneratorService

        generator = RulesGeneratorService()
        return generator.generate_rules(lang, tool, tag, model, research_summary)

    def validate_rules(content: str, review_model: str) -> str:
        """Compatibility wrapper for tests."""
        from .services import RulesGeneratorService

        generator = RulesGeneratorService()
        return generator.validate_rules(content, review_model)

    def research_with_perplexity(lang: str, tag: str) -> str:
        """Compatibility wrapper for tests."""
        from .services import ResearchService

        research = ResearchService()
        return research.research_topic(lang, tag)
