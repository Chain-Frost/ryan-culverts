"""Build one clean universal wheel for the current project version."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DIST_DIR: Path = PROJECT_ROOT / "dist"
DISTRIBUTION_PREFIX: str = "ryan_culverts-"


def _project_version() -> str:
    """Read the single authoritative package version from ``pyproject.toml``."""
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        data: dict[str, object] = tomllib.load(pyproject_file)
    project_data = data.get("project")
    if not isinstance(project_data, dict):
        raise ValueError("pyproject.toml has no [project] table.")
    project = cast(dict[str, object], project_data)
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("pyproject.toml has no nonempty project version.")
    return version


def _remove_old_distributions() -> None:
    """Remove only prior ryan-culverts distribution files from the local output folder."""
    DIST_DIR.mkdir(exist_ok=True)
    for pattern in (f"{DISTRIBUTION_PREFIX}*.whl", f"{DISTRIBUTION_PREFIX}*.tar.gz"):
        for artifact in DIST_DIR.glob(pattern):
            if artifact.is_file() and artifact.parent.resolve() == DIST_DIR.resolve():
                artifact.unlink()


def main() -> int:
    """Build and confirm exactly one version-matched universal wheel."""
    version = _project_version()
    _remove_old_distributions()
    command = [sys.executable, "-m", "build", "--wheel", "--outdir", str(DIST_DIR)]
    print(f"Using Python: {sys.executable}")
    print(f"Building version: {version}")
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode != 0:
        return result.returncode

    normalized_version = version.replace("-", "_")
    expected = DIST_DIR / f"{DISTRIBUTION_PREFIX}{normalized_version}-py3-none-any.whl"
    if not expected.is_file():
        print(f"ERROR: expected wheel is missing: {expected.name}", file=sys.stderr)
        return 1
    print(f"Built: {expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
