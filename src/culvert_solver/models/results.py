"""Hydraulic result data structures and flow regime classifications."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from .barrel import CulvertBarrel
from .enums import (
    ControlType,
    ConvergenceCalculation,
    HydraulicWarningCode,
    ProfileCurve,
    RoughnessSelectionBasis,
)
from .group import CulvertGroup

if TYPE_CHECKING:
    from ..numerical.roots import RootResult
    from ..profiles.direct_step import InletControlProfile, WaterSurfaceProfile
    from ..references.models import SourceReference
    from ..solver.resolvers import EntranceLossSelection, InletCoefficientSelection
    from .materials import RoughnessApplicabilityNotice


class FlowRegime(StrEnum):
    """Culvert hydraulic governing flow regimes."""

    INACTIVE = "inactive"
    MIXED = "mixed"
    INLET_CONTROL_UNSUBMERGED = "inlet_control_unsubmerged"
    INLET_CONTROL_TRANSITION = "inlet_control_transition"
    INLET_CONTROL_SUBMERGED = "inlet_control_submerged"
    OUTLET_CONTROL_FULL = "outlet_control_full"
    OUTLET_CONTROL_FREE_SURFACE = "outlet_control_free_surface"
    OUTLET_CONTROL_MIXED = "outlet_control_mixed"


@dataclass(frozen=True, slots=True)
class HydraulicWarning:
    """Machine-readable warning code with a concise engineering-review message."""

    code: HydraulicWarningCode
    message: str


@dataclass(frozen=True, slots=True)
class HeadLossComponents:
    """Scalar head-loss components exposed by one outlet-control calculation.

    Values are metres of head. ``None`` means the selected method does not calculate
    that component as a distinct scalar; it must not be interpreted as zero.
    """

    entrance: float | None = None
    friction: float | None = None
    exit: float | None = None
    total: float | None = None


@dataclass(frozen=True, slots=True)
class ConvergenceRecord:
    """Labelled numerical root result retained for engineering audit."""

    calculation: ConvergenceCalculation
    result: RootResult


@dataclass(frozen=True, slots=True)
class BarrelHydraulicResult:
    """Hydraulic calculation results for a single culvert barrel."""

    barrel: CulvertBarrel
    discharge: float
    headwater_elevation: float
    headwater_depth: float
    tailwater_elevation: float
    tailwater_depth: float
    regime: FlowRegime
    control_type: ControlType
    velocity_outlet: float
    outlet_depth: float
    critical_depth: float
    normal_depth: float | None = None
    profile_curve: ProfileCurve | None = None
    outlet_sequent_depth: float | None = None
    hydraulic_jump_station: float | None = None
    hydraulic_jump_swept_out: bool | None = None
    full_flow_length: float = 0.0
    inlet_control_headwater_elevation: float | None = None
    outlet_control_headwater_elevation: float | None = None
    full_flow_headwater_elevation: float | None = None
    warnings: tuple[HydraulicWarning, ...] = ()
    inlet_coefficient_selection: InletCoefficientSelection | None = None
    entrance_loss_selection: EntranceLossSelection | None = None
    adopted_roughness: float | None = None
    roughness_selection_basis: RoughnessSelectionBasis | None = None
    roughness_source: SourceReference | None = None
    roughness_notices: tuple[RoughnessApplicabilityNotice, ...] = ()
    outlet_control_losses: HeadLossComponents | None = None
    full_flow_losses: HeadLossComponents | None = None
    profile: WaterSurfaceProfile | InletControlProfile | None = None
    convergence: tuple[ConvergenceRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class GroupHydraulicResult:
    """Hydraulic calculation results for a group of identical parallel barrels."""

    group: CulvertGroup
    total_discharge: float
    barrel_discharge: float
    barrel_result: BarrelHydraulicResult
    discharge_convergence: ConvergenceRecord | None = None


@dataclass(frozen=True, slots=True)
class CrossingHydraulicResult:
    """Hydraulic calculation results across all culvert groups in a road crossing."""

    headwater_elevation: float
    total_discharge: float
    tailwater_elevation: float
    group_results: tuple[GroupHydraulicResult, ...]
    headwater_convergence: ConvergenceRecord | None = None
