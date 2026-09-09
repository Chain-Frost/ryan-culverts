"""Independent, early-stage culvert hydraulics library.

The package exposes internally tested geometry and hydraulic components through
provisional combined solvers. External engineering validation is not yet complete.
"""

from .constants import (
    GRAVITATIONAL_ACCELERATION,
    STANDARD_WATER_DENSITY,
    STANDARD_WATER_KINEMATIC_VISCOSITY,
)
from .exceptions import ConvergenceError, InvalidInputError
from .geometry.base import CrossSectionGeometry
from .geometry.circular import CircularGeometry
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
    BarrelHydraulicResult,
    ConvergenceRecord,
    CrossingHydraulicResult,
    FlowRegime,
    GroupHydraulicResult,
    HeadLossComponents,
    HydraulicWarning,
)
from .models.tailwater import TailwaterCondition
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
from .solver.barrel import solve_barrel_hydraulics
from .solver.config import DEFAULT_SOLVER_CONFIGURATION, SolverConfiguration
from .solver.crossing import solve_crossing_hydraulics
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

__all__: list[str] = [
    "AdoptedParameterSet",
    "ApplicabilityNoticeCode",
    "BOX_CONCRETE_BEVEL_45_HEADWALL",
    "BOX_CONCRETE_CHAMFER_90_HEADWALL",
    "BOX_CONCRETE_FLARED_WINGWALLS_30_75",
    "BOX_CONCRETE_PARALLEL_WINGWALLS_0",
    "CIRCULAR_CMP_HEADWALL",
    "CIRCULAR_CMP_MITERED",
    "CIRCULAR_CMP_PROJECTING",
    "CIRCULAR_CONCRETE_GROOVE_END",
    "CIRCULAR_CONCRETE_SQUARE_EDGE",
    "CONCRETE",
    "CONCRETE_BOX",
    "CONCRETE_PIPE",
    "CORRUGATED_STEEL",
    "MRWA_CSP_MANNING_TABLE",
    "MRWA_CSP_REFERENCE",
    "MRWA_CONCRETE_REFERENCE",
    "MRWA_PART5B_REFERENCE",
    "MRWA_SPEC404_REFERENCE",
    "SMOOTH_HDPE",
    "BarrelHydraulicResult",
    "CircularGeometry",
    "ConvergenceError",
    "CriticalDepthResult",
    "CrossingHydraulicResult",
    "CrossSectionGeometry",
    "CulvertBarrel",
    "CulvertCrossing",
    "CrossingSummary",
    "CulvertGroup",
    "CulvertInventory",
    "CulvertInventoryItem",
    "CulvertMaterial",
    "CspCorrugation",
    "CspManningEntry",
    "ControlType",
    "ConvergenceCalculation",
    "ConvergenceRecord",
    "DEFAULT_SOLVER_CONFIGURATION",
    "EntranceLossCoefficient",
    "ExitLossSelection",
    "ExitLossSelectionBasis",
    "EntranceLossSelection",
    "EntranceLossSelectionBasis",
    "EXTREME_HEADWATER_RATIO",
    "FlowRegime",
    "FullFlowOutletResult",
    "GeometryShape",
    "GRAVITATIONAL_ACCELERATION",
    "GroupHydraulicResult",
    "GroupSummary",
    "HeadLossComponents",
    "HydraulicWarning",
    "HydraulicWarningCode",
    "HDS5_LABORATORY_HW_D_MAX",
    "InletControlProfile",
    "InletCoefficients",
    "InletCoefficientSelection",
    "InletEquationForm",
    "InletControlResult",
    "InletSelectionBasis",
    "InvalidInputError",
    "InventorySummary",
    "NormalDepthResult",
    "ManningRoughnessSelection",
    "PartialFlowOutletResult",
    "ProfilePoint",
    "ProfileCurve",
    "RatingCurvePoint",
    "RatingCurveResult",
    "RectangularGeometry",
    "RootResult",
    "RootTolerances",
    "RoughnessSelectionBasis",
    "RoughnessApplicabilityNotice",
    "STANDARD_EXIT_LOSS_COEFFICIENT",
    "STANDARD_EXIT_LOSS_SELECTION",
    "STANDARD_INLET_COEFFICIENTS",
    "STANDARD_WATER_DENSITY",
    "STANDARD_WATER_KINEMATIC_VISCOSITY",
    "SolverConfiguration",
    "SourceReference",
    "TailwaterCondition",
    "WaterSurfaceProfile",
    "BOX_LOSS_FLARED_30_75",
    "BOX_LOSS_PARALLEL_0",
    "PIPE_CMP_LOSS_HEADWALL",
    "PIPE_CMP_LOSS_PROJECTING",
    "PIPE_LOSS_SOCKET_END",
    "PIPE_LOSS_SQUARE_EDGE",
    "calculate_critical_depth",
    "calculate_entrance_loss",
    "calculate_exit_loss",
    "calculate_friction_loss",
    "calculate_full_flow_outlet_headwater",
    "calculate_downstream_full_flow_length",
    "calculate_inlet_control_headwater",
    "calculate_normal_depth",
    "calculate_sequent_depth",
    "calculate_partial_flow_outlet_headwater",
    "calculate_total_head_loss",
    "resolve_exit_loss_coefficient",
    "compute_backwater_profile",
    "compute_inlet_control_s2_profile",
    "compute_steep_inlet_control_profile",
    "cross_section_velocity",
    "determine_governing_regime",
    "dimension_mm_to_m",
    "flow_parameter",
    "friction_head_loss",
    "froude_number",
    "hydrostatic_pressure_moment",
    "generate_barrel_rating_curve",
    "generate_crossing_rating_curve",
    "generate_discharge_range",
    "manning_discharge",
    "manning_friction_slope",
    "minor_head_loss",
    "momentum_function",
    "resolve_csp_manning_roughness",
    "resolve_entrance_loss_coefficient",
    "resolve_inlet_coefficients",
    "resolve_manning_roughness",
    "solve_barrel_hydraulics",
    "solve_bracketed",
    "solve_brent",
    "solve_crossing_hydraulics",
    "solve_group_hydraulics",
    "specific_energy",
    "submerged_headwater",
    "transition_headwater",
    "unsubmerged_headwater_form_1",
    "unsubmerged_headwater_form_2",
    "velocity_head",
]
