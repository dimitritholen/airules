import openai
import anthropic
import sys
import os
from datetime import datetime
from .venv_check import in_virtualenv
import time
import threading

class Spinner:
    def __init__(self, message="Loading..."):
        self.message = message
        self.stop_running = threading.Event()
        self.spinner_thread = threading.Thread(target=self._spin)

    def _spin(self):
        spinner_chars = "|/-\\"
        i = 0
        while not self.stop_running.is_set():
            char = spinner_chars[i % len(spinner_chars)]
            sys.stdout.write(f'\r{self.message} {char}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def __enter__(self):
        self.spinner_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_running.set()
        self.spinner_thread.join()
        sys.stdout.write(f'\r{" " * (len(self.message) + 2)}\r')
        sys.stdout.flush()

def clean_rules_content(content: str) -> str:
    """
    Removes markdown code fences from the beginning and end of the content.
    Handles ``` and ```<lang> formats.
    """
    content = content.strip()
    if content.startswith("```") and content.endswith("```"):
        lines = content.split('\n')
        cleaned_content = '\n'.join(lines[1:-1])
        return cleaned_content.strip()
    return content

def get_openai_rules(lang, tool, tags):
    """
    Query OpenAI API for best practices for the given language, tool, and tags.
    Returns a string with the recommended rules/content.
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    today_str = datetime.now().strftime("%B %d, %Y")
    framework = tags[0] if tags else 'none'
    other_tags = tags[1:]

    prompt = (
        f"Generate a set of technical, best-practice guidelines for an AI coding assistant working on a '{lang}' project. "
        f"The project's main framework is '{framework}'.\n"
    )
    if other_tags:
        prompt += f"It also uses these technologies: {', '.join(other_tags)}.\n"

    prompt += (
        f"\nThe guidelines MUST focus exclusively on code style, patterns, library usage, and conventions specific to '{lang}' and '{framework}'. "
        f"The output should be a markdown file ready for the '{tool}' tool.\n"
        f"IMPORTANT: Do NOT include any ethical guidelines, safety warnings, or self-referential statements about being an AI. "
        f"Provide only the raw, technical rules content, valid as of {today_str}."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
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

def validate_with_claude(rules):
    """
    Use Anthropic's Claude to validate and possibly refine the rules from OpenAI.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return rules # Skip validation if key is not set

    client = anthropic.Anthropic(api_key=api_key)

    prompt = (
        f"You are a senior software engineer. Review the following technical guidelines for an AI coding assistant. "
        f"Your task is to refine them for clarity, conciseness, and technical accuracy. "
        f"Do NOT add any of your own ethical or safety guidelines. Only improve the existing text. "
        f"Return only the refined rules, without any extra commentary.\n\n---\n\n{rules}"
    )

    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"[airules] WARNING: Could not validate with Claude: {e}", file=sys.stderr)
        return rules # Return original rules if validation fails

def get_rules_filepath(tool, lang, tags, project_path):
    """
    Determines the correct file path for the rules file based on the tool, language, and framework.
    """
    framework = tags[0] if tags else 'general'
    filename_base = f"{lang.lower()}_{framework.lower()}"

    if tool == 'cursor':
        dir_path = os.path.join(project_path, '.cursor')
        filename = f"{filename_base}.mdc"
    elif tool == 'roo':
        dir_path = os.path.join(project_path, '.roo')
        filename = f"{filename_base}.md"
    elif tool == 'claude':
        # Claude seems to be a special case with a fixed name
        return os.path.join(project_path, 'CLAUDE.md')
    else:
        # Default for other tools
        dir_path = os.path.join(project_path, tool)
        filename = f"{filename_base}.md"

    return os.path.join(dir_path, filename)

def prompt_overwrite(filepath):
    resp = input(f"[airules] File '{filepath}' exists. Overwrite? [y/N]: ").strip().lower()
    return resp == 'y'

def write_rules_file(filepath, content, dry_run, yes):
    if os.path.exists(filepath):
        if not yes:
            if not prompt_overwrite(filepath):
                print(f"[airules] Skipped {filepath}")
                return
    if dry_run:
        print(f"[airules] Would write to {filepath} (dry-run):\n{content}\n---")
    else:
        dir_path = os.path.dirname(filepath)
        os.makedirs(dir_path, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"[airules] Wrote {filepath}")

def main():
    if not in_virtualenv():
        print("[airules] ERROR: Please activate a virtual environment before running airules.")
        sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser(description="Configure AI rules files for your project using latest best practices.")
    parser.add_argument('--lang', type=str, required=True, help='Programming language (e.g., python, javascript)')
    parser.add_argument('--tool', type=str, required=True, help='Which rules file/tool to configure (e.g., cursor, roo, claude)')
    parser.add_argument('--tags', type=str, required=True, help='Comma-separated list of frameworks/libraries (e.g., fastapi,pytest)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing files')
    parser.add_argument('--yes', '-y', action='store_true', help='Overwrite files without prompting')
    parser.add_argument('--project-path', type=str, default='.', help='Target project directory (default: current)')
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    try:
        with Spinner(f"[airules] Querying OpenAI for '{args.lang}/{','.join(tags)}' rules..."):
            rules_content = get_openai_rules(args.lang, args.tool, tags)
        print(f"[airules] OpenAI query complete.")

        if os.environ.get("ANTHROPIC_API_KEY"):
            with Spinner("[airules] Validating rules with Anthropic Claude..."):
                rules_content = validate_with_claude(rules_content)
            print("[airules] Claude validation complete.")

    except (ValueError, RuntimeError) as e:
        print(f"\n[airules] ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    rules_content = clean_rules_content(rules_content)
    filepath = get_rules_filepath(args.tool, args.lang, tags, args.project_path)
    write_rules_file(filepath, rules_content, args.dry_run, args.yes)

if __name__ == '__main__':
    main()
