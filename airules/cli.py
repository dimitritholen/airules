import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(
        description="Configure AI rules files for your project using latest best practices via Perplexity research."
    )
    parser.add_argument('--lang', type=str, help='Programming language (e.g., python, javascript)')
    parser.add_argument('--tool', type=str, help='Which rules file/tool to configure (e.g., cursor, roo, claude)')
    parser.add_argument('--tags', type=str, help='Comma-separated list of frameworks/libraries (e.g., langgraph,pytest)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing files')
    parser.add_argument('--yes', '-y', action='store_true', help='Overwrite files without prompting')
    parser.add_argument('--project-path', type=str, default='.', help='Target project directory (default: current)')
    return parser.parse_args()

def main():
    args = parse_args()
    # Placeholder: actual logic will be implemented later
    print(f"[airules] Would configure rules for: lang={args.lang}, tool={args.tool}, tags={args.tags}, dry_run={args.dry_run}, yes={args.yes}, project_path={args.project_path}")
    # TODO: integrate Perplexity API, preview changes, prompt before overwrite, write rules files

if __name__ == "__main__":
    main()
