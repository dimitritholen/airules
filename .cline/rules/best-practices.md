# Python Coding Best Practices for AI Assistant 'cline'

## General Concepts
- **MANDATORY**: Follow PEP 8 style guide for Python code to maintain readability and consistency.
- **REQUIRED**: Docstrings are **MANDATORY** for all public modules, functions, classes, and methods.
- **MUST** use four spaces per indentation level.
- Use **ALWAYS** explicit variable names to enhance code readability.

## Code Structure
- **MANDATORY**: Project structure should adhere to common Python frameworks expectations (e.g., Flask or Django for web apps).
- **ALWAYS** keep functions short and focused; each must perform a single task or responsibility.
- **NEVER** use hard-coded passwords or sensitive tokens directly in the codebase. Use environment variables or secure vault solutions.

## Error Handling
- **MANDATORY**: Catch exceptions wherever possible. Specific exceptions **MUST** be preferred over general exceptions.
- Logging of errors is **REQUIRED** and **MUST** provide sufficient context to diagnose issues.

## Dependencies
- **MANDATORY**: Manage all project dependencies using `pip` and a `requirements.txt` file or `Pipenv`.
- **ALWAYS** ensure that the versions of third-party libraries you depend on are pinned to avoid unexpected incompatibilities.

## Testing
- **MANDATORY**: Include unit tests for all major functionality using frameworks like `pytest` or `unittest`.
- Aim for a high code coverage percentage; it is **RECOMMENDED** to have at least 80% code coverage but the more, the better.

## Security
- **MUST** use secure coding practices to prevent SQL injection, XSS, CSRF, and other common security vulnerabilities.
- User input validation is **REQUIRED** for all external or user-provided data.

## Performance
- Use **ALWAYS** performance profiling for critical applications to identify bottlenecks.
- **RECOMMENDED**: Implement caching mechanisms where appropriate to improve performance.

## Documentation
- **ALWAYS** maintain a `README.md` file with installation, configuration, and operation instructions.
- Including a `CHANGELOG.md` for tracking changes in versions is **RECOMMENDED**.

## Version Control
- **MANDATORY**: Use Git for version control.
- **ALWAYS** use meaningful commit messages; each commit should clearly describe the changes made.

## Code Reviews
- **REQUIRED**: Conduct regular code reviews to ensure compliance with these standards and overall quality improvement.
- **RECOMMENDED**: Use pull requests for introducing new features or changes, allowing for discussion and review before merging.

## Continuous Integration/Continuous Deployment (CI/CD)
- **MANDATORY**: Set up CI/CD pipelines to automate testing and deployment processes.
- **ALWAYS** ensure that main/master branches are protected: direct pushes should be disabled, and merging should require pull request reviews and passing status checks.

By adhering to these rules, 'cline' will assist in maintaining high-quality and modern Python projects. Following these guidelines ensures not only functional code but also secure, maintainable, and robust Python applications.