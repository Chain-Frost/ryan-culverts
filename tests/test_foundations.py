"""Analytical and failure-contract tests for the first foundation milestone."""

import math
from dataclasses import FrozenInstanceError, replace

import pytest

from culvert_solver import (
    ConvergenceError,
    InvalidInputError,
    RootTolerances,
    SourceReference,
    dimension_mm_to_m,
    solve_bracketed,
    solve_brent,
)
from culvert_solver.numerical.roots import RootResult


def test_irrational_root_has_error_bound_and_residual() -> None:
    result: RootResult = solve_bracketed(lambda x: x * x - 2, 0, 2)
    assert result.root == pytest.approx(math.sqrt(2), abs=2e-10)
    assert result.bracket[0] <= math.sqrt(2) <= result.bracket[1]
    assert result.residual == result.root**2 - 2
    assert result.iterations > 0


def test_decreasing_function_and_exact_endpoint() -> None:
    result = solve_bracketed(lambda x: 2 - x * x, 0, 2)
    assert result.root == pytest.approx(math.sqrt(2), abs=2e-10)
    endpoint = solve_bracketed(lambda x: x - 2, 0, 2)
    assert endpoint.root == 2
    assert endpoint.iterations == 0


def test_tiny_residual_does_not_short_circuit_interval_accuracy() -> None:
    result = solve_bracketed(lambda x: 1e-300 * (x - 0.37), 0, 1)
    assert result.root == pytest.approx(0.37, abs=2e-10)
    with pytest.raises(InvalidInputError, match="change sign"):
        solve_bracketed(lambda x: 1e-300 * (x + 1), 0, 1)


def test_extreme_brackets_do_not_overflow() -> None:
    result = solve_bracketed(lambda x: x / 1e308 - 0.25, -1e308, 1e308)
    assert result.root == pytest.approx(2.5e307)
    same_sign = solve_bracketed(lambda x: x / 1e308 - 0.75, 5e307, 1e308)
    assert same_sign.root == pytest.approx(7.5e307)

    brent = solve_brent(lambda x: x / 1e308 - 0.25, -1e308, 1e308)
    assert brent.root == pytest.approx(2.5e307)
    assert brent.bracket[0] <= brent.root <= brent.bracket[1]


def test_brent_has_independent_failure_and_residual_contracts() -> None:
    """Exercise Brent directly rather than only through hydraulic callers."""
    result = solve_brent(lambda x: x * x - 2.0, 0.0, 2.0)
    assert result.root == pytest.approx(math.sqrt(2.0), abs=2e-10)
    assert result.bracket[0] <= math.sqrt(2.0) <= result.bracket[1]
    with pytest.raises(ConvergenceError):
        solve_brent(lambda x: x * x - 2.0, 0.0, 2.0, max_iterations=1)
    with pytest.raises(InvalidInputError, match="finite"):
        solve_brent(lambda _: math.nan, -1.0, 1.0)


def test_residual_tolerance_is_separate_and_required_when_supplied() -> None:
    tolerances = RootTolerances(x_abs=1e-5, x_rel=0, residual_abs=1e-5)
    result = solve_bracketed(lambda x: 1e6 * (x - 0.37), 0, 1, tolerances=tolerances)
    assert abs(result.residual) <= 1e-5
    assert abs(result.root - 0.37) <= 1e-11


def test_convergence_failure_has_diagnostics() -> None:
    with pytest.raises(ConvergenceError) as exc:
        solve_bracketed(lambda x: x * x - 2, 0, 2, max_iterations=1)
    assert exc.value.iterations == 1
    assert exc.value.bracket == (1, 2)


def test_machine_resolution_failure_is_explicit() -> None:
    lower, upper = 1.0, math.nextafter(1.0, math.inf)
    with pytest.raises(ConvergenceError, match="resolution"):
        solve_bracketed(
            lambda x: -1 if x == lower else 1,
            lower,
            upper,
            tolerances=RootTolerances(x_abs=1e-30, x_rel=0, residual_abs=0),
        )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, True])
def test_nonfinite_inputs_and_boolean_dimensions_fail(value: float) -> None:
    with pytest.raises(InvalidInputError):
        dimension_mm_to_m(value)
    with pytest.raises(InvalidInputError):
        RootTolerances(x_abs=value)
    with pytest.raises(InvalidInputError):
        solve_bracketed(lambda x: x, value, 2)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_nonfinite_function_evaluations_fail(value: float) -> None:
    with pytest.raises(InvalidInputError, match="finite"):
        solve_bracketed(lambda _: value, -1, 1)
    with pytest.raises(InvalidInputError, match="midpoint"):
        solve_bracketed(lambda x: value if x == 0 else x, -1, 1)


@pytest.mark.parametrize("bounds", [(1, 1), (2, 1)])
def test_invalid_brackets_fail(bounds: tuple[float, float]) -> None:
    with pytest.raises(InvalidInputError):
        solve_bracketed(lambda x: x, *bounds)


@pytest.mark.parametrize("iterations", [0, -1, True])
def test_invalid_iteration_limits_fail(iterations: int) -> None:
    with pytest.raises(InvalidInputError, match="positive integer"):
        solve_bracketed(lambda x: x, -1, 1, max_iterations=iterations)


@pytest.mark.parametrize("value", [0, -1, 5e-324])
def test_dimensions_must_remain_positive_in_si(value: float) -> None:
    with pytest.raises(InvalidInputError):
        dimension_mm_to_m(value)


def test_unit_conversion_and_large_integer_rejection() -> None:
    assert dimension_mm_to_m(1200) == 1.2
    assert dimension_mm_to_m(2400) == 2.4
    with pytest.raises(InvalidInputError):
        dimension_mm_to_m(10**1000)


def test_invalid_tolerance_combinations() -> None:
    with pytest.raises(InvalidInputError):
        RootTolerances(x_abs=0, x_rel=0)
    with pytest.raises(InvalidInputError):
        RootTolerances(x_rel=-1)
    with pytest.raises(InvalidInputError):
        RootTolerances(residual_abs=-1)
    with pytest.raises(InvalidInputError):
        RootTolerances(residual_abs=math.nan)


def test_function_exceptions_are_not_silently_replaced() -> None:
    def undefined(_: float) -> float:
        msg = "physical singularity"
        raise ZeroDivisionError(msg)

    with pytest.raises(ZeroDivisionError, match="physical singularity"):
        solve_bracketed(undefined, 0, 1)


def test_source_record_requires_specific_provenance() -> None:
    source = SourceReference(
        source_id="FHWA-HDS5-2012",
        publication="Hydraulic Design of Highway Culverts",
        edition="Third edition, April 2012",
        locator="Section 3.1.4, equation 3.4b",
        url="https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf",
        applicability="Full-flow Manning friction; SI coefficient must be selected explicitly.",
    )
    with pytest.raises(InvalidInputError, match="locator"):
        replace(source, locator=" ")
    with pytest.raises(InvalidInputError, match="HTTP"):
        replace(source, url="local.pdf")
    private_source = replace(
        source,
        source_id="manufacturer-controlled-spec",
        publication="Manufacturer controlled specification",
        url=None,
    )
    assert private_source.url is None
    records: list[tuple[object, str, object]] = [
        (source, "edition", "untracked"),
        (RootTolerances(), "x_abs", 1),
        (solve_bracketed(lambda x: x, -1, 1), "root", 3),
    ]
    for record, field_name, value in records:
        with pytest.raises(FrozenInstanceError):
            setattr(record, field_name, value)
