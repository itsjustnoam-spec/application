"""
PostToolUse hook: runs the convention checks and eslint on the lines Claude just wrote.

:author: Noam
:date: 16/10/26
"""
# ----- Imports ----- #

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lint_changed import collect_problems

# ----- Consts ----- #

BLOCKING_EXIT_CODE = 2
REPORT_HEADER = (
    "Convention check failed for {path}. Fix every item below before continuing. "
    "Only lines this branch wrote are listed: leave every other line as it is.\n"
)

# ----- Functions ----- #


def read_hook_payload() -> dict[str, object]:
    """
    Read the JSON payload Claude Code sends on stdin.
    """
    raw_payload = sys.stdin.buffer.read().decode("utf-8")
    if raw_payload.strip() == "":
        return {}

    payload = json.loads(raw_payload)
    return payload if isinstance(payload, dict) else {}


def get_edited_path(payload: dict[str, object]) -> Path | None:
    """
    Return the path of the file the tool call edited.
    """
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or file_path.strip() == "":
        return None

    return Path(file_path)


def is_inside_project(path: Path) -> bool:
    """
    Check whether a file belongs to the project (scratch files outside it don't).
    """
    project_directory = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_directory is None:
        return True

    project_root = Path(project_directory).resolve()
    return path.resolve().is_relative_to(project_root)


def report_problems(path: Path, problems: list[str]) -> int:
    """
    Send the problems back to Claude and block until they're fixed.
    """
    header = REPORT_HEADER.format(path=path)
    message = header + "\n".join(problems) + "\n"
    sys.stderr.buffer.write(message.encode("utf-8"))
    sys.stderr.flush()
    return BLOCKING_EXIT_CODE


def main() -> int:
    """
    Check the lines the edit wrote against the conventions.
    """
    edited_path = get_edited_path(read_hook_payload())
    if edited_path is None or not edited_path.is_file():
        return 0

    if not is_inside_project(edited_path):
        return 0

    problems = collect_problems(edited_path, "auto")
    if len(problems) == 0:
        return 0

    return report_problems(edited_path, problems)


if __name__ == "__main__":
    sys.exit(main())
