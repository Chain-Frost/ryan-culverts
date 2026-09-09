"""Run a focused ryan-culverts versus HY-8 headwater comparison.

This is external verification tooling, not a runtime dependency of the hydraulic
library. Run with the current run-hy8 source tree on ``PYTHONPATH`` when validating
against a particular run-hy8 commit.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TextIO

from run_hy8 import (
    CircularConcreteInlet,
    CircularCorrugatedSteelInlet,
    ConcreteBoxInlet,
    Hy8CulvertResult,
    Hy8Executable,
    RoadwayProfile,
    TailwaterDefinition,
)
from run_hy8 import (
    CulvertBarrel as Hy8Barrel,
)
from run_hy8 import (
    CulvertCrossing as Hy8Crossing,
)
from run_hy8 import (
    CulvertMaterial as Hy8Material,
)
from run_hy8 import (
    CulvertShape as Hy8Shape,
)

from culvert_solver import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    BOX_LOSS_FLARED_30_75,
    CIRCULAR_CMP_HEADWALL,
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    CONCRETE,
    CORRUGATED_STEEL,
    PIPE_CMP_LOSS_HEADWALL,
    PIPE_LOSS_SQUARE_EDGE,
    CircularGeometry,
    CulvertBarrel,
    RectangularGeometry,
    solve_barrel_hydraulics,
)

HY8_REPORT_TOLERANCE = 0.0051
HY8_LENGTH_BALANCE_TOLERANCE = 0.011


@dataclass(frozen=True, slots=True)
class ComparisonCase:
    """One deliberately matched single-group calculation case."""

    case_id: str
    kind: CaseKind
    span: float
    rise: float
    length: float
    inlet_invert: float
    outlet_invert: float
    roughness: float
    tailwater: float
    discharge: float


@dataclass(frozen=True, slots=True)
class LocalComparisonResult:
    """Local fields retained for direct comparison with HY-8 diagnostics."""

    headwater: float
    velocity: float
    outlet_depth: float
    inlet_control_depth: float
    outlet_control_depth: float | None
    control: str
    regime: str
    profile_curve: str
    hydraulic_jump_station: float | None
    full_flow_length: float
    warning_codes: str


class CaseKind(StrEnum):
    """Shape/material combinations supported by this initial matrix."""

    CIRCULAR_CONCRETE = "circular_concrete"
    CIRCULAR_CSP = "circular_csp"
    CONCRETE_BOX = "concrete_box"


CASES: tuple[ComparisonCase, ...] = (
    ComparisonCase(
        "cc-low-q-low-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        9.7,
        0.25,
    ),
    ComparisonCase(
        "cc-mid-q-low-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        9.7,
        1.00,
    ),
    ComparisonCase(
        "cc-high-q-low-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        9.7,
        2.00,
    ),
    ComparisonCase(
        "cc-transition-low-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        9.7,
        2.565404273733758,
    ),
    ComparisonCase(
        "cc-mid-q-mid-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        10.3,
        1.00,
    ),
    ComparisonCase(
        "cc-mid-q-jump-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        10.45,
        1.00,
    ),
    ComparisonCase(
        "cc-mid-q-s1-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        10.70,
        1.00,
    ),
    ComparisonCase(
        "cc-long-high-q-low-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        100.0,
        10.0,
        9.9,
        0.012,
        9.9,
        3.00,
    ),
    ComparisonCase(
        "cc-high-q-high-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        11.2,
        2.00,
    ),
    ComparisonCase(
        "cc-mid-q-shallow-submerged-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        10.901,
        1.00,
    ),
    ComparisonCase(
        "cc-high-q-shallow-submerged-tw",
        CaseKind.CIRCULAR_CONCRETE,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.012,
        10.901,
        3.00,
    ),
    ComparisonCase(
        "csp-mid-q-low-tw",
        CaseKind.CIRCULAR_CSP,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.020,
        9.7,
        1.00,
    ),
    ComparisonCase(
        "csp-high-q-low-tw",
        CaseKind.CIRCULAR_CSP,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.020,
        9.7,
        2.00,
    ),
    ComparisonCase(
        "csp-high-q-high-tw",
        CaseKind.CIRCULAR_CSP,
        1.2,
        1.2,
        30.0,
        10.0,
        9.7,
        0.020,
        11.2,
        2.00,
    ),
    ComparisonCase(
        "csp-type6-free-outfall",
        CaseKind.CIRCULAR_CSP,
        0.9,
        0.9,
        10.0,
        100.2,
        100.0,
        0.020,
        100.1,
        4.63,
    ),
    ComparisonCase(
        "box-low-q-low-tw",
        CaseKind.CONCRETE_BOX,
        2.4,
        1.2,
        25.0,
        20.0,
        19.75,
        0.012,
        19.75,
        0.50,
    ),
    ComparisonCase(
        "box-mid-q-low-tw",
        CaseKind.CONCRETE_BOX,
        2.4,
        1.2,
        25.0,
        20.0,
        19.75,
        0.012,
        19.75,
        3.00,
    ),
    ComparisonCase(
        "box-high-q-low-tw",
        CaseKind.CONCRETE_BOX,
        2.4,
        1.2,
        25.0,
        20.0,
        19.75,
        0.012,
        19.75,
        6.00,
    ),
    ComparisonCase(
        "box-transition-low-tw",
        CaseKind.CONCRETE_BOX,
        2.4,
        1.2,
        25.0,
        20.0,
        19.75,
        0.012,
        19.75,
        6.532748339100821,
    ),
    ComparisonCase(
        "box-high-q-high-tw",
        CaseKind.CONCRETE_BOX,
        2.4,
        1.2,
        25.0,
        20.0,
        19.75,
        0.012,
        21.2,
        6.00,
    ),
)


def _hy8_crossing(case: ComparisonCase) -> Hy8Crossing:
    """Translate a comparison case to a matched run-hy8 crossing."""
    if case.kind is CaseKind.CIRCULAR_CONCRETE:
        shape = Hy8Shape.CIRCLE
        material = Hy8Material.CONCRETE
        inlet = CircularConcreteInlet.SQUARE_EDGE_WITH_HEADWALL
    elif case.kind is CaseKind.CIRCULAR_CSP:
        shape = Hy8Shape.CIRCLE
        material = Hy8Material.CORRUGATED_STEEL
        inlet = CircularCorrugatedSteelInlet.SQUARE_EDGE_WITH_HEADWALL
    else:
        shape = Hy8Shape.BOX
        material = Hy8Material.CONCRETE
        inlet = ConcreteBoxInlet.SQUARE_EDGE_30_TO_75_DEG_WINGWALL
    crossing = Hy8Crossing(name=case.case_id)
    crossing.tailwater = TailwaterDefinition(
        constant_elevation=case.tailwater,
        invert_elevation=case.outlet_invert,
    )
    # Keep roadway overtopping out of this single-barrel comparison.  Roadway
    # flow is a separate calculation and a fixed crest can invalidate cases
    # whose arbitrary datum happens to be higher.
    roadway_crest = max(case.inlet_invert, case.tailwater) + 10.0
    crossing.roadway = RoadwayProfile(
        width=10.0,
        stations=[-10.0, 0.0, 10.0],
        elevations=[roadway_crest, roadway_crest, roadway_crest],
    )
    crossing.culverts.append(
        Hy8Barrel(
            name="RCP",
            span=case.span,
            rise=case.rise,
            shape=shape,
            material=material,
            inlet_configuration=inlet,
            inlet_invert_station=0.0,
            outlet_invert_station=case.length,
            inlet_invert_elevation=case.inlet_invert,
            outlet_invert_elevation=case.outlet_invert,
            roadway_station=0.0,
            manning_n_top=case.roughness,
            manning_n_bottom=case.roughness,
        )
    )
    return crossing


def _local_result(case: ComparisonCase) -> LocalComparisonResult:
    """Run the local solver with coefficient choices matched to HY-8."""
    if case.kind is CaseKind.CIRCULAR_CONCRETE:
        geometry = CircularGeometry(diameter=case.span)
        material = CONCRETE
        inlet = CIRCULAR_CONCRETE_SQUARE_EDGE
        entrance_loss = PIPE_LOSS_SQUARE_EDGE
    elif case.kind is CaseKind.CIRCULAR_CSP:
        geometry = CircularGeometry(diameter=case.span)
        material = CORRUGATED_STEEL
        inlet = CIRCULAR_CMP_HEADWALL
        entrance_loss = PIPE_CMP_LOSS_HEADWALL
    else:
        geometry = RectangularGeometry(span=case.span, rise=case.rise)
        material = CONCRETE
        inlet = BOX_CONCRETE_FLARED_WINGWALLS_30_75
        entrance_loss = BOX_LOSS_FLARED_30_75
    barrel = CulvertBarrel(
        geometry=geometry,
        length=case.length,
        inlet_invert=case.inlet_invert,
        outlet_invert=case.outlet_invert,
        roughness=case.roughness,
        material=material,
        inlet_coefficients=inlet,
        entrance_loss_coefficient=entrance_loss,
    )
    result = solve_barrel_hydraulics(barrel, case.discharge, case.tailwater)
    if result.inlet_control_headwater_elevation is None:
        raise RuntimeError(f"Local solver omitted inlet-control depth for {case.case_id}.")
    outlet_control_depth = (
        result.outlet_control_headwater_elevation - case.inlet_invert
        if result.outlet_control_headwater_elevation is not None
        else None
    )
    return LocalComparisonResult(
        headwater=result.headwater_elevation,
        velocity=result.velocity_outlet,
        outlet_depth=result.outlet_depth,
        inlet_control_depth=result.inlet_control_headwater_elevation - case.inlet_invert,
        outlet_control_depth=outlet_control_depth,
        control=result.control_type.value,
        regime=result.regime.value,
        profile_curve=result.profile_curve.value if result.profile_curve is not None else "",
        hydraulic_jump_station=result.hydraulic_jump_station,
        full_flow_length=result.full_flow_length,
        warning_codes=";".join(warning.code.value for warning in result.warnings),
    )


def _validated_hy8_culvert(
    *,
    case: ComparisonCase,
    row_flow: float,
    row_velocity: float,
    row_flow_type: str,
    culverts: list[Hy8CulvertResult],
) -> Hy8CulvertResult:
    """Validate and return the single per-culvert diagnostic record."""
    if len(culverts) != 1:
        raise RuntimeError(
            f"HY-8 returned {len(culverts)} culvert records for single-culvert case {case.case_id}."
        )
    culvert = culverts[0]
    if culvert.index != 0:
        raise RuntimeError(f"HY-8 returned culvert index {culvert.index!r} for {case.case_id}.")
    numeric_values = (
        culvert.discharge,
        culvert.inlet_control_depth,
        culvert.outlet_control_depth,
        culvert.full_length,
        culvert.free_length,
        culvert.outlet_velocity,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise RuntimeError(f"HY-8 returned incomplete culvert diagnostics for {case.case_id}.")
    if abs(culvert.discharge - row_flow) > HY8_REPORT_TOLERANCE:
        raise RuntimeError(
            f"HY-8 culvert discharge disagrees with crossing flow for {case.case_id}."
        )
    if abs(culvert.outlet_velocity - row_velocity) > HY8_REPORT_TOLERANCE:
        raise RuntimeError(
            f"HY-8 culvert velocity disagrees with crossing velocity for {case.case_id}."
        )
    if culvert.flow_type != row_flow_type:
        raise RuntimeError(f"HY-8 culvert and crossing flow types disagree for {case.case_id}.")
    if culvert.full_length < 0.0 or culvert.free_length < 0.0:
        raise RuntimeError(f"HY-8 returned a negative barrel length for {case.case_id}.")
    reported_length = culvert.full_length + culvert.free_length
    if abs(reported_length - case.length) > HY8_LENGTH_BALANCE_TOLERANCE:
        raise RuntimeError(
            f"HY-8 full/free lengths total {reported_length!r}, not {case.length!r}, "
            f"for {case.case_id}."
        )
    return culvert


def parse_args() -> argparse.Namespace:
    """Parse command-line options for HY-8 execution and artifact retention."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hy8", type=Path, help="Explicit HY864.exe path")
    parser.add_argument("--workspace", type=Path, help="Keep HY-8 projects and reports here")
    parser.add_argument("--output", type=Path, help="Write UTF-8 CSV here instead of stdout")
    return parser.parse_args()


def _write_matrix(args: argparse.Namespace, output: TextIO) -> None:
    """Execute all cases and write comparison rows to an open text stream."""
    executable = Hy8Executable(args.hy8) if args.hy8 is not None else Hy8Executable()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "case_id",
            "discharge_m3s",
            "tailwater_m",
            "local_headwater_m",
            "hy8_headwater_m",
            "headwater_difference_m",
            "local_velocity_ms",
            "hy8_velocity_ms",
            "velocity_difference_ms",
            "local_outlet_depth_m",
            "local_inlet_control_depth_m",
            "local_outlet_control_depth_m",
            "local_control",
            "local_regime",
            "local_profile_curve",
            "local_hydraulic_jump_station_m",
            "local_full_flow_length_m",
            "local_warning_codes",
            "hy8_flow_type",
            "hy8_inlet_control_depth_m",
            "hy8_inlet_control_depth_qualifier",
            "hy8_outlet_control_depth_m",
            "hy8_outlet_control_depth_qualifier",
            "hy8_full_length_m",
            "hy8_free_length_m",
            "inlet_control_depth_difference_m",
            "outlet_control_depth_difference_m",
            "full_flow_length_difference_m",
        )
    )
    for case in CASES:
        local = _local_result(case)
        case_workspace = args.workspace / case.case_id if args.workspace is not None else None
        hy8_result = _hy8_crossing(case).hw_from_q(
            case.discharge,
            hy8=executable,
            workspace=case_workspace,
            keep_files=case_workspace is not None,
        )
        if hy8_result.row is None:
            raise RuntimeError(f"HY-8 returned no result row for {case.case_id}.")
        row = hy8_result.row
        # HY-8 reports flow and roadway discharge to 0.01 m3/s. Fail closed if
        # nearest-row selection or an unexpectedly low road crest changed the case.
        if not math.isfinite(row.flow) or abs(row.flow - case.discharge) > HY8_REPORT_TOLERANCE:
            raise RuntimeError(
                f"HY-8 row flow {row.flow!r} does not match requested flow "
                f"{case.discharge!r} for {case.case_id}."
            )
        if (
            not math.isfinite(row.roadway_discharge)
            or abs(row.roadway_discharge) > HY8_REPORT_TOLERANCE
        ):
            raise RuntimeError(
                f"HY-8 reported roadway discharge {row.roadway_discharge!r} "
                f"for non-overtopping case {case.case_id}."
            )
        if not math.isfinite(row.headwater_elevation) or not math.isfinite(row.velocity):
            raise RuntimeError(f"HY-8 returned non-finite hydraulics for {case.case_id}.")
        hy8_culvert = _validated_hy8_culvert(
            case=case,
            row_flow=row.flow,
            row_velocity=row.velocity,
            row_flow_type=row.flow_type,
            culverts=row.culverts,
        )
        writer.writerow(
            (
                case.case_id,
                case.discharge,
                case.tailwater,
                local.headwater,
                row.headwater_elevation,
                local.headwater - row.headwater_elevation,
                local.velocity,
                row.velocity,
                local.velocity - row.velocity,
                local.outlet_depth,
                local.inlet_control_depth,
                local.outlet_control_depth,
                local.control,
                local.regime,
                local.profile_curve,
                local.hydraulic_jump_station,
                local.full_flow_length,
                local.warning_codes,
                hy8_culvert.flow_type,
                hy8_culvert.inlet_control_depth,
                hy8_culvert.inlet_control_depth_qualifier,
                hy8_culvert.outlet_control_depth,
                hy8_culvert.outlet_control_depth_qualifier,
                hy8_culvert.full_length,
                hy8_culvert.free_length,
                local.inlet_control_depth - hy8_culvert.inlet_control_depth,
                (
                    local.outlet_control_depth - hy8_culvert.outlet_control_depth
                    if local.outlet_control_depth is not None
                    else None
                ),
                local.full_flow_length - hy8_culvert.full_length,
            )
        )


def main() -> int:
    """Execute all cases and emit an ordinary UTF-8 CSV comparison matrix."""
    args = parse_args()
    if args.output is None:
        _write_matrix(args, sys.stdout)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="") as output:
            _write_matrix(args, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
