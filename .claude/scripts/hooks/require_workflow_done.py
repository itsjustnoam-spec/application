"""
Stop hook: keeps an approved /feature run going until progress.md says Phase: DONE.

:author: Noam
:date: 17/10/26
"""
# ----- Imports ----- #

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guard_test_plan import find_active_test_plan

# ----- Consts ----- #

BLOCKING_EXIT_CODE = 2
MAX_BLOCKS_WITHOUT_PROGRESS = 3
GIT_TIMEOUT_SECONDS = 10
DONE_PHASE = "DONE"
UNKNOWN_PHASE = "unknown"
APPROVED_MARKER = "Status: APPROVED"
STATE_FILE_NAME = ".stop-hook-state.json"
PHASE_PATTERN = re.compile(r"^Phase:\s*(\S+)", re.MULTILINE)
BLOCKED_PATTERN = re.compile(r"^BLOCKED:\s*\S", re.MULTILINE)
CONTINUE_MESSAGE = (
    "The /feature workflow for '{slug}' isn't finished: progress.md says "
    "'Phase: {phase}'. Don't stop and don't write a final report yet. "
    "Continue with the next step of ~/.claude/commands/feature.md "
    "(triage, fixes, the next review round, then summary.md and "
    "'Phase: DONE'). Only if you are genuinely blocked, write "
    "'BLOCKED: <reason>' in progress.md, then stop."
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


def read_text(path: Path) -> str:
    """
    Read a text file, or return an empty string when it doesn't exist.
    """
    if not path.is_file():
        return ""

    return path.read_text(encoding="utf-8", errors="replace")


def run_git(arguments: list[str], working_directory: Path) -> str:
    """
    Run a read-only git command and return its output.
    """
    try:
        completed = subprocess.run(
            [
                "git",
                *arguments,
            ],
            cwd=working_directory,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""

    return completed.stdout


def build_progress_fingerprint(
    feature_directory: Path,
    working_directory: Path,
) -> str:
    """
    Summarize the feature files and the git state into one hash.

    :param feature_directory: The active feature's folder.
    :param working_directory: The checkout the session works in.
    :return: A hash that changes whenever the workflow makes progress.
    """
    digest = hashlib.sha256()
    feature_files = sorted(
        path
        for path in feature_directory.rglob("*")
        if path.is_file() and path.name != STATE_FILE_NAME
    )
    for feature_file in feature_files:
        file_stat = feature_file.stat()
        file_marker = f"{feature_file}:{file_stat.st_size}:{file_stat.st_mtime_ns}"
        digest.update(file_marker.encode("utf-8"))

    git_head = run_git(
        [
            "rev-parse",
            "HEAD",
        ],
        working_directory,
    )
    git_status = run_git(
        [
            "status",
            "--porcelain",
        ],
        working_directory,
    )
    digest.update(git_head.encode("utf-8"))
    digest.update(git_status.encode("utf-8"))
    return digest.hexdigest()


def count_blocks_without_progress(state_path: Path, fingerprint: str) -> int:
    """
    Count consecutive blocks with no progress, and record this block.

    :param state_path: The file that remembers the previous block.
    :param fingerprint: The current progress fingerprint.
    :return: How many blocks in a row (including this one) saw no progress.
    """
    previous_state: dict[str, object] = {}
    if state_path.is_file():
        try:
            previous_state = json.loads(read_text(state_path))
        except json.JSONDecodeError:
            previous_state = {}

    previous_blocks = previous_state.get("blocks")
    is_same_state = previous_state.get("fingerprint") == fingerprint
    blocks = 1
    if is_same_state and isinstance(previous_blocks, int):
        blocks = previous_blocks + 1

    state = {"fingerprint": fingerprint, "blocks": blocks}
    state_path.write_text(json.dumps(state), encoding="utf-8")
    return blocks


def block(message: str) -> int:
    """
    Send the reason back to Claude and block it from stopping.
    """
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    sys.stderr.flush()
    return BLOCKING_EXIT_CODE


def main() -> int:
    """
    Decide whether the session may stop.
    """
    payload = read_hook_payload()
    working_directory = Path(str(payload.get("cwd", "."))).resolve()
    active_test_plan = find_active_test_plan(working_directory)
    if active_test_plan is None:
        return 0

    feature_slug, test_plan_path = active_test_plan
    feature_directory = test_plan_path.parent
    spec = read_text(feature_directory / "spec.md")
    if APPROVED_MARKER not in spec:
        return 0

    progress = read_text(feature_directory / "progress.md")
    phase_match = PHASE_PATTERN.search(progress)
    phase = UNKNOWN_PHASE
    if phase_match is not None:
        phase = phase_match.group(1)

    is_blocked = BLOCKED_PATTERN.search(progress) is not None
    if phase == DONE_PHASE or is_blocked:
        return 0

    fingerprint = build_progress_fingerprint(
        feature_directory,
        working_directory,
    )
    state_path = feature_directory / STATE_FILE_NAME
    blocks = count_blocks_without_progress(state_path, fingerprint)
    if blocks > MAX_BLOCKS_WITHOUT_PROGRESS:
        return 0

    message = CONTINUE_MESSAGE.format(slug=feature_slug, phase=phase)
    return block(message)


if __name__ == "__main__":
    sys.exit(main())
