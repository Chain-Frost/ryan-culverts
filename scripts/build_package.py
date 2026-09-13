"""Increment the calendar version and transactionally build one verified wheel."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import cast

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DIST_DIR: Path = PROJECT_ROOT / "dist"
DISTRIBUTION_PREFIX: str = "ryan_culverts-"
CALENDAR_VERSION: re.Pattern[str] = re.compile(
    r"^(?P<year>\d{2})\.(?P<month>\d{1,2})\.(?P<day>\d{1,2})\.(?P<revision>[1-9]\d*)$"
)
SECTION_HEADER: re.Pattern[str] = re.compile(r"(?m)^\[(?P<name>[^]]+)]\s*$")
VERSION_LINE: re.Pattern[str] = re.compile(
    r'(?m)^(?P<prefix>version[\t ]*=[\t ]*")(?P<version>[^"]+)(?P<suffix>")[\t ]*$'
)
PACKAGE_VERSION_LINE: re.Pattern[str] = re.compile(
    r'(?m)^(?P<prefix>__version__[\t ]*=[\t ]*")(?P<version>[^"]+)(?P<suffix>")[\t ]*$'
)


def _package_version_path() -> Path:
    """Return the package-local version marker below the current project root."""
    return PROJECT_ROOT / "src" / "culvert_solver" / "_version.py"


def _project_version() -> str:
    """Read the single authoritative package version from ``pyproject.toml``."""
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        data: dict[str, object] = tomllib.load(pyproject_file)
    project_data = data.get("project")
    if not isinstance(project_data, dict):
        msg = "pyproject.toml has no [project] table."
        raise ValueError(msg)
    project = cast("dict[str, object]", project_data)
    version = project.get("version")
    if not isinstance(version, str) or not version:
        msg = "pyproject.toml has no nonempty project version."
        raise ValueError(msg)
    return version


def _package_version(version_path: Path) -> str:
    """Read the package-local version marker or fail explicitly."""
    match = PACKAGE_VERSION_LINE.search(version_path.read_text(encoding="utf-8"))
    if match is None:
        msg = f"{version_path} has no package-local __version__ assignment"
        raise ValueError(msg)
    return match.group("version")


def _validate_version_sources(project_version: str, package_version: str) -> None:
    """Require the generated package marker to match authoritative metadata."""
    if package_version != project_version:
        msg = f"Package-local version {package_version!r} does not match pyproject.toml version {project_version!r}"
        raise ValueError(msg)


def parse_calendar_version(version: str) -> tuple[dt.date, int]:
    """Parse one normalized ``yy.m.d.vv`` version or fail explicitly."""
    match = CALENDAR_VERSION.fullmatch(version)
    if match is None:
        msg = f"Version must use normalized yy.m.d.vv form: {version!r}"
        raise ValueError(msg)
    release_date = dt.date(
        2000 + int(match.group("year")),
        int(match.group("month")),
        int(match.group("day")),
    )
    revision = int(match.group("revision"))
    normalized = f"{release_date.year % 100}.{release_date.month}.{release_date.day}.{revision}"
    if version != normalized:
        msg = f"Version must be normalized as {normalized!r}, not {version!r}"
        raise ValueError(msg)
    return release_date, revision


def next_calendar_version(current_version: str, today: dt.date) -> str:
    """Return today's next calendar version from the current project version."""
    current_date, current_revision = parse_calendar_version(current_version)
    if today < current_date:
        msg = (
            f"Local date {today.isoformat()} precedes current release date "
            f"{current_date.isoformat()}; refusing a version regression"
        )
        raise ValueError(msg)
    revision = current_revision + 1 if current_date == today else 1
    return f"{today.year % 100}.{today.month}.{today.day}.{revision}"


def validate_explicit_version(current_version: str, requested_version: str) -> str:
    """Validate that an explicit calendar version moves the project forward."""
    current = parse_calendar_version(current_version)
    requested = parse_calendar_version(requested_version)
    if requested <= current:
        msg = f"Explicit version {requested_version!r} must be newer than {current_version!r}"
        raise ValueError(msg)
    return requested_version


def replace_project_version(project_path: Path, new_version: str) -> str:
    """Replace only the version in the TOML ``[project]`` section."""
    content = project_path.read_text(encoding="utf-8")
    headers = list(SECTION_HEADER.finditer(content))
    for index, header in enumerate(headers):
        if header.group("name") != "project":
            continue
        section_end = headers[index + 1].start() if index + 1 < len(headers) else len(content)
        section = content[header.end() : section_end]
        match = VERSION_LINE.search(section)
        if match is None:
            break
        updated_section = VERSION_LINE.sub(rf"\g<prefix>{new_version}\g<suffix>", section, count=1)
        project_path.write_text(
            f"{content[: header.end()]}{updated_section}{content[section_end:]}",
            encoding="utf-8",
            newline="\n",
        )
        return match.group("version")
    msg = "pyproject.toml [project] has no version field"
    raise ValueError(msg)


def replace_package_version(version_path: Path, new_version: str) -> str:
    """Replace the sole package-local version assignment."""
    content = version_path.read_text(encoding="utf-8")
    matches = tuple(PACKAGE_VERSION_LINE.finditer(content))
    if len(matches) != 1:
        msg = f"{version_path} must contain exactly one package-local __version__ assignment"
        raise ValueError(msg)
    match = matches[0]
    version_path.write_text(
        PACKAGE_VERSION_LINE.sub(rf"\g<prefix>{new_version}\g<suffix>", content, count=1),
        encoding="utf-8",
        newline="\n",
    )
    return match.group("version")


def _restore_version_sources(
    project_path: Path,
    project_content: str,
    version_path: Path,
    version_content: str,
) -> None:
    """Restore both authoritative and generated version sources after failure."""
    project_path.write_text(project_content, encoding="utf-8", newline="\n")
    version_path.write_text(version_content, encoding="utf-8", newline="\n")


def _run_build(output_dir: Path) -> int:
    """Build a wheel into temporary storage and return the frontend exit status."""
    command = [sys.executable, "-m", "build", "--wheel", "--outdir", str(output_dir)]
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


def _run_verification(wheel: Path) -> int:
    """Verify a staged wheel without importing from the source checkout."""
    command = [sys.executable, str(PROJECT_ROOT / "scripts" / "verify_wheel.py"), str(wheel)]
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


def promote_wheel(wheel: Path) -> Path:
    """Promote a verified wheel, then remove older project distributions."""
    DIST_DIR.mkdir(exist_ok=True)
    destination = DIST_DIR / wheel.name
    incoming = DIST_DIR / f".{wheel.name}.incoming"
    if incoming.exists():
        incoming.unlink()
    try:
        shutil.copy2(wheel, incoming)
        incoming.replace(destination)
    finally:
        if incoming.exists():
            incoming.unlink()
    for pattern in (f"{DISTRIBUTION_PREFIX}*.whl", f"{DISTRIBUTION_PREFIX}*.tar.gz"):
        for artifact in DIST_DIR.glob(pattern):
            if artifact != destination and artifact.is_file() and artifact.parent.resolve() == DIST_DIR.resolve():
                artifact.unlink()
    return destination


def main(argv: list[str] | None = None, *, today: dt.date | None = None) -> int:
    """Select a version, stage and verify its wheel, then promote it."""
    parser = argparse.ArgumentParser(description=__doc__)
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument(
        "--version", help="Use this explicit newer yy.m.d.vv version instead of auto-incrementing."
    )
    version_group.add_argument(
        "--no-bump",
        action="store_true",
        help="Build the version already declared in pyproject.toml (intended for CI).",
    )
    args = parser.parse_args(argv)

    project_path = PROJECT_ROOT / "pyproject.toml"
    package_version_path = _package_version_path()
    try:
        current_version = _project_version()
        package_version = _package_version(package_version_path)
        _validate_version_sources(current_version, package_version)
        if args.no_bump:
            parse_calendar_version(current_version)
            version = current_version
        elif args.version is not None:
            version = validate_explicit_version(current_version, args.version)
        else:
            version = next_calendar_version(current_version, today or dt.date.today())
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    previous_content = project_path.read_text(encoding="utf-8")
    previous_package_version_content = package_version_path.read_text(encoding="utf-8")
    print(f"Using Python: {sys.executable}")
    print(f"Current version: {current_version}")
    print(f"Building version: {version}")

    try:
        if version != current_version:
            replace_project_version(project_path, version)
            replace_package_version(package_version_path, version)
        with tempfile.TemporaryDirectory(prefix="ryan-culverts-build-") as build_directory:
            build_dir = Path(build_directory)
            build_status = _run_build(build_dir)
            if build_status != 0:
                _restore_version_sources(
                    project_path,
                    project_content=previous_content,
                    version_path=package_version_path,
                    version_content=previous_package_version_content,
                )
                return build_status
            expected = build_dir / f"{DISTRIBUTION_PREFIX}{version}-py3-none-any.whl"
            if not expected.is_file():
                _restore_version_sources(
                    project_path,
                    project_content=previous_content,
                    version_path=package_version_path,
                    version_content=previous_package_version_content,
                )
                print(f"ERROR: expected wheel is missing: {expected.name}", file=sys.stderr)
                return 1
            verification_status = _run_verification(expected)
            if verification_status != 0:
                _restore_version_sources(
                    project_path,
                    project_content=previous_content,
                    version_path=package_version_path,
                    version_content=previous_package_version_content,
                )
                return verification_status
            promoted = promote_wheel(expected)
    except Exception:
        _restore_version_sources(
            project_path,
            project_content=previous_content,
            version_path=package_version_path,
            version_content=previous_package_version_content,
        )
        raise

    print(f"Built and verified: {promoted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
