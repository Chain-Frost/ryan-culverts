"""Verify the current ryan-culverts universal wheel."""

from __future__ import annotations

import argparse
import hashlib
import tomllib
import zipfile
from pathlib import Path
from typing import cast

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DIST_DIR: Path = PROJECT_ROOT / "dist"
DISTRIBUTION_PREFIX: str = "ryan_culverts-"


def _project_metadata() -> tuple[str, str]:
    """Read the authoritative project version and licence expression."""
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        data: dict[str, object] = tomllib.load(pyproject_file)
    project_data = data.get("project")
    if not isinstance(project_data, dict):
        msg = "pyproject.toml has no [project] table."
        raise ValueError(msg)
    project = cast("dict[str, object]", project_data)
    version = project.get("version")
    licence = project.get("license")
    if not isinstance(version, str) or not version:
        msg = "pyproject.toml has no nonempty project version."
        raise ValueError(msg)
    if not isinstance(licence, str) or not licence:
        msg = "pyproject.toml has no SPDX licence expression."
        raise ValueError(msg)
    return version, licence


def _normalized(content: bytes) -> bytes:
    """Normalize UTF-8 text newlines for archive comparisons."""
    return content.decode("utf-8").replace("\r\n", "\n").encode("utf-8")


def _single_name(names: set[str], suffix: str) -> str:
    """Return one archive member ending in suffix or fail explicitly."""
    matches = sorted(name for name in names if name.endswith(suffix))
    if len(matches) != 1:
        msg = f"Expected one *{suffix} member, found {len(matches)}."
        raise ValueError(msg)
    return matches[0]


def _metadata_field(metadata: str, field: str) -> tuple[str, ...]:
    """Return all values for one core-metadata field."""
    prefix = f"{field}: "
    return tuple(line.removeprefix(prefix) for line in metadata.splitlines() if line.startswith(prefix))


def _verify_wheel(wheel: Path, version: str, licence: str, repository_license: bytes) -> None:
    """Verify wheel metadata, licence, typed marker, and production-only contents."""
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_name = _single_name(names, ".dist-info/METADATA")
        license_name = _single_name(names, ".dist-info/licenses/LICENSE")
        metadata = archive.read(metadata_name).decode("utf-8")
        if _metadata_field(metadata, "Version") != (version,):
            msg = "Wheel Version metadata does not match pyproject.toml."
            raise ValueError(msg)
        if _metadata_field(metadata, "License-Expression") != (licence,):
            msg = "Wheel License-Expression does not match pyproject.toml."
            raise ValueError(msg)
        if _metadata_field(metadata, "License-File") != ("LICENSE",):
            msg = "Wheel does not declare the packaged LICENSE file."
            raise ValueError(msg)
        if "culvert_solver/py.typed" not in names:
            msg = "Wheel does not contain culvert_solver/py.typed."
            raise ValueError(msg)
        if any(name.startswith(("tests/", "docs/", "reference_docs/")) for name in names):
            msg = "Wheel contains development or reference inputs."
            raise ValueError(msg)
        if _normalized(archive.read(license_name)) != repository_license:
            msg = "Wheel LICENSE differs from the repository LICENSE."
            raise ValueError(msg)


def _sha256(path: Path) -> str:
    """Return a lowercase SHA-256 artifact digest."""
    digest = hashlib.sha256()
    with path.open("rb") as artifact_file:
        for block in iter(lambda: artifact_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def retained_wheel(version: str) -> Path:
    """Return the sole retained project wheel when it matches the project version."""
    wheels = sorted(DIST_DIR.glob(f"{DISTRIBUTION_PREFIX}*.whl"))
    if len(wheels) != 1:
        msg = f"Expected exactly one retained project wheel under dist/, found {len(wheels)}."
        raise ValueError(msg)
    wheel = wheels[0]
    expected_name = f"{DISTRIBUTION_PREFIX}{version}-py3-none-any.whl"
    if wheel.name != expected_name:
        msg = f"Retained wheel {wheel.name} does not match project version {version}."
        raise ValueError(msg)
    return wheel


def main(argv: list[str] | None = None) -> int:
    """Verify the wheel and print its reproducibility identifier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "wheel",
        nargs="?",
        type=Path,
        help="Specific staged wheel to verify; defaults to the current wheel under dist/.",
    )
    args = parser.parse_args(argv)
    version, licence = _project_metadata()
    expected_name = f"{DISTRIBUTION_PREFIX}{version}-py3-none-any.whl"
    wheel = args.wheel.resolve() if args.wheel is not None else retained_wheel(version)
    if not wheel.is_file():
        msg = "Build the current wheel first."
        raise FileNotFoundError(msg)
    if wheel.name != expected_name:
        msg = f"Expected wheel named {expected_name}, found {wheel.name}."
        raise ValueError(msg)
    repository_license = _normalized((PROJECT_ROOT / "LICENSE").read_bytes())
    _verify_wheel(wheel, version, licence, repository_license)
    print(f"Verified: {wheel.name} ({wheel.stat().st_size} bytes, sha256={_sha256(wheel)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
