# airules

A universal CLI utility to configure AI rules files (e.g., .roo/rules, CLAUDE.md, .cursor/rules) for any project, based on the latest industry best practices via live Perplexity research.

## Features
- Supports any language or framework via `--lang` and `--tags` options
- Configures rules for tools like Cursor, Roo, Claude, and more
- Uses live Perplexity API for up-to-date best practices
- Dry-run mode to preview changes
- Prompts before overwriting existing files
- Simple one-command install (packaged for PyPI)
- Designed for future MCP integration

## Quickstart

```bash
# Create and activate a virtual environment (required)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the CLI (auto-detects project context if possible)
python -m airules.cli --lang python --tool cursor --tags langgraph,langchain,pytest

# Run tests
make test
```

## Options
- `--lang <language>`: Programming language (e.g., python, javascript)
- `--tool <tool>`: Which rules file/tool to configure (e.g., cursor, roo, claude)
- `--tags <tag1,tag2,...>`: Comma-separated list of frameworks/libraries
- `--dry-run`: Show what would be changed without writing files
- `--yes`, `-y`: Overwrite files without prompting
- `--project-path <path>`: (Optional) Target project directory

## Development
- Code files are kept short and simple
- Tests and >85% coverage are required
- All lint and security issues must be fixed
- ALWAYS use a virtual environment for all development and usage

---

This project is in early development. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
