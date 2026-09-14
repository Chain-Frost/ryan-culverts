"""Focused tests for downstream-consumable roadway hydraulic result state."""

import pytest

from culvert_solver import (
    RoadwayCrestPoint,
    RoadwayCrestProfile,
    RoadwayProfileWeir,
    RoadwaySurface,
    RoadwayWeir,
    calculate_roadway_overtopping,
)


def test_constant_crest_exposes_free_unit_discharge_and_physical_length() -> None:
    roadway = RoadwayWeir(
        crest_elevation=12.0,
        crest_length=20.0,
        discharge_coefficient=1.6,
    )

    result = calculate_roadway_overtopping(roadway, 12.5, 11.5)
    segment = result.segment_results[0]

    assert segment.flow_state == "free_unsubmerged"
    assert segment.physical_interval_length == pytest.approx(20.0)
    assert segment.effective_length == pytest.approx(20.0)
    assert segment.unit_discharge == pytest.approx(result.discharge / 20.0)
    assert segment.submergence_ratio is None
    assert segment.submergence_factor is None


def test_supported_submerged_result_exposes_ratio_factor_and_unit_discharge() -> None:
    roadway = RoadwayWeir(
        crest_elevation=12.0,
        crest_length=25.0,
        discharge_coefficient=1.6,
        surface=RoadwaySurface.PAVED,
    )

    result = calculate_roadway_overtopping(roadway, 12.5, 12.45)
    segment = result.segment_results[0]

    assert segment.flow_state == "supported_submerged"
    assert segment.submergence_ratio == pytest.approx(0.9)
    assert segment.submergence_factor == pytest.approx(0.92)
    assert segment.unit_discharge == pytest.approx(1.6 * 0.5**1.5 * 0.92)


def test_zero_flow_result_is_explicitly_inactive() -> None:
    roadway = RoadwayWeir(
        crest_elevation=11.0,
        crest_length=20.0,
        discharge_coefficient=1.6,
    )

    result = calculate_roadway_overtopping(roadway, 12.0, 12.0)
    segment = result.segment_results[0]

    assert segment.flow_state == "inactive"
    assert segment.unit_discharge == 0.0
    assert segment.submergence_ratio is None
    assert segment.submergence_factor is None


def test_irregular_profile_distinguishes_physical_and_effective_lengths() -> None:
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

    assert result.segment_results
    assert {segment.flow_state for segment in result.segment_results} == {"free_unsubmerged"}
    assert {segment.physical_interval_length for segment in result.segment_results} == {10.0}
    assert all(segment.effective_length < segment.physical_interval_length for segment in result.segment_results)
    for source_interval_index in (0, 1):
        interval_segments = [
            segment for segment in result.segment_results if segment.source_interval_index == source_interval_index
        ]
        assert sum(segment.effective_length for segment in interval_segments) == pytest.approx(10.0)
