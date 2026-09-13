"""User-supplied tailwater rating-curve contracts and solver integration."""

import pytest

from culvert_solver import (
    CONCRETE,
    CircularGeometry,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    InvalidInputError,
    SourceReference,
    TailwaterBoundary,
    TailwaterInterpolation,
    TailwaterMethod,
    TailwaterRatingCurve,
    TailwaterRatingPoint,
    generate_crossing_rating_curve,
    solve_barrel_hydraulics,
    solve_crossing_hydraulics,
    solve_group_hydraulics,
)

CURVE_SOURCE = SourceReference(
    source_id="TEST-RECEIVING-WATER-RATING",
    publication="Project hydraulic model",
    edition="Revision A",
    locator="Downstream boundary rating table",
    url=None,
    applicability="Test fixture only.",
)


def _boundary() -> TailwaterRatingCurve:
    return TailwaterRatingCurve(
        points=(
            TailwaterRatingPoint(1.0, 98.75),
            TailwaterRatingPoint(4.0, 99.0),
            TailwaterRatingPoint(10.0, 99.5),
        ),
        rating_curve_source=CURVE_SOURCE,
    )


def _crossing() -> CulvertCrossing:
    barrel = CulvertBarrel(
        geometry=CircularGeometry(1.2),
        length=40.0,
        inlet_invert=100.0,
        outlet_invert=99.0,
        roughness=0.013,
        material=CONCRETE,
    )
    return CulvertCrossing(groups=(CulvertGroup(barrel, 1), CulvertGroup(barrel, 3)))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_rating_point_rejects_nonfinite_values(value: float) -> None:
    with pytest.raises(InvalidInputError):
        TailwaterRatingPoint(value, 100.0)
    with pytest.raises(InvalidInputError):
        TailwaterRatingPoint(1.0, value)


def test_rating_point_rejects_negative_discharge() -> None:
    with pytest.raises(InvalidInputError, match="nonnegative"):
        TailwaterRatingPoint(-1.0, 100.0)


def test_rating_curve_requires_two_points() -> None:
    with pytest.raises(InvalidInputError, match="at least two"):
        TailwaterRatingCurve(
            points=(TailwaterRatingPoint(1.0, 100.0),),
            rating_curve_source=CURVE_SOURCE,
        )


@pytest.mark.parametrize(
    ("points", "message"),
    [
        (((1.0, 100.0), (1.0, 100.1)), "strictly increasing"),
        (((2.0, 100.0), (1.0, 100.1)), "strictly increasing"),
        (((1.0, 100.1), (2.0, 100.0)), "nondecreasing"),
    ],
)
def test_rating_curve_rejects_nonmonotonic_points(
    points: tuple[tuple[float, float], tuple[float, float]],
    message: str,
) -> None:
    typed_points = tuple(TailwaterRatingPoint(*point) for point in points)
    with pytest.raises(InvalidInputError, match=message):
        TailwaterRatingCurve(points=typed_points, rating_curve_source=CURVE_SOURCE)


def test_rating_curve_returns_exact_points_and_linear_interpolation() -> None:
    boundary = TailwaterRatingCurve(
        points=(
            TailwaterRatingPoint(0.0, 100.0),
            TailwaterRatingPoint(2.0, 100.0),
            TailwaterRatingPoint(6.0, 101.0),
        ),
        rating_curve_source=CURVE_SOURCE,
    )
    flat = boundary.resolve(1.0)
    exact = boundary.resolve(2.0)
    interpolated = boundary.resolve(4.0)

    assert isinstance(boundary, TailwaterBoundary)
    assert flat.elevation == 100.0
    assert flat.interpolation is TailwaterInterpolation.LINEAR
    assert exact.elevation == 100.0
    assert exact.interpolation is TailwaterInterpolation.EXACT_POINT
    assert interpolated.elevation == pytest.approx(100.5)
    assert interpolated.interpolation is TailwaterInterpolation.LINEAR
    assert interpolated.method is TailwaterMethod.RATING_CURVE
    assert interpolated.discharge == 4.0
    assert interpolated.rating_curve == boundary.points
    assert interpolated.rating_curve_source is CURVE_SOURCE


@pytest.mark.parametrize("discharge", [0.9, 10.1])
def test_rating_curve_rejects_out_of_range_discharge(discharge: float) -> None:
    with pytest.raises(InvalidInputError, match=r"outside.*range"):
        _boundary().resolve(discharge)


def test_forward_barrel_group_and_crossing_use_applicable_flow_basis() -> None:
    crossing = _crossing()
    group = crossing.groups[1]
    boundary = _boundary()

    barrel_result = solve_barrel_hydraulics(group.barrel, 2.0, boundary)
    group_result = solve_group_hydraulics(group, 6.0, boundary)
    crossing_result = solve_crossing_hydraulics(crossing, 8.0, boundary)

    assert barrel_result.tailwater_resolution is not None
    assert barrel_result.tailwater_resolution.discharge == 2.0
    assert group_result.tailwater_resolution is not None
    assert group_result.tailwater_resolution.discharge == 6.0
    assert crossing_result.tailwater_resolution is not None
    assert crossing_result.tailwater_resolution.discharge == 8.0
    assert crossing_result.tailwater_elevation == pytest.approx(boundary.resolve(8.0).elevation)
    assert all(
        result.tailwater_resolution is crossing_result.tailwater_resolution
        and result.barrel_result.tailwater_resolution is crossing_result.tailwater_resolution
        for result in crossing_result.group_results
    )


def test_crossing_rating_curve_resolves_boundary_for_every_total_flow() -> None:
    boundary = _boundary()
    curve = generate_crossing_rating_curve(_crossing(), (2.0, 5.0, 8.0), boundary)
    resolutions = tuple(point.tailwater_resolution for point in curve.points)

    assert all(resolution is not None for resolution in resolutions)
    assert tuple(resolution.discharge for resolution in resolutions if resolution is not None) == (2.0, 5.0, 8.0)
    assert tuple(point.tailwater_elevation for point in curve.points) == pytest.approx(
        tuple(boundary.resolve(q).elevation for q in (2.0, 5.0, 8.0))
    )
