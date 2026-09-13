"""Tests for the documented top-level public API contract."""

import inspect
import re
from importlib.metadata import version
from pathlib import Path
from typing import get_type_hints

import pytest

import culvert_solver as cs

TAILWATER_INPUT_FUNCTIONS = (
    cs.generate_barrel_rating_curve,
    cs.generate_crossing_rating_curve,
    cs.resolve_tailwater,
    cs.solve_barrel_discharge_for_headwater,
    cs.solve_barrel_discharge_for_headwater_ratio,
    cs.solve_barrel_hydraulics,
    cs.solve_crossing_discharge_for_headwater,
    cs.solve_crossing_hydraulics,
    cs.solve_group_discharge_for_headwater,
    cs.solve_group_hydraulics,
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_MEMBER = re.compile(r"^\s+- ([A-Za-z_][A-Za-z0-9_]*)$", re.MULTILINE)


def test_public_version_matches_installed_distribution() -> None:
    assert cs.__version__ == version("ryan-culverts")


def test_all_names_are_available() -> None:
    assert cs.__all__
    assert len(cs.__all__) == len(set(cs.__all__))
    assert all(hasattr(cs, name) for name in cs.__all__)


def test_all_public_callables_have_documentation() -> None:
    undocumented = [
        name for name in cs.__all__ if callable(getattr(cs, name)) and not inspect.getdoc(getattr(cs, name))
    ]
    assert undocumented == []


def test_api_pages_cover_each_public_name_once() -> None:
    api_pages = (PROJECT_ROOT / "docs" / "api.md", *(PROJECT_ROOT / "docs" / "api").glob("*.md"))
    documented = [
        match.group(1) for page in api_pages for match in API_MEMBER.finditer(page.read_text(encoding="utf-8"))
    ]
    expected = set(cs.__all__) - {"__version__"}

    assert set(documented) == expected
    assert len(documented) == len(expected)


@pytest.mark.parametrize("solver", TAILWATER_INPUT_FUNCTIONS)
def test_forward_tailwater_contract_is_public_and_documented(solver: object) -> None:
    assert get_type_hints(solver)["tailwater"] == cs.TailwaterInput
    assert "TailwaterInput" in (inspect.getdoc(solver) or "")
