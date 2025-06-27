# Python Project Documentation Rules

## General Documentation Principles
- **MANDATORY**: All Python functions and methods **MUST** have docstrings.
- **REQUIRED**: Every module **MUST** contain a module-level docstring explaining the purpose and usage of the module.
- Documentation **MUST** be written in English using clear, precise, and easy-to-understand language.

## Style and Format
- **MANDATORY**: Use [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) for docstring conventions unless specified otherwise by project requirements.
- **ALWAYS** write docstrings using triple double quotes.
- **REQUIRED**: Include a concise description at the beginning of each docstring followed by a more detailed explanation if necessary.

## Content Specifics
### Functions and Methods
- **MANDATORY**:
  - A brief description of the function/method.
  - List parameters with a description, their type, and if they are optional.
  - Describe return type and semantics.
- **NEVER** include trivial comments inside functions; focus on why something is done, not how.

### Classes
- **MANDATORY**:
  - Documentation for each class **MUST** describe its purpose and behavior in the system.
  - Document all public methods and properties.
  - If inheritance is used, note how and why it deviates from the base class.

### Variables and Constants
- **REQUIRED**: All global variables and constants **MUST** be documented explaining their usage and necessity in the module.

## Examples and Usage
- **ALWAYS** provide simple examples in the docstring when introducing complex functions or classes.
- **RECOMMENDED**: Use examples that illustrate typical use cases and edge cases.

## External Documentation
- **MANDATORY**: If any external libraries or frameworks are used, documentation **MUST** include their version and relevant details on integration.
- **RECOMMENDED**: Link to official documentation or relevant sections when referring to external tools or libraries.

## Automation and Tools
- **REQUIRED**:
  - Use tools such as `Sphinx` for generating documentation from docstrings.
  - Integrate documentation generation into the build process to ensure it is always up-to-date.
- **RECOMMENDED**: Configure continuous integration tools to automatically validate documentation against code changes.

## Versioning Documentation
- **REQUIRED**: Update documentation to reflect any changes in code usage or functionality along with code updates.
- **ALWAYS** maintain a changelog that details significant changes, enhancements, and fixes in the documentation similar to the codebase.

## Review and Maintenance
- **MANDATORY**: All documentation **MUST** be peer-reviewed before merging changes in code repositories.
- Documentation **SHOULD** be regularly reviewed and updated to keep pace with changes in the project.