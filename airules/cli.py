import os
import sys
import threading
import time
from datetime import datetime
from typing import List, Optional

import anthropic
import openai
import typer
from rich.console import Console

from .config import CONFIG_PATH, create_default_config, get_config
from .tui import ConfigTUI
from .venv_check import in_virtualenv

app = typer.Typer(help="A CLI to generate AI coding assistant rules for your project.")
console = Console()


class Spinner:
    def __init__(self, message="Loading..."):
        self.message = message
        self.stop_running = threading.Event()
        self.spinner_thread = threading.Thread(target=self._spin)
        self.GREEN = '\033[92m'
        self.ENDC = '\033[0m'

    def _spin(self):
        spinner_chars = "✨💫✨"
        i = 0
        while not self.stop_running.is_set():
            char = spinner_chars[i % len(spinner_chars)]
            console.print(f'\r{self.GREEN}{self.message} {char}{self.ENDC}', end="")
            time.sleep(0.15)
            i += 1

    def __enter__(self):
        self.spinner_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_running.set()
        self.spinner_thread.join()
        console.print(f'\r{" " * (len(self.message) + 5)}\r', end="")


def clean_rules_content(content: str) -> str:
    content = content.strip()
    if content.startswith("```") and content.endswith("```"):
        lines = content.split('\n')
        cleaned_content = '\n'.join(lines[1:-1])
        return cleaned_content.strip()
    return content

def research_with_perplexity(lang: str, tag: str) -> str:
    """Performs research using Perplexity API and returns the findings."""
    client = openai.OpenAI(
        api_key=os.environ.get("PERPLEXITY_API_KEY"),
        base_url="https://api.perplexity.ai"
    )
    if not client.api_key:
        raise ValueError("PERPLEXITY_API_KEY environment variable not set for --research flag.")

    prompt = f"Provide a detailed, up-to-date summary of best practices for '{tag}' in a '{lang}' project. Focus on technical guidelines, code standards, and common pitfalls."
    try:
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": "You are a senior software engineer and research assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Failed to query Perplexity API: {e}") from e

def get_openai_rules(lang, tool, tag, model, research_summary: Optional[str] = None):
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    today_str = datetime.now().strftime("%B %d, %Y")
    
    research_context = ""
    if research_summary:
        research_context = f"\n\nUse the following research summary as context:\n---\n{research_summary}\n---"

    prompt = (
        f"Generate a set of technical, best-practice guidelines for an AI coding assistant. "
        f"The guidelines are for a '{lang}' project, focusing specifically on the topic of '{tag}'.\n"
        f"The output should be a markdown file ready for the '{tool}' tool.{research_context}\n"
        f"IMPORTANT: Do NOT include any ethical guidelines, safety warnings, or self-referential statements about being an AI. "
        f"Provide only the raw, technical rules content, valid as of {today_str}."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in software development best practices and AI-assisted coding."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Failed to query OpenAI API: {e}") from e

def validate_with_claude(rules, model):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return rules

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"You are a senior software engineer. Review the following technical guidelines for an AI coding assistant. "
        f"Your task is to refine them for clarity, conciseness, and technical accuracy. "
        f"Do NOT add any of your own ethical or safety guidelines. Only improve the existing text. "
        f"Return only the refined rules, without any extra commentary.\n\n---\n\n{rules}"
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        console.print(f"\n[yellow]WARNING: Could not validate with Claude: {e}[/yellow]", file=sys.stderr)
        return rules

def get_rules_filepath(tool, lang, tag, project_path):
    safe_tag = tag.lower().replace(' ', '_').replace('-', '_')
    filename_base = f"{lang.lower()}_{safe_tag}"

    if tool == 'cursor':
        dir_path = os.path.join(project_path, '.cursor')
        filename = f"{filename_base}.mdc"
    else:
        dir_path = os.path.join(project_path, f".{tool}")
        filename = f"{filename_base}.md"

    return os.path.join(dir_path, filename)

def write_rules_file(filepath, content, dry_run, yes):
    if os.path.exists(filepath) and not dry_run and not yes:
        if not typer.confirm(f"[airules] File '{filepath}' exists. Overwrite?"):
            console.print(f"[yellow]Skipped {filepath}[/yellow]")
            return
    if dry_run:
        console.print(f"--- DRY RUN: {filepath} ---")
        console.print(content)
        console.print("--- END DRY RUN ---")
    else:
        dir_path = os.path.dirname(filepath)
        os.makedirs(dir_path, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        console.print(f"[bold green]✓ Wrote:[/] {filepath}")


@app.command()
def init():
    """
    Initializes airules by creating a default .airulesrc config file.
    """
    if not in_virtualenv():
        console.print("[bold red]ERROR: Please activate a virtual environment before running airules.[/bold red]")
        raise typer.Exit(code=1)

    created, path = create_default_config()
    if created:
        console.print(f"[bold green]✓ Config file created at:[/] {path}")
    else:
        console.print(f"[yellow]Config file already exists at:[/] {path}")

def run_generation_pipeline(
    tool: str,
    primary_model: str,
    research: bool,
    review_model: Optional[str],
    dry_run: bool,
    yes: bool,
    project_path: str
):
    if not CONFIG_PATH.exists():
        console.print("[bold red]ERROR: No .airulesrc file found. Please run 'airules init' first.[/bold red]")
        raise typer.Exit(code=1)

    config = get_config()
    lang = config.get('settings', 'language')
    tags_str = config.get('topics', 'tags', fallback='')
    tags = [t.strip() for t in tags_str.split(',') if t.strip()]

    console.print(f"[bold]Generating rules for [cyan]{lang}[/cyan] using tool [cyan]{tool}[/cyan]...[/bold]")

    for tag in tags:
        try:
            research_summary = None
            if research:
                with Spinner(f"Researching '{tag}' with Perplexity"):
                    research_summary = research_with_perplexity(lang, tag)

            with Spinner(f"Generating rules for '{tag}'"):
                rules_content = get_openai_rules(lang, tool, tag, primary_model, research_summary=research_summary)
                if review_model and os.environ.get("ANTHROPIC_API_KEY"):
                    rules_content = validate_with_claude(rules_content, review_model)

            rules_content = clean_rules_content(rules_content)
            filepath = get_rules_filepath(tool, lang, tag, project_path)
            write_rules_file(filepath, rules_content, dry_run, yes)

        except (ValueError, RuntimeError) as e:
            console.print(f"\n[bold red]✗ ERROR processing tag '{tag}': {e}[/bold red]", file=sys.stderr)
            continue


def _create_command(tool_name: str):
    def _command(
        primary: str = typer.Option("gpt-4-turbo", "--primary", help="Primary model for rule generation."),
        review: Optional[str] = typer.Option(None, "--review", help="Review model for refinement."),
        research: bool = typer.Option(False, "--research", help="Perform research with Perplexity first."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without writing files."),
        yes: bool = typer.Option(False, "-y", "--yes", help="Overwrite files without prompting."),
        project_path: str = typer.Option(".", help="Target project directory.")
    ):
        """Generate rules for a specific tool."""
        run_generation_pipeline(
            tool=tool_name,
            primary_model=primary,
            research=research,
            review_model=review,
            dry_run=dry_run,
            yes=yes,
            project_path=project_path
        )
    return _command

for tool in ["cursor", "roo", "copilot", "claude"]:
    app.command(name=tool, help=f"Generate rules for {tool.capitalize()}.")(_create_command(tool))

@app.command()
def config():
    """Open an interactive TUI to configure .airulesrc."""
    tui = ConfigTUI()
    tui.run()


if __name__ == "__main__":
    app()
