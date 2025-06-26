import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
import openai
import typer
from rich.console import Console

from .config import create_default_config, get_config, get_config_path
from .venv_check import in_virtualenv

__version__ = "1.0.0"


def version_callback(value: bool):
    if value:
        console.print(
            f"[bold blue]rules4[/bold blue] version [bold green]{__version__}[/bold green]"
        )
        console.print(
            "[dim]A CLI to generate AI coding assistant rules for your project[/dim]"
        )
        raise typer.Exit()


app = typer.Typer(
    help="""Generate AI coding assistant rules for your project

[bold blue]EXAMPLES:[/bold blue]
  [dim]$[/dim] rules4 copilot --lang python --tags "pytest" --primary gpt-4-turbo
  [dim]$[/dim] rules4 copilot --lang javascript --research --review claude-3-5-sonnet-20241022
  [dim]$[/dim] rules4 generate --lang go --tags "code style,testing"
  [dim]$[/dim] rules4 cursor --lang typescript --tags "react,hooks" --dry-run

[bold blue]TIPS:[/bold blue]
  [green]•[/green] Run [bold]'rules4 init'[/bold] to create config file
  [green]•[/green] Use [bold]'--research'[/bold] for better results
  [green]•[/green] Available: [italic]cursor, cline, roo, copilot, claude[/italic]
""",
    rich_markup_mode="rich"
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
):
    """A CLI to generate AI coding assistant rules for your project

    Generate customized rules for popular AI coding assistants like Cursor, Cline,
    Roo, GitHub Copilot, and Claude. Supports research-backed rule generation and
    multi-model review processes.

    [bold blue]Getting Started:[/bold blue]
    [green]1.[/green] Run [bold]'rules4 init'[/bold] to create a configuration file
    [green]2.[/green] Set your API keys in environment variables
    [green]3.[/green] Generate rules with [bold]'rules4 <tool>'[/bold] or [bold]'rules4 generate'[/bold]
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


console = Console()
error_console = Console(stderr=True)


class Spinner:
    def __init__(self, message="Loading..."):
        self.message = message
        self.stop_running = threading.Event()
        self.spinner_thread = threading.Thread(target=self._spin)
        # Ensure the thread is marked as daemon so it doesn't block program exit
        self.spinner_thread.daemon = True
        # ANSI color and formatting codes
        self.BLUE = "\033[94m"
        self.CYAN = "\033[96m"
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.MAGENTA = "\033[95m"
        self.DIM = "\033[2m"
        self.BOLD = "\033[1m"
        self.ENDC = "\033[0m"
        # Hide cursor
        self.HIDE_CURSOR = "\033[?25l"
        self.SHOW_CURSOR = "\033[?25h"
        
        # Different spinner styles
        self.spinners = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "dots2": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
            "line": ["⎯", "⎯⎯", "⎯⎯⎯", "⎯⎯⎯⎯", "⎯⎯⎯⎯⎯", "⎯⎯⎯⎯", "⎯⎯⎯", "⎯⎯", "⎯"],
            "stars": ["✶", "✸", "✹", "✺", "✹", "✸"],
            "arc": ["◜", "◠", "◝", "◞", "◡", "◟"],
            "circle": ["◐", "◓", "◑", "◒"],
            "bouncing": ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"],
            "progress": ["[    ]", "[=   ]", "[==  ]", "[=== ]", "[====]", "[ ===]", "[  ==]", "[   =]"],
            "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
            "clock": ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"],
            "earth": ["🌍", "🌎", "🌏"],
            "hearts": ["💛", "💙", "💜", "💚", "❤️ "],
            "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "grow": ["▁", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"]
        }
        
        # Use a nice default spinner
        self.current_spinner = self.spinners["dots"]
        self.frame_delay = 0.08  # Faster, smoother animation

    def _spin(self):
        i = 0
        # Hide cursor at start
        sys.stdout.write(self.HIDE_CURSOR)
        sys.stdout.flush()

        while not self.stop_running.is_set():
            # Get current frame
            frame = self.current_spinner[i % len(self.current_spinner)]
            
            # Build the complete line with colors
            output = f"\r{self.CYAN}{frame}{self.ENDC} {self.BOLD}{self.message}{self.ENDC}"
            
            # Write the spinner with proper line clearing
            sys.stdout.write("\r\033[K" + output)
            sys.stdout.flush()

            time.sleep(self.frame_delay)
            i += 1

    def __enter__(self):
        # Clear any existing output on the line
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        # Start the spinner thread
        self.spinner_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_running.set()
        self.spinner_thread.join()
        # Clear the spinner line and show cursor
        sys.stdout.write("\r\033[K")
        sys.stdout.write(self.SHOW_CURSOR)
        sys.stdout.flush()
        # Brief pause to ensure cleanup completes
        time.sleep(0.05)


def clean_rules_content(content: str) -> str:
    """Clean markdown code blocks from the content.

    Tests use escaped newlines (\\n), so we need to handle them properly.
    """
    # Replace escaped newlines with actual newlines for proper parsing
    content = content.replace("\\n", "\n").strip()

    # Handle markdown code blocks
    if content.startswith("```") and content.endswith("```"):
        lines = content.split("\n")
        # Skip first line (which might have language name) and last line
        cleaned_content = "\n".join(lines[1:-1])
        return cleaned_content.strip()

    return content


def research_with_perplexity(lang: str, tag: str) -> str:
    """Performs research using Perplexity API and returns the findings."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        error_console.print("\n[bold red]✗ Missing Perplexity API Key[/bold red]")
        error_console.print(
            "[yellow]To use the --research flag, you need to set your Perplexity API key:[/yellow]"
        )
        error_console.print("[dim]export PERPLEXITY_API_KEY='your-api-key-here'[/dim]")
        error_console.print(
            "\n[blue]Get your API key at: https://www.perplexity.ai/settings/api[/blue]"
        )
        raise typer.Exit(code=1)

    client = openai.OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    prompt = f"Your goal is to provide rulesets for AI coding assistants in a '{lang}' project using '{tag}'. Focus the best rulesets on Github for similar projects and return only the best industry standard best practices in the correct format."

    response = client.chat.completions.create(
        model="sonar-pro",
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant that provides concise, expert-level summaries for software development best practices.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def get_openai_rules(
    lang: str,
    tool: str,
    tag: str,
    primary_model: str,
    research_summary: Optional[str] = None,
) -> str:
    """Generates coding assistant rules using OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        error_console.print("\n[bold red]✗ Missing OpenAI API Key[/bold red]")
        error_console.print(
            "[yellow]To generate rules, you need to set your OpenAI API key:[/yellow]"
        )
        error_console.print("[dim]export OPENAI_API_KEY='your-api-key-here'[/dim]")
        error_console.print(
            "\n[blue]Get your API key at: https://platform.openai.com/api-keys[/blue]"
        )
        raise typer.Exit(code=1)

    client = openai.OpenAI(api_key=api_key)

    today = datetime.now().strftime("%Y-%m-%d")

    prompt_sections = [
        f"Generate a set of rules for the AI coding assistant '{tool}' for a '{lang}' project.",
        f"Use best practices and industry standard rulesets with clarity and proper formatting.",
        f"Keep the rules concise and to the point.",
        f"The rules should focus on the topic: '{tag}'.",
        f"The current date is {today}. The rules should be modern and reflect the latest standards.",
        "The output should be a markdown file, containing only the rules, without any additional explanations or preamble.",
        "Start the file with a title that includes the language and tag.",
    ]

    if research_summary:
        prompt_sections.append("\n--- RESEARCH SUMMARY ---\n")
        prompt_sections.append(research_summary)
        prompt_sections.append("\n--- END RESEARCH SUMMARY ---\n")
        prompt_sections.append(
            "Based on the research summary above, generate the rules file."
        )

    prompt = "\n".join(prompt_sections)

    response = client.chat.completions.create(
        model=primary_model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in generating rules for AI coding assistants. Your output must be only the raw markdown content for the rules file.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def validate_with_claude(content: str, review_model: str) -> str:
    """Validates and refines the generated rules using Anthropic's Claude."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        error_console.print("\n[bold red]✗ Missing Anthropic API Key[/bold red]")
        error_console.print(
            "[yellow]To use the --review flag with Claude, you need to set your Anthropic API key:[/yellow]"
        )
        error_console.print("[dim]export ANTHROPIC_API_KEY='your-api-key-here'[/dim]")
        error_console.print(
            "\n[blue]Get your API key at: https://console.anthropic.com/account/keys[/blue]"
        )
        raise typer.Exit(code=1)

    today = datetime.now().strftime("%Y-%m-%d")

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=review_model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"Please review and refine the following AI coding assistant rules. Ensure they are clear, concise, and follow best practices and industry standards as of {today}. Return only the refined markdown content, without any preamble.\n\n---\n\n{content}",
            }
        ],
    )
    # Access the text content from the response
    # Type ignore due to complex Anthropic API response types
    return response.content[0].text  # type: ignore


def get_rules_filepath(tool: str, lang: str, tag: str, project_path: str) -> Path:
    """Determines the appropriate file path for the generated rules."""
    project_root = Path(project_path)
    if tool == "claude":
        return project_root / "CLAUDE.md"
    elif tool == "copilot":
        rules_dir = project_root / ".github"
        return rules_dir / f"copilot-{lang}-{tag}.md"

    extension = "mdc" if tool == "cursor" else "md"
    folder = f".{tool}"

    rules_dir = project_root / folder / "rules"
    return rules_dir / f"{tag}.{extension}"


def write_rules_file(filepath: Path, content: str, dry_run: bool, yes: bool, tool: str):
    """Writes the rules content to the specified file path."""
    if dry_run:
        console.print(
            f"[bold yellow]--DRY RUN--[/bold yellow] Would write {len(content)} chars to {filepath}"
        )
        console.print("--BEGIN PREVIEW--")
        console.print(content)
        console.print("--END PREVIEW--")
        return

    filepath.parent.mkdir(parents=True, exist_ok=True)

    file_existed = filepath.exists()
    write_mode = "a" if tool == "claude" else "w"

    if write_mode == "w" and file_existed and not yes:
        try:
            overwrite = typer.confirm(f"File {filepath} already exists. Overwrite?")
            if not overwrite:
                console.print("[yellow]Skipping file.[/yellow]")
                return
        except Exception:
            # This helps with test environment where stdin/stdout might be redirected
            console.print("[yellow]Skipping file.[/yellow]")
            return

    with open(filepath, write_mode) as f:
        if write_mode == "a" and file_existed:
            f.write("\n\n---\n\n")
        f.write(content)

    action = "appended to" if write_mode == "a" and file_existed else "written to"
    console.print(f"[bold green]✓ Rules {action} {filepath}[/bold green]")


@app.command()
def init():
    """Initialize a new .rules4rc configuration file

    Creates a default configuration file in the current directory with:
    [green]•[/green] Default language and tool settings
    [green]•[/green] Customizable tags for rule generation  
    [green]•[/green] Environment variable references for API keys

    [yellow]Must be run inside a virtual environment for safety.[/yellow]
    """
    if not in_virtualenv():
        console.print(
            "[bold red]✗ This command must be run in a virtual environment.[/bold red]"
        )
        raise typer.Exit(code=1)

    if get_config_path().exists():
        console.print("[yellow]✓ .rules4rc already exists.[/yellow]")
        return

    create_default_config()
    console.print("[bold green]✓ Created default .rules4rc.[/bold green]")


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
    if not in_virtualenv():
        console.print(
            "[bold red]✗ This command must be run in a virtual environment.[/bold red]"
        )
        raise typer.Exit(code=1)

    # Check if we have required parameters or need to load config
    if lang and tags:
        # All required parameters provided, no config needed
        current_lang = lang
        current_tags_str = tags
        current_tags = [tag.strip() for tag in current_tags_str.split(",")]
    else:
        # Need to load config for missing parameters
        try:
            config = get_config()
            # Use provided lang and tags, or fallback to config
            current_lang = (
                lang if lang else config.get("settings", "language", fallback="python")
            )
            current_tags_str = (
                tags if tags else config.get("settings", "tags", fallback="security")
            )
            current_tags = [tag.strip() for tag in current_tags_str.split(",")]
        except FileNotFoundError:
            console.print(
                "[bold red]✗ No .rules4rc file found. Please run 'rules4 init' first,[/bold red]"
            )
            console.print(
                "[yellow]or provide both --lang and --tags parameters.[/yellow]"
            )
            raise typer.Exit(code=1)

    has_errors = False
    for tag_item in current_tags:
        try:
            research_summary = None
            if research:
                with Spinner(f"Researching '{tag_item}' with Perplexity"):
                    research_summary = research_with_perplexity(current_lang, tag_item)

            with Spinner(f"Generating rules for '{tag_item}'"):
                rules_content = get_openai_rules(
                    current_lang,
                    tool,
                    tag_item,
                    primary_model,
                    research_summary=research_summary,
                )
                if review_model:
                    rules_content = validate_with_claude(rules_content, review_model)

            rules_content = clean_rules_content(rules_content)
            filepath = get_rules_filepath(tool, current_lang, tag_item, project_path)
            write_rules_file(filepath, rules_content, dry_run, yes, tool)

        except (ValueError, RuntimeError, openai.OpenAIError, typer.Abort) as e:
            if isinstance(e, typer.Abort):
                # Handle user abort (like when they say 'n' to overwrite)
                error_console.print("\n[yellow]Operation aborted by user.[/yellow]")
                return
            error_console.print(
                f"\n[bold red]✗ ERROR processing tag '{tag_item}': {e}[/bold red]"
            )
            has_errors = True

    if has_errors:
        raise typer.Exit(1)


def _create_command(tool_name: str):
    def _command(
        primary: str = typer.Option(
            "gpt-4-turbo", "--primary", help="Primary model for rule generation."
        ),
        review: Optional[str] = typer.Option(
            None, "--review", help="Review model for refinement."
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
    ):
        """Generate rules for a specific tool."""
        run_generation_pipeline(
            tool=tool_name,
            primary_model=primary,
            research=research,
            review_model=review,
            dry_run=dry_run,
            yes=yes,
            project_path=project_path,
            lang=lang,
            tags=tags,
        )

    return _command


for tool in ["cursor", "cline", "roo", "copilot", "claude"]:
    app.command(name=tool, help=f"Generate rules for {tool.capitalize()}.")(
        _create_command(tool)
    )


@app.command()
def generate(
    primary: str = typer.Option(
        "gpt-4-turbo", "--primary", help="Primary model for rule generation."
    ),
    review: Optional[str] = typer.Option(
        None, "--review", help="Review model for refinement."
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
):
    """Generate rules for all tools configured in .rules4rc

    Processes all tools specified in your configuration file and generates
    appropriate rules for each one. This is the most efficient way to set up
    rules for multiple AI coding assistants at once.

    [bold blue]Features:[/bold blue]
    [green]•[/green] Batch processing for multiple tools
    [green]•[/green] Respects .rules4rc configuration settings
    [green]•[/green] Supports research-backed generation
    [green]•[/green] Optional Claude review for quality assurance
    """
    if not in_virtualenv():
        console.print(
            "[bold red]✗ This command must be run in a virtual environment.[/bold red]"
        )
        raise typer.Exit(code=1)

    try:
        config = get_config()
        tools_str = config.get("settings", "tools", fallback="roo")
        tools = [tool.strip() for tool in tools_str.split(",")]

        console.print(
            f"[bold blue]Generating rules for {len(tools)} tool(s): {', '.join(tools)}[/bold blue]"
        )

        for tool in tools:
            if tool not in ["cursor", "cline", "roo", "copilot", "claude"]:
                console.print(
                    f"[yellow]Warning: Unsupported tool '{tool}' in config. Skipping.[/yellow]"
                )
                continue

            console.print(f"[bold]\nProcessing {tool.upper()}[/bold]")
            run_generation_pipeline(
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
        console.print(
            "[bold red]✗ No .rules4rc file found. Please run 'rules4 init' first.[/bold red]"
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
