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
from dataclasses import dataclass, replace
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
    CulvertCrossing,
    CulvertGroup,
    RectangularGeometry,
    solve_barrel_hydraulics,
    solve_crossing_hydraulics,
)

HY8_REPORT_TOLERANCE = 0.0051
HY8_LENGTH_BALANCE_TOLERANCE = 0.011
HETEROGENEOUS_DISCHARGES: tuple[float, ...] = (0.5, 1.0, 2.0, 3.0, 5.0, 8.0)


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

DISCREPANCY_SWEEP_DISCHARGES: dict[str, tuple[float, ...]] = {
    "cc-long-high-q-low-tw": (
        2.6,
        2.7,
        2.8,
        2.9,
        3.0,
        3.1,
        3.2,
        3.21,
        3.22,
        3.23,
        3.24,
        3.25,
        3.26,
        3.27,
        3.28,
        3.29,
        3.3,
        3.4,
    ),
    "csp-type6-free-outfall": (3.8, 4.0, 4.2, 4.4, 4.6, 4.63, 4.8, 5.0, 5.2),
}


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


def _hy8_heterogeneous_crossing() -> Hy8Crossing:
    """Return the version-pinned mixed circular/box comparison crossing."""
    crossing = Hy8Crossing(name="mixed-relief-crossing")
    crossing.tailwater = TailwaterDefinition(constant_elevation=99.0, invert_elevation=99.0)
    crossing.roadway = RoadwayProfile(
        width=10.0,
        stations=[-10.0, 0.0, 10.0],
        elevations=[120.0, 120.0, 120.0],
    )
    crossing.culverts.extend(
        (
            Hy8Barrel(
                name="circular",
                span=1.0,
                rise=1.0,
                shape=Hy8Shape.CIRCLE,
                material=Hy8Material.CONCRETE,
                number_of_barrels=1,
                inlet_configuration=CircularConcreteInlet.SQUARE_EDGE_WITH_HEADWALL,
                inlet_invert_station=0.0,
                outlet_invert_station=40.0,
                inlet_invert_elevation=100.0,
                outlet_invert_elevation=99.0,
                roadway_station=0.0,
                manning_n_top=0.013,
                manning_n_bottom=0.013,
            ),
            Hy8Barrel(
                name="box-relief",
                span=1.2,
                rise=0.8,
                shape=Hy8Shape.BOX,
                material=Hy8Material.CONCRETE,
                number_of_barrels=2,
                inlet_configuration=ConcreteBoxInlet.SQUARE_EDGE_30_TO_75_DEG_WINGWALL,
                inlet_invert_station=0.0,
                outlet_invert_station=30.0,
                inlet_invert_elevation=101.0,
                outlet_invert_elevation=99.5,
                roadway_station=0.0,
                manning_n_top=0.015,
                manning_n_bottom=0.015,
            ),
        )
    )
    return crossing


def _local_heterogeneous_crossing() -> CulvertCrossing:
    """Return the local crossing matched to ``_hy8_heterogeneous_crossing``."""
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
        msg = f"Local solver omitted inlet-control depth for {case.case_id}."
        raise RuntimeError(msg)
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
        msg = f"HY-8 returned {len(culverts)} culvert records for single-culvert case {case.case_id}."
        raise RuntimeError(msg)
    culvert = culverts[0]
    if culvert.index != 0:
        msg = f"HY-8 returned culvert index {culvert.index!r} for {case.case_id}."
        raise RuntimeError(msg)
    numeric_values = (
        culvert.discharge,
        culvert.inlet_control_depth,
        culvert.outlet_control_depth,
        culvert.full_length,
        culvert.free_length,
        culvert.outlet_velocity,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        msg = f"HY-8 returned incomplete culvert diagnostics for {case.case_id}."
        raise RuntimeError(msg)
    if abs(culvert.discharge - row_flow) > HY8_REPORT_TOLERANCE:
        msg = f"HY-8 culvert discharge disagrees with crossing flow for {case.case_id}."
        raise RuntimeError(msg)
    if abs(culvert.outlet_velocity - row_velocity) > HY8_REPORT_TOLERANCE:
        msg = f"HY-8 culvert velocity disagrees with crossing velocity for {case.case_id}."
        raise RuntimeError(msg)
    if culvert.flow_type != row_flow_type:
        msg = f"HY-8 culvert and crossing flow types disagree for {case.case_id}."
        raise RuntimeError(msg)
    if culvert.full_length < 0.0 or culvert.free_length < 0.0:
        msg = f"HY-8 returned a negative barrel length for {case.case_id}."
        raise RuntimeError(msg)
    reported_length = culvert.full_length + culvert.free_length
    if abs(reported_length - case.length) > HY8_LENGTH_BALANCE_TOLERANCE:
        msg = f"HY-8 full/free lengths total {reported_length!r}, not {case.length!r}, for {case.case_id}."
        raise RuntimeError(msg)
    return culvert


def parse_args() -> argparse.Namespace:
    """Parse command-line options for HY-8 execution and artifact retention."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hy8", type=Path, help="Explicit HY864.exe path")
    parser.add_argument("--workspace", type=Path, help="Keep HY-8 projects and reports here")
    parser.add_argument("--output", type=Path, help="Write UTF-8 CSV here instead of stdout")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--discrepancy-sweep",
        action="store_true",
        help="Run nearby discharges for the retained Type 6 and crown-transition cases",
    )
    mode.add_argument(
        "--heterogeneous-crossing",
        action="store_true",
        help="Run the mixed circular/box crossing and regime-transition rating fixture",
    )
    return parser.parse_args()


def _selected_cases(args: argparse.Namespace) -> tuple[ComparisonCase, ...]:
    """Return the standard matrix or the two focused discrepancy sweeps."""
    if not args.discrepancy_sweep:
        return CASES
    cases_by_id = {case.case_id: case for case in CASES}
    return tuple(
        replace(
            cases_by_id[case_id],
            case_id=f"{case_id}-q{discharge:.2f}",
            discharge=discharge,
        )
        for case_id, discharges in DISCREPANCY_SWEEP_DISCHARGES.items()
        for discharge in discharges
    )


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
    for case in _selected_cases(args):
        local = _local_result(case)
        case_workspace = args.workspace / case.case_id if args.workspace is not None else None
        hy8_result = _hy8_crossing(case).hw_from_q(
            case.discharge,
            hy8=executable,
            workspace=case_workspace,
            keep_files=case_workspace is not None,
        )
        if hy8_result.row is None:
            msg = f"HY-8 returned no result row for {case.case_id}."
            raise RuntimeError(msg)
        row = hy8_result.row
        # HY-8 reports flow and roadway discharge to 0.01 m3/s. Fail closed if
        # nearest-row selection or an unexpectedly low road crest changed the case.
        if not math.isfinite(row.flow) or abs(row.flow - case.discharge) > HY8_REPORT_TOLERANCE:
            msg = f"HY-8 row flow {row.flow!r} does not match requested flow {case.discharge!r} for {case.case_id}."
            raise RuntimeError(msg)
        if not math.isfinite(row.roadway_discharge) or abs(row.roadway_discharge) > HY8_REPORT_TOLERANCE:
            msg = f"HY-8 reported roadway discharge {row.roadway_discharge!r} for non-overtopping case {case.case_id}."
            raise RuntimeError(msg)
        if not math.isfinite(row.headwater_elevation) or not math.isfinite(row.velocity):
            msg = f"HY-8 returned non-finite hydraulics for {case.case_id}."
            raise RuntimeError(msg)
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


def _write_heterogeneous_matrix(args: argparse.Namespace, output: TextIO) -> None:
    """Execute the mixed-crossing comparison and retain allocation evidence."""
    executable = Hy8Executable(args.hy8) if args.hy8 is not None else Hy8Executable()
    local_crossing = _local_heterogeneous_crossing()
    hy8_crossing = _hy8_heterogeneous_crossing()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "case_id",
            "discharge_m3s",
            "tailwater_m",
            "local_headwater_m",
            "hy8_headwater_m",
            "headwater_difference_m",
            "local_circular_flow_m3s",
            "hy8_circular_flow_m3s",
            "circular_flow_difference_m3s",
            "local_box_group_flow_m3s",
            "hy8_box_group_flow_m3s",
            "box_group_flow_difference_m3s",
            "local_circular_velocity_ms",
            "hy8_circular_velocity_ms",
            "circular_velocity_difference_ms",
            "local_box_velocity_ms",
            "hy8_box_velocity_ms",
            "box_velocity_difference_ms",
            "local_circular_control",
            "local_circular_regime",
            "hy8_circular_flow_type",
            "local_box_control",
            "local_box_regime",
            "hy8_box_flow_type",
            "local_conservation_difference_m3s",
            "hy8_conservation_difference_m3s",
            "local_common_headwater_spread_m",
            "hy8_roadway_discharge_m3s",
        )
    )
    for discharge in HETEROGENEOUS_DISCHARGES:
        local = solve_crossing_hydraulics(local_crossing, discharge, 99.0)
        case_workspace = args.workspace / f"q-{discharge:.2f}" if args.workspace is not None else None
        hy8_result = hy8_crossing.hw_from_q(
            discharge,
            hy8=executable,
            workspace=case_workspace,
            keep_files=case_workspace is not None,
        )
        if hy8_result.row is None:
            msg = f"HY-8 returned no mixed-crossing result row at Q={discharge}."
            raise RuntimeError(msg)
        row = hy8_result.row
        if abs(row.flow - discharge) > HY8_REPORT_TOLERANCE:
            msg = f"HY-8 row flow {row.flow!r} does not match requested mixed-crossing flow {discharge!r}."
            raise RuntimeError(msg)
        if abs(row.roadway_discharge) > HY8_REPORT_TOLERANCE:
            msg = f"HY-8 reported roadway flow in the mixed-crossing case at Q={discharge}."
            raise RuntimeError(msg)
        if len(row.culverts) != 2 or tuple(item.index for item in row.culverts) != (0, 1):
            msg = f"HY-8 did not return the two ordered mixed-crossing culvert records at Q={discharge}."
            raise RuntimeError(msg)
        if not all(
            math.isfinite(value)
            for value in (
                row.headwater_elevation,
                row.culverts[0].discharge,
                row.culverts[1].discharge,
                row.culverts[0].outlet_velocity,
                row.culverts[1].outlet_velocity,
            )
        ):
            msg = f"HY-8 returned nonfinite mixed-crossing values at Q={discharge}."
            raise RuntimeError(msg)

        circular_local, box_local = local.group_results
        circular_hy8, box_hy8 = row.culverts
        local_conservation = circular_local.total_discharge + box_local.total_discharge - discharge
        hy8_conservation = circular_hy8.discharge + box_hy8.discharge - row.flow
        local_headwaters = tuple(item.barrel_result.headwater_elevation for item in local.group_results)
        writer.writerow(
            (
                f"mixed-relief-q{discharge:.2f}",
                discharge,
                99.0,
                local.headwater_elevation,
                row.headwater_elevation,
                local.headwater_elevation - row.headwater_elevation,
                circular_local.total_discharge,
                circular_hy8.discharge,
                circular_local.total_discharge - circular_hy8.discharge,
                box_local.total_discharge,
                box_hy8.discharge,
                box_local.total_discharge - box_hy8.discharge,
                circular_local.barrel_result.velocity_outlet,
                circular_hy8.outlet_velocity,
                circular_local.barrel_result.velocity_outlet - circular_hy8.outlet_velocity,
                box_local.barrel_result.velocity_outlet,
                box_hy8.outlet_velocity,
                box_local.barrel_result.velocity_outlet - box_hy8.outlet_velocity,
                circular_local.barrel_result.control_type.value,
                circular_local.barrel_result.regime.value,
                circular_hy8.flow_type,
                box_local.barrel_result.control_type.value,
                box_local.barrel_result.regime.value,
                box_hy8.flow_type,
                local_conservation,
                hy8_conservation,
                max(local_headwaters) - min(local_headwaters),
                row.roadway_discharge,
            )
        )


def main() -> int:
    """Execute all cases and emit an ordinary UTF-8 CSV comparison matrix."""
    args = parse_args()
    writer = _write_heterogeneous_matrix if args.heterogeneous_crossing else _write_matrix
    if args.output is None:
        writer(args, sys.stdout)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="") as output:
            writer(args, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
