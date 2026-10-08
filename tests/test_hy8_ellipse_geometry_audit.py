"""Regression check for the retained HY-8 ShapeDB versus exact ellipse audit.

This verifies the audit's arithmetic and provenance only. It is explicitly
not a HY-8 executable test or a hydraulic parity acceptance fixture.
"""

import csv
from pathlib import Path

import pytest

from culvert_solver import HorizontalEllipseGeometry

_AUDIT = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "validation_data"
    / "hy8_8_0_1_2_concrete_ellipse_area_audit.csv"
)
_SHAPE_DB_SHA256 = "2479e9444feaff529313e18a1b26fc2de4f6b6c541db58477da6bebc602164a7"
_RUN_HY8_COMMIT = "28e7909afd5ae53c4357380ef70c5f2e482c917d"


def test_hy8_concrete_catalogue_area_differs_from_exact_ellipse() -> None:
    """Do not mistake a nominal HY-8 catalogue ellipse for an exact ellipse."""
    with _AUDIT.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 23
    assert {int(row["row_index_zero_based"]) for row in rows} == set(range(23))

    for row in rows:
        assert row["shape_db_sha256"] == _SHAPE_DB_SHA256
        assert row["run_hy8_commit"] == _RUN_HY8_COMMIT
        span = float(row["span_in"]) * 0.0254
        rise = float(row["rise_in"]) * 0.0254
        geometry = HorizontalEllipseGeometry(span=span, rise=rise)
        exact_area = geometry.area_full
        recorded_exact_area = float(row["exact_ellipse_area_m2"])
        shape_db_area = float(row["shape_db_area_m2"])
        recorded_difference = float(row["shape_db_minus_ellipse_m2"])
        recorded_percent = float(row["shape_db_minus_ellipse_percent"])

        assert recorded_exact_area == pytest.approx(exact_area, abs=1e-9)
        assert shape_db_area > exact_area
        assert recorded_difference == pytest.approx(shape_db_area - exact_area, abs=2e-9)
        assert recorded_percent == pytest.approx(100.0 * (shape_db_area / exact_area - 1.0), abs=1e-4)
