"""Coupled inverse-capacity tests for discharge-dependent tailwater boundaries."""

import pytest

from culvert_solver import (
    CONCRETE,
    CircularGeometry,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    InvalidInputError,
    ManningChannelTailwater,
    RectangularGeometry,
    RoadwayWeir,
    SourceReference,
    TailwaterMethod,
    TailwaterRatingCurve,
    TailwaterRatingPoint,
    TrapezoidalChannel,
    solve_barrel_discharge_for_headwater,
    solve_barrel_discharge_for_headwater_ratio,
    solve_barrel_hydraulics,
    solve_crossing_discharge_for_headwater,
    solve_crossing_hydraulics,
    solve_group_discharge_for_headwater,
    solve_group_hydraulics,
)

CURVE_SOURCE = SourceReference(
    source_id="TEST-INVERSE-RATING",
    publication="Project hydraulic model",
    edition="Revision A",
    locator="Downstream boundary rating table",
    url=None,
    applicability="Coupled inverse test fixture only.",
)


def _barrel() -> CulvertBarrel:
    return CulvertBarrel(
        geometry=CircularGeometry(1.0),
        length=40.0,
        inlet_invert=100.0,
        outlet_invert=99.0,
        roughness=0.013,
        material=CONCRETE,
    )


def _manning_tailwater() -> ManningChannelTailwater:
    return ManningChannelTailwater(
        section=TrapezoidalChannel(8.0, 3.0, 3.0),
        channel_invert_elevation=98.5,
        roughness=0.035,
        friction_slope=0.002,
    )


def _heterogeneous_crossing(*, roadway: RoadwayWeir | None = None) -> CulvertCrossing:
    second_barrel = CulvertBarrel(
        geometry=RectangularGeometry(1.2, 0.8),
        length=30.0,
        inlet_invert=100.2,
        outlet_invert=99.2,
        roughness=0.015,
        material=CONCRETE,
    )
    return CulvertCrossing(
        groups=(CulvertGroup(_barrel(), 1), CulvertGroup(second_barrel, 2)),
        roadway=roadway,
    )


def test_barrel_and_headwater_ratio_round_trip_manning_tailwater() -> None:
    barrel = _barrel()
    boundary = _manning_tailwater()
    expected_discharge = 2.0
    forward = solve_barrel_hydraulics(barrel, expected_discharge, boundary)

    from_elevation = solve_barrel_discharge_for_headwater(
        barrel,
        forward.headwater_elevation,
        boundary,
    )
    from_ratio = solve_barrel_discharge_for_headwater_ratio(
        barrel,
        forward.headwater_depth / barrel.geometry.rise,
        boundary,
    )

    assert from_elevation == pytest.approx(expected_discharge, abs=1e-4)
    assert from_ratio == pytest.approx(expected_discharge, abs=1e-4)
    assert forward.tailwater_resolution is not None
    assert forward.tailwater_resolution.method is TailwaterMethod.MANNING_NORMAL_DEPTH
    assert forward.tailwater_resolution.discharge == expected_discharge


def test_group_inverse_resolves_manning_tailwater_from_total_group_flow() -> None:
    group = CulvertGroup(_barrel(), 3)
    boundary = _manning_tailwater()
    expected_discharge = 6.0
    forward = solve_group_hydraulics(group, expected_discharge, boundary)

    inverse = solve_group_discharge_for_headwater(
        group,
        forward.barrel_result.headwater_elevation,
        boundary,
    )

    assert inverse == pytest.approx(expected_discharge, abs=1e-4)
    assert forward.tailwater_resolution is not None
    assert forward.tailwater_resolution.discharge == expected_discharge


def test_heterogeneous_crossing_inverse_couples_total_flow_and_tailwater() -> None:
    crossing = _heterogeneous_crossing()
    boundary = _manning_tailwater()
    expected_discharge = 5.0
    forward = solve_crossing_hydraulics(crossing, expected_discharge, boundary)

    inverse = solve_crossing_discharge_for_headwater(
        crossing,
        forward.headwater_elevation,
        boundary,
    )

    assert inverse == pytest.approx(expected_discharge, abs=1e-4)
    assert forward.tailwater_resolution is not None
    assert forward.tailwater_resolution.discharge == expected_discharge
    assert len({type(group.group.barrel.geometry) for group in forward.group_results}) == 2
    assert sum(group.total_discharge for group in forward.group_results) == pytest.approx(expected_discharge)


def test_crossing_inverse_preserves_supported_roadway_overtopping() -> None:
    roadway = RoadwayWeir(
        crest_elevation=101.5,
        crest_length=20.0,
        discharge_coefficient=1.6,
    )
    crossing = _heterogeneous_crossing(roadway=roadway)
    boundary = _manning_tailwater()
    expected_discharge = 8.0
    forward = solve_crossing_hydraulics(crossing, expected_discharge, boundary)

    inverse = solve_crossing_discharge_for_headwater(
        crossing,
        forward.headwater_elevation,
        boundary,
    )

    assert inverse == pytest.approx(expected_discharge, abs=1e-4)
    assert forward.culvert_discharge > 0.0
    assert forward.roadway_discharge > 0.0
    assert forward.tailwater_elevation < roadway.crest_elevation


def test_rating_curve_inverse_stays_inside_supplied_discharge_range() -> None:
    boundary = TailwaterRatingCurve(
        points=(
            TailwaterRatingPoint(0.1, 98.7),
            TailwaterRatingPoint(3.0, 99.0),
            TailwaterRatingPoint(8.0, 99.4),
        ),
        rating_curve_source=CURVE_SOURCE,
    )
    barrel = _barrel()
    expected_discharge = 2.0
    forward = solve_barrel_hydraulics(barrel, expected_discharge, boundary)

    inverse = solve_barrel_discharge_for_headwater(
        barrel,
        forward.headwater_elevation,
        boundary,
    )

    assert inverse == pytest.approx(expected_discharge, abs=1e-4)
    assert boundary.min_discharge <= inverse <= boundary.max_discharge


def test_rating_curve_inverse_rejects_targets_outside_supported_flow_range() -> None:
    boundary = TailwaterRatingCurve(
        points=(
            TailwaterRatingPoint(0.1, 98.7),
            TailwaterRatingPoint(3.0, 99.0),
            TailwaterRatingPoint(8.0, 99.4),
        ),
        rating_curve_source=CURVE_SOURCE,
    )
    barrel = _barrel()
    minimum_headwater = solve_barrel_hydraulics(barrel, boundary.min_discharge, boundary).headwater_elevation
    maximum_headwater = solve_barrel_hydraulics(barrel, boundary.max_discharge, boundary).headwater_elevation

    with pytest.raises(InvalidInputError, match="below the tailwater rating-curve range"):
        solve_barrel_discharge_for_headwater(
            barrel,
            (barrel.inlet_invert + minimum_headwater) / 2.0,
            boundary,
        )
    with pytest.raises(InvalidInputError, match="above the tailwater rating-curve range"):
        solve_barrel_discharge_for_headwater(barrel, maximum_headwater + 1.0, boundary)


def test_coupled_inverse_rejects_nonpositive_gravity() -> None:
    with pytest.raises(InvalidInputError, match="g must be strictly positive"):
        solve_barrel_discharge_for_headwater(
            _barrel(),
            headwater_elevation=101.0,
            tailwater=_manning_tailwater(),
            g=0.0,
        )
