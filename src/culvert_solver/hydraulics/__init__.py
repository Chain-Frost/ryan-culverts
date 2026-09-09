"""SI hydraulic primitives and fundamental relations."""

from .critical import CriticalDepthResult, calculate_critical_depth
from .momentum import calculate_sequent_depth, hydrostatic_pressure_moment, momentum_function
from .normal import NormalDepthResult, calculate_normal_depth
from .primitives import (
    cross_section_velocity,
    friction_head_loss,
    froude_number,
    manning_discharge,
    manning_friction_slope,
    minor_head_loss,
    specific_energy,
    velocity_head,
)

__all__: list[str] = [
    "CriticalDepthResult",
    "NormalDepthResult",
    "calculate_critical_depth",
    "calculate_normal_depth",
    "calculate_sequent_depth",
    "cross_section_velocity",
    "friction_head_loss",
    "froude_number",
    "hydrostatic_pressure_moment",
    "manning_discharge",
    "manning_friction_slope",
    "minor_head_loss",
    "momentum_function",
    "specific_energy",
    "velocity_head",
]
