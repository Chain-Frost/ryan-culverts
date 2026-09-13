"""Focused tests for irregular roadway profiles and sourced submergence correction."""

import pytest

from culvert_solver import (
    CONCRETE,
    CircularGeometry,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    InvalidInputError,
    RoadwayCrestPoint,
    RoadwayCrestProfile,
    RoadwayProfileWeir,
    RoadwaySurface,
    RoadwayWeir,
    SourceReference,
    TailwaterRatingCurve,
    TailwaterRatingPoint,
    calculate_roadway_overtopping,
    solve_crossing_discharge_for_headwater,
    solve_crossing_hydraulics,
)

RATING_SOURCE = SourceReference(
    source_id="TEST-ROADWAY-TAILWATER",
    publication="Roadway test fixture",
    edition="Revision A",
    locator="Synthetic downstream rating curve",
    url=None,
    applicability="CS-028 coupled roadway-tailwater regression test only.",
)


def _crossing(roadway: RoadwayWeir | RoadwayProfileWeir) -> CulvertCrossing:
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )
    return CulvertCrossing(groups=[CulvertGroup(barrel, quantity=1)], roadway=roadway)


def test_flat_profile_matches_constant_crest_and_preserves_segment_sum() -> None:
    constant = RoadwayWeir(
        crest_elevation=12.0,
        crest_length=25.0,
        discharge_coefficient=1.6,
    )
    profile = RoadwayProfileWeir(
        profile=RoadwayCrestProfile(
            [
                RoadwayCrestPoint(0.0, 12.0),
                RoadwayCrestPoint(25.0, 12.0),
            ]
        ),
        discharge_coefficient=1.6,
    )

    constant_result = calculate_roadway_overtopping(constant, 12.5, 11.8)
    profile_result = calculate_roadway_overtopping(profile, 12.5, 11.8)

    assert profile_result.discharge == pytest.approx(constant_result.discharge)
    assert sum(segment.discharge for segment in profile_result.segment_results) == pytest.approx(
        profile_result.discharge
    )
    assert sum(segment.effective_length for segment in profile_result.segment_results) == pytest.approx(25.0)


def test_sag_profile_retains_local_geometry_and_flow_contributions() -> None:
    roadway = RoadwayProfileWeir(
        profile=RoadwayCrestProfile(
            [
                RoadwayCrestPoint(0.0, 12.4),
                RoadwayCrestPoint(10.0, 12.0),
                RoadwayCrestPoint(20.0, 12.4),
            ]
        ),
        discharge_coefficient=1.6,
    )

    result = calculate_roadway_overtopping(roadway, 12.5, 11.5)

    assert result.discharge > 0.0
    assert result.upstream_head == pytest.approx(0.5)
    assert sum(segment.discharge for segment in result.segment_results) == pytest.approx(result.discharge)
    assert {segment.source_interval_index for segment in result.segment_results} == {0, 1}
    assert min(segment.crest_elevation for segment in result.segment_results) < max(
        segment.crest_elevation for segment in result.segment_results
    )


def test_paved_submergence_uses_digitised_fhwa_factor() -> None:
    roadway = RoadwayWeir(
        crest_elevation=12.0,
        crest_length=25.0,
        discharge_coefficient=1.6,
        surface=RoadwaySurface.PAVED,
    )

    result = calculate_roadway_overtopping(roadway, 12.5, 12.45)
    segment = result.segment_results[0]

    assert segment.submergence_correction is not None
    assert segment.submergence_correction.ratio == pytest.approx(0.9)
    assert segment.submergence_correction.factor == pytest.approx(0.92)
    assert result.discharge == pytest.approx(1.6 * 25.0 * 0.5**1.5 * 0.92)


def test_submerged_roadway_without_surface_fails_closed() -> None:
    roadway = RoadwayWeir(
        crest_elevation=12.0,
        crest_length=25.0,
        discharge_coefficient=1.6,
    )

    with pytest.raises(InvalidInputError, match="requires roadway.surface"):
        calculate_roadway_overtopping(roadway, 12.5, 12.1)


def test_irregular_roadway_participates_in_common_headwater_conservation() -> None:
    roadway = RoadwayProfileWeir(
        profile=RoadwayCrestProfile(
            [
                RoadwayCrestPoint(0.0, 11.4),
                RoadwayCrestPoint(10.0, 11.0),
                RoadwayCrestPoint(20.0, 11.4),
            ]
        ),
        discharge_coefficient=1.6,
    )

    result = solve_crossing_hydraulics(_crossing(roadway), total_discharge=8.0, tailwater=9.5)

    assert result.roadway_result is not None
    assert result.roadway_discharge > 0.0
    assert result.culvert_discharge > 0.0
    assert result.culvert_discharge + result.roadway_discharge == pytest.approx(8.0, abs=1e-5)


def test_submerged_roadway_round_trip_with_discharge_dependent_tailwater() -> None:
    roadway = RoadwayWeir(
        crest_elevation=11.0,
        crest_length=20.0,
        discharge_coefficient=1.6,
        surface=RoadwaySurface.PAVED,
    )
    boundary = TailwaterRatingCurve(
        points=(
            TailwaterRatingPoint(0.1, 10.8),
            TailwaterRatingPoint(8.0, 11.2),
            TailwaterRatingPoint(20.0, 11.5),
        ),
        rating_curve_source=RATING_SOURCE,
    )
    crossing = _crossing(roadway)

    forward = solve_crossing_hydraulics(crossing, total_discharge=8.0, tailwater=boundary)
    inverse = solve_crossing_discharge_for_headwater(
        crossing,
        headwater_elevation=forward.headwater_elevation,
        tailwater=boundary,
    )

    assert forward.tailwater_elevation == pytest.approx(11.2)
    assert forward.roadway_result is not None
    assert any(
        segment.submergence_correction is not None
        for segment in forward.roadway_result.segment_results
    )
    assert inverse == pytest.approx(8.0, abs=1e-4)
