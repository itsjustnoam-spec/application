from collections.abc import Callable
from pathlib import Path

COMPLIANT_SOURCE = '"""\nEntities.\n\n:author: Noam\n:date: 16/10/26\n"""\n# ----- Imports ----- #\n\nimport os\n'
VIOLATING_SOURCE = COMPLIANT_SOURCE + "\n# ----- Functions ----- #\n\n\ndef save_entity(entity) -> None:\n    print(os.sep, entity)\n"


def test_post_edit_checks_compliant_python_file_allows(write_python_file: Callable[..., Path], run_hook: Callable[..., object]):
    path = write_python_file(COMPLIANT_SOURCE)

    completed = run_hook("post_edit_checks.py", {"tool_name": "Write", "tool_input": {"file_path": str(path)}})

    assert completed.returncode == 0


def test_post_edit_checks_violating_python_file_blocks_with_rule_ids(
    write_python_file: Callable[..., Path],
    run_hook: Callable[..., object],
):
    path = write_python_file(VIOLATING_SOURCE)

    completed = run_hook("post_edit_checks.py", {"tool_name": "Edit", "tool_input": {"file_path": str(path)}})

    assert completed.returncode == 2
    assert "PY-01" in completed.stderr
    assert "PY-02" in completed.stderr


def test_post_edit_checks_non_code_file_allows(tmp_path: Path, run_hook: Callable[..., object]):
    path = tmp_path / "notes.md"
    path.write_text("# Notes\n", encoding="utf-8")

    completed = run_hook("post_edit_checks.py", {"tool_name": "Write", "tool_input": {"file_path": str(path)}})

    assert completed.returncode == 0


def test_post_edit_checks_missing_file_path_allows(run_hook: Callable[..., object]):
    completed = run_hook("post_edit_checks.py", {"tool_name": "Write", "tool_input": {}})

    assert completed.returncode == 0


def test_post_edit_checks_file_outside_project_is_skipped(
    tmp_path: Path,
    write_python_file: Callable[..., Path],
    run_hook: Callable[..., object],
):
    path = write_python_file(VIOLATING_SOURCE)
    project_directory = tmp_path / "project"
    project_directory.mkdir()
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(path)}}

    completed = run_hook(
        "post_edit_checks.py",
        payload,
        {"CLAUDE_PROJECT_DIR": str(project_directory)},
    )

    assert completed.returncode == 0
