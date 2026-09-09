"""Fundamental SI open-channel and closed-conduit hydraulic primitives."""

import math

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError


def cross_section_velocity(discharge: float, area: float) -> float:
    """Mean cross-sectional velocity V = Q / A in metres per second."""
    q: float = finite(discharge, "discharge")
    a: float = finite(area, "area")
    if a <= 0:
        raise InvalidInputError("area must be strictly positive.")
    return q / a


def velocity_head(
    velocity: float,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Velocity head hv = V² / (2*g) in metres."""
    v: float = finite(velocity, "velocity")
    accel: float = finite(g, "g")
    if accel <= 0:
        raise InvalidInputError("g must be strictly positive.")
    return (v * v) / (2.0 * accel)


def specific_energy(depth: float, velocity_head: float) -> float:
    """Specific energy E = y + hv in metres.

    Assumes uniform velocity distribution (Coriolis coefficient alpha = 1).
    """
    y: float = finite(depth, "depth")
    if y < 0:
        raise InvalidInputError("depth must be nonnegative.")
    hv: float = finite(velocity_head, "velocity_head")
    if hv < 0:
        raise InvalidInputError("velocity_head must be nonnegative.")
    return y + hv


def froude_number(
    discharge: float,
    area: float,
    top_width: float,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> float:
    """Froude number Fr = sqrt(Q² * T / (g * A³)) for free-surface flow.

    Requires positive area, top width, and gravitational acceleration.
    Raises InvalidInputError for closed-conduit flow where top width is zero.
    """
    q: float = finite(discharge, "discharge")
    a: float = finite(area, "area")
    if a <= 0:
        raise InvalidInputError("area must be strictly positive.")
    t: float = finite(top_width, "top_width")
    if t <= 0:
        raise InvalidInputError(
            "top_width must be strictly positive for free-surface Froude calculation."
        )
    accel: float = finite(g, "g")
    if accel <= 0:
        raise InvalidInputError("g must be strictly positive.")

    ratio: float = (q * q * t) / (accel * a * a * a)
    return math.sqrt(ratio)


def manning_discharge(
    area: float,
    hydraulic_radius: float,
    slope: float,
    roughness: float,
) -> float:
    """Manning uniform discharge Q = (1 / n) * A * R^(2/3) * sqrt(S0) in cubic metres per second."""
    a: float = finite(area, "area")
    if a < 0:
        raise InvalidInputError("area must be nonnegative.")
    r: float = finite(hydraulic_radius, "hydraulic_radius")
    if r < 0:
        raise InvalidInputError("hydraulic_radius must be nonnegative.")
    s0: float = finite(slope, "slope")
    if s0 < 0:
        raise InvalidInputError("slope must be nonnegative.")
    n: float = finite(roughness, "roughness")
    if n <= 0:
        raise InvalidInputError("roughness must be strictly positive.")

    if a == 0 or r == 0 or s0 == 0:
        return 0.0

    return (1.0 / n) * a * (r ** (2.0 / 3.0)) * math.sqrt(s0)


def manning_friction_slope(
    discharge: float,
    area: float,
    hydraulic_radius: float,
    roughness: float,
) -> float:
    """Manning friction slope Sf = (n * |Q| / (A * R^(2/3)))² (dimensionless)."""
    q: float = finite(discharge, "discharge")
    a: float = finite(area, "area")
    if a <= 0:
        raise InvalidInputError("area must be strictly positive.")
    r: float = finite(hydraulic_radius, "hydraulic_radius")
    if r <= 0:
        raise InvalidInputError("hydraulic_radius must be strictly positive.")
    n: float = finite(roughness, "roughness")
    if n <= 0:
        raise InvalidInputError("roughness must be strictly positive.")

    if q == 0:
        return 0.0

    ratio: float = (n * abs(q)) / (a * (r ** (2.0 / 3.0)))
    return ratio * ratio


def friction_head_loss(length: float, friction_slope: float) -> float:
    """Friction head loss hf = L * Sf in metres."""
    length_val: float = finite(length, "length")
    if length_val < 0:
        raise InvalidInputError("length must be nonnegative.")
    sf_val: float = finite(friction_slope, "friction_slope")
    if sf_val < 0:
        raise InvalidInputError("friction_slope must be nonnegative.")
    return length_val * sf_val


def minor_head_loss(loss_coefficient: float, velocity_head: float) -> float:
    """Minor / local head loss h_local = K * hv in metres."""
    k: float = finite(loss_coefficient, "loss_coefficient")
    if k < 0:
        raise InvalidInputError("loss_coefficient must be nonnegative.")
    hv: float = finite(velocity_head, "velocity_head")
    if hv < 0:
        raise InvalidInputError("velocity_head must be nonnegative.")
    return k * hv
