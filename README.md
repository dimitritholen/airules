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

## Usage

```bash
# Basic usage (auto-detects project context if possible)
airules

# Specify language, tool, and tags explicitly
airules --lang python --tool cursor --tags langgraph,langchain,pytest

# Preview changes without writing files
airules --lang python --tool cursor --tags pytest --dry-run
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

---

This project is in early development. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
