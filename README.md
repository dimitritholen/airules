# rules4

A universal CLI utility to configure AI rules files (e.g., .roo/rules, CLAUDE.md, .cursor/rules) for any project, based on the latest industry best practices via live Perplexity research.

## Features

- Supports any language or framework via `--lang` and `--tags` options
- Configures rules for tools like Cursor, Roo, Claude, and more
- Flexible model selection: Use OpenAI or Anthropic models for both generation and review
- Mix and match models: e.g., Claude for generation, GPT-4 for review
- Uses live Perplexity API for up-to-date best practices
- Built-in `--list-models` command to see all available models
- Dry-run mode to preview changes
- Prompts before overwriting existing files
- Simple one-command install (packaged for PyPI)
- Designed for future MCP integration

## Program Flow

The following diagram shows the complete execution flow of the rules4 CLI with all parameters and decision points:

```mermaid
flowchart TD
    A[CLI Entry Point: rules4] --> B{Command Type?}
    
    %% Main command branches
    B --> C[init]
    B --> D[list-models]
    B --> E[Tool Commands: cursor/cline/roo/copilot/claude]
    B --> F[generate]
    B --> G[--version/-v]
    B --> H[No Command: Show Help]
    
    %% Version and Help
    G --> G1[Display Version & Exit]
    H --> H1[Display Main Help & Exit]
    
    %% Init Command Flow
    C --> C1[require_virtualenv]
    C1 --> C2{Virtual Env Active?}
    C2 -->|No| C3[Raise VirtualEnvironmentError & Exit]
    C2 -->|Yes| C4{.rules4rc exists?}
    C4 -->|Yes| C5[Print Warning: Already Exists]
    C4 -->|No| C6[create_default_config]
    C6 --> C7[Write .rules4rc with defaults:<br/>language=python<br/>tags=security,best-practices<br/>tools=cursor,roo,claude,copilot,cline]
    C7 --> C8[Print Success Message]
    
    %% List Models Command Flow
    D --> D1[require_virtualenv]
    D1 --> D2{Virtual Env Active?}
    D2 -->|No| D3[Raise VirtualEnvironmentError & Exit]
    D2 -->|Yes| D4[Display Available Models:<br/>OpenAI, Anthropic, Perplexity]
    
    %% Tool Command Flow
    E --> E1[ToolCommandHandler.execute]
    E1 --> E2[Parse Parameters:<br/>--primary, --review, --research<br/>--lang, --tags, --dry-run<br/>--yes, --project-path]
    E2 --> E3[GenerationPipelineService.run_pipeline]
    
    %% Generate Command Flow
    F --> F1[GenerateCommandHandler.execute]
    F1 --> F2[require_virtualenv]
    F2 --> F3{Virtual Env Active?}
    F3 -->|No| F4[Raise VirtualEnvironmentError & Exit]
    F3 -->|Yes| F5[get_config]
    F5 --> F6{.rules4rc exists?}
    F6 -->|No| F7[Raise FileNotFoundError:<br/>Run 'rules4 init' first]
    F6 -->|Yes| F8[Parse tools from config]
    F8 --> F9[For each tool in config:<br/>cursor, cline, roo, copilot, claude]
    F9 --> F10[GenerationPipelineService.run_pipeline for each tool]
    
    %% Generation Pipeline Service (Core Flow)
    E3 --> GP1[Generation Pipeline Service]
    F10 --> GP1
    GP1 --> GP2[_validate_environment:<br/>Check virtual environment]
    GP2 --> GP3{Virtual Env Active?}
    GP3 -->|No| GP4[Raise ConfigurationError & Exit]
    GP3 -->|Yes| GP5[_get_configuration:<br/>Resolve lang & tags]
    
    %% Configuration Resolution
    GP5 --> GP6{Lang provided?}
    GP6 -->|No| GP7{Config file exists?}
    GP7 -->|Yes| GP8[Get lang from config<br/>default: python]
    GP7 -->|No| GP9[Require --lang parameter]
    GP6 -->|Yes| GP10[Use provided lang]
    GP8 --> GP10
    GP9 --> GP11[Raise ConfigurationError & Exit]
    
    GP10 --> GP12{Tags provided?}
    GP12 -->|No| GP13{Config file exists?}
    GP13 -->|Yes| GP14[Get tags from config<br/>default: general]
    GP13 -->|No| GP15[Use default: general]
    GP12 -->|Yes| GP16[Parse comma-separated tags]
    GP14 --> GP16
    GP15 --> GP16
    
    %% Process Each Tag
    GP16 --> GP17[For each tag: _process_single_tag]
    GP17 --> GP18{Research enabled?}
    
    %% Research Phase
    GP18 -->|Yes| R1[ResearchService.research_topic]
    R1 --> R2[Check PERPLEXITY_API_KEY]
    R2 --> R3{API Key present?}
    R3 -->|No| R4[Raise APIError: Missing Key]
    R3 -->|Yes| R5[Create PerplexityClient]
    R5 --> R6[Call Perplexity API:<br/>sonar-pro model]
    R6 --> R7{API Success?}
    R7 -->|No| R8[Raise APIError]
    R7 -->|Yes| R9[Return research summary]
    R9 --> GP19[Continue with research_summary]
    GP18 -->|No| GP19[research_summary = None]
    
    %% Generation Phase
    GP19 --> GEN1[RulesGeneratorService.generate_rules]
    GEN1 --> GEN2[Build generation prompt:<br/>- Tool, language, tag<br/>- Current date<br/>- Enforcement language rules<br/>- Research summary if available]
    GEN2 --> GEN3[AIClientFactory.get_client for primary model]
    GEN3 --> GEN4{Model provider?}
    
    %% Client Selection
    GEN4 -->|OpenAI| GEN5[Check OPENAI_API_KEY]
    GEN4 -->|Anthropic| GEN6[Check ANTHROPIC_API_KEY]
    GEN4 -->|Unknown| GEN7[Raise APIError: Unknown model]
    
    GEN5 --> GEN8{OpenAI Key present?}
    GEN8 -->|No| GEN9[Raise APIError: Missing OpenAI Key]
    GEN8 -->|Yes| GEN10[Create OpenAIClient]
    
    GEN6 --> GEN11{Anthropic Key present?}
    GEN11 -->|No| GEN12[Raise APIError: Missing Anthropic Key]
    GEN11 -->|Yes| GEN13[Create AnthropicClient]
    
    %% API Generation
    GEN10 --> GEN14[Call OpenAI API with chat completion]
    GEN13 --> GEN15[Call Anthropic API with messages]
    GEN14 --> GEN16{API Success?}
    GEN15 --> GEN16
    GEN16 -->|No| GEN17[Raise APIError]
    GEN16 -->|Yes| GEN18[Get generated rules content]
    
    %% Review Phase
    GEN18 --> GEN19{Review model specified?}
    GEN19 -->|Yes| GEN20[RulesGeneratorService.validate_rules]
    GEN20 --> GEN21[Build review prompt with enforcement rules]
    GEN21 --> GEN22[Call review model API]
    GEN22 --> GEN23{Review API Success?}
    GEN23 -->|No| GEN24[Raise APIError]
    GEN23 -->|Yes| GEN25[Get refined rules content]
    GEN19 -->|No| GEN25[Use original content]
    
    %% Content Processing & File Writing
    GEN25 --> W1[ContentProcessor.clean_rules_content]
    W1 --> W2[Remove markdown code blocks<br/>Clean escaped newlines]
    W2 --> W3[FileManager.get_rules_filepath]
    W3 --> W4{Tool type?}
    
    %% File Path Generation
    W4 -->|claude| W5[project_path/CLAUDE.md]
    W4 -->|copilot| W6[project_path/.github/copilot-{lang}-{tag}.md]
    W4 -->|cursor| W7[project_path/.cursor/rules/{tag}.mdc]
    W4 -->|cline/roo| W8[project_path/.{tool}/rules/{tag}.md]
    
    %% File Writing Decision
    W5 --> W9[FileManager.write_rules_file]
    W6 --> W9
    W7 --> W9
    W8 --> W9
    
    W9 --> W10{Dry run mode?}
    W10 -->|Yes| W11[Preview file content<br/>Show what would be written]
    W10 -->|No| W12[Create parent directories]
    W12 --> W13{Tool is claude?}
    W13 -->|Yes| W14[Append mode: Add separator + content]
    W13 -->|No| W15{File exists?}
    W15 -->|Yes & --yes not set| W16[Prompt user for overwrite]
    W16 --> W17{User confirms?}
    W17 -->|No| W18[Skip file writing]
    W17 -->|Yes| W19[Overwrite file]
    W15 -->|Yes & --yes set| W19
    W15 -->|No| W19
    W14 --> W20[Write to file]
    W19 --> W20
    
    W20 --> W21[Print success message]
    W11 --> W22[Show preview and continue]
    W18 --> W23[Print skip message]
    W21 --> END1[End for this tag]
    W22 --> END1
    W23 --> END1
    
    %% Error Handling
    C3 --> ERR[Exit with code 1]
    D3 --> ERR
    F4 --> ERR
    F7 --> ERR
    GP4 --> ERR
    GP11 --> ERR
    R4 --> ERR
    R8 --> ERR
    GEN7 --> ERR
    GEN9 --> ERR
    GEN12 --> ERR
    GEN17 --> ERR
    GEN24 --> ERR
    
    classDef commandNode fill:#e1f5fe
    classDef decisionNode fill:#fff3e0
    classDef processNode fill:#f3e5f5
    classDef errorNode fill:#ffebee
    classDef successNode fill:#e8f5e8
    
    class A,C,D,E,F,G,H commandNode
    class B,C2,C4,D2,F3,F6,GP3,GP6,GP7,GP12,GP13,GP18,R3,R7,GEN4,GEN8,GEN11,GEN16,GEN19,GEN23,W4,W10,W13,W15,W17 decisionNode
    class GP1,GP2,GP5,R1,GEN1,W1,W9 processNode
    class C3,D3,F4,F7,GP4,GP11,R4,R8,GEN7,GEN9,GEN12,GEN17,GEN24,ERR errorNode
    class C8,D4,W21,END1 successNode
```

This diagram illustrates the complete program execution flow including:

- **Command routing** and parameter parsing
- **Virtual environment validation** (required for all operations)
- **Configuration resolution** from CLI parameters and config files
- **Optional research phase** using Perplexity API
- **Rule generation** with OpenAI or Anthropic models
- **Optional review phase** for content refinement
- **File writing** with tool-specific paths and overwrite handling
- **Error handling** and exit points

## Installation

```bash
pip install rules4
```

## Quick Start

Generate rules for your favorite AI coding assistant directly:

```bash
# For Cursor
rules4 cursor --lang python --tags "testing,security"

# For Claude with research
rules4 claude --research --lang javascript --tags "react,typescript"

# For all configured tools (requires initialization)
rules4 generate
```

**Optional**: Initialize a configuration file for your project to set defaults:

```bash
rules4 init
```

This creates a `.rules4rc` file with default settings, allowing you to use `rules4 generate` to build rules for all configured tools at once.

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

### Generating Rules for All Configured Tools

If you have a `.rules4rc` file configured (created with `rules4 init`), you can generate rules for all specified tools:

```bash
rules4 generate --lang go --tags "code style"
```

This command will:

- Read the list of tools from your `.rules4rc` file.
- Generate rules for each tool, focusing on `code style` for Go projects.

**Note**: The `generate` command requires a `.rules4rc` configuration file. Individual tool commands (like `rules4 cursor`, `rules4 claude`) work without any configuration.

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
