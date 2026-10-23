"""
Find the lines a branch changed, so the checks report only on code the branch wrote.

:author: Noam
:date: 23/10/26
"""
# ----- Imports ----- #

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

# ----- Consts ----- #

HUNK_HEADER_PATTERN = re.compile(
    r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@",
    re.MULTILINE,
)
BASE_LINE_PATTERN = re.compile(
    r"^Base:\s*`?([0-9A-Za-z][\w./-]*)`?\s*$",
    re.MULTILINE,
)
BASE_CANDIDATES = (
    "origin/HEAD",
    "origin/main",
    "origin/master",
)
GIT_TIMEOUT_SECONDS = 20

# ----- Classes ----- #


@dataclass(frozen=True)
class ChangedLines:
    """
    The lines of one file that the branch added or changed.
    """
    is_new_file: bool
    line_numbers: frozenset[int]

    def includes(self, line_number: int) -> bool:
        """
        Check whether the branch wrote a line.

        :param line_number: A 1-based line number in the current file.
        :return: Whether the line is new or changed in this branch (every line of a new file is).
        """
        return self.is_new_file or line_number in self.line_numbers

# ----- Functions ----- #


def run_git(arguments: list[str], working_directory: Path) -> subprocess.CompletedProcess[str] | None:
    """
    Run a git command and return its result, or None when git can't run.
    """
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=working_directory,
            check=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def find_git_root(path: Path) -> Path | None:
    """
    Find the root of the git checkout that holds a file.
    """
    directory = path.resolve().parent
    completed = run_git(
        [
            "rev-parse",
            "--show-toplevel",
        ],
        directory,
    )
    if completed is None or completed.returncode != 0:
        return None

    return Path(completed.stdout.strip())


def read_feature_base(git_root: Path) -> str | None:
    """
    Read the base commit that the active feature recorded in its progress file.

    :param git_root: The root of the checkout.
    :return: The `Base:` value of the active feature's progress.md, when there is one.
    """
    active_marker = git_root / "docs" / "features" / ".active"
    if not active_marker.is_file():
        return None

    slug = active_marker.read_text(encoding="utf-8").strip()
    progress_file = git_root / "docs" / "features" / slug / "progress.md"
    if slug == "" or not progress_file.is_file():
        return None

    progress_text = progress_file.read_text(encoding="utf-8")
    base_match = BASE_LINE_PATTERN.search(progress_text)
    if base_match is None:
        return None

    return base_match.group(1)


def find_merge_base(git_root: Path) -> str | None:
    """
    Find where the current branch split from the remote default branch.
    """
    for candidate in BASE_CANDIDATES:
        completed = run_git(
            [
                "merge-base",
                "HEAD",
                candidate,
            ],
            git_root,
        )
        if completed is not None and completed.returncode == 0:
            return completed.stdout.strip()
    return None


def resolve_base(path: Path, requested_base: str) -> str | None:
    """
    Resolve the commit that a file's changes are measured against.

    :param path: The file being checked.
    :param requested_base: A git ref, or `auto` to use the active feature's base or the merge base.
    :return: The ref to diff against, or None when the file isn't in a git checkout.
    """
    git_root = find_git_root(path)
    if git_root is None:
        return None

    if requested_base != "auto":
        return requested_base

    feature_base = read_feature_base(git_root)
    if feature_base is not None:
        return feature_base

    return find_merge_base(git_root) or "HEAD"


def parse_added_lines(diff_output: str) -> frozenset[int]:
    """
    Collect the new-side line numbers of every hunk in a unified diff with no context lines.
    """
    line_numbers: set[int] = set()
    for hunk_match in HUNK_HEADER_PATTERN.finditer(diff_output):
        start_line = int(hunk_match.group(1))
        line_count = int(hunk_match.group(2) or 1)
        end_line = start_line + line_count
        line_numbers.update(range(start_line, end_line))
    return frozenset(line_numbers)


def get_changed_lines(path: Path, requested_base: str) -> ChangedLines:
    """
    Find the lines of a file that the branch added or changed since its base.

    :param path: The file being checked.
    :param requested_base: A git ref, or `auto` (see resolve_base).
    :return: The changed lines; a file outside git, or one that didn't exist at the base, counts as new.
    """
    git_root = find_git_root(path)
    base = resolve_base(path, requested_base)
    if git_root is None or base is None:
        return ChangedLines(True, frozenset())

    resolved_root = git_root.resolve()
    resolved_path = path.resolve()
    relative_path = resolved_path.relative_to(resolved_root)
    posix_path = relative_path.as_posix()
    existed_at_base = run_git(
        [
            "cat-file",
            "-e",
            f"{base}:{posix_path}",
        ],
        git_root,
    )
    if existed_at_base is None or existed_at_base.returncode != 0:
        return ChangedLines(True, frozenset())

    diff = run_git(
        [
            "diff",
            "-U0",
            "--no-color",
            "--no-ext-diff",
            base,
            "--",
            posix_path,
        ],
        git_root,
    )
    if diff is None or diff.returncode != 0:
        return ChangedLines(True, frozenset())

    return ChangedLines(False, parse_added_lines(diff.stdout))
