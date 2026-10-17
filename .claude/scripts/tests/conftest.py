import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIRECTORY))


@pytest.fixture
def write_python_file(tmp_path: Path) -> Callable[[str, str], Path]:
    def _write(source: str, file_name: str = "module.py") -> Path:
        path = tmp_path / "app" / file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def run_hook() -> Callable[..., subprocess.CompletedProcess[str]]:
    def _run(
        hook_name: str,
        payload: dict[str, object],
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = {
            name: value
            for name, value in os.environ.items()
            if name != "CLAUDE_PROJECT_DIR"
        }
        environment.update(extra_environment or {})
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIRECTORY / "hooks" / hook_name)],
            input=json.dumps(payload),
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=60,
        )

    return _run
