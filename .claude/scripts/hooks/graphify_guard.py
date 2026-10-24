"""
PreToolUse hook: forwards search and file-read calls to graphify's own guard, which reminds Claude to query the graph first.

:author: Noam
:date: 24/10/26
"""
# ----- Imports ----- #

import shutil
import subprocess
import sys

# ----- Consts ----- #

GUARD_TIMEOUT_SECONDS = 8
GUARD_KINDS = frozenset(
    {
        "search",
        "read",
    },
)

# ----- Functions ----- #


def main() -> int:
    """
    Run `graphify hook-guard <kind>` with the hook payload when graphify is installed; never block the tool.
    """
    graphify = shutil.which("graphify")
    kind = sys.argv[1] if len(sys.argv) > 1 else ""
    if graphify is None or kind not in GUARD_KINDS:
        return 0

    payload = sys.stdin.buffer.read()
    try:
        completed = subprocess.run(
            [
                graphify,
                "hook-guard",
                kind,
            ],
            input=payload,
            check=False,
            capture_output=True,
            timeout=GUARD_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0
    sys.stdout.buffer.write(completed.stdout)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
