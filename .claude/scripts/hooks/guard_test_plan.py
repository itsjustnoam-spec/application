"""
PreToolUse hook: blocks adding tests that are not listed in the active feature's test-plan.md.

:author: Noam
:date: 16/10/26
"""
# ----- Imports ----- #

import json
import re
import sys
from pathlib import Path

# ----- Consts ----- #

BLOCKING_EXIT_CODE = 2
ACTIVE_FEATURE_MARKER = Path("docs") / "features" / ".active"
TEST_PLAN_FILE_NAME = "test-plan.md"
GIT_ENTRY_NAME = ".git"
PYTHON_TEST_PATTERN = re.compile(
    r"^\s*(?:async\s+)?def\s+(test_\w+)\s*\(",
    re.MULTILINE,
)
FRONTEND_TEST_PATTERN = re.compile(
    r"""^\s*(?:it|test)(?:\.(?:only|skip|todo|fixme|fail|fails|slow|concurrent))?\s*\(\s*(['"`])(.+?)\1""",
    re.MULTILINE,
)
FRONTEND_TEST_SUFFIXES = (".spec.ts", ".test.ts", ".spec.js", ".test.js")
EDIT_TOOL_NAMES = ("Edit", "MultiEdit")

# ----- Functions ----- #


def read_hook_payload() -> dict[str, object]:
    """
    Reads the JSON payload Claude Code sends on stdin.
    """
    raw_payload = sys.stdin.buffer.read().decode("utf-8")
    if raw_payload.strip() == "":
        return {}

    payload = json.loads(raw_payload)
    return payload if isinstance(payload, dict) else {}


def is_python_test_file(path: Path) -> bool:
    """
    Tells whether a path is a pytest test module.
    """
    return path.suffix == ".py" and path.name.startswith("test_")


def is_frontend_test_file(path: Path) -> bool:
    """
    Tells whether a path is a Vitest or Playwright test file.
    """
    is_in_tests_folder = "__tests__" in path.parts
    has_test_suffix = path.name.endswith(FRONTEND_TEST_SUFFIXES)
    return has_test_suffix or is_in_tests_folder


def extract_test_names(path: Path, source: str) -> list[str]:
    """
    Extracts the test names a test file declares.
    """
    if is_python_test_file(path):
        return PYTHON_TEST_PATTERN.findall(source)

    test_matches = FRONTEND_TEST_PATTERN.finditer(source)
    return [
        test_match.group(2)
        for test_match in test_matches
    ]


def read_existing_source(path: Path) -> str:
    """
    Reads a file's current content, or an empty string when it doesn't exist.
    """
    if not path.is_file():
        return ""

    return path.read_text(encoding="utf-8-sig", errors="replace")


def collect_source_changes(tool_name: str, tool_input: dict[str, object]) -> list[tuple[str, str]]:
    """
    Lists the (before, after) text pairs a Write or Edit call would apply.

    :param tool_name: The tool being called.
    :param tool_input: The tool's input payload.
    :return: The replaced text and its replacement for every change in the call.
    """
    if tool_name not in EDIT_TOOL_NAMES:
        file_path = str(tool_input.get("file_path", ""))
        new_content = str(tool_input.get("content", ""))
        return [(read_existing_source(Path(file_path)), new_content)]

    raw_edits = tool_input.get("edits")
    edits: list[object] = [tool_input]
    if isinstance(raw_edits, list):
        edits = raw_edits

    source_changes: list[tuple[str, str]] = []
    for edit in edits:
        if isinstance(edit, dict):
            old_source = str(edit.get("old_string", ""))
            new_source = str(edit.get("new_string", ""))
            source_changes.append((old_source, new_source))
    return source_changes


def find_added_test_names(path: Path, source_changes: list[tuple[str, str]]) -> list[str]:
    """
    Lists the tests that a change adds.
    """
    added_test_names: list[str] = []
    for old_source, new_source in source_changes:
        existing_names = set(extract_test_names(path, old_source))
        for test_name in extract_test_names(path, new_source):
            if test_name not in existing_names:
                added_test_names.append(test_name)
    return added_test_names


def find_active_test_plan(start_directory: Path) -> tuple[str, Path] | None:
    """
    Finds the test plan of the feature running in the checkout that contains the start directory.

    :param start_directory: The directory of the test file being written.
    :return: The active feature slug and its test-plan path, when a feature is active.
    """
    for directory in (start_directory, *start_directory.parents):
        marker = directory / ACTIVE_FEATURE_MARKER
        if marker.is_file():
            feature_slug = marker.read_text(encoding="utf-8").strip()
            return feature_slug, marker.parent / feature_slug / TEST_PLAN_FILE_NAME

        if (directory / GIT_ENTRY_NAME).exists():
            break
    return None


def block(message: str) -> int:
    """
    Sends the reason back to Claude and blocks the edit.
    """
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    sys.stderr.flush()
    return BLOCKING_EXIT_CODE


def main() -> int:
    """
    Blocks new tests that aren't in the active feature's test plan.
    """
    payload = read_hook_payload()
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    path = Path(str(tool_input.get("file_path", "")))
    is_python_test = is_python_test_file(path)
    if not is_python_test and not is_frontend_test_file(path):
        return 0

    tool_name = str(payload.get("tool_name", ""))
    source_changes = collect_source_changes(tool_name, tool_input)
    added_test_names = find_added_test_names(path, source_changes)
    if len(added_test_names) == 0:
        return 0

    active_test_plan = find_active_test_plan(path.resolve().parent)
    if active_test_plan is None:
        return 0

    feature_slug, test_plan_path = active_test_plan
    if not test_plan_path.is_file():
        return block(
            f"Blocked: feature '{feature_slug}' has no {test_plan_path}. "
            "Write the test plan (test name, file path, what it tests, expected result) before writing tests.",
        )

    test_plan = test_plan_path.read_text(encoding="utf-8")
    unplanned_names = [
        test_name
        for test_name in added_test_names
        if test_name not in test_plan
    ]
    if len(unplanned_names) == 0:
        return 0

    return block(
        f"Blocked: these tests are not in {test_plan_path}: {', '.join(unplanned_names)}. "
        "Add a row for each one to the test plan first, then write the test.",
    )


if __name__ == "__main__":
    sys.exit(main())
