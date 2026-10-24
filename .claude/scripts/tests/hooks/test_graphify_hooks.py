import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest


def make_fake_graphify(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        fake = directory / "graphify.cmd"
        fake.write_text("@echo off\r\necho fake graphify %*\r\n", encoding="utf-8")
        return fake

    fake = directory / "graphify"
    fake.write_text("#!/bin/sh\necho fake graphify \"$@\"\n", encoding="utf-8")
    fake.chmod(0o755)
    return fake


def make_repository(tmp_path: Path, with_graph: bool) -> Path:
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True, stdin=subprocess.DEVNULL, capture_output=True)
    if with_graph:
        (repository / "graphify-out").mkdir()
        (repository / "graphify-out" / "graph.json").write_text("{}", encoding="utf-8")

    return repository


def path_with(directory: Path | None) -> str:
    python_directory = str(Path(sys.executable).parent)
    entries = [python_directory] if directory is None else [str(directory), python_directory]
    system_root = os.environ.get("SystemRoot")
    if system_root is not None:
        entries.append(str(Path(system_root) / "System32"))

    git = subprocess.run(
        ["git", "--exec-path"],
        capture_output=True,
        text=True,
        check=True,
        stdin=subprocess.DEVNULL,
    )
    entries.append(str(Path(git.stdout.strip()).parent.parent.parent / "cmd"))
    entries.append("/usr/bin")
    return os.pathsep.join(entries)


def test_graphify_session_without_graphify_does_nothing(tmp_path: Path, run_hook: Callable[..., subprocess.CompletedProcess[str]]):
    repository = make_repository(tmp_path, with_graph=True)

    completed = run_hook(
        "graphify_session.py",
        {"hook_event_name": "SessionStart", "cwd": str(repository)},
        {"PATH": path_with(None)},
    )

    assert completed.returncode == 0
    assert completed.stdout == ""


def test_graphify_session_with_a_graph_starts_an_update_and_adds_the_rules(
    tmp_path: Path,
    run_hook: Callable[..., subprocess.CompletedProcess[str]],
):
    repository = make_repository(tmp_path, with_graph=True)
    fake_directory = tmp_path / "bin"
    make_fake_graphify(fake_directory)

    completed = run_hook(
        "graphify_session.py",
        {"hook_event_name": "SessionStart", "cwd": str(repository)},
        {"PATH": path_with(fake_directory)},
    )

    assert completed.returncode == 0
    assert "graphify query" in completed.stdout
    log_path = repository / ".git" / "graphify-update.log"
    for _ in range(50):
        if log_path.is_file() and "fake graphify update ." in log_path.read_text(encoding="utf-8"):
            break

        time.sleep(0.1)
    assert "fake graphify update ." in log_path.read_text(encoding="utf-8")


def test_graphify_session_without_a_graph_says_it_is_being_built(
    tmp_path: Path,
    run_hook: Callable[..., subprocess.CompletedProcess[str]],
):
    repository = make_repository(tmp_path, with_graph=False)
    fake_directory = tmp_path / "bin"
    make_fake_graphify(fake_directory)

    completed = run_hook(
        "graphify_session.py",
        {"hook_event_name": "SessionStart", "cwd": str(repository)},
        {"PATH": path_with(fake_directory)},
    )

    assert "being built" in completed.stdout


@pytest.mark.parametrize("kind", ["search", "unknown"])
def test_graphify_guard_without_graphify_allows_silently(
    kind: str,
    tmp_path: Path,
):
    hook = Path(__file__).resolve().parents[2] / "hooks" / "graphify_guard.py"

    completed = subprocess.run(
        [sys.executable, str(hook), kind],
        input='{"tool_name": "Grep", "tool_input": {"pattern": "x"}}',
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": path_with(None)},
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
