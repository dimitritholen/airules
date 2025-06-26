# Auto Feature Documentation

The auto feature is an intelligent project analysis system that automatically detects your project's framework, dependencies, and requirements to generate appropriate AI coding assistant rules.

## Overview

The auto feature consists of several components working together:

1. **Framework Detector** - Identifies the programming languages and frameworks used
2. **Dependency Analyzer** - Analyzes package files and dependencies
3. **Package Parser** - Parses various package manifest files
4. **Tag Generator** - Creates relevant tags based on project analysis
5. **Rule Generator** - Generates AI assistant rules based on the analysis

## Usage

### Basic Usage

```bash
# Auto-detect and generate rules for all configured tools
rules4 auto

# Auto-detect with research enhancement
rules4 auto --research

# Auto-detect with validation by Claude
rules4 auto --review claude-3-sonnet-20240229

# Full pipeline with research and validation
rules4 auto --research --review claude-3-sonnet-20240229
```

### Advanced Options

```bash
# Specify project path (default: current directory)
rules4 auto --project-path /path/to/project

# Generate rules for specific tools only
rules4 auto --tools cursor,claude

# Override detected language
rules4 auto --lang python --tags "web,api,testing"

# Dry run to see what would be generated
rules4 auto --dry-run

# Skip confirmation prompts
rules4 auto --yes
```

## Supported Project Types

### Python Projects

The auto feature detects Python projects by looking for:

- `requirements.txt`
- `pyproject.toml`
- `setup.py`
- `Pipfile`
- `poetry.lock`
- `environment.yml` (conda)

**Supported Frameworks:**
- Flask
- Django
- FastAPI
- Streamlit
- Pytest (testing)
- Black (formatting)
- Flake8 (linting)

**Example Output:**
```markdown
# Auto-Generated Python Rules

This is a Flask web application with the following characteristics:
- Uses pytest for testing
- Has black for code formatting
- Uses flake8 for linting
- Includes SQLAlchemy for database operations

## Best Practices
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write comprehensive tests
- Keep requirements.txt up to date
```

### JavaScript/TypeScript Projects

The auto feature detects JavaScript/TypeScript projects by looking for:

- `package.json`
- `package-lock.json`
- `yarn.lock`
- `tsconfig.json`
- `jsconfig.json`

**Supported Frameworks:**
- React
- Next.js
- Vue.js
- Angular
- Express.js
- Node.js
- Jest (testing)
- ESLint (linting)
- Prettier (formatting)

**Example Output:**
```markdown
# Auto-Generated React/TypeScript Rules

This is a React application with TypeScript and the following tools:
- Material-UI for component library
- React Router for navigation
- Axios for HTTP requests
- Jest and React Testing Library for testing

## Best Practices
- Use TypeScript strict mode
- Follow React hooks best practices
- Implement proper error boundaries
- Write unit tests for components
```

### Rust Projects

The auto feature detects Rust projects by looking for:

- `Cargo.toml`
- `Cargo.lock`

**Supported Features:**
- Serde for serialization
- Tokio for async runtime
- Clap for CLI parsing
- Reqwest for HTTP client

**Example Output:**
```markdown
# Auto-Generated Rust Rules

This is a Rust application with async capabilities:
- Uses Tokio for async runtime
- Serde for JSON serialization
- Clap for command-line interface
- Anyhow for error handling

## Best Practices
- Use Result<T, E> for error handling
- Follow Rust naming conventions
- Write comprehensive unit tests
- Use cargo fmt for formatting
```

### Mixed/Monorepo Projects

The auto feature can handle projects with multiple languages and frameworks:

```bash
# Example monorepo structure
my-app/
├── backend/          # Python FastAPI
│   ├── requirements.txt
│   └── main.py
├── frontend/         # React TypeScript
│   ├── package.json
│   └── src/
├── mobile/          # React Native
│   ├── package.json
│   └── App.tsx
└── shared/          # Common utilities
    └── types.ts
```

The auto feature will detect all components and generate appropriate rules for each.

## Configuration

The auto feature respects your `.airulesrc` configuration:

```ini
[settings]
language = auto        # Let auto feature detect
tags = auto           # Let auto feature generate
tools = cursor,claude # Only generate for these tools
```

### Advanced Configuration

```ini
[auto]
# Minimum confidence threshold for framework detection (0.0-1.0)
confidence_threshold = 0.7

# Maximum depth for directory traversal
max_depth = 10

# File patterns to ignore during analysis
ignore_patterns = node_modules,venv,.git,dist,build

# Custom framework detection rules
[auto.frameworks]
flask = requirements.txt contains flask
django = requirements.txt contains django OR manage.py exists
react = package.json contains react
```

## Testing

The auto feature includes comprehensive test coverage:

### Running Tests

```bash
# Run all auto feature tests
make test

# Run only integration tests
make test-integration

# Run performance benchmarks
make test-performance

# Run error handling tests
make test-error-handling

# Generate coverage report
make test-coverage
```

### Test Project Fixtures

The test suite includes realistic project fixtures:

- **Python Flask** - Web application with dependencies
- **Django** - Full MVC framework with models and views
- **React TypeScript** - Modern React app with Material-UI
- **Next.js** - Server-side rendered React application
- **Rust** - CLI application with async capabilities
- **FastAPI** - Modern Python API framework

### Performance Benchmarks

The auto feature is benchmarked for performance:

- **Small projects** (< 50 files): < 500ms
- **Medium projects** (< 200 files): < 2 seconds
- **Large projects** (< 1000 files): < 5 seconds

### Error Handling

The auto feature handles various error conditions gracefully:

- Missing or corrupted package files
- Network failures during API calls
- Permission denied errors
- Circular symbolic links
- Very deep directory structures
- Large binary files
- Unicode and special characters

## API Integration

The auto feature integrates with multiple AI services:

### OpenAI Integration
- Used for primary rule generation
- Supports GPT-4 and GPT-3.5-turbo models
- Handles rate limiting and retries

### Anthropic Integration
- Used for rule validation and improvement
- Supports Claude-3 models
- Optional enhancement step

### Perplexity Integration
- Used for research and context gathering
- Provides up-to-date framework information
- Optional research step

## Troubleshooting

### Common Issues

**Framework not detected:**
```bash
# Override detection
rules4 auto --lang python --tags "flask,web,api"

# Check project structure
rules4 auto --dry-run --verbose
```

**API rate limits:**
```bash
# Use different models or reduce frequency
rules4 auto --primary gpt-3.5-turbo
```

**Permission errors:**
```bash
# Check directory permissions
ls -la /path/to/project

# Use different project path
rules4 auto --project-path /accessible/path
```

**Slow analysis:**
```bash
# Limit analysis depth
rules4 auto --max-depth 5

# Exclude large directories
rules4 auto --ignore node_modules,venv,.git
```

### Debug Mode

```bash
# Enable verbose output
rules4 auto --verbose

# Show analysis details
rules4 auto --debug

# Dry run to see detection results
rules4 auto --dry-run
```

## Examples

### Example 1: Flask Web Application

```bash
cd my-flask-app
rules4 auto --research --review claude-3-sonnet-20240229
```

**Generated files:**
- `.cursor/rules/python.mdc`
- `.cursor/rules/web.mdc`
- `.cursor/rules/testing.mdc`
- `CLAUDE.md` (appended)

### Example 2: React TypeScript Project

```bash
cd my-react-app
rules4 auto --tools cursor,copilot
```

**Generated files:**
- `.cursor/rules/javascript.mdc`
- `.cursor/rules/react.mdc`
- `.github/copilot-javascript-react.md`

### Example 3: Full-Stack Monorepo

```bash
cd my-monorepo
rules4 auto --research
```

**Detected components:**
- Backend: Python FastAPI
- Frontend: Next.js TypeScript
- Mobile: React Native
- Database: PostgreSQL

**Generated rules for each component with appropriate tags and frameworks.**

## Best Practices

1. **Run auto feature from project root** - Ensures complete analysis
2. **Use research flag for new frameworks** - Gets latest best practices
3. **Review generated rules** - Customize based on team preferences
4. **Update regularly** - Re-run when dependencies change
5. **Commit generated rules** - Share with team members
6. **Use validation** - Improve rule quality with AI review

## Limitations

- Requires active internet connection for API calls
- Limited to supported frameworks and languages
- May not detect highly customized project structures
- API costs apply for rule generation
- Analysis time increases with project size

## Future Enhancements

- Support for more programming languages (Go, PHP, Ruby)
- Custom framework definition files
- Integration with more AI services
- Caching for faster re-analysis
- Team collaboration features
- IDE integrations