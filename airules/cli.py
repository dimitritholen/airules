import requests
import sys
import os
from .venv_check import in_virtualenv

def get_perplexity_rules(lang, tool, tags):
    """
    Query Perplexity API for best practices for the given language, tool, and tags.
    Returns a string with the recommended rules/content.
    """
    # Placeholder: Replace with actual Perplexity API call and parsing
    query = f"best industry standard rules for a {lang} project with {', '.join(tags)} rules for {tool}"
    # Example: Use requests to call Perplexity API (API key/config required)
    # resp = requests.post('https://api.perplexity.ai/v1/ask', json={...})
    # return resp.json()['result']
    return f"[MOCK] {query} (Perplexity integration needed)"

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
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"[airules] Wrote {filepath}")

def main():
    if not in_virtualenv():
        print("[airules] ERROR: Please activate a virtual environment before running airules.")
        sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser(description="Configure AI rules files for your project using latest best practices via Perplexity research.")
    parser.add_argument('--lang', type=str, required=True, help='Programming language (e.g., python, javascript)')
    parser.add_argument('--tool', type=str, required=True, help='Which rules file/tool to configure (e.g., cursor, roo, claude)')
    parser.add_argument('--tags', type=str, required=True, help='Comma-separated list of frameworks/libraries (e.g., langgraph,pytest)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing files')
    parser.add_argument('--yes', '-y', action='store_true', help='Overwrite files without prompting')
    parser.add_argument('--project-path', type=str, default='.', help='Target project directory (default: current)')
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    rules_content = get_perplexity_rules(args.lang, args.tool, tags)

    tool_to_file = {
        'cursor': '.cursor/rules',
        'roo': '.roo/rules',
        'claude': 'CLAUDE.md',
    }
    rules_file = tool_to_file.get(args.tool.lower(), f"{args.tool}.rules")
    rules_path = os.path.join(args.project_path, rules_file)
    rules_dir = os.path.dirname(rules_path)
    if rules_dir and not os.path.exists(rules_dir):
        os.makedirs(rules_dir, exist_ok=True)
    write_rules_file(rules_path, rules_content, args.dry_run, args.yes)

if __name__ == "__main__":
    main()
