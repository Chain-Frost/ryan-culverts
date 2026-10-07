"""Configuration policies for hydraulic solvers and coefficient resolution."""

from dataclasses import dataclass

from ..inlet_control.coefficients import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75 as INLET_BOX_FLARED,
)
from ..inlet_control.coefficients import (
    CIRCULAR_CMP_HEADWALL as INLET_CMP_HEADWALL,
)
from ..inlet_control.coefficients import (
    CIRCULAR_CONCRETE_SQUARE_EDGE as INLET_CONCRETE_SQUARE,
)
from ..inlet_control.coefficients import InletCoefficients
from ..outlet_control.losses import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75 as LOSS_BOX_FLARED,
)
from ..outlet_control.losses import (
    PIPE_CMP_HEADWALL as LOSS_CMP_HEADWALL,
)
from ..outlet_control.losses import (
    PIPE_CONCRETE_SQUARE_EDGE as LOSS_CONCRETE_SQUARE,
)
from ..outlet_control.losses import EntranceLossCoefficient


@dataclass(frozen=True, slots=True)
class SolverConfiguration:
    """Immutable configuration object holding solver-facing defaults and policies.

    This class decouples hardcoded library defaults from the resolution logic,
    allowing consumers to inject project-specific defaults without mutating
    global state.
    """

    default_circular_concrete_inlet: InletCoefficients = INLET_CONCRETE_SQUARE
    default_circular_cmp_inlet: InletCoefficients = INLET_CMP_HEADWALL
    default_rectangular_inlet: InletCoefficients = INLET_BOX_FLARED
    default_circular_concrete_loss: EntranceLossCoefficient = LOSS_CONCRETE_SQUARE
    default_circular_cmp_loss: EntranceLossCoefficient = LOSS_CMP_HEADWALL
    default_rectangular_loss: EntranceLossCoefficient = LOSS_BOX_FLARED


DEFAULT_SOLVER_CONFIGURATION = SolverConfiguration()
