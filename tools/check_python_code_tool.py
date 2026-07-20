"""
Check Python Code Tool.

Performs the deterministic part of a code review: syntax
validation and static checks based on the AST. The qualitative
review (logic, design, feedback) is done by the professor using
the code review procedure from the knowledge base.

The code is only parsed, never executed.
"""

import ast
import re

try:
    from .tool import Tool
except ImportError:
    from tool import Tool


MAX_LINE_LENGTH = 100
SNAKE_CASE_PATTERN = re.compile(r"^_{0,2}[a-z][a-z0-9_]*$")
PASCAL_CASE_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def check_python_code(code: str) -> str:
    """
    Statically analyze a Python snippet and return a report.

    Parameters:
        code (str): The Python source code to check.

    Returns:
        str: A structured report with syntax status, statistics
             and style issues found.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return (
            "SYNTAX ERROR - the code does not compile.\n"
            f"Line {error.lineno}: {error.msg}\n"
            f"  {error.text.strip() if error.text else ''}"
        )

    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    issues = []

    for func in functions:
        if not SNAKE_CASE_PATTERN.match(func.name):
            issues.append(
                f"Line {func.lineno}: function '{func.name}' does not follow "
                "snake_case naming (PEP 8)."
            )
        if ast.get_docstring(func) is None:
            issues.append(
                f"Line {func.lineno}: function '{func.name}' has no docstring."
            )

    for cls in classes:
        if not PASCAL_CASE_PATTERN.match(cls.name):
            issues.append(
                f"Line {cls.lineno}: class '{cls.name}' does not follow "
                "PascalCase naming (PEP 8)."
            )

    for handler in (n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)):
        if handler.type is None:
            issues.append(
                f"Line {handler.lineno}: bare 'except:' clause - catch "
                "specific exceptions instead."
            )

    for line_number, line in enumerate(code.splitlines(), start=1):
        if len(line) > MAX_LINE_LENGTH:
            issues.append(
                f"Line {line_number}: line is {len(line)} characters long "
                f"(max recommended: {MAX_LINE_LENGTH})."
            )

    report = [
        "SYNTAX: OK - the code compiles.",
        f"Functions: {len(functions)} | Classes: {len(classes)}",
    ]
    if issues:
        report.append(f"Style issues found ({len(issues)}):")
        report.extend(f"- {issue}" for issue in issues)
    else:
        report.append("No style issues detected by static analysis.")

    report.append(
        "Note: this is a static check only. Logic, correctness and design "
        "must still be reviewed manually."
    )
    return "\n".join(report)


check_python_code_tool = Tool(
    name="check_python_code",
    description=(
        "Statically analyzes a Python code snippet: verifies the syntax and "
        "reports style issues (naming conventions, missing docstrings, bare "
        "except clauses, overly long lines). Always use it FIRST when "
        "reviewing or grading student code. The code is never executed."
    ),
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python source code to analyze."
            }
        },
        "required": ["code"]
    },
    callback=check_python_code
)
