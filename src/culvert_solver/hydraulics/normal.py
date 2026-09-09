"""Normal depth calculations for culvert cross-sections under uniform flow."""

import math
from dataclasses import dataclass

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..geometry.base import CrossSectionGeometry
from ..geometry.circular import CircularGeometry
from ..numerical.roots import RootResult, solve_brent
from ..numerical.tolerances import RootTolerances
from .primitives import froude_number

_DEFAULT_NORMAL_TOLERANCES = RootTolerances(x_abs=1e-7, x_rel=1e-9)

# Fraction of diameter where circular Manning conveyance reaches its maximum
_CIRCULAR_MAX_CONVEYANCE_DEPTH_RATIO: float = 0.9381796


@dataclass(frozen=True, slots=True)
class NormalDepthResult:
    """Normal depth calculation outcome and associated hydraulic terms.

    depth: Normal depth in metres.
    velocity: Mean velocity at normal depth in metres per second.
    froude_number: Froude number at normal depth (float('nan') if full/closed).
    conveyance: Manning conveyance K = A * R^(2/3) in m^(8/3).
    is_full: True if normal depth reaches or exceeds the conduit rise.
    capacity_exceeded: True if discharge exceeds open-channel conveyance capacity.
    convergence: Root diagnostics for numerically solved depths; ``None`` for exact
        zero-flow and capacity-boundary outcomes.
    """

    depth: float
    velocity: float
    froude_number: float
    conveyance: float
    is_full: bool
    capacity_exceeded: bool
    convergence: RootResult | None = None


def calculate_normal_depth(
    geometry: CrossSectionGeometry,
    discharge: float,
    slope: float,
    roughness: float,
    *,
    g: float = GRAVITATIONAL_ACCELERATION,
    tolerances: RootTolerances = _DEFAULT_NORMAL_TOLERANCES,
) -> NormalDepthResult:
    """Compute the uniform flow normal depth satisfying Manning's equation.

    For circular conduits, solves strictly on the stable monotonically increasing
    branch (y <= 0.9382 * D), avoiding the non-monotone crown region.
    """
    q: float = finite(discharge, "discharge")
    if q < 0:
        raise InvalidInputError("discharge must be nonnegative.")
    s0: float = finite(slope, "slope")
    if s0 < 0:
        raise InvalidInputError("slope must be nonnegative.")
    n: float = finite(roughness, "roughness")
    if n <= 0:
        raise InvalidInputError("roughness must be strictly positive.")
    accel: float = finite(g, "g")
    if accel <= 0:
        raise InvalidInputError("g must be strictly positive.")

    if q == 0.0:
        return NormalDepthResult(
            depth=0.0,
            velocity=0.0,
            froude_number=0.0,
            conveyance=0.0,
            is_full=False,
            capacity_exceeded=False,
        )

    if s0 == 0.0:
        raise InvalidInputError("Normal depth is undefined for zero slope with positive discharge.")

    k_req: float = (n * q) / math.sqrt(s0)

    # Circular geometry: solve on stable conveyance branch [0, 0.93818 * D]
    if isinstance(geometry, CircularGeometry):
        d: float = geometry.diameter
        y_peak: float = _CIRCULAR_MAX_CONVEYANCE_DEPTH_RATIO * d
        r_peak: float = geometry.hydraulic_radius(y_peak)
        k_max: float = geometry.area(y_peak) * (r_peak ** (2.0 / 3.0))
        k_full: float = geometry.area_full * (geometry.hydraulic_radius_full ** (2.0 / 3.0))

        if k_req > k_max:
            return NormalDepthResult(
                depth=d,
                velocity=q / geometry.area_full,
                froude_number=math.nan,
                conveyance=k_full,
                is_full=True,
                capacity_exceeded=True,
            )

        if k_req == k_max:
            a_peak = geometry.area(y_peak)
            v_peak = q / a_peak
            t_peak = geometry.top_width(y_peak)
            fr_peak = froude_number(q, a_peak, t_peak, accel)
            return NormalDepthResult(
                depth=y_peak,
                velocity=v_peak,
                froude_number=fr_peak,
                conveyance=k_max,
                is_full=False,
                capacity_exceeded=False,
            )

        def f_conveyance_circ(y: float) -> float:
            r_val: float = geometry.hydraulic_radius(y)
            return geometry.area(y) * (r_val ** (2.0 / 3.0)) - k_req

        root_res = solve_brent(f_conveyance_circ, 0.0, y_peak, tolerances=tolerances)
        yn = root_res.root
        a = geometry.area(yn)
        v = q / a
        t = geometry.top_width(yn)
        fr = froude_number(q, a, t, accel)
        k_val = a * (geometry.hydraulic_radius(yn) ** (2.0 / 3.0))
        return NormalDepthResult(
            depth=yn,
            velocity=v,
            froude_number=fr,
            conveyance=k_val,
            is_full=False,
            capacity_exceeded=False,
            convergence=root_res,
        )

    # Rectangular / general cross-sections: monotonic on [0, rise]
    rise: float = geometry.rise
    k_full = geometry.area_full * (geometry.hydraulic_radius_full ** (2.0 / 3.0))

    if k_req > k_full:
        return NormalDepthResult(
            depth=rise,
            velocity=q / geometry.area_full,
            froude_number=math.nan,
            conveyance=k_full,
            is_full=True,
            capacity_exceeded=True,
        )

    if k_req == k_full:
        return NormalDepthResult(
            depth=rise,
            velocity=q / geometry.area_full,
            froude_number=math.nan,
            conveyance=k_full,
            is_full=True,
            capacity_exceeded=False,
        )

    def f_conveyance(y: float) -> float:
        r_val: float = geometry.hydraulic_radius(y)
        return geometry.area(y) * (r_val ** (2.0 / 3.0)) - k_req

    root_res = solve_brent(f_conveyance, 0.0, rise, tolerances=tolerances)
    yn = root_res.root
    a = geometry.area(yn)
    v = q / a
    t = geometry.top_width(yn)
    fr = froude_number(q, a, t, accel)
    k_val = a * (geometry.hydraulic_radius(yn) ** (2.0 / 3.0))
    return NormalDepthResult(
        depth=yn,
        velocity=v,
        froude_number=fr,
        conveyance=k_val,
        is_full=False,
        capacity_exceeded=False,
        convergence=root_res,
    )
