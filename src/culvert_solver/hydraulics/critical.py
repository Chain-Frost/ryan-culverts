"""Critical depth calculations for culvert cross-sections."""

import math
from dataclasses import dataclass

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..geometry.base import CrossSectionGeometry
from ..geometry.rectangular import RectangularGeometry
from ..numerical.roots import RootResult, solve_brent
from ..numerical.tolerances import RootTolerances
from .primitives import froude_number

_DEFAULT_CRITICAL_TOLERANCES = RootTolerances(x_abs=1e-7, x_rel=1e-9)


@dataclass(frozen=True, slots=True)
class CriticalDepthResult:
    """Critical depth calculation outcome and associated hydraulic terms.

    depth: Critical depth in metres.
    specific_energy: Specific energy E = yc + Vc²/(2g) in metres.
    froude_number: Froude number at critical depth (1.0 for open-channel flow).
    is_submerged: True if critical depth reaches or exceeds the conduit rise.
    convergence: Root diagnostics for numerically solved depths; ``None`` for analytical
        and boundary outcomes.
    """

    depth: float
    specific_energy: float
    froude_number: float
    is_submerged: bool
    convergence: RootResult | None = None


def calculate_critical_depth(
    geometry: CrossSectionGeometry,
    discharge: float,
    *,
    g: float = GRAVITATIONAL_ACCELERATION,
    tolerances: RootTolerances = _DEFAULT_CRITICAL_TOLERANCES,
) -> CriticalDepthResult:
    """Compute the critical depth where Froude number Fr = 1 (minimum specific energy).

    For rectangular cross-sections, an exact closed-form analytical solution is used.
    For other geometries, the continuous relation g*A(y)³ - Q²*T(y) = 0 is solved
    using a bracket-preserving Brent solver.
    """
    q: float = finite(discharge, "discharge")
    if q < 0:
        raise InvalidInputError("discharge must be nonnegative.")
    accel: float = finite(g, "g")
    if accel <= 0:
        raise InvalidInputError("g must be strictly positive.")

    if q == 0.0:
        return CriticalDepthResult(
            depth=0.0,
            specific_energy=0.0,
            froude_number=0.0,
            is_submerged=False,
        )

    # Rectangular analytical closed-form: yc = (q_unit² / g)^(1/3)
    if isinstance(geometry, RectangularGeometry):
        b: float = geometry.span
        q_unit: float = q / b
        yc: float = (q_unit * q_unit / accel) ** (1.0 / 3.0)
        if yc >= geometry.rise:
            vc_full: float = q / geometry.area_full
            hv_full: float = (vc_full * vc_full) / (2.0 * accel)
            return CriticalDepthResult(
                depth=yc,
                specific_energy=yc + hv_full,
                froude_number=math.nan,
                is_submerged=True,
            )
        a: float = geometry.area(yc)
        vc: float = q / a
        hv: float = (vc * vc) / (2.0 * accel)
        t: float = geometry.top_width(yc)
        fr: float = froude_number(discharge=q, area=a, top_width=t, g=accel)
        return CriticalDepthResult(
            depth=yc,
            specific_energy=yc + hv,
            froude_number=fr,
            is_submerged=False,
        )

    # General / Circular cross-section: solve g * A(y)³ - Q² * T(y) = 0
    rise: float = geometry.rise

    def f_critical(y: float) -> float:
        a_val: float = geometry.area(y)
        t_val: float = geometry.top_width(y)
        return accel * (a_val**3) - (q * q) * t_val

    # Test lower bound near zero
    y_low: float = 1e-7 * rise
    f_low: float = f_critical(y_low)
    if f_low >= 0:
        a = geometry.area(y_low)
        vc = q / a
        hv = (vc * vc) / (2.0 * accel)
        t = geometry.top_width(y_low)
        fr = froude_number(discharge=q, area=a, top_width=t, g=accel)
        return CriticalDepthResult(
            depth=y_low,
            specific_energy=y_low + hv,
            froude_number=fr,
            is_submerged=False,
        )

    # Test upper bound near crown
    y_high: float = (1.0 - 1e-7) * rise
    f_high: float = f_critical(y_high)

    # If critical depth exceeds the crown
    if f_high <= 0:
        vc_full = q / geometry.area_full
        hv_full = (vc_full * vc_full) / (2.0 * accel)
        return CriticalDepthResult(
            depth=rise,
            specific_energy=rise + hv_full,
            froude_number=math.nan,
            is_submerged=True,
        )

    # Solve bracketed root on (y_low, y_high)
    root_result: RootResult = solve_brent(
        function=f_critical,
        lower=y_low,
        upper=y_high,
        tolerances=tolerances,
    )
    yc = root_result.root
    a = geometry.area(yc)
    vc = q / a
    hv = (vc * vc) / (2.0 * accel)
    t = geometry.top_width(yc)
    fr = froude_number(discharge=q, area=a, top_width=t, g=accel)
    return CriticalDepthResult(
        depth=yc,
        specific_energy=yc + hv,
        froude_number=fr,
        is_submerged=False,
        convergence=root_result,
    )
