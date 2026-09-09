"""Tests for FHWA HDS-5 roadway overtopping and crossing flow allocation."""

import pytest

from culvert_solver import (
    CONCRETE,
    CircularGeometry,
    ControlType,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    CulvertInventoryItem,
    FlowRegime,
    InvalidInputError,
    RoadwayOvertoppingResult,
    RoadwayWeir,
    calculate_roadway_overtopping,
    generate_crossing_rating_curve,
    solve_crossing_hydraulics,
)


def _crossing(roadway: RoadwayWeir | None = None) -> CulvertCrossing:
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )
    return CulvertCrossing(groups=[CulvertGroup(barrel, quantity=1)], roadway=roadway)


def test_unsubmerged_roadway_overtopping_matches_hds5_equation() -> None:
    """HDS-5 Eq. 3.9 is evaluated directly in SI units."""
    roadway = RoadwayWeir(
        crest_elevation=12.0,
        crest_length=25.0,
        discharge_coefficient=1.6,
    )

    result: RoadwayOvertoppingResult = calculate_roadway_overtopping(
        roadway, headwater_elevation=12.5, tailwater_elevation=11.8
    )

    assert result.upstream_head == 0.5
    assert result.discharge == pytest.approx(1.6 * 25.0 * 0.5**1.5)


def test_roadway_is_inactive_at_or_below_crest() -> None:
    roadway = RoadwayWeir(crest_elevation=12.0, crest_length=25.0, discharge_coefficient=1.6)

    result: RoadwayOvertoppingResult = calculate_roadway_overtopping(
        roadway=roadway, headwater_elevation=12.0, tailwater_elevation=11.8
    )

    assert result.upstream_head == 0.0
    assert result.discharge == 0.0


def test_submerged_roadway_flow_fails_closed() -> None:
    roadway = RoadwayWeir(crest_elevation=12.0, crest_length=25.0, discharge_coefficient=1.6)

    with pytest.raises(expected_exception=InvalidInputError, match="Submerged roadway overtopping"):
        calculate_roadway_overtopping(roadway, headwater_elevation=12.5, tailwater_elevation=12.1)


def test_crossing_allocates_flow_between_culvert_and_roadway() -> None:
    roadway = RoadwayWeir(crest_elevation=11.0, crest_length=20.0, discharge_coefficient=1.6)
    crossing = _crossing(roadway)

    result = solve_crossing_hydraulics(crossing, total_discharge=8.0, tailwater=9.5)

    assert result.headwater_elevation > roadway.crest_elevation
    assert result.roadway_result is not None
    assert result.roadway_discharge > 0.0
    assert result.culvert_discharge > 0.0
    assert result.culvert_discharge + result.roadway_discharge == pytest.approx(8.0, abs=1e-5)
    assert result.roadway_result.headwater_elevation == result.headwater_elevation


def test_crossing_without_roadway_preserves_existing_result_contract() -> None:
    result = solve_crossing_hydraulics(_crossing(), total_discharge=2.0, tailwater=9.5)

    assert result.roadway_result is None
    assert result.roadway_discharge == 0.0
    assert result.culvert_discharge == pytest.approx(result.total_discharge)


def test_lower_roadway_can_convey_flow_before_higher_culvert_activates() -> None:
    roadway = RoadwayWeir(crest_elevation=9.0, crest_length=20.0, discharge_coefficient=1.6)
    crossing = _crossing(roadway)

    result = solve_crossing_hydraulics(crossing, total_discharge=0.5, tailwater=8.5)

    assert 9.0 < result.headwater_elevation < 10.0
    assert result.culvert_discharge == 0.0
    assert result.roadway_discharge == pytest.approx(0.5, abs=1e-5)


def test_rating_curve_identifies_roadway_only_and_combined_points() -> None:
    roadway = RoadwayWeir(crest_elevation=9.0, crest_length=2.0, discharge_coefficient=1.6)
    result = generate_crossing_rating_curve(_crossing(roadway), [0.5, 8.0], tailwater=8.5)

    assert result.points[0].control_type is ControlType.ROADWAY
    assert result.points[0].regime is FlowRegime.ROADWAY_OVERTOPPING
    assert result.points[0].outlet_velocity == 0.0
    assert result.points[0].headwater_depth > 0.0
    assert result.points[1].control_type is ControlType.MIXED
    assert result.points[1].regime is FlowRegime.MIXED


def test_roadway_model_rejects_nonpositive_inputs() -> None:
    with pytest.raises(InvalidInputError, match="crest_length"):
        RoadwayWeir(crest_elevation=12.0, crest_length=0.0, discharge_coefficient=1.6)
    with pytest.raises(InvalidInputError, match="discharge_coefficient"):
        RoadwayWeir(crest_elevation=12.0, crest_length=20.0, discharge_coefficient=0.0)


def test_inventory_rejects_result_for_different_roadway() -> None:
    configured = _crossing(
        RoadwayWeir(crest_elevation=11.0, crest_length=20.0, discharge_coefficient=1.6)
    )
    solved_for = _crossing(
        RoadwayWeir(crest_elevation=11.1, crest_length=20.0, discharge_coefficient=1.6)
    )
    result = solve_crossing_hydraulics(solved_for, total_discharge=8.0, tailwater=9.5)

    with pytest.raises(InvalidInputError, match="result roadway"):
        CulvertInventoryItem("crossing-1", configured, result)
