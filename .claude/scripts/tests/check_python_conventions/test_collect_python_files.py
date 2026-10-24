from pathlib import Path

from check_python_conventions import collect_python_files


def test_collect_python_files_skips_virtualenvs_and_caches(tmp_path: Path):
    service = tmp_path / "service"
    for relative_path in ("app/site.py", ".venv/lib/site.py", "node_modules/x/tool.py", "app/__pycache__/site.py"):
        file_path = service / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("", encoding="utf-8")

    python_files = collect_python_files([str(service)])

    assert python_files == [service / "app" / "site.py"]


def test_collect_python_files_inside_a_folder_named_like_a_skipped_one_still_finds_files(tmp_path: Path):
    service = tmp_path / "venv" / "service"
    file_path = service / "app" / "site.py"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("", encoding="utf-8")

    python_files = collect_python_files([str(service)])

    assert python_files == [file_path]
