"""Exercise comparison-case selection without requiring the optional run-hy8 adapter."""

import argparse
import importlib.util
import math
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest

SCRIPT = Path(__file__).absolute().parents[1] / "scripts" / "compare_hy8.py"


class ComparisonCaseProtocol(Protocol):
    """Fields required by the selection regression tests."""

    case_id: str
    discharge: float


class ComparisonResultProtocol(Protocol):
    """Locally calculated fields needed for the high-flow preflight."""

    headwater: float
    velocity: float
    outlet_depth: float


def _load_comparator(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Stub only the optional adapter while importing the real comparison script."""
    adapter = ModuleType("run_hy8")
    for name in (
        "CircularConcreteInlet",
        "CircularCorrugatedSteelInlet",
        "ConcreteBoxInlet",
        "EllipticalConcreteInlet",
        "Hy8CulvertResult",
        "Hy8Executable",
        "RoadwayProfile",
        "TailwaterDefinition",
        "CulvertBarrel",
        "CulvertCrossing",
        "CulvertMaterial",
        "CulvertShape",
    ):
        setattr(adapter, name, object)
    monkeypatch.setitem(sys.modules, "run_hy8", adapter)
    spec = importlib.util.spec_from_file_location("_test_compare_hy8", SCRIPT)
    if spec is None or spec.loader is None:
        msg = "Cannot import the comparison script."
        raise AssertionError(msg)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


def _cases(module: ModuleType, **kwargs: bool) -> tuple[ComparisonCaseProtocol, ...]:
    defaults = {"elliptical": False, "elliptical_sweep": False, "discrepancy_sweep": False}
    defaults.update(kwargs)
    select = cast(
        "Callable[[argparse.Namespace], tuple[ComparisonCaseProtocol, ...]]",
        module.__dict__["_selected_cases"],
    )
    return select(argparse.Namespace(**defaults))


def test_sweep_is_explicit_and_preserves_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Original six cases and unrelated default matrix stay unchanged."""
    module = _load_comparator(monkeypatch)
    baseline = _cases(module, elliptical=True)
    expanded = _cases(module, elliptical_sweep=True)
    original_ids = [case.case_id for case in baseline]

    assert len(baseline) == 6
    assert len(expanded) == 18
    assert [case.case_id for case in expanded[:6]] == original_ids
    assert [case.discharge for case in expanded[:6]] == [0.5, 1.0, 2.0] * 2
    assert len({case.case_id for case in expanded}) == len(expanded)
    assert all("ellipse" not in case.case_id for case in _cases(module))


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        ("83x53", (3.0, 5.0, 6.0, 8.0, 12.0)),
        ("128x82", (3.0, 5.0, 10.0, 15.0, 18.0, 25.0, 35.0)),
    ],
)
def test_higher_discharge_cases_are_exact(
    monkeypatch: pytest.MonkeyPatch,
    size: str,
    expected: tuple[float, ...],
) -> None:
    """Higher-flow cases carry the existing catalogue geometry and input settings."""
    module = _load_comparator(monkeypatch)
    baseline = _cases(module, elliptical=True)
    expanded = _cases(module, elliptical_sweep=True)
    original = next(c for c in baseline if c.case_id == f"ellipse-{size}-low")
    extra = [c for c in expanded[6:] if c.case_id.startswith(f"ellipse-{size}-")]
    assert tuple(c.discharge for c in extra) == expected
    assert {c.case_id for c in extra} == {f"ellipse-{size}-q{q:.2f}" for q in expected}
    assert all(c.case_id != original.case_id for c in extra)


def test_percentages_use_depth_not_absolute_elevation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Percentage figures are signed and protect against a nonpositive denominator."""
    module = _load_comparator(monkeypatch)
    percent = cast("Callable[[float, float], float | None]", module.__dict__["_difference_percent"])
    assert percent(0.31, 0.34) == pytest.approx(-8.8235294117647)
    assert percent(3.06, 3.0) == pytest.approx(2.0)
    assert percent(1.0, 0.0) is None


def test_elliptical_flags_are_mutually_exclusive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not accidentally mix the retained evidence and extended matrix."""
    module = _load_comparator(monkeypatch)
    parse = cast("Callable[[], argparse.Namespace]", module.__dict__["parse_args"])
    monkeypatch.setattr(sys, "argv", ["compare_hy8.py", "--elliptical", "--elliptical-sweep"])
    with pytest.raises(SystemExit) as error:
        parse()
    assert error.value.code == 2


def test_all_sweep_cases_run_in_local_hydraulic_solver(monkeypatch: pytest.MonkeyPatch) -> None:
    """All 18 local sides must be computable before asking for Windows HY-8."""
    module = _load_comparator(monkeypatch)
    local_result = cast(
        "Callable[[ComparisonCaseProtocol], ComparisonResultProtocol]",
        module.__dict__["_local_result"],
    )
    for case in _cases(module, elliptical_sweep=True):
        result = local_result(case)
        assert math.isfinite(result.headwater), case.case_id
        assert math.isfinite(result.velocity), case.case_id
        assert result.velocity > 0.0, case.case_id
        assert math.isfinite(result.outlet_depth), case.case_id
