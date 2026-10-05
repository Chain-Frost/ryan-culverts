"""Run a public-API smoke calculation against an installed wheel."""

from __future__ import annotations

import importlib.metadata
import tomllib
from pathlib import Path

import culvert_solver as cs

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Verify version discovery and a small geometry calculation."""
    installed_version = importlib.metadata.version("ryan-culverts")
    metadata = importlib.metadata.metadata("ryan-culverts")
    if cs.__version__ != installed_version:
        msg = f"Public version {cs.__version__!r} does not match metadata {installed_version!r}."
        raise RuntimeError(msg)
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as stream:
        expected_python = tomllib.load(stream)["project"]["requires-python"]
    installed_python = metadata["Requires-Python"] or ""
    # Build backends can reorder comma-separated constraints in core metadata.
    if {part.strip() for part in installed_python.split(",")} != {part.strip() for part in expected_python.split(",")}:
        msg = f"Installed wheel Requires-Python {installed_python!r} does not match pyproject.toml {expected_python!r}."
        raise RuntimeError(msg)
    project_urls = set(metadata.get_all("Project-URL") or ())
    expected_urls = {
        "Documentation, https://chain-frost.github.io/ryan-culverts/",
        "Changelog, https://github.com/Chain-Frost/ryan-culverts/blob/main/docs/changelog.md",
    }
    if not expected_urls.issubset(project_urls):
        msg = "Installed wheel does not contain the documented project URLs."
        raise RuntimeError(msg)
    geometry = cs.CircularGeometry(diameter=1.0)
    if abs(geometry.area(0.5) - geometry.area_full / 2.0) > 1e-12:
        msg = "Installed-wheel public geometry calculation failed."
        raise RuntimeError(msg)
    print(f"Installed-wheel smoke test passed for ryan-culverts {cs.__version__}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
