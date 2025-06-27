# Python Coding Standards: PEP 8

## Syntax and Naming Conventions
- **ALWAYS** adhere to the PEP 8 guideline for maximum line length of 79 characters for code and 72 for comments.
- **MANDATORY** use of `snake_case` for function and variable names.
- **MUST** use `CapWords` convention for class names.

## Indentation and Whitespace
- **REQUIRED** to use 4 spaces per indentation level. **NEVER** use tabs for indentation.
- **ALWAYS** surround these binary operators with a single space on either side: assignment (`=`), augmented assignment (`+=`, `-=`, etc.), comparisons (`==`, `<`, `>`, `!=`, `<>`, `<=`, `>=`, `in`, `not in`, `is`, `is not`), Booleans (`and`, `or`, `not`).
- **NEVER** add extra spaces around function calls, brackets, or keyword arguments.
- **MANDATORY** single new line at the end of each file.

## Comments
- **REQUIRED** to keep comments up-to-date with code changes.
- **MUST** write comments as complete sentences.
- Inline comments **SHOULD** be used sparingly.
- **ALWAYS** place inline comments on the line immediately above the code line it refers to and should be indented to the same level.

## Docstrings
- **MANDATORY** to include docstrings for public modules, functions, classes, and methods.
- **REQUIRED** docstrings should follow the ["numpydoc" docstring guide](https://numpydoc.readthedocs.io/en/latest/format.html).

## Imports 
- **MUST** place all imports at the top of the file.
- **ALWAYS** use absolute imports over relative imports.
- Imports **SHOULD** be grouped in the following order:
  1. Standard library imports.
  2. Related third party imports.
  3. Local application/library specific imports.
- **MANDATORY** to put a blank line between each group of imports.

## Exception Handling
- **ALWAYS** use explicit exception handling rather than generic exceptions, except for the final block.
- **SHOULD** minimize the amount of code in a try block.

## Programming Recommendations
- **NEVER** use lambdas which are complex; instead, define a function.
- **ALWAYS** use list comprehensions and generator expressions for simple tasks, preferring these over manual "for" loops and map function calls.
- Comparisons to singletons like `None` **SHOULD** always be done with `is` or `is not`, never the equality operators.

## Testing and Debugging
- **REQUIRED** to write tests for modules and functions.
- Debug print statements **SHOULD** never appear in the final code.

## Code Layout
- **MANDATORY** to separate top-level function and class definitions with two blank lines.
- Method definitions inside a class **SHOULD** be separated by a single blank line.
- **NEVER** use multiple statements on a single line (e.g., `a = 1; b = 2`).