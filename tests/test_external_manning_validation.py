"""Version-pinned channel normal-depth comparison against HEC-RAS."""

import csv
from collections import Counter
from pathlib import Path

import pytest

from culvert_solver import RectangularChannel, TrapezoidalChannel, calculate_channel_normal_depth

DATA_PATH = Path(__file__).resolve().parents[1] / "docs" / "validation_data" / "hecras_7_0_1_normal_depth.csv"
DEPTH_TOLERANCE_M = 0.0002
GEOMETRY_TOLERANCE = 0.00002


def _rows() -> tuple[dict[str, str | None], ...]:
    with DATA_PATH.open(encoding="utf-8", newline="") as stream:
        return tuple(csv.DictReader(stream))


def _text(row: dict[str, str | None], key: str) -> str:
    value = row[key]
    assert value is not None
    return value


def _number(row: dict[str, str | None], key: str) -> float:
    return float(_text(row, key))


def test_external_matrix_covers_four_shapes_at_two_flow_scales() -> None:
    rows = _rows()
    counts = Counter(_text(row, "section_kind") for row in rows)
    assert counts == {
        "rectangular": 2,
        "symmetric_trapezoidal": 2,
        "asymmetric_trapezoidal": 2,
        "triangular": 2,
    }
    for section_kind in counts:
        discharges = [_number(row, "discharge_m3s") for row in rows if _text(row, "section_kind") == section_kind]
        assert discharges[0] < discharges[1]


def test_channel_normal_depth_matches_hecras_7_0_1_evidence() -> None:
    for row in _rows():
        bottom_width = _number(row, "bottom_width_m")
        left_slope = _number(row, "left_side_slope_h_per_v")
        right_slope = _number(row, "right_side_slope_h_per_v")
        if _text(row, "section_kind") == "rectangular":
            section = RectangularChannel(bottom_width)
        else:
            section = TrapezoidalChannel(bottom_width, left_slope, right_slope)

        result = calculate_channel_normal_depth(
            section,
            _number(row, "discharge_m3s"),
            _number(row, "friction_slope"),
            _number(row, "manning_n"),
        )
        assert result.depth == pytest.approx(_number(row, "local_normal_depth_m"), abs=1e-12)
        assert result.depth == pytest.approx(_number(row, "hecras_normal_depth_m"), abs=DEPTH_TOLERANCE_M)
        assert result.depth - _number(row, "hecras_normal_depth_m") == pytest.approx(
            _number(row, "depth_difference_m"), abs=1e-12
        )


@pytest.mark.parametrize(
    "column",
    [
        "geometry_area_difference_m2",
        "geometry_perimeter_difference_m",
        "geometry_top_width_difference_m",
    ],
)
def test_hecras_geometry_matches_intended_sections(column: str) -> None:
    assert max(abs(_number(row, column)) for row in _rows()) <= GEOMETRY_TOLERANCE
