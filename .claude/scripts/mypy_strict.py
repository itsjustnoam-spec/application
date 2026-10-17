"""
Runs mypy --strict and drops only the missing-return-annotation errors of functions that return nothing.

:author: Noam
:date: 16/10/26
"""
# ----- Imports ----- #

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

from check_python_conventions import FUNCTION_NODE_TYPES, function_returns_value

# ----- Consts ----- #

MISSING_RETURN_MESSAGE = "Function is missing a return type annotation"
UNTYPED_CALL_PATTERN = re.compile(
    r'Call to untyped function "(?P<name>[^"]+)" in typed context',
)
SKIPPED_DIRECTORY_NAMES = {
    ".venv",
    "node_modules",
    ".git",
}
MYPY_LINE_PATTERN = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+):(?:\d+:)? (?P<severity>error|note): ",
)
MYPY_UNAVAILABLE_EXIT_CODE = 2
MYPY_UNAVAILABLE_MESSAGE = "mypy could not run (is it installed in this project?)\n"
SUCCESS_MESSAGE = "Success: no issues found (functions without '-> None' are allowed)."
MYPY_ARGUMENTS = [
    "--strict",
    "--show-error-codes",
    "--no-error-summary",
    "--no-color-output",
]

# ----- Functions ----- #


def build_mypy_command(mypy_arguments: list[str]) -> list[str]:
    """
    Build the mypy command, preferring uv, then mypy, then python -m mypy.
    """
    if shutil.which("uv") is not None:
        return [
            "uv",
            "run",
            "mypy",
            *MYPY_ARGUMENTS,
            *mypy_arguments,
        ]

    if shutil.which("mypy") is not None:
        return [
            "mypy",
            *MYPY_ARGUMENTS,
            *mypy_arguments,
        ]

    return [
        sys.executable,
        "-m",
        "mypy",
        *MYPY_ARGUMENTS,
        *mypy_arguments,
    ]


def find_none_returning_lines(path: Path) -> set[int]:
    """
    Find the lines mypy may report for functions that never return a value.

    :param path: The Python file to inspect.
    :return: The `def` and decorator line numbers of every function that returns nothing.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (OSError, SyntaxError):
        return set()
    function_lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, FUNCTION_NODE_TYPES):
            continue

        if function_returns_value(node):
            continue

        function_lines.add(node.lineno)
        function_lines.update(
            decorator.lineno
            for decorator in node.decorator_list
        )
    return function_lines


def is_unannotated_none_returning(
    function_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """
    Check whether a function has no annotations at all and returns nothing.

    :param function_node: The function to inspect.
    :return: Whether mypy sees the function as untyped only because the
        convention omits "-> None".
    """
    if function_node.returns is not None:
        return False

    arguments = [
        *function_node.args.posonlyargs,
        *function_node.args.args,
        *function_node.args.kwonlyargs,
    ]
    if any(
        argument.annotation is not None
        for argument in arguments
    ):
        return False

    return not function_returns_value(function_node)


def find_untyped_none_returning_names(root: Path) -> set[str]:
    """
    Collect the names of functions that mypy calls untyped only because of the
    no "-> None" convention.

    :param root: The directory whose Python files are scanned.
    :return: The names of functions without annotations that return nothing.
    """
    function_names: set[str] = set()
    for python_file in root.rglob("*.py"):
        if SKIPPED_DIRECTORY_NAMES.intersection(python_file.parts):
            continue

        try:
            source = python_file.read_text(encoding="utf-8-sig")
            tree = ast.parse(source)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, FUNCTION_NODE_TYPES):
                continue

            if is_unannotated_none_returning(node):
                function_names.add(node.name)

    return function_names


def is_convention_untyped_call(
    output_line: str,
    function_names: set[str],
) -> bool:
    """
    Check whether a mypy line reports a call to a convention-untyped function.

    :param output_line: One line of mypy output.
    :param function_names: Names from find_untyped_none_returning_names.
    :return: Whether the error only exists because "-> None" is omitted.
    """
    call_match = UNTYPED_CALL_PATTERN.search(output_line)
    if call_match is None:
        return False

    return call_match.group("name") in function_names


def filter_mypy_output(output_lines: list[str]) -> list[str]:
    """
    Remove the errors that only exist because functions returning nothing omit "-> None".

    :param output_lines: Raw mypy output lines.
    :return: The output lines that still matter.
    """
    function_lines_by_path: dict[str, set[int]] = {}
    suppressed_locations: set[tuple[str, str]] = set()
    untyped_names = find_untyped_none_returning_names(Path.cwd())
    kept_lines: list[str] = []
    for output_line in output_lines:
        line_match = MYPY_LINE_PATTERN.match(output_line)
        if line_match is None:
            kept_lines.append(output_line)
            continue

        file_name = line_match.group("path")
        location = (file_name, line_match.group("line"))
        is_note = line_match.group("severity") == "note"
        if is_note and location in suppressed_locations:
            continue

        if is_convention_untyped_call(output_line, untyped_names):
            continue

        if MISSING_RETURN_MESSAGE not in output_line:
            kept_lines.append(output_line)
            continue

        if location[0] not in function_lines_by_path:
            file_path = Path(location[0])
            function_lines = find_none_returning_lines(file_path)
            function_lines_by_path[location[0]] = function_lines

        if int(location[1]) in function_lines_by_path[location[0]]:
            suppressed_locations.add(location)
            continue

        kept_lines.append(output_line)
    return kept_lines


def main() -> int:
    """
    Run mypy --strict and print the errors that matter.
    """
    mypy_arguments = sys.argv[1:] if len(sys.argv) > 1 else ["."]
    completed = subprocess.run(
        build_mypy_command(mypy_arguments),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output_lines = completed.stdout.splitlines()
    has_mypy_findings = any(
        MYPY_LINE_PATTERN.match(output_line) is not None
        for output_line in output_lines
    )
    if completed.returncode not in (0, 1) or (completed.returncode == 1 and not has_mypy_findings):
        sys.stderr.write(MYPY_UNAVAILABLE_MESSAGE)
        sys.stderr.write(completed.stdout + completed.stderr)
        return MYPY_UNAVAILABLE_EXIT_CODE

    kept_lines = filter_mypy_output(output_lines)
    error_count = sum(
        1
        for kept_line in kept_lines
        if ": error: " in kept_line
    )
    for kept_line in kept_lines:
        print(kept_line)
    if error_count == 0:
        print(SUCCESS_MESSAGE)
        return 0

    print(f"Found {error_count} error(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
