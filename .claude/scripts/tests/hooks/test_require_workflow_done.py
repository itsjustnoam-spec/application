from collections.abc import Callable
from pathlib import Path

import pytest

APPROVED_SPEC = "# Spec: Sites\n\nStatus: APPROVED (17/10/26)\n"
DRAFT_SPEC = "# Spec: Sites\n\nStatus: DRAFT\n"


@pytest.fixture
def make_feature(tmp_path: Path) -> Callable[..., Path]:
    def _make(spec: str, progress: str | None) -> Path:
        (tmp_path / ".git").mkdir()
        features_directory = tmp_path / "docs" / "features"
        feature_directory = features_directory / "sites"
        feature_directory.mkdir(parents=True)
        (features_directory / ".active").write_text("sites\n", encoding="utf-8")
        (feature_directory / "spec.md").write_text(spec, encoding="utf-8")
        if progress is not None:
            (feature_directory / "progress.md").write_text(progress, encoding="utf-8")

        return tmp_path

    return _make


def stop_payload(project: Path) -> dict[str, object]:
    return {"hook_event_name": "Stop", "cwd": str(project), "stop_hook_active": False}


def test_require_workflow_done_no_active_feature_allows_stop(
    tmp_path: Path,
    run_hook: Callable[..., object],
):
    completed = run_hook("require_workflow_done.py", stop_payload(tmp_path))

    assert completed.returncode == 0


def test_require_workflow_done_before_approval_allows_stop(
    make_feature: Callable[..., Path],
    run_hook: Callable[..., object],
):
    project = make_feature(DRAFT_SPEC, None)

    completed = run_hook("require_workflow_done.py", stop_payload(project))

    assert completed.returncode == 0


def test_require_workflow_done_unfinished_phase_blocks_stop(
    make_feature: Callable[..., Path],
    run_hook: Callable[..., object],
):
    project = make_feature(APPROVED_SPEC, "Phase: REVIEW-ROUND-1\n")

    completed = run_hook("require_workflow_done.py", stop_payload(project))

    assert completed.returncode == 2
    assert "Phase: REVIEW-ROUND-1" in completed.stderr


@pytest.mark.parametrize("progress", [
    "Phase: DONE\n",
    "Phase: FIX-ROUND-2\nBLOCKED: the test database is down\n",
])
def test_require_workflow_done_done_or_blocked_allows_stop(
    make_feature: Callable[..., Path],
    run_hook: Callable[..., object],
    progress: str,
):
    project = make_feature(APPROVED_SPEC, progress)

    completed = run_hook("require_workflow_done.py", stop_payload(project))

    assert completed.returncode == 0


def test_require_workflow_done_no_progress_allows_stop_after_three_blocks(
    make_feature: Callable[..., Path],
    run_hook: Callable[..., object],
):
    project = make_feature(APPROVED_SPEC, "Phase: TESTS\n")
    payload = stop_payload(project)
    run_hook("require_workflow_done.py", payload)
    run_hook("require_workflow_done.py", payload)
    run_hook("require_workflow_done.py", payload)

    completed = run_hook("require_workflow_done.py", payload)

    assert completed.returncode == 0


def test_require_workflow_done_progress_resets_the_block_count(
    make_feature: Callable[..., Path],
    run_hook: Callable[..., object],
):
    project = make_feature(APPROVED_SPEC, "Phase: TESTS\n")
    payload = stop_payload(project)
    progress_path = project / "docs" / "features" / "sites" / "progress.md"
    run_hook("require_workflow_done.py", payload)
    run_hook("require_workflow_done.py", payload)
    run_hook("require_workflow_done.py", payload)
    progress_path.write_text("Phase: REVIEW-ROUND-1\n", encoding="utf-8")

    completed = run_hook("require_workflow_done.py", payload)

    assert completed.returncode == 2
