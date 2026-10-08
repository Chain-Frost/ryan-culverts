"""Normal depth calculations for culvert cross-sections under uniform flow."""

import math
from dataclasses import dataclass
from functools import lru_cache

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..geometry.base import CrossSectionGeometry
from ..geometry.circular import CircularGeometry
from ..geometry.elliptical import HorizontalEllipseGeometry, VerticalEllipseGeometry
from ..geometry.hy8_oval import Hy8ConcreteOvalGeometry, hy8_oval_max_conveyance_depth
from ..numerical.roots import RootResult, solve_brent
from ..numerical.tolerances import RootTolerances
from .primitives import froude_number

_DEFAULT_NORMAL_TOLERANCES = RootTolerances(x_abs=1e-7, x_rel=1e-9)

# Fraction of diameter where circular Manning conveyance reaches its maximum
_CIRCULAR_MAX_CONVEYANCE_DEPTH_RATIO: float = 0.9381796


def _section_conveyance(geometry: CrossSectionGeometry, depth: float) -> float:
    area = geometry.area(depth)
    radius = geometry.hydraulic_radius(depth)
    return area * (radius ** (2.0 / 3.0))


@lru_cache(maxsize=256)
def _ellipse_max_conveyance_depth_for_dimensions(span: float, rise: float) -> float:
    """Locate and cache the conveyance maximum for one ellipse geometry."""
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry
    if span > rise:
        geometry = HorizontalEllipseGeometry(span=span, rise=rise)
    else:
        geometry = VerticalEllipseGeometry(span=span, rise=rise)

    lower = 0.0
    upper = rise
    for _ in range(80):
        first = lower + (upper - lower) / 3.0
        second = upper - (upper - lower) / 3.0
        if _section_conveyance(geometry, first) < _section_conveyance(geometry, second):
            lower = first
        else:
            upper = second
    return (lower + upper) / 2.0


def _ellipse_max_conveyance_depth(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
) -> float:
    """Return the cached rising-branch conveyance maximum for a closed ellipse."""
    return _ellipse_max_conveyance_depth_for_dimensions(geometry.span, geometry.rise)


def _closed_section_max_conveyance_depth(
    geometry: CircularGeometry | HorizontalEllipseGeometry | VerticalEllipseGeometry | Hy8ConcreteOvalGeometry,
) -> float:
    """Select a shape-specific stable open-channel conveyance peak."""
    if isinstance(geometry, CircularGeometry):
        return _CIRCULAR_MAX_CONVEYANCE_DEPTH_RATIO * geometry.diameter
    if isinstance(geometry, Hy8ConcreteOvalGeometry):
        return hy8_oval_max_conveyance_depth(geometry.catalogue_index)
    return _ellipse_max_conveyance_depth(geometry)


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

    For circular and elliptical closed conduits, solves strictly on the stable
    monotonically increasing conveyance branch, avoiding the non-monotone crown region.
    """
    q: float = finite(discharge, "discharge")
    if q < 0:
        msg = "discharge must be nonnegative."
        raise InvalidInputError(msg)
    s0: float = finite(slope, "slope")
    if s0 < 0:
        msg = "slope must be nonnegative."
        raise InvalidInputError(msg)
    n: float = finite(roughness, "roughness")
    if n <= 0:
        msg = "roughness must be strictly positive."
        raise InvalidInputError(msg)
    accel: float = finite(g, "g")
    if accel <= 0:
        msg = "g must be strictly positive."
        raise InvalidInputError(msg)

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
        msg = "Normal depth is undefined for zero slope with positive discharge."
        raise InvalidInputError(msg)

    k_req: float = (n * q) / math.sqrt(s0)

    # Closed circles and ellipses reach maximum conveyance before the crown.
    if isinstance(geometry, (CircularGeometry, HorizontalEllipseGeometry, VerticalEllipseGeometry, Hy8ConcreteOvalGeometry)):
        y_peak = _closed_section_max_conveyance_depth(geometry)
        k_max = _section_conveyance(geometry, y_peak)
        k_full = _section_conveyance(geometry, geometry.rise)

        if k_req > k_max:
            return NormalDepthResult(
                depth=geometry.rise,
                velocity=q / geometry.area_full,
                froude_number=math.nan,
                conveyance=k_full,
                is_full=True,
                capacity_exceeded=True,
            )

        if k_req == k_max:
            area_peak = geometry.area(y_peak)
            velocity_peak = q / area_peak
            top_width_peak = geometry.top_width(y_peak)
            froude_peak = froude_number(q, area_peak, top_width_peak, accel)
            return NormalDepthResult(
                depth=y_peak,
                velocity=velocity_peak,
                froude_number=froude_peak,
                conveyance=k_max,
                is_full=False,
                capacity_exceeded=False,
            )

        def f_conveyance_closed(y: float) -> float:
            return _section_conveyance(geometry, y) - k_req

        root_res = solve_brent(f_conveyance_closed, 0.0, y_peak, tolerances=tolerances)
        yn = root_res.root
        area = geometry.area(yn)
        velocity = q / area
        top_width = geometry.top_width(yn)
        froude = froude_number(q, area, top_width, accel)
        return NormalDepthResult(
            depth=yn,
            velocity=velocity,
            froude_number=froude,
            conveyance=_section_conveyance(geometry, yn),
            is_full=False,
            capacity_exceeded=False,
            convergence=root_res,
        )

    # Rectangular / remaining general cross-sections: monotonic on [0, rise]
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
