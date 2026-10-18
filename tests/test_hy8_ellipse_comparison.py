"""Check retained executable evidence without requiring HY-8 or its adapter."""

import csv
import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "docs" / "validation_data"
EVIDENCE = DATA / "hy8_8_0_1_2_ellipse"


def _requested_value(report: str, label: str) -> str:
    """Read the requested-flow column after the minimum-flow column."""
    line = next(line for line in report.splitlines() if line.startswith(label + ","))
    return line.split(",")[2].strip()


def test_native_ellipse_evidence_integrity() -> None:
    """Native reports and projects must survive checkout without byte changes."""
    manifest = json.loads((EVIDENCE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["executable_version"] == "8.0.1.2"
    assert manifest["run_hy8"] == "2026.10.18.2"
    assert len(manifest["files"]) == 25
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest


def test_ellipse_fixture_has_requested_positive_barrel_flow() -> None:
    """Check CSV against the requested column of each independent native report."""
    with (DATA / "hy8_8_0_1_2_ellipse_comparison.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected = {f"ellipse-{size}-{flow}" for size in ("83x53", "128x82") for flow in ("low", "mid", "high")}
    assert {row["case_id"] for row in rows} == expected
    assert len(rows) == 6
    for row in rows:
        discharge = float(row["discharge_m3s"])
        assert discharge > 0.0
        assert float(row["hy8_total_discharge_m3s"]) == discharge
        assert float(row["hy8_culvert_discharge_m3s"]) == discharge
        assert float(row["hy8_roadway_discharge_m3s"]) == 0.0
        report = next((EVIDENCE / row["case_id"]).glob("*.rst")).read_text(encoding="utf-8")
        assert float(_requested_value(report, "Total Discharge (cms)")) == discharge
        assert float(_requested_value(report, "RCP Discharge (cms)")) == discharge
        assert float(_requested_value(report, "Roadway Discharge (cms)")) == 0.0
        assert float(_requested_value(report, "Headwater Elevation (m)")) == float(row["hy8_headwater_m"])
        assert float(_requested_value(report, "Outlet Velocity (m/s)")) == float(row["hy8_velocity_ms"])
        assert _requested_value(report, "Flow Type") == row["hy8_flow_type"]
