"""Pure SI implementations of FHWA HDS-5 inlet-control equations."""

import math

from .._validation import finite
from ..exceptions import InvalidInputError
from .coefficients import InletCoefficients

# SI unit conversion constant from FHWA HDS-5 Appendix A, printed page A.2.
KU_SI: float = 1.811

# Dimensionless discharge thresholds defining the transition zone in HDS-5 Appendix A
Q_STAR_UNSUBMERGED_LIMIT: float = 3.5
Q_STAR_SUBMERGED_THRESHOLD: float = 4.0


def flow_parameter(discharge: float, area: float, rise: float, ku: float = KU_SI) -> float:
    """Compute the dimensionless discharge parameter q* = (Ku * Q) / (A * D^0.5)."""
    q: float = finite(discharge, "discharge")
    if q < 0:
        msg = "discharge must be nonnegative."
        raise InvalidInputError(msg)
    a: float = finite(area, "area")
    if a <= 0:
        msg = "area must be strictly positive."
        raise InvalidInputError(msg)
    d: float = finite(rise, "rise")
    if d <= 0:
        msg = "rise must be strictly positive."
        raise InvalidInputError(msg)
    ku_val: float = finite(ku, "ku")

    if q == 0.0:
        return 0.0
    return (ku_val * q) / (a * math.sqrt(d))


def unsubmerged_headwater_form_1(
    q_star: float,
    hc_over_d: float,
    slope: float,
    coefficients: InletCoefficients,
) -> float:
    """Compute unsubmerged headwater ratio HWi / D using HDS-5 Equation A.1.

    HWi / D = Hc / D + K * (q*)^M + Ks * S
    """
    qs: float = finite(q_star, "q_star")
    if qs < 0:
        msg = "q_star must be nonnegative."
        raise InvalidInputError(msg)
    hc_d: float = finite(hc_over_d, "hc_over_d")
    s: float = finite(slope, "slope")
    if s < 0:
        msg = "slope must be nonnegative."
        raise InvalidInputError(msg)

    if qs == 0.0:
        return 0.0
    val: float = hc_d + coefficients.k * (qs**coefficients.m) + coefficients.slope_correction * s
    return max(0.0, val)


def unsubmerged_headwater_form_2(
    q_star: float,
    coefficients: InletCoefficients,
) -> float:
    """Compute unsubmerged headwater ratio HWi / D using HDS-5 Equation A.2.

    HWi / D = K * (q*)^M
    """
    qs: float = finite(q_star, "q_star")
    if qs < 0:
        msg = "q_star must be nonnegative."
        raise InvalidInputError(msg)

    if qs == 0.0:
        return 0.0
    val: float = coefficients.k * (qs**coefficients.m)
    return max(0.0, val)


def submerged_headwater(
    q_star: float,
    slope: float,
    coefficients: InletCoefficients,
) -> float:
    """Compute submerged orifice headwater ratio HWi / D using HDS-5 Equation A.3.

    HWi / D = c * (q*)² + Y + Ks * S
    """
    qs: float = finite(q_star, "q_star")
    if qs < 0:
        msg = "q_star must be nonnegative."
        raise InvalidInputError(msg)
    s: float = finite(slope, "slope")
    if s < 0:
        msg = "slope must be nonnegative."
        raise InvalidInputError(msg)

    val: float = coefficients.c * (qs * qs) + coefficients.y + coefficients.slope_correction * s
    return max(0.0, val)


def transition_headwater(
    q_star: float,
    hwi_d_unsub_at_limit: float,
    hwi_d_sub_at_threshold: float,
    unsubmerged_tangent: float,
    submerged_tangent: float,
    q_star_low: float = Q_STAR_UNSUBMERGED_LIMIT,
    q_star_high: float = Q_STAR_SUBMERGED_THRESHOLD,
) -> float:
    """Join inlet-control branches with a cubic curve tangent at both endpoints.

    HDS-5 Appendix A, printed page A.1, specifies a curve drawn between and tangent
    to the unsubmerged and submerged curves, and printed page A.6 says the nomograph
    transition was drawn by hand. It does not prescribe a digital interpolation
    algorithm. Cubic Hermite interpolation is the project's deterministic C1
    implementation of that construction; it is not HY-8's fitted polynomial method.
    """
    qs: float = finite(q_star, "q_star")
    h1: float = finite(hwi_d_unsub_at_limit, "hwi_d_unsub_at_limit")
    h2: float = finite(hwi_d_sub_at_threshold, "hwi_d_sub_at_threshold")
    q1: float = finite(q_star_low, "q_star_low")
    q2: float = finite(q_star_high, "q_star_high")
    tangent1: float = finite(unsubmerged_tangent, "unsubmerged_tangent")
    tangent2: float = finite(submerged_tangent, "submerged_tangent")

    if q2 <= q1:
        msg = "q_star_high must be strictly greater than q_star_low."
        raise InvalidInputError(msg)
    if not q1 <= qs <= q2:
        msg = "q_star must lie within the transition interval."
        raise InvalidInputError(msg)

    interval: float = q2 - q1
    ratio: float = (qs - q1) / interval
    h00: float = 2.0 * ratio**3 - 3.0 * ratio**2 + 1.0
    h10: float = ratio**3 - 2.0 * ratio**2 + ratio
    h01: float = -2.0 * ratio**3 + 3.0 * ratio**2
    h11: float = ratio**3 - ratio**2
    return h00 * h1 + h10 * interval * tangent1 + h01 * h2 + h11 * interval * tangent2
