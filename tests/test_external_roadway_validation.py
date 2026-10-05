"""Offline hydraulic checks against retained, version-pinned roadway evidence."""

import csv
import json
from itertools import pairwise
from pathlib import Path

import pytest

from culvert_solver import (
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    CONCRETE,
    PIPE_LOSS_SQUARE_EDGE,
    CircularGeometry,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    InvalidInputError,
    RoadwayCrestPoint,
    RoadwayCrestProfile,
    RoadwayOvertoppingInput,
    RoadwayProfileWeir,
    RoadwaySurface,
    RoadwayWeir,
    calculate_roadway_overtopping,
    solve_crossing_hydraulics,
)

DATA = Path(__file__).resolve().parents[1] / "docs" / "validation_data"
MATRIX = DATA / "hy8_8_0_1_2_roadway_overtopping.csv"
BOUNDARIES = DATA / "hy8_8_0_1_2_roadway_overtopping_boundaries.csv"


def _rows(path: Path) -> tuple[dict[str, str | None], ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        return tuple(csv.DictReader(stream))


def _text(row: dict[str, str | None], name: str) -> str:
    value = row[name]
    assert value is not None
    return value


def _number(row: dict[str, str | None], name: str) -> float:
    return float(_text(row, name))


def _roadway(row: dict[str, str | None]) -> RoadwayOvertoppingInput:
    surface = RoadwaySurface(_text(row, "local_surface")) if _text(row, "local_surface") else None
    if _text(row, "profile") == "constant":
        return RoadwayWeir(12.0, 20.0, 1.6, surface=surface)
    points = tuple(RoadwayCrestPoint(float(x), float(z)) for x, z in json.loads(_text(row, "points_json")))
    return RoadwayProfileWeir(RoadwayCrestProfile(points), 1.6, surface=surface)


def _crossing(row: dict[str, str | None]) -> CulvertCrossing:
    barrel = CulvertBarrel(
        CircularGeometry(1.2),
        length=30.0,
        inlet_invert=_number(row, "inlet_invert_m"),
        outlet_invert=9.7,
        roughness=0.012,
        material=CONCRETE,
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
        entrance_loss_coefficient=PIPE_LOSS_SQUARE_EDGE,
    )
    return CulvertCrossing(groups=(CulvertGroup(barrel, 1),), roadway=_roadway(row))


@pytest.mark.parametrize("row", _rows(MATRIX), ids=lambda row: row["case_id"])
def test_retained_crossings_conserve_flow_and_reproduce_local_segments(row: dict[str, str | None]) -> None:
    flow, tailwater = _number(row, "requested_discharge_m3s"), _number(row, "tailwater_m")
    result = solve_crossing_hydraulics(_crossing(row), flow, tailwater)
    assert result.culvert_discharge + result.roadway_discharge == pytest.approx(flow, abs=1e-5)
    assert result.headwater_elevation == pytest.approx(_number(row, "local_headwater_m"), abs=1e-6)
    assert result.roadway_result is not None
    assert sum(s.discharge for s in result.roadway_result.segment_results) == pytest.approx(result.roadway_discharge)
    retained = json.loads(_text(row, "local_segments_json"))
    assert len(retained) == len(result.roadway_result.segment_results)
    for segment, evidence in zip(result.roadway_result.segment_results, retained, strict=True):
        assert segment.discharge == pytest.approx(evidence["discharge"], abs=1e-5)
        assert segment.unit_discharge * segment.effective_length == pytest.approx(segment.discharge)
        assert segment.physical_interval_length > 0.0
        assert segment.physical_interval_length == pytest.approx(evidence["physical_interval_length"])
        assert segment.flow_state.value == evidence["flow_state"]
        assert segment.integration_source.source_id == evidence["integration_source"]["source_id"]
    external_closure = _number(row, "hy8_culvert_m3s") + _number(row, "hy8_roadway_m3s") - _number(row, "hy8_total_m3s")
    assert external_closure == pytest.approx(_number(row, "hy8_closure_m3s"), abs=1e-12)
    # Retain native residuals beyond three half report increments as unresolved;
    # do not widen a tolerance to turn them into acceptance evidence.
    assert _text(row, "hy8_closure_classification") == (
        "externally corroborated" if abs(external_closure) <= 0.0151 else "external-software behaviour unresolved"
    )
    if _text(row, "local_surface"):
        assert _text(row, "roadway_classification") == "unsupported comparison"
        assert _text(row, "crossing_classification") == "unsupported comparison"


@pytest.mark.parametrize("row", [r for r in _rows(MATRIX) if not r["local_surface"]], ids=lambda row: row["case_id"])
def test_free_roadway_precision_disposition_and_independent_integral(row: dict[str, str | None]) -> None:
    headwater, tailwater = _number(row, "hy8_headwater_m"), _number(row, "tailwater_m")
    road = _roadway(row)
    result = calculate_roadway_overtopping(road, headwater, tailwater)
    lower_road = calculate_roadway_overtopping(road, headwater - 0.005, tailwater).discharge
    upper_road = calculate_roadway_overtopping(road, headwater + 0.005, tailwater).discharge
    # Coefficient-card precision is 3e-7 SI; propagate it rather than adding a fitted tolerance.
    lower = lower_road * ((1.6 - 3e-7) / 1.6) - 0.005
    upper = upper_road * ((1.6 + 3e-7) / 1.6) + 0.005
    external = _number(row, "hy8_roadway_m3s")
    corroborated = lower <= external <= upper
    assert _text(row, "roadway_classification") == (
        "externally corroborated" if corroborated else "external-software behaviour unresolved"
    )
    if _text(row, "profile") == "constant":
        assert corroborated
    # Closed-form integration of (HW - linear crest)**1.5 is independent of quadrature.
    exact = 0.0
    points = [RoadwayCrestPoint(float(x), float(z)) for x, z in json.loads(_text(row, "points_json"))]
    for left, right in pairwise(points):
        first = max(headwater - left.elevation, 0.0)
        last = max(headwater - right.elevation, 0.0)
        dz = right.elevation - left.elevation
        integral = (first**2.5 - last**2.5) / (2.5 * dz) if dz else first**1.5
        exact += 1.6 * (right.station - left.station) * integral
    # Four-point integration of x**1.5 over [0,1] underestimates its exact integral
    # by 0.00012404 relative. A 0.0002 envelope covers the wet-edge cusp, separately
    # from the external-software precision band above.
    assert result.discharge == pytest.approx(exact, rel=2e-4, abs=1e-12)


@pytest.mark.parametrize("row", _rows(BOUNDARIES), ids=lambda row: row["case_id"])
def test_boundary_evidence_preserves_local_fail_closed_contract(row: dict[str, str | None]) -> None:
    surface = RoadwaySurface(_text(row, "local_surface")) if _text(row, "local_surface") else None
    road = RoadwayWeir(12.0, 20.0, 1.6, surface=surface)
    headwater, tailwater = _number(row, "requested_headwater_m"), _number(row, "tailwater_m")
    if _text(row, "local_outcome") == "rejected":
        with pytest.raises(InvalidInputError):
            calculate_roadway_overtopping(road, headwater, tailwater)
    else:
        assert calculate_roadway_overtopping(road, headwater, tailwater).discharge == pytest.approx(
            _number(row, "local_roadway_m3s"), abs=1e-10
        )
    assert _text(row, "classification") != "externally corroborated"
