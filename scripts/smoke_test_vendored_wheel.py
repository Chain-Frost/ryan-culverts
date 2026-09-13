"""Smoke-test culvert_solver from an installed parent wheel with stale metadata present."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys
from pathlib import Path
from typing import Protocol, cast

HOST_DISTRIBUTION = "culvert-solver-vendored-smoke"


class _Geometry(Protocol):
    area_full: float

    def area(self, depth: float) -> float:
        """Return wetted area at depth."""
        ...


class _GeometryFactory(Protocol):
    def __call__(self, *, diameter: float) -> _Geometry:
        """Construct circular geometry."""
        ...


class _CulvertSolverModule(Protocol):
    __file__: str | None
    __version__: str
    CircularGeometry: _GeometryFactory


def main(argv: list[str] | None = None) -> int:
    """Verify the vendored import location, local version, and a public calculation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-root", required=True, type=Path)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--unrelated-version", required=True)
    args = parser.parse_args(argv)

    expected_root = args.expected_root.resolve()
    sys.path.insert(0, str(expected_root))
    package = cast("_CulvertSolverModule", importlib.import_module("culvert_solver"))
    package_file = package.__file__
    if package_file is None or not Path(package_file).resolve().is_relative_to(expected_root):
        msg = f"culvert_solver resolved outside the vendored install root: {package_file}"
        raise RuntimeError(msg)
    if importlib.metadata.version(HOST_DISTRIBUTION) != "1.0.0":
        msg = "Vendored host distribution metadata is unavailable."
        raise RuntimeError(msg)
    unrelated_version = importlib.metadata.version("ryan-culverts")
    if unrelated_version != args.unrelated_version:
        msg = f"Expected unrelated ryan-culverts metadata {args.unrelated_version!r}, found {unrelated_version!r}."
        raise RuntimeError(msg)
    if package.__version__ != args.expected_version:
        msg = f"Vendored version {package.__version__!r} does not match package-local {args.expected_version!r}."
        raise RuntimeError(msg)
    geometry = package.CircularGeometry(diameter=1.0)
    if abs(geometry.area(0.5) - geometry.area_full / 2.0) > 1e-12:
        msg = "Vendored-wheel public geometry calculation failed."
        raise RuntimeError(msg)
    print(
        f"Vendored-wheel smoke test passed for culvert_solver {package.__version__}; "
        f"ignored unrelated ryan-culverts {unrelated_version}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
