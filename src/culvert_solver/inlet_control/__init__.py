"""Inlet-control hydraulics, empirical coefficients, and FHWA equation solvers."""

from .coefficients import (
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
from .fhwa import (
    flow_parameter,
    submerged_headwater,
    transition_headwater,
    unsubmerged_headwater_form_1,
    unsubmerged_headwater_form_2,
)
from .solver import (
    EXTREME_HEADWATER_RATIO,
    HDS5_LABORATORY_HW_D_MAX,
    InletControlResult,
    calculate_inlet_control_headwater,
)

__all__: list[str] = [
    "BOX_CONCRETE_BEVEL_45_HEADWALL",
    "BOX_CONCRETE_CHAMFER_90_HEADWALL",
    "BOX_CONCRETE_FLARED_WINGWALLS_30_75",
    "BOX_CONCRETE_PARALLEL_WINGWALLS_0",
    "CIRCULAR_CMP_HEADWALL",
    "CIRCULAR_CMP_MITERED",
    "CIRCULAR_CMP_PROJECTING",
    "CIRCULAR_CONCRETE_GROOVE_END",
    "CIRCULAR_CONCRETE_SQUARE_EDGE",
    "STANDARD_INLET_COEFFICIENTS",
    "InletCoefficients",
    "InletControlResult",
    "EXTREME_HEADWATER_RATIO",
    "HDS5_LABORATORY_HW_D_MAX",
    "calculate_inlet_control_headwater",
    "flow_parameter",
    "submerged_headwater",
    "transition_headwater",
    "unsubmerged_headwater_form_1",
    "unsubmerged_headwater_form_2",
]
