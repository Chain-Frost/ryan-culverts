"""Open-channel momentum relations used to assess hydraulic-jump admissibility."""

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..geometry.base import CrossSectionGeometry
from ..numerical.roots import solve_bracketed
from ..numerical.tolerances import RootTolerances
from .critical import calculate_critical_depth

_SEQUENT_DEPTH_TOLERANCES = RootTolerances(x_abs=1e-7, x_rel=1e-9)


def hydrostatic_pressure_moment(
    geometry: CrossSectionGeometry,
    depth: float,
) -> float:
    """Return the hydrostatic first moment about the free surface in cubic metres.

    Built-in geometries use exact expressions. A composite-Simpson fallback in
    :class:`CrossSectionGeometry` keeps the relation available to future shapes.
    """
    y = finite(depth, "depth")
    if y < 0.0 or y > geometry.rise:
        raise InvalidInputError("depth must be between zero and the geometry rise.")
    return geometry.hydrostatic_pressure_moment(y)


def momentum_function(
    geometry: CrossSectionGeometry,
    discharge: float,
    depth: float,
    *,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Return open-channel momentum function ``Q^2/(g*A) + A*y_bar`` in m3."""
    q = finite(discharge, "discharge")
    if q <= 0.0:
        raise InvalidInputError("discharge must be strictly positive.")
    accel = finite(g, "g")
    if accel <= 0.0:
        raise InvalidInputError("g must be strictly positive.")
    y = finite(depth, "depth")
    if y <= 0.0 or y >= geometry.rise:
        raise InvalidInputError("depth must be strictly between zero and the geometry rise.")
    return q * q / (accel * geometry.area(y)) + hydrostatic_pressure_moment(geometry, y)


def calculate_sequent_depth(
    geometry: CrossSectionGeometry,
    discharge: float,
    supercritical_depth: float,
    *,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float | None:
    """Return the subcritical conjugate depth for a supercritical approach.

    The two depths have equal momentum functions. ``None`` means the conjugate
    free surface would reach or exceed the crown, so no free-surface root exists
    within the closed culvert section.
    """
    q = finite(discharge, "discharge")
    if q <= 0.0:
        raise InvalidInputError("discharge must be strictly positive.")
    y1 = finite(supercritical_depth, "supercritical_depth")
    rise = geometry.rise
    if y1 <= 0.0 or y1 >= rise:
        raise InvalidInputError(
            "supercritical_depth must be strictly between zero and the geometry rise."
        )

    critical_depth = calculate_critical_depth(geometry, q, g=g).depth
    depth_epsilon = max(1e-8, rise * 1e-7)
    if y1 >= critical_depth - depth_epsilon:
        raise InvalidInputError("supercritical_depth must be below critical depth.")

    target_momentum = momentum_function(geometry, q, y1, g=g)

    def residual(depth: float) -> float:
        return momentum_function(geometry, q, depth, g=g) - target_momentum

    lower = critical_depth + depth_epsilon
    upper = rise - depth_epsilon
    if residual(upper) <= 0.0:
        return None
    return solve_bracketed(
        residual,
        lower,
        upper,
        tolerances=_SEQUENT_DEPTH_TOLERANCES,
    ).root
