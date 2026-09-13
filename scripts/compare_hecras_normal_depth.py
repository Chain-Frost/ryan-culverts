"""Compare channel normal depth with HEC-RAS through its Windows COM API.

The script clones an official HEC-RAS example before changing it. The downloaded
example is therefore source evidence, not a writable execution workspace. The
generated projects and HEC-RAS result files belong under ``validation_artifacts``.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import math
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TextIO, cast

from culvert_solver import RectangularChannel, TrapezoidalChannel, calculate_channel_normal_depth

FT_PER_M = 3.280839895013123
CFS_PER_M3S = 35.31466672148859
HECRAS_PROG_ID = "RAS701.HECRASController"
EXPECTED_HECRAS_VERSION = "HEC-RAS 7.0.1 June 2026"
DEPTH_COMPARISON_TOLERANCE_M = 0.0002
GEOMETRY_COMPARISON_TOLERANCE = 0.00002
SOURCE_PROJECT = "MIXED.PRJ"
SOURCE_GEOMETRY = "MIXED.g01"
SOURCE_FLOW = "MIXED.f01"


class _HECRASController(Protocol):
    """COM operations used by the comparison harness."""

    def HECRASVersion(self) -> str: ...

    def Project_Open(self, project_path: str) -> None: ...

    def Project_Close(self) -> None: ...

    def Compute_HideComputationWindow(self) -> None: ...

    def Compute_CurrentPlan(
        self, message_count: None, messages: None, blocking: bool
    ) -> tuple[bool, int, tuple[str, ...], bool]: ...

    def Output_GetNodes(
        self, river_index: int, reach_index: int, node_count: int, stations: None, node_types: None
    ) -> tuple[int, int, int, tuple[str, ...], tuple[str, ...]]: ...

    def Output_NodeOutput(
        self, river_index: int, reach_index: int, node_index: int, upstream_downstream: int, profile: int, variable: int
    ) -> tuple[float, int, int, int, int, int, int]: ...

    def QuitRas(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ComparisonCase:
    """One channel geometry evaluated at two discharges."""

    case_id: str
    bottom_width_m: float
    left_side_slope: float
    right_side_slope: float
    roughness: float
    friction_slope: float
    discharges_m3s: tuple[float, float]

    @property
    def section_kind(self) -> str:
        """Return the documented section classification."""
        if self.bottom_width_m == 0.0:
            return "triangular"
        if self.left_side_slope == self.right_side_slope == 0.0:
            return "rectangular"
        if self.left_side_slope == self.right_side_slope:
            return "symmetric_trapezoidal"
        return "asymmetric_trapezoidal"

    def section(self) -> RectangularChannel | TrapezoidalChannel:
        """Build the corresponding local SI section."""
        if self.section_kind == "rectangular":
            return RectangularChannel(self.bottom_width_m)
        return TrapezoidalChannel(self.bottom_width_m, self.left_side_slope, self.right_side_slope)


CASES: tuple[ComparisonCase, ...] = (
    ComparisonCase("rectangular", 5.0, 0.0, 0.0, 0.030, 0.0010, (0.5, 4.211434583596904)),
    ComparisonCase("symmetric-trapezoidal", 3.0, 2.0, 2.0, 0.030, 0.0015, (0.5, 3.2256777519932003)),
    ComparisonCase("asymmetric-trapezoidal", 4.0, 3.0, 2.0, 0.035, 0.0020, (0.5, 9.26246172103823)),
    ComparisonCase("triangular", 0.0, 1.0, 2.0, 0.025, 0.0030, (0.5, 2.342083113322061)),
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template", type=Path, required=True, help="Official Mixed Flow Regime Channel example directory"
    )
    parser.add_argument("--workspace", type=Path, required=True, help="New directory for cloned writable projects")
    parser.add_argument("--output", type=Path, help="Write UTF-8 CSV here instead of stdout")
    return parser.parse_args()


def _controller() -> _HECRASController:
    """Create the version-pinned HEC-RAS automation controller."""
    try:
        client = importlib.import_module("win32com.client")
    except ImportError as exc:
        message = "pywin32 and HEC-RAS 7.0.1 are required to run this optional comparison."
        raise RuntimeError(message) from exc
    controller = cast("_HECRASController", client.gencache.EnsureDispatch(HECRAS_PROG_ID))
    version = controller.HECRASVersion()
    if version != EXPECTED_HECRAS_VERSION:
        controller.QuitRas()
        message = f"Expected {EXPECTED_HECRAS_VERSION!r}, got {version!r}."
        raise RuntimeError(message)
    return controller


def _source_files(template: Path) -> tuple[Path, Path, Path]:
    """Validate and return the minimum official template files."""
    paths = (template / SOURCE_PROJECT, template / SOURCE_GEOMETRY, template / SOURCE_FLOW)
    missing = tuple(str(path) for path in paths if not path.is_file())
    if missing:
        message = f"Template is missing required files: {', '.join(missing)}"
        raise FileNotFoundError(message)
    return paths


def _hec_field(value: float) -> str:
    """Format one value for HEC-RAS's eight-column legacy text records."""
    rendered = f"{value:.7g}"
    if len(rendered) > 8:
        message = f"Value {value!r} does not fit a HEC-RAS eight-column field."
        raise ValueError(message)
    return f"{rendered:>8}"


def _station_elevations(case: ComparisonCase, base_elevation_ft: float) -> tuple[float, ...]:
    """Return station/elevation pairs for a ten-metre-deep section envelope."""
    envelope_height_ft = 10.0 * FT_PER_M
    bottom_width_ft = case.bottom_width_m * FT_PER_M
    left_run_ft = case.left_side_slope * envelope_height_ft
    right_run_ft = case.right_side_slope * envelope_height_ft
    bottom_left = left_run_ft
    bottom_right = bottom_left + bottom_width_ft
    right_edge = bottom_right + right_run_ft
    if bottom_left == bottom_right:
        return (
            0.0,
            base_elevation_ft + envelope_height_ft,
            bottom_left,
            base_elevation_ft,
            right_edge,
            base_elevation_ft + envelope_height_ft,
        )
    return (
        0.0,
        base_elevation_ft + envelope_height_ft,
        bottom_left,
        base_elevation_ft,
        bottom_right,
        base_elevation_ft,
        right_edge,
        base_elevation_ft + envelope_height_ft,
    )


def _replace_cross_section(block: re.Match[str], case: ComparisonCase) -> str:
    """Replace one source cross-section geometry while retaining its invert."""
    text = block.group(0)
    station_match = re.search(r"#Sta/Elev=\s*\d+\s*\r?\n(?P<values>.*?)(?=\r?\n#Mann=)", text, flags=re.DOTALL)
    if station_match is None:
        message = "A template cross section has no station/elevation record."
        raise RuntimeError(message)
    source_values = tuple(
        float(value) for value in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", station_match["values"])
    )
    if len(source_values) < 6 or len(source_values) % 2:
        message = "A template station/elevation record is malformed."
        raise RuntimeError(message)
    base_elevation = min(source_values[1::2])
    values = _station_elevations(case, base_elevation)
    station_record = f"#Sta/Elev= {len(values) // 2} \n{''.join(_hec_field(value) for value in values)}"
    text = text[: station_match.start()] + station_record + text[station_match.end() :]

    right_edge = values[-2]
    manning_record = (
        "#Mann= 3 ,0,0\n"
        f"{_hec_field(0.0)}{'':8}{_hec_field(0.0)}"
        f"{_hec_field(0.0)}{_hec_field(case.roughness)}{_hec_field(0.0)}"
        f"{_hec_field(right_edge)}{'':8}{_hec_field(0.0)}"
    )
    text, replacements = re.subn(r"#Mann=.*?\r?\n.*?(?=\r?\nBank Sta=)", manning_record, text, count=1, flags=re.DOTALL)
    if replacements != 1:
        message = "A template cross section has no replaceable Manning record."
        raise RuntimeError(message)
    return re.sub(r"Bank Sta=.*", f"Bank Sta=0,{right_edge:.7g}", text, count=1)


def _write_geometry(path: Path, case: ComparisonCase) -> None:
    """Convert every source cross section to the selected prismatic geometry."""
    source = path.read_text(encoding="ascii")
    pattern = re.compile(r"(?ms)^Type RM Length L Ch R = 1 .*?(?=^Type RM Length L Ch R =|\Z)")
    converted, count = pattern.subn(lambda block: _replace_cross_section(block, case), source)
    if count == 0:
        message = "The template geometry contains no cross sections."
        raise RuntimeError(message)
    path.write_text(converted, encoding="ascii", newline="\r\n")


def _write_flow(path: Path, case: ComparisonCase) -> tuple[float, float]:
    """Set two steady flows and matching upstream/downstream normal slopes."""
    source = path.read_text(encoding="ascii")
    inputs_cfs = tuple(float(f"{flow * CFS_PER_M3S:.7g}") for flow in case.discharges_m3s)
    flow_line = "".join(_hec_field(flow) for flow in inputs_cfs)
    source, flow_count = re.subn(
        r"(?m)(^River Rch & RM=.*\r?\n).*?$", lambda match: f"{match.group(1)}{flow_line}", source, count=1
    )
    source, up_count = re.subn(r"(?m)^Up Slope=.*$", f"Up Slope={case.friction_slope:.7g}", source)
    source, down_count = re.subn(r"(?m)^Dn Slope=.*$", f"Dn Slope={case.friction_slope:.7g}", source)
    if (flow_count, up_count, down_count) != (1, 2, 2):
        message = "The template flow records do not match the expected two-profile project."
        raise RuntimeError(message)
    path.write_text(source, encoding="ascii", newline="\r\n")
    return cast("tuple[float, float]", inputs_cfs)


def _clone_case(template: Path, workspace: Path, case: ComparisonCase) -> tuple[Path, tuple[float, float]]:
    """Clone and transform the official example for one section configuration."""
    destination = workspace / case.case_id
    if destination.exists():
        message = f"Case workspace already exists: {destination}. Choose a new workspace."
        raise FileExistsError(message)
    shutil.copytree(
        template,
        destination,
        ignore=shutil.ignore_patterns("*.hdf", "*.O*", "*.r[0-9][0-9]", "*.computeMsgs.txt"),
    )
    _write_geometry(destination / SOURCE_GEOMETRY, case)
    flows_cfs = _write_flow(destination / SOURCE_FLOW, case)
    return destination / SOURCE_PROJECT, flows_cfs


def _node_value(controller: _HECRASController, node_index: int, profile: int, variable: int) -> float:
    """Return one result at the first river/reach and selected node/profile."""
    result = controller.Output_NodeOutput(1, 1, node_index, 0, profile, variable)
    value = result[0]
    if not math.isfinite(value):
        message = f"HEC-RAS returned a non-finite output for profile {profile}, variable {variable}."
        raise RuntimeError(message)
    return value


def _run_case(
    controller: _HECRASController, project: Path, case: ComparisonCase, inputs_cfs: tuple[float, float]
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    """Compute one project and return its two comparison rows."""
    controller.Project_Open(str(project.resolve()))
    try:
        controller.Compute_HideComputationWindow()
        completed, _, messages, _ = controller.Compute_CurrentPlan(None, None, True)
        if not completed:
            message = f"HEC-RAS failed {case.case_id}: {'; '.join(messages)}"
            raise RuntimeError(message)
        _, _, node_count, _, _ = controller.Output_GetNodes(1, 1, 0, None, None)
        rows: list[tuple[object, ...]] = []
        for profile, input_cfs in enumerate(inputs_cfs, start=1):
            output_cfs = _node_value(controller, node_count, profile, 9)
            hecras_depth_m = _node_value(controller, node_count, profile, 4) / FT_PER_M
            wse_ft = _node_value(controller, node_count, profile, 2)
            invert_ft = _node_value(controller, node_count, profile, 5)
            hecras_area_m2 = _node_value(controller, node_count, profile, 10) / FT_PER_M**2
            hecras_perimeter_m = _node_value(controller, node_count, profile, 14) / FT_PER_M
            hecras_top_width_m = _node_value(controller, node_count, profile, 29) / FT_PER_M
            if not math.isclose(wse_ft - invert_ft, hecras_depth_m * FT_PER_M, abs_tol=2e-5):
                message = f"HEC-RAS depth and WSE-minus-invert disagree for {case.case_id}, profile {profile}."
                raise RuntimeError(message)
            if not math.isclose(output_cfs, input_cfs, abs_tol=0.001):
                message = f"HEC-RAS output flow does not match the input for {case.case_id}, profile {profile}."
                raise RuntimeError(message)
            discharge_m3s = output_cfs / CFS_PER_M3S
            section = case.section()
            area_difference_m2 = section.area(hecras_depth_m) - hecras_area_m2
            perimeter_difference_m = section.wetted_perimeter(hecras_depth_m) - hecras_perimeter_m
            top_width_difference_m = section.top_width(hecras_depth_m) - hecras_top_width_m
            if (
                max(abs(area_difference_m2), abs(perimeter_difference_m), abs(top_width_difference_m))
                > GEOMETRY_COMPARISON_TOLERANCE
            ):
                message = (
                    f"HEC-RAS geometry outputs do not match the intended section for {case.case_id}, profile {profile}."
                )
                raise RuntimeError(message)
            local_depth_m = calculate_channel_normal_depth(
                section, discharge_m3s, case.friction_slope, case.roughness
            ).depth
            if abs(local_depth_m - hecras_depth_m) > DEPTH_COMPARISON_TOLERANCE_M:
                message = f"Normal-depth comparison exceeded tolerance for {case.case_id}, profile {profile}."
                raise RuntimeError(message)
            rows.append(
                (
                    f"{case.case_id}-q{profile}",
                    case.section_kind,
                    case.bottom_width_m,
                    case.left_side_slope,
                    case.right_side_slope,
                    case.roughness,
                    case.friction_slope,
                    discharge_m3s,
                    output_cfs,
                    local_depth_m,
                    hecras_depth_m,
                    local_depth_m - hecras_depth_m,
                    hecras_area_m2,
                    area_difference_m2,
                    hecras_perimeter_m,
                    perimeter_difference_m,
                    hecras_top_width_m,
                    top_width_difference_m,
                )
            )
        return cast("tuple[tuple[object, ...], tuple[object, ...]]", tuple(rows))
    finally:
        controller.Project_Close()


def _write_comparison(args: argparse.Namespace, output: TextIO) -> None:
    """Clone, execute, and write all comparison cases."""
    template = args.template.resolve()
    _source_files(template)
    workspace = args.workspace.resolve()
    if workspace.exists():
        message = f"Workspace already exists: {workspace}. Choose a new workspace."
        raise FileExistsError(message)
    workspace.mkdir(parents=True)
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "case_id",
            "section_kind",
            "bottom_width_m",
            "left_side_slope_h_per_v",
            "right_side_slope_h_per_v",
            "manning_n",
            "friction_slope",
            "discharge_m3s",
            "hecras_discharge_cfs",
            "local_normal_depth_m",
            "hecras_normal_depth_m",
            "depth_difference_m",
            "hecras_flow_area_m2",
            "geometry_area_difference_m2",
            "hecras_wetted_perimeter_m",
            "geometry_perimeter_difference_m",
            "hecras_top_width_m",
            "geometry_top_width_difference_m",
        )
    )
    controller = _controller()
    try:
        for case in CASES:
            project, inputs_cfs = _clone_case(template, workspace, case)
            writer.writerows(_run_case(controller, project, case, inputs_cfs))
    finally:
        controller.QuitRas()


def main() -> int:
    """Execute the version-pinned HEC-RAS comparison."""
    args = parse_args()
    if args.output is None:
        _write_comparison(args, sys.stdout)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="") as output:
            _write_comparison(args, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
