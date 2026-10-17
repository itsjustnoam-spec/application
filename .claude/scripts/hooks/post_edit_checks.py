"""
PostToolUse hook: runs the convention checker and linters on the file Claude just edited.

:author: Noam
:date: 16/10/26
"""
# ----- Imports ----- #

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from check_python_conventions import check_python_file

# ----- Consts ----- #

BLOCKING_EXIT_CODE = 2
LINTER_TIMEOUT_SECONDS = 45
PYTHON_SUFFIXES = (".py",)
FRONTEND_SUFFIXES = (".vue", ".ts", ".tsx", ".js", ".mjs")
PYTHON_PROJECT_MARKER = "pyproject.toml"
FRONTEND_PROJECT_MARKER = "package.json"
RUFF_VENV_CANDIDATES = (".venv/Scripts/ruff.exe", ".venv/bin/ruff")
ESLINT_BIN_CANDIDATES = ("node_modules/.bin/eslint.cmd", "node_modules/.bin/eslint")

# ----- Functions ----- #


def read_hook_payload() -> dict[str, object]:
    raw_payload = sys.stdin.buffer.read().decode("utf-8")
    if raw_payload.strip() == "":
        return {}

    payload = json.loads(raw_payload)
    return payload if isinstance(payload, dict) else {}


def get_edited_path(payload: dict[str, object]) -> Path | None:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or file_path.strip() == "":
        return None

    return Path(file_path)


def find_project_root(path: Path, marker: str) -> Path | None:
    for directory in path.resolve().parents:
        if (directory / marker).is_file():
            return directory
    return None


def find_ruff(project_root: Path | None) -> str | None:
    if project_root is not None:
        for candidate in RUFF_VENV_CANDIDATES:
            if (project_root / candidate).is_file():
                return str(project_root / candidate)

    return shutil.which("ruff")


def find_eslint(path: Path) -> tuple[str, Path] | None:
    """
    Finds the nearest project-local eslint binary above the edited file.

    :param path: The edited frontend file.
    :return: The eslint executable and the directory to run it from, when one is installed.
    """
    for directory in path.resolve().parents:
        for candidate in ESLINT_BIN_CANDIDATES:
            if (directory / candidate).is_file():
                return str(directory / candidate), directory
    return None


def run_linter(command: list[str], working_directory: Path | None) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=working_directory,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=LINTER_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as linter_error:
        return f"Could not run {command[0]}: {linter_error}"
    if completed.returncode == 0:
        return ""

    return (completed.stdout + completed.stderr).strip()


def collect_python_problems(path: Path) -> list[str]:
    violations = check_python_file(path)
    problems = [violation.format_for_output() for violation in violations]
    ruff = find_ruff(find_project_root(path, PYTHON_PROJECT_MARKER))
    if ruff is None:
        return problems

    ruff_output = run_linter(
        [
            ruff,
            "check",
            "--no-fix",
            "--output-format",
            "concise",
            str(path),
        ],
        find_project_root(path, PYTHON_PROJECT_MARKER),
    )
    if ruff_output != "":
        problems.append(ruff_output)

    return problems


def collect_frontend_problems(path: Path) -> list[str]:
    eslint = find_eslint(path)
    if eslint is None:
        return []

    eslint_executable, working_directory = eslint
    eslint_output = run_linter(
        [eslint_executable, str(path)],
        working_directory,
    )
    return [] if eslint_output == "" else [eslint_output]


def report_problems(path: Path, problems: list[str]) -> int:
    message = (
        f"Convention check failed for {path}. Fix every item below before continuing:\n"
        + "\n".join(problems)
        + "\n"
    )
    sys.stderr.buffer.write(message.encode("utf-8"))
    sys.stderr.flush()
    return BLOCKING_EXIT_CODE


def main() -> int:
    edited_path = get_edited_path(read_hook_payload())
    if edited_path is None or not edited_path.is_file():
        return 0

    problems: list[str] = []
    if edited_path.suffix in PYTHON_SUFFIXES:
        problems = collect_python_problems(edited_path)
    elif edited_path.suffix in FRONTEND_SUFFIXES:
        problems = collect_frontend_problems(edited_path)

    if len(problems) == 0:
        return 0

    return report_problems(edited_path, problems)


if __name__ == "__main__":
    sys.exit(main())
