"""Run a public-API smoke calculation against an installed wheel."""

from __future__ import annotations

import importlib.metadata

import culvert_solver as cs


def main() -> int:
    """Verify version discovery and a small geometry calculation."""
    installed_version = importlib.metadata.version("ryan-culverts")
    metadata = importlib.metadata.metadata("ryan-culverts")
    if cs.__version__ != installed_version:
        msg = f"Public version {cs.__version__!r} does not match metadata {installed_version!r}."
        raise RuntimeError(msg)
    if metadata["Requires-Python"] != "<3.15,>=3.14":
        msg = "Installed wheel does not declare the supported Python baseline."
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
