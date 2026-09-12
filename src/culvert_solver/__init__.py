"""Independent, early-stage culvert hydraulics library.

The package exposes internally tested geometry and hydraulic components through
provisional combined solvers. External engineering validation is not yet complete.
"""

from importlib.metadata import PackageNotFoundError, version

from .channel.geometry import (
    OpenChannelSection,
    RectangularChannel,
    TrapezoidalChannel,
    hydraulic_radius,
)
from .channel.uniform import ChannelNormalDepthResult, calculate_channel_normal_depth
from .constants import (
    GRAVITATIONAL_ACCELERATION,
    STANDARD_WATER_DENSITY,
    STANDARD_WATER_KINEMATIC_VISCOSITY,
)
from .exceptions import ConvergenceError, InvalidInputError
from .geometry.base import CrossSectionGeometry
from .geometry.circular import CircularGeometry
from .geometry.filleted_rectangular import FilletedRectangularGeometry
from .geometry.rectangular import RectangularGeometry
from .hydraulics.critical import CriticalDepthResult, calculate_critical_depth
from .hydraulics.momentum import (
    calculate_sequent_depth,
    hydrostatic_pressure_moment,
    momentum_function,
)
from .hydraulics.normal import NormalDepthResult, calculate_normal_depth
from .hydraulics.primitives import (
    cross_section_velocity,
    friction_head_loss,
    froude_number,
    manning_discharge,
    manning_friction_slope,
    minor_head_loss,
    specific_energy,
    velocity_head,
    water_surface_elevation_from_energy_grade,
)
from .inlet_control.coefficients import (
    BOX_CONCRETE_BEVEL_45_HEADWALL,
    BOX_CONCRETE_CHAMFER_90_HEADWALL,
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    BOX_CONCRETE_PARALLEL_WINGWALLS_0,
    CIRCULAR_CMP_HEADWALL,
    CIRCULAR_CMP_MITERED,
    CIRCULAR_CMP_PROJECTING,
    CIRCULAR_CONCRETE_GROOVE_END,
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    STANDARD_INLET_COEFFICIENTS,
    InletCoefficients,
)
from .inlet_control.fhwa import (
    flow_parameter,
    submerged_headwater,
    transition_headwater,
    unsubmerged_headwater_form_1,
    unsubmerged_headwater_form_2,
)
from .inlet_control.modern_box import (
    FHWA_HRT_06_138_REFERENCE,
    FHWA_MODERN_BOX_HW_D_MAX,
    FHWA_MODERN_BOX_HW_D_MIN,
    BoxCrownTreatment,
    BoxWingwallTreatment,
    ModernBoxInlet,
    ModernBoxInletCoefficients,
    ModernBoxInletResult,
    calculate_modern_box_inlet_headwater,
    resolve_modern_box_inlet_coefficients,
)
from .inlet_control.solver import (
    EXTREME_HEADWATER_RATIO,
    HDS5_LABORATORY_HW_D_MAX,
    InletControlResult,
    calculate_inlet_control_headwater,
)
from .models.barrel import CulvertBarrel
from .models.collection import (
    AdoptedParameterSet,
    CrossingSummary,
    CulvertInventory,
    CulvertInventoryItem,
    GroupSummary,
    InventorySummary,
)
from .models.crossing import CulvertCrossing
from .models.enums import (
    ApplicabilityNoticeCode,
    ControlType,
    ConvergenceCalculation,
    CspCorrugation,
    EntranceLossSelectionBasis,
    ExitLossSelectionBasis,
    GeometryShape,
    HydraulicResultStatus,
    HydraulicWarningCode,
    InletEquationForm,
    InletSelectionBasis,
    ProfileCurve,
    RoughnessSelectionBasis,
)
from .models.group import CulvertGroup
from .models.materials import (
    CONCRETE,
    CONCRETE_BOX,
    CONCRETE_PIPE,
    CORRUGATED_STEEL,
    MRWA_CONCRETE_REFERENCE,
    MRWA_CSP_MANNING_TABLE,
    MRWA_CSP_REFERENCE,
    MRWA_PART5B_REFERENCE,
    MRWA_SPEC404_REFERENCE,
    SMOOTH_HDPE,
    CspManningEntry,
    CulvertMaterial,
    ManningRoughnessSelection,
    RoughnessApplicabilityNotice,
    resolve_csp_manning_roughness,
    resolve_manning_roughness,
)
from .models.results import (
    NCHRP_734_REPRESENTATIVE_BARREL,
    REPRESENTATIVE_BARREL_EQUAL_FLOW_NOTICE,
    BarrelHydraulicResult,
    ConvergenceRecord,
    CrossingHydraulicResult,
    FlowRegime,
    GroupHydraulicResult,
    HeadLossComponents,
    HydraulicApplicabilityNotice,
    HydraulicWarning,
)
from .models.roadway import FHWA_HDS5_ROADWAY_OVERTOPPING, RoadwayWeir
from .models.tailwater import (
    FHWA_HDS5_NORMAL_DEPTH_TAILWATER,
    ManningChannelTailwater,
    TailwaterBoundary,
    TailwaterCondition,
    TailwaterInput,
    TailwaterMethod,
    TailwaterResolution,
    resolve_tailwater,
)
from .numerical.roots import RootResult, solve_bracketed, solve_brent
from .numerical.tolerances import RootTolerances
from .outlet_control.full_flow import (
    FullFlowOutletResult,
    calculate_downstream_full_flow_length,
    calculate_full_flow_outlet_headwater,
)
from .outlet_control.losses import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75 as BOX_LOSS_FLARED_30_75,
)
from .outlet_control.losses import (
    BOX_CONCRETE_PARALLEL_WINGWALLS_0 as BOX_LOSS_PARALLEL_0,
)
from .outlet_control.losses import (
    PIPE_CMP_HEADWALL as PIPE_CMP_LOSS_HEADWALL,
)
from .outlet_control.losses import (
    PIPE_CMP_PROJECTING as PIPE_CMP_LOSS_PROJECTING,
)
from .outlet_control.losses import (
    PIPE_CONCRETE_SOCKET_END as PIPE_LOSS_SOCKET_END,
)
from .outlet_control.losses import (
    PIPE_CONCRETE_SQUARE_EDGE as PIPE_LOSS_SQUARE_EDGE,
)
from .outlet_control.losses import (
    STANDARD_EXIT_LOSS_COEFFICIENT,
    STANDARD_EXIT_LOSS_SELECTION,
    EntranceLossCoefficient,
    ExitLossSelection,
    calculate_entrance_loss,
    calculate_exit_loss,
    calculate_friction_loss,
    calculate_total_head_loss,
    resolve_exit_loss_coefficient,
)
from .outlet_control.partial_flow import (
    PartialFlowOutletResult,
    calculate_partial_flow_outlet_headwater,
)
from .profiles.direct_step import (
    InletControlProfile,
    ProfilePoint,
    WaterSurfaceProfile,
    compute_backwater_profile,
    compute_inlet_control_s2_profile,
    compute_steep_inlet_control_profile,
)
from .references.models import SourceReference
from .roadway.overtopping import RoadwayOvertoppingResult, calculate_roadway_overtopping
from .solver.barrel import solve_barrel_hydraulics
from .solver.config import DEFAULT_SOLVER_CONFIGURATION, SolverConfiguration
from .solver.crossing import (
    solve_barrel_discharge_for_headwater,
    solve_barrel_discharge_for_headwater_ratio,
    solve_crossing_discharge_for_headwater,
    solve_crossing_hydraulics,
    solve_group_discharge_for_headwater,
)
from .solver.group import solve_group_hydraulics
from .solver.rating_curve import (
    RatingCurvePoint,
    RatingCurveResult,
    generate_barrel_rating_curve,
    generate_crossing_rating_curve,
    generate_discharge_range,
)
from .solver.regime import determine_governing_regime
from .solver.resolvers import (
    EntranceLossSelection,
    InletCoefficientSelection,
    resolve_entrance_loss_coefficient,
    resolve_inlet_coefficients,
)
from .units.conversion import dimension_mm_to_m

try:
    __version__ = version("ryan-culverts")
except PackageNotFoundError:
    # A source-tree import can occur before installation during development.
    __version__ = "0+unknown"

__all__: list[str] = [
    "BOX_CONCRETE_BEVEL_45_HEADWALL",
    "BOX_CONCRETE_CHAMFER_90_HEADWALL",
    "BOX_CONCRETE_FLARED_WINGWALLS_30_75",
    "BOX_CONCRETE_PARALLEL_WINGWALLS_0",
    "BOX_LOSS_FLARED_30_75",
    "BOX_LOSS_PARALLEL_0",
    "CIRCULAR_CMP_HEADWALL",
    "CIRCULAR_CMP_MITERED",
    "CIRCULAR_CMP_PROJECTING",
    "CIRCULAR_CONCRETE_GROOVE_END",
    "CIRCULAR_CONCRETE_SQUARE_EDGE",
    "CONCRETE",
    "CONCRETE_BOX",
    "CONCRETE_PIPE",
    "CORRUGATED_STEEL",
    "DEFAULT_SOLVER_CONFIGURATION",
    "EXTREME_HEADWATER_RATIO",
    "FHWA_HDS5_NORMAL_DEPTH_TAILWATER",
    "FHWA_HDS5_ROADWAY_OVERTOPPING",
    "FHWA_HRT_06_138_REFERENCE",
    "FHWA_MODERN_BOX_HW_D_MAX",
    "FHWA_MODERN_BOX_HW_D_MIN",
    "GRAVITATIONAL_ACCELERATION",
    "HDS5_LABORATORY_HW_D_MAX",
    "MRWA_CONCRETE_REFERENCE",
    "MRWA_CSP_MANNING_TABLE",
    "MRWA_CSP_REFERENCE",
    "MRWA_PART5B_REFERENCE",
    "MRWA_SPEC404_REFERENCE",
    "NCHRP_734_REPRESENTATIVE_BARREL",
    "PIPE_CMP_LOSS_HEADWALL",
    "PIPE_CMP_LOSS_PROJECTING",
    "PIPE_LOSS_SOCKET_END",
    "PIPE_LOSS_SQUARE_EDGE",
    "REPRESENTATIVE_BARREL_EQUAL_FLOW_NOTICE",
    "SMOOTH_HDPE",
    "STANDARD_EXIT_LOSS_COEFFICIENT",
    "STANDARD_EXIT_LOSS_SELECTION",
    "STANDARD_INLET_COEFFICIENTS",
    "STANDARD_WATER_DENSITY",
    "STANDARD_WATER_KINEMATIC_VISCOSITY",
    "AdoptedParameterSet",
    "ApplicabilityNoticeCode",
    "BarrelHydraulicResult",
    "BoxCrownTreatment",
    "BoxWingwallTreatment",
    "ChannelNormalDepthResult",
    "CircularGeometry",
    "ControlType",
    "ConvergenceCalculation",
    "ConvergenceError",
    "ConvergenceRecord",
    "CriticalDepthResult",
    "CrossSectionGeometry",
    "CrossingHydraulicResult",
    "CrossingSummary",
    "CspCorrugation",
    "CspManningEntry",
    "CulvertBarrel",
    "CulvertCrossing",
    "CulvertGroup",
    "CulvertInventory",
    "CulvertInventoryItem",
    "CulvertMaterial",
    "EntranceLossCoefficient",
    "EntranceLossSelection",
    "EntranceLossSelectionBasis",
    "ExitLossSelection",
    "ExitLossSelectionBasis",
    "FilletedRectangularGeometry",
    "FlowRegime",
    "FullFlowOutletResult",
    "GeometryShape",
    "GroupHydraulicResult",
    "GroupSummary",
    "HeadLossComponents",
    "HydraulicApplicabilityNotice",
    "HydraulicResultStatus",
    "HydraulicWarning",
    "HydraulicWarningCode",
    "InletCoefficientSelection",
    "InletCoefficients",
    "InletControlProfile",
    "InletControlResult",
    "InletEquationForm",
    "InletSelectionBasis",
    "InvalidInputError",
    "InventorySummary",
    "ManningChannelTailwater",
    "ManningRoughnessSelection",
    "ModernBoxInlet",
    "ModernBoxInletCoefficients",
    "ModernBoxInletResult",
    "NormalDepthResult",
    "OpenChannelSection",
    "PartialFlowOutletResult",
    "ProfileCurve",
    "ProfilePoint",
    "RatingCurvePoint",
    "RatingCurveResult",
    "RectangularChannel",
    "RectangularGeometry",
    "RoadwayOvertoppingResult",
    "RoadwayWeir",
    "RootResult",
    "RootTolerances",
    "RoughnessApplicabilityNotice",
    "RoughnessSelectionBasis",
    "SolverConfiguration",
    "SourceReference",
    "TailwaterBoundary",
    "TailwaterCondition",
    "TailwaterInput",
    "TailwaterMethod",
    "TailwaterResolution",
    "TrapezoidalChannel",
    "WaterSurfaceProfile",
    "__version__",
    "calculate_channel_normal_depth",
    "calculate_critical_depth",
    "calculate_downstream_full_flow_length",
    "calculate_entrance_loss",
    "calculate_exit_loss",
    "calculate_friction_loss",
    "calculate_full_flow_outlet_headwater",
    "calculate_inlet_control_headwater",
    "calculate_modern_box_inlet_headwater",
    "calculate_normal_depth",
    "calculate_partial_flow_outlet_headwater",
    "calculate_roadway_overtopping",
    "calculate_sequent_depth",
    "calculate_total_head_loss",
    "compute_backwater_profile",
    "compute_inlet_control_s2_profile",
    "compute_steep_inlet_control_profile",
    "cross_section_velocity",
    "determine_governing_regime",
    "dimension_mm_to_m",
    "flow_parameter",
    "friction_head_loss",
    "froude_number",
    "generate_barrel_rating_curve",
    "generate_crossing_rating_curve",
    "generate_discharge_range",
    "hydraulic_radius",
    "hydrostatic_pressure_moment",
    "manning_discharge",
    "manning_friction_slope",
    "minor_head_loss",
    "momentum_function",
    "resolve_csp_manning_roughness",
    "resolve_entrance_loss_coefficient",
    "resolve_exit_loss_coefficient",
    "resolve_inlet_coefficients",
    "resolve_manning_roughness",
    "resolve_modern_box_inlet_coefficients",
    "resolve_tailwater",
    "solve_barrel_discharge_for_headwater",
    "solve_barrel_discharge_for_headwater_ratio",
    "solve_barrel_hydraulics",
    "solve_bracketed",
    "solve_brent",
    "solve_crossing_discharge_for_headwater",
    "solve_crossing_hydraulics",
    "solve_group_discharge_for_headwater",
    "solve_group_hydraulics",
    "specific_energy",
    "submerged_headwater",
    "transition_headwater",
    "unsubmerged_headwater_form_1",
    "unsubmerged_headwater_form_2",
    "velocity_head",
    "water_surface_elevation_from_energy_grade",
]
