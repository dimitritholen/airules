# rules4

A universal CLI utility to configure AI rules files (e.g., .roo/rules, CLAUDE.md, .cursor/rules) for any project, based on the latest industry best practices via live Perplexity research.

![rules4.png](rules4.png)

## Features

- **🔍 Automatic Project Analysis**: `rules4 auto` intelligently detects your project's language, frameworks, and generates appropriate tags
- **🎯 Smart Detection**: Supports 50+ programming languages and 50+ frameworks (React, Django, FastAPI, etc.)
- **⚡ Zero Configuration**: Works out-of-the-box without manual setup - just run `rules4 auto`
- **🛠️ Manual Control**: Override auto-detection with `--lang` and `--tags` options when needed
- **🤖 Multi-Tool Support**: Configures rules for Cursor, Roo, Claude, Copilot, and Cline
- **🔄 Flexible Model Selection**: Use OpenAI or Anthropic models for both generation and review
- **🔀 Mix and Match**: e.g., Claude for generation, GPT-4 for review
- **🔬 Live Research**: Uses Perplexity API for up-to-date best practices
- **📋 Model Discovery**: Built-in `--list-models` command to see all available models
- **👀 Preview Mode**: Dry-run mode to preview changes before writing
- **⚠️ Safe Defaults**: Prompts before overwriting existing files
- **📦 Easy Install**: Simple one-command install (packaged for PyPI)
- **🔮 Future Ready**: Designed for MCP integration

## Program Flow

The following diagram shows the core execution flow:

```mermaid
flowchart TD
    A[CLI Command] --> B[Parse language and tags]
    B --> C[Loop through each tag]
    C --> D{Research enabled?}
    D -->|Yes| E[Call Perplexity API]
    D -->|No| F[Skip research]
    E --> G[Primary model generates rules]
    F --> G
    G --> H{Review model specified?}
    H -->|Yes| I[Review model refines rules]
    H -->|No| J[Use original rules]
    I --> K[Save to tool-specific folder]
    J --> K
    K --> L{More tags?}
    L -->|Yes| C
    L -->|No| M[Complete]
```

## Installation

```bash
pip install rules4
```

## Quick Start

### 🚀 The Smart Way (Recommended)

Let rules4 automatically analyze your project and generate intelligent rules:

```bash
# Automatically detect language, frameworks, and generate rules for all tools
rules4 auto

# Auto-detect with research for cutting-edge best practices
rules4 auto --research

# Auto-detect for a specific tool
rules4 auto cursor

# Auto-detect with model selection
rules4 auto --primary gpt-4-turbo --review claude-3-5-sonnet-20241022
```

### 🎯 The Manual Way

Or specify everything manually for precise control:

```bash
# For Cursor
rules4 cursor --lang python --tags "testing,security"

# For Claude with research
rules4 claude --research --lang javascript --tags "react,typescript"

# For all configured tools (requires initialization)
rules4 generate
```

### ⚙️ Configuration (Optional)

Initialize a configuration file for your project to set defaults:

```bash
rules4 init
```

This creates a `.rules4rc` file with default settings for batch operations.

## API Keys and Environment Variables

`rules4` interacts with various AI models and research services. To use these features, you need to set up the corresponding API keys as environment variables:

- **OPENAI_API_KEY**: Required for generating rules using OpenAI models (e.g., `gpt-4-turbo`, `gpt-4o`).
- **ANTHROPIC_API_KEY**: Required for generating rules using Anthropic models (e.g., `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`).
- **PERPLEXITY_API_KEY**: Required if you use the `--research` flag to perform research with Perplexity AI.

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

You can specify a primary model, a review model, and enable research. Both `--primary` and `--review` flags support OpenAI and Anthropic models:

```bash
# Use Claude as primary, GPT-4 as reviewer
rules4 copilot --primary claude-3-5-sonnet-20241022 --review gpt-4o --research --lang javascript --tags "react,typescript"

# Use GPT-4 for both generation and review
rules4 cursor --primary gpt-4-turbo --review gpt-4o --lang python --tags "async,testing"

# Use Claude for both generation and review
rules4 claude --primary claude-3-opus-20240229 --review claude-3-5-sonnet-20241022 --lang go --tags "concurrency"
```

These commands demonstrate the flexibility:

- You can use any combination of OpenAI and Anthropic models
- The same model can be used for both primary generation and review
- Research always uses Perplexity's `sonar-pro` model

### 🤖 Automatic Project Analysis (`rules4 auto`)

The auto command is the smartest way to generate rules. It analyzes your project structure and automatically determines the best settings:

#### **What It Detects:**

**Languages (50+):**
- Python, JavaScript, TypeScript, Java, Go, Rust, C#, PHP, Ruby, C++, Swift, Kotlin, Dart, Elixir, Scala, Clojure, Haskell, R, Julia, and more...

**Frameworks & Libraries (50+):**
- **Frontend**: React, Vue, Angular, Svelte, Next.js, Nuxt.js
- **Backend**: Django, Flask, FastAPI, Express, Spring Boot, ASP.NET, Laravel  
- **Mobile**: React Native, Flutter, Ionic, Xamarin
- **Testing**: Jest, pytest, Mocha, Cypress, Selenium
- **Build Tools**: webpack, Vite, Rollup, Parcel, Cargo, Maven, Gradle

**Smart Tags Generated:**
- **Architecture**: microservices, monolith, serverless, api
- **Development**: testing, security, performance, documentation
- **Technologies**: database, web-development, mobile, machine-learning
- **Practices**: ci-cd, devops, containerization, cloud-native

#### **Auto Command Examples:**

```bash
# Basic auto-detection for all configured tools
rules4 auto

# Tool-specific auto-generation  
rules4 auto cursor
rules4 auto claude

# Auto-detection with research and review
rules4 auto --research --review claude-3-5-sonnet-20241022

# Override auto-detected language but keep detected frameworks
rules4 auto --lang typescript

# Override auto-detected tags but keep detected language
rules4 auto --tags "performance,security,testing"

# Combination with all features
rules4 auto cursor --primary gpt-4-turbo --research --dry-run
```

#### **How It Works:**

1. **🔍 Scans** your project directory structure
2. **🎯 Detects** programming languages from file extensions and content
3. **📦 Analyzes** package files (package.json, requirements.txt, etc.)
4. **🛠️ Identifies** frameworks and build tools
5. **🏷️ Generates** intelligent tags based on project characteristics
6. **⚡ Executes** the same high-quality generation pipeline as manual commands

### Generating Rules for All Configured Tools

If you have a `.rules4rc` file configured (created with `rules4 init`), you can generate rules for all specified tools:

```bash
rules4 generate --lang go --tags "code style"
```

This command will:

- Read the list of tools from your `.rules4rc` file.
- Generate rules for each tool, focusing on `code style` for Go projects.

**Note**: The `generate` command requires a `.rules4rc` configuration file. Individual tool commands (like `rules4 cursor`, `rules4 claude`) and the `auto` command work without any configuration.

### Command-Line Options

- `--primary <model_name>`: Specify the primary AI model for rule generation. Supports both OpenAI and Anthropic models (e.g., `gpt-4-turbo`, `gpt-4o`, `claude-3-5-sonnet-20241022`).
- `--review <model_name>`: Specify an AI model for reviewing and refining the generated rules. Also supports both OpenAI and Anthropic models.
- `--research`: Enable research using Perplexity AI before rule generation.
- `--lang <language>`: Specify the programming language for rule generation (e.g., `python`, `javascript`, `go`).
- `--tags <tag1,tag2,...>`: Comma-separated list of tags or topics for rule generation (e.g., `pytest,langgraph`, `react,typescript`, `code style`).
- `--dry-run`: Preview the changes without actually writing any files.
- `--yes`, `-y`: Overwrite existing files without prompting for confirmation.
- `--project-path <path>`: (Optional) Specify the target project directory. Defaults to the current directory.

### Listing Available Models

To see all available models for use with `--primary` and `--review`:

```bash
rules4 list-models
```

This will display models grouped by provider (OpenAI, Anthropic, and Perplexity).

---

This project is in early development. For contributions, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Publishing

For maintainers, this project includes a comprehensive publishing system:

### Prerequisites

```bash
# Install publishing dependencies
pip install build twine

# Set up API tokens
export PYPI_API_TOKEN="your-pypi-token"           # For PyPI
export TEST_PYPI_API_TOKEN="your-test-pypi-token" # For TestPyPI
```

### Publishing Commands

```bash
# Test publish (recommended first)
./publish.sh --test --dry-run    # Preview what would be published to TestPyPI
./publish.sh --test              # Publish to TestPyPI

# Production publish
./publish.sh --dry-run           # Preview what would be published to PyPI
./publish.sh                     # Publish to PyPI

# With version update
./publish.sh --version 1.2.3     # Update version and publish
```

### Make Commands

```bash
make publish-test    # Publish to TestPyPI
make publish         # Publish to PyPI
```

### Publishing Features

The enhanced `publish.sh` script includes:

- ✅ **Pre-flight checks**: Virtual environment, dependencies, API tokens
- ✅ **Quality assurance**: Runs all tests and linting before publishing
- ✅ **Version management**: Automatic version updates in both `pyproject.toml` and CLI
- ✅ **Dual repositories**: Support for both PyPI and TestPyPI
- ✅ **Safety features**: Dry-run mode, build validation, error handling
- ✅ **User experience**: Colored output, progress indicators, helpful messages

## Development

### Setup

```bash
# Clone and setup
git clone https://github.com/dimitritholen/airules.git
cd airules
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Quality Assurance

```bash
make test         # Run tests
make lint         # Run all linting checks
make lint-fix     # Auto-fix formatting issues
make format       # Format code with black
make type-check   # Run mypy type checking
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make test lint` to ensure quality
5. Submit a pull request

## Support

- 📖 [Documentation](https://github.com/dimitritholen/airules)
- 🐛 [Bug Reports](https://github.com/dimitritholen/airules/issues)
- 💡 [Feature Requests](https://github.com/dimitritholen/airules/issues)
