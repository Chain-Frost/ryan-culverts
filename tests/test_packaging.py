from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from scripts import build_package


def test_calendar_version_increments_same_day() -> None:
    assert build_package.next_calendar_version("26.9.9.1", dt.date(2026, 9, 9)) == "26.9.9.2"


def test_calendar_version_resets_revision_on_new_day() -> None:
    assert build_package.next_calendar_version("26.9.9.7", dt.date(2026, 9, 10)) == "26.9.10.1"


def test_calendar_version_rejects_clock_before_current_release() -> None:
    with pytest.raises(ValueError, match="refusing a version regression"):
        build_package.next_calendar_version("26.9.10.1", dt.date(2026, 9, 9))


@pytest.mark.parametrize("version", ["26.09.09.1", "2026.9.9.1", "26.2.30.1", "26.9.9.0"])
def test_calendar_version_rejects_invalid_or_non_normalized_values(version: str) -> None:
    with pytest.raises(ValueError):
        build_package.parse_calendar_version(version)


def test_explicit_version_must_move_forward() -> None:
    assert build_package.validate_explicit_version("26.9.9.1", "26.9.9.4") == "26.9.9.4"
    with pytest.raises(ValueError, match="must be newer"):
        build_package.validate_explicit_version("26.9.9.1", "26.9.9.1")


def test_replace_project_version_changes_only_project_section(tmp_path: Path) -> None:
    project = tmp_path / "pyproject.toml"
    project.write_text(
        '[project]\nname = "example"\nversion = "26.9.9.1"\n\n[tool.example]\nversion = "keep"\n',
        encoding="utf-8",
    )

    previous = build_package.replace_project_version(project, "26.9.9.2")

    assert previous == "26.9.9.1"
    assert 'version = "26.9.9.2"' in project.read_text(encoding="utf-8")
    assert 'version = "keep"' in project.read_text(encoding="utf-8")


def test_failed_build_restores_version_and_retains_wheel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "pyproject.toml"
    original = '[project]\nname = "ryan-culverts"\nversion = "26.9.9.1"\n'
    project.write_text(original, encoding="utf-8")
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    previous_wheel = dist_dir / "ryan_culverts-26.9.9.1-py3-none-any.whl"
    previous_wheel.write_bytes(b"previous wheel")
    monkeypatch.setattr(build_package, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build_package, "DIST_DIR", dist_dir)

    def fail_build(_output_dir: Path) -> int:
        return 17

    monkeypatch.setattr(build_package, "_run_build", fail_build)

    status = build_package.main([], today=dt.date(2026, 9, 9))

    assert status == 17
    assert project.read_text(encoding="utf-8") == original
    assert previous_wheel.read_bytes() == b"previous wheel"


def test_non_increasing_cli_version_fails_without_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "pyproject.toml"
    original = '[project]\nname = "ryan-culverts"\nversion = "26.9.9.2"\n'
    project.write_text(original, encoding="utf-8")
    monkeypatch.setattr(build_package, "PROJECT_ROOT", tmp_path)

    status = build_package.main(["--version", "26.9.9.2"])

    assert status == 2
    assert project.read_text(encoding="utf-8") == original


def test_failed_verification_restores_version_and_retains_wheel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "pyproject.toml"
    original = '[project]\nname = "ryan-culverts"\nversion = "26.9.9.1"\n'
    project.write_text(original, encoding="utf-8")
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    previous_wheel = dist_dir / "ryan_culverts-26.9.9.1-py3-none-any.whl"
    previous_wheel.write_bytes(b"previous wheel")
    monkeypatch.setattr(build_package, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build_package, "DIST_DIR", dist_dir)

    def successful_build(output_dir: Path) -> int:
        (output_dir / "ryan_culverts-26.9.9.2-py3-none-any.whl").write_bytes(b"candidate")
        return 0

    def failed_verification(_wheel: Path) -> int:
        return 19

    monkeypatch.setattr(build_package, "_run_build", successful_build)
    monkeypatch.setattr(build_package, "_run_verification", failed_verification)

    status = build_package.main([], today=dt.date(2026, 9, 9))

    assert status == 19
    assert project.read_text(encoding="utf-8") == original
    assert previous_wheel.read_bytes() == b"previous wheel"
    assert list(dist_dir.glob("ryan_culverts-26.9.9.2-*.whl")) == []


def test_promote_wheel_keeps_only_new_project_distribution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "ryan_culverts-26.9.9.1-py3-none-any.whl").write_bytes(b"old")
    (dist_dir / "ryan_culverts-26.9.9.1.tar.gz").write_bytes(b"old source")
    unrelated = dist_dir / "other_package-1-py3-none-any.whl"
    unrelated.write_bytes(b"unrelated")
    staged = tmp_path / "ryan_culverts-26.9.9.2-py3-none-any.whl"
    staged.write_bytes(b"new")
    monkeypatch.setattr(build_package, "DIST_DIR", dist_dir)

    promoted = build_package.promote_wheel(staged)

    assert promoted.read_bytes() == b"new"
    assert [path.name for path in dist_dir.glob("ryan_culverts-*")] == [promoted.name]
    assert unrelated.read_bytes() == b"unrelated"
