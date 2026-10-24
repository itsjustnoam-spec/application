from pathlib import Path

import pytest

from changed_lines import read_feature_base

SHA = "0123456789abcdef0123456789abcdef01234567"


@pytest.mark.parametrize("base_line", [
    f"Base: {SHA}",
    f"Base: `{SHA}`",
    f"Base: {SHA} (merge base of origin/main)",
])
def test_read_feature_base_reads_the_sha_after_base(tmp_path: Path, base_line: str):
    features_directory = tmp_path / "docs" / "features"
    (features_directory / "BTRC-1-x").mkdir(parents=True)
    (features_directory / ".active").write_text("BTRC-1-x\n", encoding="utf-8")
    (features_directory / "BTRC-1-x" / "progress.md").write_text(f"Phase: IMPLEMENT\n\n{base_line}\n", encoding="utf-8")

    base = read_feature_base(tmp_path)

    assert base == SHA


def test_read_feature_base_placeholder_is_ignored(tmp_path: Path):
    features_directory = tmp_path / "docs" / "features"
    (features_directory / "BTRC-1-x").mkdir(parents=True)
    (features_directory / ".active").write_text("BTRC-1-x\n", encoding="utf-8")
    (features_directory / "BTRC-1-x" / "progress.md").write_text("Base: <commit SHA>\n", encoding="utf-8")

    base = read_feature_base(tmp_path)

    assert base is None
