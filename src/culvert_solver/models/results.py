"""Hydraulic result data structures and flow regime classifications."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from ..references.models import SourceReference
from .barrel import CulvertBarrel
from .enums import (
    ApplicabilityNoticeCode,
    ControlType,
    ConvergenceCalculation,
    HydraulicResultStatus,
    HydraulicWarningCode,
    ProfileCurve,
    RoughnessSelectionBasis,
)
from .group import CulvertGroup

if TYPE_CHECKING:
    from ..numerical.roots import RootResult
    from ..outlet_control.losses import ExitLossSelection
    from ..profiles.direct_step import InletControlProfile, WaterSurfaceProfile
    from ..roadway.overtopping import RoadwayOvertoppingResult
    from ..solver.resolvers import EntranceLossSelection, InletCoefficientSelection
    from .materials import RoughnessApplicabilityNotice
    from .tailwater import TailwaterResolution


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
    ROADWAY_OVERTOPPING = "roadway_overtopping"


@dataclass(frozen=True, slots=True)
class HydraulicWarning:
    """Machine-readable warning code with a concise engineering-review message."""

    code: HydraulicWarningCode
    message: str

    @property
    def result_status(self) -> HydraulicResultStatus:
        """Return the minimum result status implied by this warning."""
        return _WARNING_RESULT_STATUS[self.code]


_WARNING_RESULT_STATUS: dict[HydraulicWarningCode, HydraulicResultStatus] = {
    HydraulicWarningCode.INLET_CONTROL_HIGH_HEAD_EXTENSION: HydraulicResultStatus.VALID_WITH_ADVISORY,
    HydraulicWarningCode.INLET_CONTROL_EXTREME_HEADWATER: HydraulicResultStatus.VALID_WITH_ADVISORY,
    HydraulicWarningCode.INLET_OUTLET_DEPTH_APPROXIMATION: HydraulicResultStatus.APPROXIMATE,
    HydraulicWarningCode.MIXED_FLOW_NOT_RESOLVED: HydraulicResultStatus.UNRESOLVED,
}
_RESULT_STATUS_PRIORITY: dict[HydraulicResultStatus, int] = {
    HydraulicResultStatus.VALID: 0,
    HydraulicResultStatus.VALID_WITH_ADVISORY: 1,
    HydraulicResultStatus.APPROXIMATE: 2,
    HydraulicResultStatus.UNRESOLVED: 3,
}


def aggregate_result_status(statuses: tuple[HydraulicResultStatus, ...]) -> HydraulicResultStatus:
    """Return the most conservative status, or ``VALID`` for an empty collection."""
    return max(statuses, key=_RESULT_STATUS_PRIORITY.__getitem__, default=HydraulicResultStatus.VALID)


@dataclass(frozen=True, slots=True)
class HydraulicApplicabilityNotice:
    """Machine-readable hydraulic limitation with its supporting source."""

    code: ApplicabilityNoticeCode
    message: str
    source: SourceReference


NCHRP_734_REPRESENTATIVE_BARREL = SourceReference(
    source_id="NCHRP-734-2012-CHAPTER-5-MULTI-BARREL",
    publication="Hydraulic Loss Coefficients for Culverts, NCHRP Report 734",
    edition="2012",
    locator="Chapter 5 conclusions, printed page 49 (local PDF page 57)",
    url="https://doi.org/10.17226/22673",
    applicability=(
        "Representative average-barrel superposition for total flow through hydraulically "
        "identical parallel barrels under sufficiently uniform approach conditions."
    ),
    notes=(
        "Reported nonuniform-approach, depressed-barrel, and individual-barrel differences "
        "are observed limitations, not deterministic correction factors."
    ),
)

REPRESENTATIVE_BARREL_EQUAL_FLOW_NOTICE = HydraulicApplicabilityNotice(
    code=ApplicabilityNoticeCode.REPRESENTATIVE_BARREL_EQUAL_FLOW,
    message=(
        "Total group discharge uses a representative-barrel equal-flow assumption for "
        "hydraulically identical barrels under sufficiently uniform approach conditions. "
        "Individual barrel discharge and velocity may differ with nonuniform approach flow "
        "or depressed barrels, so barrel-specific performance requires separate review."
    ),
    source=NCHRP_734_REPRESENTATIVE_BARREL,
)


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
    exit_loss_selection: ExitLossSelection | None = None
    adopted_roughness: float | None = None
    roughness_selection_basis: RoughnessSelectionBasis | None = None
    roughness_source: SourceReference | None = None
    roughness_notices: tuple[RoughnessApplicabilityNotice, ...] = ()
    outlet_control_losses: HeadLossComponents | None = None
    full_flow_losses: HeadLossComponents | None = None
    profile: WaterSurfaceProfile | InletControlProfile | None = None
    convergence: tuple[ConvergenceRecord, ...] = ()
    tailwater_resolution: TailwaterResolution | None = None

    @property
    def status(self) -> HydraulicResultStatus:
        """Return the most conservative status implied by structured warnings."""
        return aggregate_result_status(tuple(warning.result_status for warning in self.warnings))


@dataclass(frozen=True, slots=True)
class GroupHydraulicResult:
    """Hydraulic results for identical barrels, including equal-flow applicability."""

    group: CulvertGroup
    total_discharge: float
    barrel_discharge: float
    barrel_result: BarrelHydraulicResult
    discharge_convergence: ConvergenceRecord | None = None
    tailwater_resolution: TailwaterResolution | None = None
    applicability_notices: tuple[HydraulicApplicabilityNotice, ...] = ()

    def __post_init__(self) -> None:
        if self.group.quantity <= 1 or REPRESENTATIVE_BARREL_EQUAL_FLOW_NOTICE in self.applicability_notices:
            return
        object.__setattr__(
            self,
            "applicability_notices",
            (*self.applicability_notices, REPRESENTATIVE_BARREL_EQUAL_FLOW_NOTICE),
        )

    @property
    def status(self) -> HydraulicResultStatus:
        """Return the representative barrel's computational resolution status."""
        return self.barrel_result.status


@dataclass(frozen=True, slots=True)
class CrossingHydraulicResult:
    """Hydraulic results across a crossing, including aggregated applicability notices."""

    headwater_elevation: float
    total_discharge: float
    tailwater_elevation: float
    group_results: tuple[GroupHydraulicResult, ...]
    headwater_convergence: ConvergenceRecord | None = None
    roadway_result: RoadwayOvertoppingResult | None = None
    tailwater_resolution: TailwaterResolution | None = None
    applicability_notices: tuple[HydraulicApplicabilityNotice, ...] = ()

    def __post_init__(self) -> None:
        notices: tuple[HydraulicApplicabilityNotice, ...] = tuple(
            dict.fromkeys(
                (
                    *self.applicability_notices,
                    *(notice for result in self.group_results for notice in result.applicability_notices),
                )
            )
        )
        object.__setattr__(self, "applicability_notices", notices)

    @property
    def status(self) -> HydraulicResultStatus:
        """Conservatively aggregate the status of active culvert groups."""
        return aggregate_result_status(
            tuple(result.status for result in self.group_results if result.barrel_discharge > 0.0)
        )

    @property
    def culvert_discharge(self) -> float:
        """Total discharge conveyed through culvert groups in cubic metres per second."""
        return sum(result.total_discharge for result in self.group_results)

    @property
    def roadway_discharge(self) -> float:
        """Roadway-overtopping discharge, or zero when no roadway flow is active."""
        return 0.0 if self.roadway_result is None else self.roadway_result.discharge
