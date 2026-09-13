"""Version-pinned heterogeneous crossing and rating validation against HY-8."""

import csv
from pathlib import Path

import pytest

from culvert_solver import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    BOX_LOSS_FLARED_30_75,
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    CONCRETE,
    PIPE_LOSS_SQUARE_EDGE,
    CircularGeometry,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    FlowRegime,
    RectangularGeometry,
    generate_crossing_rating_curve,
    solve_crossing_hydraulics,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "docs" / "validation_data" / "hy8_8_0_1_2_heterogeneous_crossing.csv"
HEADWATER_TOLERANCE_M = 0.03
GROUP_FLOW_TOLERANCE_M3S = 0.02
VELOCITY_TOLERANCE_MS = 0.03
HY8_REPORT_CONSERVATION_TOLERANCE_M3S = 0.011


def _crossing() -> CulvertCrossing:
    circular = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.0),
        length=40.0,
        inlet_invert=100.0,
        outlet_invert=99.0,
        roughness=0.013,
        material=CONCRETE,
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
        entrance_loss_coefficient=PIPE_LOSS_SQUARE_EDGE,
    )
    box = CulvertBarrel(
        geometry=RectangularGeometry(span=1.2, rise=0.8),
        length=30.0,
        inlet_invert=101.0,
        outlet_invert=99.5,
        roughness=0.015,
        material=CONCRETE,
        inlet_coefficients=BOX_CONCRETE_FLARED_WINGWALLS_30_75,
        entrance_loss_coefficient=BOX_LOSS_FLARED_30_75,
    )
    return CulvertCrossing(groups=(CulvertGroup(circular, 1), CulvertGroup(box, 2)))


def _rows() -> tuple[dict[str, str | None], ...]:
    with DATA_PATH.open(encoding="utf-8", newline="") as stream:
        return tuple(csv.DictReader(stream))


def _text(row: dict[str, str | None], key: str) -> str:
    value = row[key]
    assert value is not None
    return value


def _number(row: dict[str, str | None], key: str) -> float:
    return float(_text(row, key))


def test_heterogeneous_crossing_matches_pinned_external_evidence() -> None:
    """Check headwater, group allocation, and outlet velocities against HY-8 8.0.1.2."""
    crossing = _crossing()
    rows = _rows()
    assert len(rows) == 6

    for row in rows:
        discharge = _number(row, "discharge_m3s")
        result = solve_crossing_hydraulics(crossing, discharge, _number(row, "tailwater_m"))
        circular, box = result.group_results

        assert result.headwater_elevation == pytest.approx(_number(row, "hy8_headwater_m"), abs=HEADWATER_TOLERANCE_M)
        assert circular.total_discharge == pytest.approx(
            _number(row, "hy8_circular_flow_m3s"), abs=GROUP_FLOW_TOLERANCE_M3S
        )
        assert box.total_discharge == pytest.approx(
            _number(row, "hy8_box_group_flow_m3s"), abs=GROUP_FLOW_TOLERANCE_M3S
        )
        assert circular.barrel_result.velocity_outlet == pytest.approx(
            _number(row, "hy8_circular_velocity_ms"), abs=VELOCITY_TOLERANCE_MS
        )
        assert box.barrel_result.velocity_outlet == pytest.approx(
            _number(row, "hy8_box_velocity_ms"), abs=VELOCITY_TOLERANCE_MS
        )
        assert sum(group.total_discharge for group in result.group_results) == pytest.approx(discharge, abs=1e-5)
        assert all(
            group.barrel_result.headwater_elevation == pytest.approx(result.headwater_elevation, abs=1e-6)
            for group in result.group_results
        )
        assert abs(_number(row, "hy8_conservation_difference_m3s")) <= (HY8_REPORT_CONSERVATION_TOLERANCE_M3S)
        assert _number(row, "hy8_roadway_discharge_m3s") == 0.0


def test_external_rating_fixture_spans_activation_and_group_regime_changes() -> None:
    rows = _rows()
    discharges = tuple(_number(row, "discharge_m3s") for row in rows)
    curve = generate_crossing_rating_curve(_crossing(), discharges, tailwater=99.0)

    assert tuple(point.regime for point in curve.points) == (
        FlowRegime.INLET_CONTROL_UNSUBMERGED,
        FlowRegime.INLET_CONTROL_UNSUBMERGED,
        FlowRegime.MIXED,
        FlowRegime.MIXED,
        FlowRegime.MIXED,
        FlowRegime.INLET_CONTROL_SUBMERGED,
    )
    assert tuple(_text(row, "hy8_box_flow_type") for row in rows[:2]) == ("0-NF", "0-NF")
    assert (
        tuple((_text(row, "hy8_circular_flow_type"), _text(row, "hy8_box_flow_type")) for row in rows[2:5])
        == (("5-S2n", "1-S2n"),) * 3
    )
    assert (
        _text(rows[-1], "hy8_circular_flow_type"),
        _text(rows[-1], "hy8_box_flow_type"),
    ) == ("5-S2n", "5-S2n")
