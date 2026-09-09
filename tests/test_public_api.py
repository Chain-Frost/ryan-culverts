"""Tests for the documented top-level public API contract."""

from importlib.metadata import version

import culvert_solver as cs


def test_public_version_matches_installed_distribution() -> None:
    assert cs.__version__ == version("ryan-culverts")


def test_all_names_are_available() -> None:
    assert cs.__all__
    assert len(cs.__all__) == len(set(cs.__all__))
    assert all(hasattr(cs, name) for name in cs.__all__)
