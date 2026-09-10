"""Flow-basis integration tests for discharge-dependent tailwater."""

import pytest

from culvert_solver import (
    CONCRETE,
    CircularGeometry,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    ManningChannelTailwater,
    TailwaterMethod,
    TrapezoidalChannel,
    generate_crossing_rating_curve,
    solve_barrel_hydraulics,
    solve_crossing_hydraulics,
    solve_group_hydraulics,
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


def _tailwater() -> ManningChannelTailwater:
    return ManningChannelTailwater(
        section=TrapezoidalChannel(8.0, 3.0, 3.0),
        channel_invert_elevation=98.5,
        roughness=0.035,
        friction_slope=0.002,
    )


def test_standalone_barrel_and_group_use_their_receiving_flow() -> None:
    group = _crossing().groups[1]
    boundary = _tailwater()
    barrel_result = solve_barrel_hydraulics(group.barrel, 2.0, boundary)
    group_result = solve_group_hydraulics(group, 6.0, boundary)

    assert barrel_result.tailwater_resolution is not None
    assert barrel_result.tailwater_resolution.discharge == 2.0
    assert group_result.tailwater_resolution is not None
    assert group_result.tailwater_resolution.discharge == 6.0
    assert group_result.barrel_result.tailwater_resolution is group_result.tailwater_resolution


def test_crossing_resolves_tailwater_once_from_total_flow() -> None:
    crossing = _crossing()
    boundary = _tailwater()
    result = solve_crossing_hydraulics(crossing, 8.0, boundary)
    expected = boundary.resolve(8.0)
    assert result.tailwater_elevation == pytest.approx(expected.elevation, abs=1e-7)
    assert result.tailwater_resolution is not None
    assert result.tailwater_resolution.discharge == 8.0
    assert result.tailwater_resolution.method is TailwaterMethod.MANNING_NORMAL_DEPTH
    assert sum(item.total_discharge for item in result.group_results) == pytest.approx(8.0, abs=1e-4)
    assert all(
        item.tailwater_resolution is result.tailwater_resolution
        and item.barrel_result.tailwater_resolution is result.tailwater_resolution
        for item in result.group_results
    )


def test_crossing_rating_curve_recalculates_tailwater_per_point() -> None:
    boundary = _tailwater()
    curve = generate_crossing_rating_curve(_crossing(), (2.0, 5.0, 8.0), tailwater=boundary)
    expected = [boundary.resolve(q).elevation for q in (2.0, 5.0, 8.0)]
    stages = [point.tailwater_elevation for point in curve.points]
    assert stages == pytest.approx(expected, abs=1e-7)
    assert stages[0] < stages[1] < stages[2]
    resolutions = [point.tailwater_resolution for point in curve.points]
    assert all(resolution is not None for resolution in resolutions)
    assert [resolution.discharge for resolution in resolutions if resolution is not None] == [
        2.0,
        5.0,
        8.0,
    ]
    last_point = curve.points[-1]
    assert last_point.tailwater_resolution is not None
    assert last_point.tailwater_resolution.depth is not None
    assert last_point.tailwater_depth == pytest.approx(
        max(0.0, last_point.tailwater_elevation - _crossing().min_outlet_invert)
    )
    assert last_point.tailwater_resolution.depth == pytest.approx(
        last_point.tailwater_elevation - boundary.channel_invert_elevation
    )
