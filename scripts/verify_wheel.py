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
        raise ValueError("pyproject.toml has no [project] table.")
    project = cast(dict[str, object], project_data)
    version = project.get("version")
    licence = project.get("license")
    if not isinstance(version, str) or not version:
        raise ValueError("pyproject.toml has no nonempty project version.")
    if not isinstance(licence, str) or not licence:
        raise ValueError("pyproject.toml has no SPDX licence expression.")
    return version, licence


def _normalized(content: bytes) -> bytes:
    """Normalize UTF-8 text newlines for archive comparisons."""
    return content.decode("utf-8").replace("\r\n", "\n").encode("utf-8")


def _single_name(names: set[str], suffix: str) -> str:
    """Return one archive member ending in suffix or fail explicitly."""
    matches = sorted(name for name in names if name.endswith(suffix))
    if len(matches) != 1:
        raise ValueError(f"Expected one *{suffix} member, found {len(matches)}.")
    return matches[0]


def _metadata_field(metadata: str, field: str) -> tuple[str, ...]:
    """Return all values for one core-metadata field."""
    prefix = f"{field}: "
    return tuple(
        line.removeprefix(prefix) for line in metadata.splitlines() if line.startswith(prefix)
    )


def _verify_wheel(wheel: Path, version: str, licence: str, repository_license: bytes) -> None:
    """Verify wheel metadata, licence, typed marker, and production-only contents."""
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_name = _single_name(names, ".dist-info/METADATA")
        license_name = _single_name(names, ".dist-info/licenses/LICENSE")
        metadata = archive.read(metadata_name).decode("utf-8")
        if _metadata_field(metadata, "Version") != (version,):
            raise ValueError("Wheel Version metadata does not match pyproject.toml.")
        if _metadata_field(metadata, "License-Expression") != (licence,):
            raise ValueError("Wheel License-Expression does not match pyproject.toml.")
        if _metadata_field(metadata, "License-File") != ("LICENSE",):
            raise ValueError("Wheel does not declare the packaged LICENSE file.")
        if "culvert_solver/py.typed" not in names:
            raise ValueError("Wheel does not contain culvert_solver/py.typed.")
        if any(name.startswith(("tests/", "docs/", "reference_docs/")) for name in names):
            raise ValueError("Wheel contains development or reference inputs.")
        if _normalized(archive.read(license_name)) != repository_license:
            raise ValueError("Wheel LICENSE differs from the repository LICENSE.")


def _sha256(path: Path) -> str:
    """Return a lowercase SHA-256 artifact digest."""
    digest = hashlib.sha256()
    with path.open("rb") as artifact_file:
        for block in iter(lambda: artifact_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    wheel = args.wheel.resolve() if args.wheel is not None else DIST_DIR / expected_name
    if not wheel.is_file():
        raise FileNotFoundError("Build the current wheel first.")
    if wheel.name != expected_name:
        raise ValueError(f"Expected wheel named {expected_name}, found {wheel.name}.")
    repository_license = _normalized((PROJECT_ROOT / "LICENSE").read_bytes())
    _verify_wheel(wheel, version, licence, repository_license)
    print(f"Verified: {wheel.name} ({wheel.stat().st_size} bytes, sha256={_sha256(wheel)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
