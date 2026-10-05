"""Retain HY-8 roadway comparisons without calibrating the independent solver.

Run with PYTHONPATH=src and the optional run-hy8 distribution installed. HY-8
adapters and report parsing remain in run-hy8; this script only authors cases,
verifies saved input parity, and compares public hydraulic results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
import zipfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from loguru import logger
from run_hy8 import (
    CircularConcreteInlet,
    FlowDefinition,
    Hy8Executable,
    RoadwayOvertoppingPolicy,
    RoadwayProfile,
    RoadwayShape,
    TailwaterDefinition,
    load_project_from_hy8,
)
from run_hy8 import CulvertBarrel as Hy8Barrel
from run_hy8 import CulvertCrossing as Hy8Crossing
from run_hy8 import CulvertMaterial as Hy8Material
from run_hy8 import RoadwaySurface as Hy8Surface
from run_hy8.hydraulics import FlowSearchError

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
    RoadwayOvertoppingSegmentResult,
    RoadwayProfileWeir,
    RoadwaySurface,
    RoadwayWeir,
    calculate_roadway_overtopping,
    solve_crossing_discharge_for_headwater,
    solve_crossing_hydraulics,
)

COEFFICIENT = 1.6
REPORT_HALF_INCREMENT = 0.005
INPUT_LENGTH_TOLERANCE = 4e-7
INPUT_COEFFICIENT_TOLERANCE = 3e-7
PROFILES: dict[str, tuple[tuple[float, float], ...]] = {
    "constant": ((0.0, 12.0), (20.0, 12.0)),
    "slope": ((0.0, 12.0), (10.0, 12.5), (20.0, 13.0)),
    "sag": ((0.0, 13.0), (5.0, 12.4), (10.0, 12.0), (15.0, 12.3), (20.0, 12.8)),
}


@dataclass(frozen=True, slots=True)
class Case:
    """Explicit SI inputs for one crossing discharge comparison."""

    case_id: str
    profile: str
    discharge: float
    tailwater: float = 9.7
    inlet_invert: float = 10.0
    local_surface: RoadwaySurface | None = None
    hy8_surface: Hy8Surface = Hy8Surface.USER_DEFINED
    target_ratio: float | None = None


def roadway(case: Case) -> RoadwayOvertoppingInput:
    """Construct the public local roadway object."""
    points = PROFILES[case.profile]
    if case.profile == "constant":
        return RoadwayWeir(12.0, 20.0, COEFFICIENT, surface=case.local_surface)
    return RoadwayProfileWeir(
        RoadwayCrestProfile(tuple(RoadwayCrestPoint(*point) for point in points)),
        COEFFICIENT,
        surface=case.local_surface,
    )


def local_crossing(case: Case) -> CulvertCrossing:
    """Build the matched single-barrel concrete crossing."""
    barrel = CulvertBarrel(
        CircularGeometry(1.2),
        length=30.0,
        inlet_invert=case.inlet_invert,
        outlet_invert=9.7,
        roughness=0.012,
        material=CONCRETE,
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
        entrance_loss_coefficient=PIPE_LOSS_SQUARE_EDGE,
    )
    return CulvertCrossing(groups=(CulvertGroup(barrel, 1),), roadway=roadway(case))


def cases() -> tuple[Case, ...]:
    """Cover free activation, partially wet profiles, coupling and submergence."""
    matrix: list[Case] = []
    for profile in PROFILES:
        matrix.extend(Case(f"road-only-{profile}-{q:g}", profile, q, inlet_invert=15.0) for q in (0.1, 1.0, 10.0, 20.0))
        matrix.extend(Case(f"combined-{profile}-{q:g}", profile, q) for q in (1.0, 3.45, 4.0, 8.0, 20.0))
    for surface in RoadwaySurface:
        for ratio in (0.5, 0.8, 0.9, 0.98, 0.99):
            seed = Case("seed", "constant", 1.0, 12.0 + ratio, local_surface=surface)
            discharge = solve_crossing_discharge_for_headwater(local_crossing(seed), 13.0, seed.tailwater)
            matrix.extend(
                replace(
                    seed,
                    case_id=f"sub-{surface.value}-{external.name.lower()}-{ratio:g}",
                    discharge=discharge,
                    hy8_surface=external,
                    target_ratio=ratio,
                )
                for external in (Hy8Surface.USER_DEFINED, Hy8Surface[surface.name])
            )
    return tuple(matrix)


def hy8_crossing(case: Case) -> Hy8Crossing:
    """Author HY-8 inputs using only the supported adapter API."""
    points = PROFILES[case.profile]
    crossing = Hy8Crossing(
        name=case.case_id,
        flow=FlowDefinition(user_values=[case.discharge]),
        tailwater=TailwaterDefinition(constant_elevation=case.tailwater, invert_elevation=9.7),
        roadway=RoadwayProfile(
            width=10.0,
            shape=RoadwayShape.CONSTANT if case.profile == "constant" else RoadwayShape.IRREGULAR,
            stations=[p[0] for p in points],
            elevations=[p[1] for p in points],
            surface=case.hy8_surface,
            discharge_coefficient=COEFFICIENT,
        ),
    )
    crossing.add_barrel(
        Hy8Barrel(
            name="RCP",
            span=1.2,
            rise=1.2,
            material=Hy8Material.CONCRETE,
            inlet_configuration=CircularConcreteInlet.SQUARE_EDGE_WITH_HEADWALL,
            inlet_invert_elevation=case.inlet_invert,
            outlet_invert_elevation=9.7,
            outlet_invert_station=30.0,
            manning_n_top=0.012,
            manning_n_bottom=0.012,
        )
    )
    return crossing


def verify_saved(case: Case, project_path: Path, *, check_discharge: bool = True) -> None:
    """Reject changed geometry, boundary, coefficient or inlet configuration."""
    expected = hy8_crossing(case)
    saved = load_project_from_hy8(project_path).crossings[0]
    if saved.roadway.shape != expected.roadway.shape or saved.roadway.surface != case.hy8_surface:
        message = f"HY-8 changed roadway shape/surface for {case.case_id}."
        raise ValueError(message)
    pairs = [
        *zip(saved.roadway.stations, expected.roadway.stations, strict=True),
        *zip(saved.roadway.elevations, expected.roadway.elevations, strict=True),
        (saved.roadway.width, 10.0),
        (saved.tailwater.constant_elevation, case.tailwater),
        (saved.tailwater.invert_elevation, 9.7),
    ]
    if any(not math.isfinite(a) or abs(a - b) > INPUT_LENGTH_TOLERANCE for a, b in pairs):
        message = f"HY-8 changed roadway geometry/tailwater for {case.case_id}."
        raise ValueError(message)
    coefficient = saved.roadway.discharge_coefficient
    if coefficient is None or abs(coefficient - COEFFICIENT) > INPUT_COEFFICIENT_TOLERANCE:
        message = f"HY-8 did not preserve the coefficient card for {case.case_id}."
        raise ValueError(message)
    if len(saved.culverts) != 1:
        message = "Expected one saved culvert."
        raise ValueError(message)
    actual, requested = saved.culverts[0], expected.culverts[0]
    for name in (
        "span",
        "rise",
        "inlet_invert_elevation",
        "outlet_invert_elevation",
        "outlet_invert_station",
        "inlet_invert_station",
        "manning_n_top",
        "manning_n_bottom",
        "roadway_station",
    ):
        if abs(getattr(actual, name) - getattr(requested, name)) > INPUT_LENGTH_TOLERANCE:
            message = f"HY-8 changed culvert {name} for {case.case_id}."
            raise ValueError(message)
    if (
        actual.inlet_configuration != requested.inlet_configuration
        or actual.material != requested.material
        or actual.shape != requested.shape
        or actual.number_of_barrels != 1
    ):
        message = f"HY-8 changed the culvert semantic configuration for {case.case_id}."
        raise ValueError(message)
    if check_discharge and min(abs(q - case.discharge) for q in saved.flow.sequence()) > INPUT_LENGTH_TOLERANCE:
        message = f"HY-8 did not retain requested discharge for {case.case_id}."
        raise ValueError(message)


def segment_evidence(segment: RoadwayOvertoppingSegmentResult) -> dict[str, object]:
    """Retain physical, integration and hydraulic state fields with provenance."""
    return {
        **asdict(segment),
        "physical_interval_length": segment.physical_interval_length,
        "unit_discharge": segment.unit_discharge,
        "flow_state": segment.flow_state.value,
        "submergence_ratio": segment.submergence_ratio,
        "submergence_factor": segment.submergence_factor,
    }


def free_report_band(case: Case, headwater: float) -> tuple[float, float]:
    """Propagate report head rounding and coefficient-card rounding into flow."""
    road = roadway(case)
    bounds: list[float] = []
    for sign in (-1, 1):
        bounded_road = replace(road, discharge_coefficient=COEFFICIENT + sign * INPUT_COEFFICIENT_TOLERANCE)
        result = calculate_roadway_overtopping(bounded_road, headwater + sign * REPORT_HALF_INCREMENT, case.tailwater)
        bounds.append(result.discharge + sign * REPORT_HALF_INCREMENT)
    return bounds[0], bounds[1]


def compare(case: Case, executable: Hy8Executable, workspace: Path) -> dict[str, str]:
    """Execute one case and retain separate roadway and coupling evidence."""
    folder = workspace / case.case_id
    result = hy8_crossing(case).hw_from_q(
        case.discharge,
        hy8=executable,
        workspace=folder,
        keep_files=True,
        roadway_overtopping=RoadwayOvertoppingPolicy.ALLOW,
    )
    row = result.row
    if row is None or len(row.culverts) != 1:
        message = f"HY-8 omitted the selected row/culvert for {case.case_id}."
        raise ValueError(message)
    if any(
        not math.isfinite(v)
        for v in (
            row.flow,
            row.headwater_elevation,
            row.roadway_discharge,
            row.culverts[0].discharge,
            row.culverts[0].outlet_velocity,
        )
    ):
        message = f"Nonfinite HY-8 result for {case.case_id}."
        raise ValueError(message)
    if abs(row.flow - case.discharge) > REPORT_HALF_INCREMENT + INPUT_LENGTH_TOLERANCE:
        message = f"HY-8 selected a different discharge for {case.case_id}."
        raise ValueError(message)
    project = next(folder.glob("*.hy8"))
    verify_saved(case, project)
    local = solve_crossing_hydraulics(local_crossing(case), case.discharge, case.tailwater)
    data = {
        "case_id": case.case_id,
        "profile": case.profile,
        "points_json": json.dumps(PROFILES[case.profile]),
        "inlet_invert_m": str(case.inlet_invert),
        "requested_discharge_m3s": str(case.discharge),
        "tailwater_m": str(case.tailwater),
        "coefficient_si": str(COEFFICIENT),
        "local_surface": "" if case.local_surface is None else case.local_surface.value,
        "hy8_surface": case.hy8_surface.name,
        "target_ratio": str(case.target_ratio or ""),
        "local_headwater_m": str(local.headwater_elevation),
        "hy8_headwater_m": str(row.headwater_elevation),
        "headwater_difference_m": str(local.headwater_elevation - row.headwater_elevation),
        "local_roadway_m3s": str(local.roadway_discharge),
        "hy8_roadway_m3s": str(row.roadway_discharge),
        "roadway_difference_m3s": str(local.roadway_discharge - row.roadway_discharge),
        "local_culvert_m3s": str(local.culvert_discharge),
        "hy8_culvert_m3s": str(row.culverts[0].discharge),
        "culvert_difference_m3s": str(local.culvert_discharge - row.culverts[0].discharge),
        "local_velocity_ms": str(local.group_results[0].barrel_result.velocity_outlet),
        "hy8_velocity_ms": str(row.culverts[0].outlet_velocity),
        "local_regime": local.group_results[0].barrel_result.regime.value,
        "hy8_flow_type": row.culverts[0].flow_type,
        "local_closure_m3s": str(local.culvert_discharge + local.roadway_discharge - case.discharge),
        "hy8_total_m3s": str(row.flow),
        "hy8_closure_m3s": str(row.culverts[0].discharge + row.roadway_discharge - row.flow),
        "hy8_closure_classification": "externally corroborated"
        if abs(row.culverts[0].discharge + row.roadway_discharge - row.flow) <= 0.0151
        else "external-software behaviour unresolved",
        "local_segments_json": json.dumps([segment_evidence(s) for s in local.roadway_result.segment_results])
        if local.roadway_result is not None
        else "[]",
        "local_road_at_hy8_hw_m3s": "",
        "free_report_lower_m3s": "",
        "free_report_upper_m3s": "",
        "roadway_classification": "unsupported comparison",
        "crossing_classification": "unsupported comparison",
        "disposition": "Surface and fixed-coefficient submergence cannot be matched independently in HY-8.",
        "project_sha256": hashlib.sha256(project.read_bytes()).hexdigest(),
        "rst_sha256": hashlib.sha256(project.with_suffix(".rst").read_bytes()).hexdigest(),
        "rsql_sha256": hashlib.sha256(project.with_suffix(".rsql").read_bytes()).hexdigest(),
    }
    if case.local_surface is None:
        at_external = calculate_roadway_overtopping(roadway(case), row.headwater_elevation, case.tailwater)
        lower, upper = free_report_band(case, row.headwater_elevation)
        classification = (
            "externally corroborated"
            if lower <= row.roadway_discharge <= upper
            else "external-software behaviour unresolved"
        )
        data.update(
            local_road_at_hy8_hw_m3s=str(at_external.discharge),
            free_report_lower_m3s=str(lower),
            free_report_upper_m3s=str(upper),
            roadway_classification=classification,
            crossing_classification=classification
            if case.inlet_invert == 15.0
            else "external-software behaviour unresolved",
            disposition="Roadway evaluated at external reported stage; crossing differences retained separately.",
        )
    return data


def boundary_rows(executable: Hy8Executable, workspace: Path) -> list[dict[str, str]]:
    """Retain boundary outcomes without equating rounded stages to exact stages."""
    inputs = (
        ("crest", 12.0, 9.7, None, 3.45),
        ("equal", 13.0, 13.0, RoadwaySurface.PAVED, 1.0),
        ("supported-0.98", 13.0, 12.98, RoadwaySurface.PAVED, 19.2),
        ("supported-0.99", 13.0, 12.99, RoadwaySurface.PAVED, 16.0),
        ("gap-0.995", 13.0, 12.995, RoadwaySurface.PAVED, 16.0),
        ("reverse", 12.9, 13.0, RoadwaySurface.PAVED, 1.0),
        ("missing-surface", 13.0, 12.9, None, 30.0),
    )
    rows: list[dict[str, str]] = []
    for name, headwater, tailwater, surface, hint in inputs:
        case = Case(f"boundary-{name}", "constant", hint, tailwater, local_surface=surface)
        data = {
            "case_id": name,
            "requested_headwater_m": str(headwater),
            "tailwater_m": str(tailwater),
            "local_surface": "" if surface is None else surface.value,
            "local_outcome": "",
            "local_roadway_m3s": "",
            "local_error": "",
            "local_segments_json": "[]",
            "hy8_outcome": "",
            "hy8_headwater_m": "",
            "hy8_total_m3s": "",
            "hy8_roadway_m3s": "",
            "hy8_error": "",
            "classification": "external-software behaviour unresolved",
            "disposition": "Inverse search uses 0.01 m stage tolerance and a positive 0.05 m3/s seed; exact-stage behaviour cannot be inferred.",
        }
        try:
            local = calculate_roadway_overtopping(roadway(case), headwater, tailwater)
        except InvalidInputError as exc:
            data.update(local_outcome="rejected", local_error=str(exc))
        else:
            data.update(
                local_outcome="value",
                local_roadway_m3s=str(local.discharge),
                local_segments_json=json.dumps([segment_evidence(s) for s in local.segment_results]),
            )
        folder = workspace / case.case_id
        try:
            result = hy8_crossing(case).q_from_hw(
                headwater,
                q_hint=hint,
                hy8=executable,
                workspace=folder,
                keep_files=True,
                roadway_overtopping=RoadwayOvertoppingPolicy.ALLOW,
            )
        except FlowSearchError as exc:
            data.update(hy8_outcome="inverse search failed", hy8_error=str(exc))
        else:
            row = result.row
            if row is None:
                message = f"HY-8 omitted boundary result {name}."
                raise ValueError(message)
            data.update(
                hy8_outcome="value",
                hy8_headwater_m=str(row.headwater_elevation),
                hy8_total_m3s=str(row.flow),
                hy8_roadway_m3s=str(row.roadway_discharge),
            )
        for project in folder.glob("*.hy8"):
            verify_saved(case, project, check_discharge=False)
        if name in ("supported-0.98", "supported-0.99", "missing-surface"):
            data.update(
                classification="unsupported comparison",
                disposition="No independently matched paved correction or missing-surface equivalent in HY-8 USER_DEFINED mode.",
            )
        rows.append(data)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write uniform evidence rows using UTF-8 and explicit CSV escaping."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Write compact CSV and exact execution identity alongside ignored raw files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hy8", type=Path)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--adapter-commit", required=True)
    parser.add_argument("--local-commit", required=True)
    args = parser.parse_args()
    logger.disable("run_hy8")
    distribution = importlib.metadata.distribution("run-hy8")
    with zipfile.ZipFile(args.wheel) as wheel:
        for name in wheel.namelist():
            if name.startswith("run_hy8/") and name.endswith((".py", "py.typed")):
                installed = Path(str(distribution.locate_file(name))).read_bytes().replace(b"\r\n", b"\n")
                if installed != wheel.read(name).replace(b"\r\n", b"\n"):
                    message = f"Installed adapter differs from pinned wheel: {name}."
                    raise ValueError(message)
    executable = Hy8Executable(args.hy8)
    matrix = cases()
    rows: list[dict[str, str]] = []
    for case in matrix:
        rows.append(compare(case, executable, args.workspace))
        print(f"{case.case_id}: {rows[-1]['roadway_classification']}", file=sys.stderr)
    write_csv(args.output, rows)
    boundary_path = args.output.with_stem(args.output.stem + "_boundaries")
    write_csv(boundary_path, boundary_rows(executable, args.workspace))
    identity = {
        "date": "2026-10-06",
        "local_commit": args.local_commit,
        "adapter_commit": args.adapter_commit,
        "wheel_sha256": hashlib.sha256(args.wheel.read_bytes()).hexdigest(),
        "installed_source_matches_wheel": True,
        "shared_inputs": {
            "diameter_m": 1.2,
            "length_m": 30.0,
            "outlet_invert_m": 9.7,
            "roughness": 0.012,
            "barrels": 1,
            "inlet": "circular concrete square edge with headwall",
            "top_width_m": 10.0,
            "exit_loss_option": 0,
            "profile_option": "HY-8 default",
            "display_units": "SI",
            "coefficient_si": COEFFICIENT,
        },
        "python": platform.python_version(),
        "windows": platform.platform(),
        "run_hy8_version": distribution.version,
        "hy8_sha256": hashlib.sha256(executable.exe_path.read_bytes()).hexdigest(),
        "installed_package_hashes": {
            str(path): hashlib.sha256(Path(str(distribution.locate_file(path))).read_bytes()).hexdigest()
            for path in distribution.files or ()
            if str(path).startswith("run_hy8/") and str(path).endswith(".py")
        },
        "case_count": len(rows),
        "boundary_csv_sha256": hashlib.sha256(boundary_path.read_bytes()).hexdigest(),
        "boundary_artifact_hashes": {
            str(path.relative_to(args.workspace)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(args.workspace.glob("boundary-*/*"))
            if path.suffix in (".hy8", ".rst", ".rsql")
        },
        "csv_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }
    args.output.with_suffix(".json").write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
