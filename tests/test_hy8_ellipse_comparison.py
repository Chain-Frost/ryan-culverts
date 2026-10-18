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


def test_retained_sweep_integrity_and_native_hydraulics() -> None:
    """Audit all sweep rows against native reports and preserve the original baseline."""
    evidence = DATA / "hy8_8_0_1_2_ellipse_sweep"
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["case_count"] == 18
    assert len(manifest["files"]) == 73
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((evidence / name).read_bytes()).hexdigest() == digest
    with (evidence / "comparison.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    with (DATA / "hy8_8_0_1_2_ellipse_comparison.csv").open(encoding="utf-8", newline="") as stream:
        baseline = list(csv.DictReader(stream))
    assert len(rows) == 18
    assert len({row["case_id"] for row in rows}) == 18
    for row, original in zip(rows[:6], baseline, strict=True):
        assert {key: row[key] for key in original} == original
    for row in rows:
        case = evidence / row["case_id"]
        for extension in ("hy8", "rst", "rsql", "plt"):
            assert len(list(case.glob(f"*.{extension}"))) == 1
        report = next(case.glob("*.rst")).read_text(encoding="utf-8")
        discharge = float(row["discharge_m3s"])
        assert discharge > 0
        for label in ("Total Discharge (cms)", "RCP Discharge (cms)"):
            assert float(_requested_value(report, label)) == discharge
        assert float(_requested_value(report, "Roadway Discharge (cms)")) == 0.0
        assert float(row["hy8_culvert_discharge_m3s"]) == discharge
        assert float(row["hy8_total_discharge_m3s"]) == discharge
        assert float(row["hy8_roadway_discharge_m3s"]) == 0.0
        assert float(_requested_value(report, "Headwater Elevation (m)")) == float(row["hy8_headwater_m"])
        assert float(_requested_value(report, "Outlet Velocity (m/s)")) == float(row["hy8_velocity_ms"])
        assert _requested_value(report, "Flow Type") == row["hy8_flow_type"]
        full = float(_requested_value(report, "Length Full (m)"))
        free = float(_requested_value(report, "Length Free (m) "))
        assert full >= 0
        assert free >= 0
        assert abs(full + free - 30.0) <= 0.011


def test_targeted_critical_sweep_native_evidence() -> None:
    """Keep five new cases and two anchors auditable against their full native curves."""
    evidence = DATA / "hy8_8_0_1_2_ellipse_critical"
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((evidence / name).read_bytes()).hexdigest() == digest
    with (evidence / "diagnostics.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [float(row["discharge_m3s"]) for row in rows] == [25, 28, 30, 32, 34, 35, 36]
    curves = json.loads((evidence / "curves.json").read_text(encoding="utf-8"))
    for row in rows:
        q = float(row["discharge_m3s"])
        case = evidence / row["case_id"]
        report = next(case.glob("*.rst")).read_text(encoding="utf-8")
        assert float(_requested_value(report, "RCP Discharge (cms)")) == q
        assert float(_requested_value(report, "Roadway Discharge (cms)")) == 0
        assert float(_requested_value(report, "Headwater Elevation (m)")) == float(row["hy8_headwater_m"])
        assert float(_requested_value(report, "Outlet Velocity (m/s)")) == float(row["hy8_velocity_ms"])
        lines = next(case.glob("*.plt")).read_text(encoding="utf-8").split("FlowProfile: 1")[1].splitlines()
        extracted: dict[str, list[list[float]]] = {}
        series = ""
        for line in lines:
            if line.startswith("Series:"):
                series = line.split(":", 1)[1].strip()
                extracted[series] = []
            elif line.startswith("point:"):
                extracted[series].append([float(value) for value in line.split(":", 1)[1].split()])
        assert extracted == curves[str(q)]["series"]
        for name in ("Critical", "Normal", "Profile", "Headwater"):
            for position, point in (("first", extracted[name][0]), ("last", extracted[name][-1])):
                prefix = f"hy8_{name.lower()}_{position}"
                assert float(row[prefix + "_station_m"]) == point[0]
                assert float(row[prefix + "_elevation_m"]) == point[1]
        if q in (25, 35):
            for native in case.iterdir():
                original = DATA / "hy8_8_0_1_2_ellipse_sweep" / row["case_id"] / native.name
                assert native.read_bytes() == original.read_bytes()
