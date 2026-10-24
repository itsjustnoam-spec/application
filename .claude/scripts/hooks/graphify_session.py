"""
SessionStart hook: brings the project's graphify knowledge graph up to date and tells Claude to use it.

:author: Noam
:date: 24/10/26
"""
# ----- Imports ----- #

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ----- Consts ----- #

GRAPH_FILE = Path("graphify-out") / "graph.json"
GIT_TIMEOUT_SECONDS = 10
GRAPH_READY_CONTEXT = (
    "This project has a graphify knowledge graph in graphify-out/ (code only), updating in the background now. "
    "Before your first grep, search, or source-file read for a codebase question, run "
    "`graphify query \"<question>\"`; use `graphify path \"<A>\" \"<B>\"` for how two things connect, "
    "`graphify explain \"<name>\"` for one function or class, and `graphify affected \"<name>\"` for what a change "
    "impacts. Read files only for the lines the graph pointed to. Put this rule in every subagent prompt that "
    "explores code. After changing code, run `graphify update .`."
)
GRAPH_BUILDING_CONTEXT = (
    "graphify is installed but this project had no graph yet: it is being built in the background into "
    "graphify-out/ (code only). Once graphify-out/graph.json exists, run `graphify query \"<question>\"` before "
    "grepping or reading source files."
)
WINDOWS_DETACHED_PROCESS = 0x00000008
WINDOWS_NEW_PROCESS_GROUP = 0x00000200
DETACHED_FLAGS = {
    "nt": WINDOWS_DETACHED_PROCESS | WINDOWS_NEW_PROCESS_GROUP,
    "posix": 0,
}

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


def run_git(arguments: list[str], working_directory: Path) -> str | None:
    """
    Run a git command and return its trimmed output, or None when it fails.
    """
    try:
        completed = subprocess.run(
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
    if completed.returncode != 0:
        return None

    return completed.stdout.strip()


def find_checkout_root(payload: dict[str, object]) -> Path | None:
    """
    Find the root of the checkout (main checkout or worktree) the session runs in.

    :param payload: The hook payload, whose `cwd` is the session's directory.
    :return: The checkout root, or None outside a git repository.
    """
    raw_directory = payload.get("cwd")
    directory = Path.cwd()
    if isinstance(raw_directory, str):
        directory = Path(raw_directory)

    top_level = run_git(
        [
            "rev-parse",
            "--show-toplevel",
        ],
        directory,
    )
    if top_level is None:
        return None

    return Path(top_level)


def find_log_path(checkout_root: Path) -> Path:
    """
    Choose where the background update writes its output, outside the tracked files.

    :param checkout_root: The checkout root.
    :return: A log file inside this checkout's git directory.
    """
    git_directory = run_git(
        [
            "rev-parse",
            "--absolute-git-dir",
        ],
        checkout_root,
    )
    if git_directory is None:
        return checkout_root / "graphify-update.log"

    return Path(git_directory) / "graphify-update.log"


def start_background_update(graphify: str, checkout_root: Path):
    """
    Start `graphify update .` (code only, no LLM) in the background, so the session doesn't wait for it.

    :param graphify: The graphify executable.
    :param checkout_root: The checkout whose graph is updated.
    """
    environment = {
        **os.environ,
        "GRAPHIFY_BACKEND": "none",
    }
    log_path = find_log_path(checkout_root)
    with log_path.open("w", encoding="utf-8") as log_file:
        subprocess.Popen(
            [
                graphify,
                "update",
                ".",
            ],
            cwd=checkout_root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=os.name == "posix",
            creationflags=DETACHED_FLAGS.get(os.name, 0),
        )


def main() -> int:
    """
    Update the graph of the session's checkout and add the graphify rules to Claude's context.
    """
    graphify = shutil.which("graphify")
    if graphify is None:
        return 0

    checkout_root = find_checkout_root(read_hook_payload())
    if checkout_root is None:
        return 0

    has_graph = (checkout_root / GRAPH_FILE).is_file()
    start_background_update(graphify, checkout_root)
    context = GRAPH_READY_CONTEXT if has_graph else GRAPH_BUILDING_CONTEXT
    sys.stdout.buffer.write((context + "\n").encode("utf-8"))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
