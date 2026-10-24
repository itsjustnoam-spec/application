from collections.abc import Callable
from pathlib import Path

import pytest

from mypy_strict import filter_mypy_output, find_untyped_none_returning_names

SOURCE = '''def save(x: int):
    print(x)


def compute(x: int):
    return x + 1


def stream(x: int):
    yield x


def bare():
    print(1)
'''


def test_filter_mypy_output_none_returning_function_drops_error(write_python_file: Callable[..., Path]):
    path = write_python_file(SOURCE)
    output_lines = [f"{path}:1: error: Function is missing a return type annotation  [no-untyped-def]"]

    kept_lines = filter_mypy_output(output_lines)

    assert kept_lines == []


def test_filter_mypy_output_value_returning_function_keeps_error(write_python_file: Callable[..., Path]):
    path = write_python_file(SOURCE)
    output_lines = [f"{path}:5: error: Function is missing a return type annotation  [no-untyped-def]"]

    kept_lines = filter_mypy_output(output_lines)

    assert kept_lines == output_lines


def test_filter_mypy_output_generator_function_keeps_error(write_python_file: Callable[..., Path]):
    path = write_python_file(SOURCE)
    output_lines = [f"{path}:9: error: Function is missing a return type annotation  [no-untyped-def]"]

    kept_lines = filter_mypy_output(output_lines)

    assert kept_lines == output_lines


def test_filter_mypy_output_suppressed_error_drops_its_note(write_python_file: Callable[..., Path]):
    path = write_python_file(SOURCE)
    output_lines = [
        f"{path}:13: error: Function is missing a return type annotation  [no-untyped-def]",
        f'{path}:13: note: Use "-> None" if function does not return a value',
    ]

    kept_lines = filter_mypy_output(output_lines)

    assert kept_lines == []


def test_filter_mypy_output_other_errors_are_kept(write_python_file: Callable[..., Path]):
    path = write_python_file(SOURCE)
    output_lines = [f"{path}:2: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]"]

    kept_lines = filter_mypy_output(output_lines)

    assert kept_lines == output_lines


def test_filter_mypy_output_untyped_call_to_none_returning_function_is_dropped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    (tmp_path / "jobs.py").write_text(
        "def run_cleanup():\n    print(1)\n\n\ndef run_report() -> int:\n    return 1\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    output_lines = [
        'jobs.py:9: error: Call to untyped function "run_cleanup" in typed context  [no-untyped-call]',
    ]

    kept_lines = filter_mypy_output(output_lines)

    assert kept_lines == []


def test_filter_mypy_output_untyped_call_to_unknown_function_is_kept(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)
    output_lines = [
        'jobs.py:9: error: Call to untyped function "legacy_helper" in typed context  [no-untyped-call]',
    ]

    kept_lines = filter_mypy_output(output_lines)

    assert kept_lines == output_lines


def test_find_untyped_none_returning_names_works_inside_a_worktree(tmp_path: Path):
    service = tmp_path / ".claude" / "worktrees" / "BTRC-1-x" / "service"
    service.mkdir(parents=True)
    (service / "helpers.py").write_text("def helper():\n    print(1)\n", encoding="utf-8")

    function_names = find_untyped_none_returning_names(service)

    assert function_names == {"helper"}
