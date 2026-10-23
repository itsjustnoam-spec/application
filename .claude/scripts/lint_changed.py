"""
Run the convention checks and eslint on files, and report only what the branch wrote.

:author: Noam
:date: 23/10/26
"""
# ----- Imports ----- #

import argparse
import json
import subprocess
import sys
from pathlib import Path

from changed_lines import get_changed_lines
from check_python_conventions import check_changed_python_file
from check_vue_conventions import FRONTEND_SUFFIXES, check_changed_vue_file

# ----- Consts ----- #

ESLINT_BIN_CANDIDATES = (
    "node_modules/.bin/eslint.cmd",
    "node_modules/.bin/eslint",
)
ESLINT_FILE_SUFFIXES = (
    ".vue",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
)
ESLINT_TIMEOUT_SECONDS = 45
DESCRIPTION = "Check files against the conventions and eslint, reporting only the lines the branch wrote."
SINCE_HELP = "The git ref the branch is compared to ('auto': the feature's base or the merge base)."

# ----- Functions ----- #


def find_eslint(path: Path) -> tuple[str, Path] | None:
    """
    Find the nearest project-local eslint binary above a file.

    :param path: The frontend file.
    :return: The eslint executable and the directory to run it from, when one is installed.
    """
    for directory in path.resolve().parents:
        for candidate in ESLINT_BIN_CANDIDATES:
            if (directory / candidate).is_file():
                return str(directory / candidate), directory
    return None


def run_eslint(path: Path) -> list[tuple[int | None, str]]:
    """
    Run the project's eslint on one file.

    :param path: The frontend file.
    :return: Each problem's line and text; a line of None means eslint itself failed.
    """
    eslint = find_eslint(path)
    if eslint is None:
        return []

    eslint_executable, working_directory = eslint
    try:
        completed = subprocess.run(
            [
                eslint_executable,
                "--format",
                "json",
                str(path),
            ],
            cwd=working_directory,
            check=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=ESLINT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as eslint_error:
        return [(None, f"Could not run eslint: {eslint_error}")]

    try:
        results = json.loads(completed.stdout)
    except json.JSONDecodeError:
        output = (completed.stdout + completed.stderr).strip()
        return [] if completed.returncode == 0 else [(None, output)]

    return [
        format_eslint_message(path, message)
        for result in results
        for message in result.get("messages", [])
    ]


def format_eslint_message(path: Path, message: dict[str, object]) -> tuple[int | None, str]:
    """
    Turn one eslint JSON message into its line and a 'path:line: rule text' description.
    """
    line = message.get("line")
    line_number = line if isinstance(line, int) else None
    rule_id = message.get("ruleId")
    text = message.get("message")
    return line_number, f"{path}:{line_number}: {rule_id} {text}"


def collect_problems(path: Path, base: str) -> list[str]:
    """
    Collect the convention and lint problems on the lines of a file that the branch wrote.

    :param path: The file to check.
    :param base: The git ref the branch is compared to, or `auto`.
    :return: One line of text per problem.
    """
    if path.suffix == ".py":
        return [
            violation.format_for_output()
            for violation in check_changed_python_file(path, base)
        ]

    if path.suffix not in ESLINT_FILE_SUFFIXES:
        return []

    problems: list[str] = []
    if path.suffix in FRONTEND_SUFFIXES:
        problems += [
            violation.format_for_output()
            for violation in check_changed_vue_file(path, base)
        ]

    changed_lines = get_changed_lines(path, base)
    problems += [
        problem
        for line, problem in run_eslint(path)
        if line is None or changed_lines.includes(line)
    ]
    return problems


def write_utf8(text: str):
    """
    Write text to stdout as UTF-8.
    """
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.flush()


def main() -> int:
    """
    Check the given files and print every problem on the lines the branch wrote.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "paths",
        nargs="+",
        help="Files to check.",
    )
    parser.add_argument(
        "--since",
        default="auto",
        help=SINCE_HELP,
    )
    parsed_arguments = parser.parse_args()
    problems: list[str] = []
    for raw_path in parsed_arguments.paths:
        path = Path(raw_path)
        if path.is_file():
            problems += collect_problems(
                path,
                parsed_arguments.since,
            )
    if len(problems) == 0:
        return 0

    for problem in problems:
        write_utf8(problem + "\n")
    summary = f"{len(problems)} problem(s) on lines this branch wrote.\n"
    write_utf8(summary)
    return 1


if __name__ == "__main__":
    sys.exit(main())
