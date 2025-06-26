# rules4

A universal CLI utility to configure AI rules files (e.g., .roo/rules, CLAUDE.md, .cursor/rules) for any project, based on the latest industry best practices via live Perplexity research.

## Features
- Supports any language or framework via `--lang` and `--tags` options
- Configures rules for tools like Cursor, Roo, Claude, and more
- Uses live Perplexity API for up-to-date best practices
- Dry-run mode to preview changes
- Prompts before overwriting existing files
- Simple one-command install (packaged for PyPI)
- Designed for future MCP integration

## Installation

```bash
pip install rules4
```

## API Keys and Environment Variables

`rules4` interacts with various AI models and research services. To use these features, you need to set up the corresponding API keys as environment variables:

-   **OPENAI_API_KEY**: Required for generating rules using OpenAI models (e.g., `gpt-4-turbo`).
-   **ANTHROPIC_API_KEY**: Required if you use the `--review` flag with an Anthropic model (e.g., `claude-4-sonnet`).
-   **PERPLEXITY_API_KEY**: Required if you use the `--research` flag to perform research with Perplexity AI.

Example (add to your shell profile, e.g., `~/.bashrc` or `~/.zshrc`):

```bash
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export PERPLEXITY_API_KEY="your_perplexity_api_key"
```

## Usage

### Basic Rule Generation

To generate rules for a specific tool (e.g., `copilot`) for a given language and tags:

```bash
rules4 copilot --lang python --tags "pytest,langgraph"
```

This command will:
- Use `gpt-4-turbo` as the primary model (default).
- Generate rules for Python projects, focusing on `pytest` and `langgraph`.
- Save the rules to `.github/copilot-python-pytest,langgraph.md` (or similar, depending on the tool).

### Advanced Usage

You can specify a primary model, a review model, and enable research:

```bash
rules4 copilot --primary gpt4.1 --review claude-4-sonnet --research --lang javascript --tags "react,typescript"
```

This command will:
- Use `gpt4.1` as the primary model for rule generation.
- Perform research using Perplexity AI before generating rules.
- Have `claude-4-sonnet` review and refine the generated rules.
- Generate rules for JavaScript projects, focusing on `react` and `typescript`.

### Generating Rules for All Configured Tools

If you have a `.rules4rc` file configured, you can generate rules for all specified tools:

```bash
rules4 generate --lang go --tags "code style"
```

This command will:
- Read the list of tools from your `.rules4rc` file.
- Generate rules for each tool, focusing on `code style` for Go projects.

### Command-Line Options

- `--primary <model_name>`: Specify the primary AI model for rule generation (e.g., `gpt-4-turbo`, `gpt4.1`).
- `--review <model_name>`: Specify an AI model for reviewing and refining the generated rules (e.g., `claude-4-sonnet`).
- `--research`: Enable research using Perplexity AI before rule generation.
- `--lang <language>`: Specify the programming language for rule generation (e.g., `python`, `javascript`, `go`).
- `--tags <tag1,tag2,...>`: Comma-separated list of tags or topics for rule generation (e.g., `pytest,langgraph`, `react,typescript`, `code style`).
- `--dry-run`: Preview the changes without actually writing any files.
- `--yes`, `-y`: Overwrite existing files without prompting for confirmation.
- `--project-path <path>`: (Optional) Specify the target project directory. Defaults to the current directory.

---

This project is in early development. For contributions, see [CONTRIBUTING.md](CONTRIBUTING.md).

