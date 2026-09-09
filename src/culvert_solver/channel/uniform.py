"""Manning uniform-flow calculations for prismatic open channels."""

import math
from dataclasses import dataclass

from .._validation import finite, positive_integer
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import ConvergenceError, InvalidInputError
from ..hydraulics.primitives import cross_section_velocity, froude_number, manning_discharge
from ..numerical.roots import RootResult, solve_brent
from ..numerical.tolerances import RootTolerances
from .geometry import OpenChannelSection

_DEFAULT_CHANNEL_NORMAL_TOLERANCES = RootTolerances(x_abs=1e-7, x_rel=1e-9)


@dataclass(frozen=True, slots=True)
class ChannelNormalDepthResult:
    """Auditable uniform-flow normal-depth result for an open channel."""

    depth: float
    area: float
    wetted_perimeter: float
    top_width: float
    hydraulic_radius: float
    velocity: float
    froude_number: float
    section_factor: float
    conveyance: float
    convergence: RootResult | None = None


def calculate_channel_normal_depth(
    section: OpenChannelSection,
    discharge: float,
    friction_slope: float,
    roughness: float,
    *,
    g: float = GRAVITATIONAL_ACCELERATION,
    initial_upper_depth: float = 1.0,
    max_bracket_expansions: int = 60,
    tolerances: RootTolerances = _DEFAULT_CHANNEL_NORMAL_TOLERANCES,
) -> ChannelNormalDepthResult:
    """Solve Manning normal depth for a prismatic open channel.

    ``friction_slope`` is the Manning energy slope. A representative bed slope
    is commonly used only under the uniform-flow assumption.
    """
    if not isinstance(section, OpenChannelSection):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidInputError("section must satisfy the OpenChannelSection protocol.")
    q: float = finite(discharge, "discharge")
    if q < 0.0:
        raise InvalidInputError("discharge must be nonnegative.")
    slope: float = finite(friction_slope, "friction_slope")
    if slope < 0.0:
        raise InvalidInputError("friction_slope must be nonnegative.")
    n: float = finite(roughness, "roughness")
    if n <= 0.0:
        raise InvalidInputError("roughness must be strictly positive.")
    accel: float = finite(g, "g")
    if accel <= 0.0:
        raise InvalidInputError("g must be strictly positive.")
    upper: float = finite(initial_upper_depth, "initial_upper_depth")
    if upper <= 0.0:
        raise InvalidInputError("initial_upper_depth must be strictly positive.")
    expansion_limit: int = positive_integer(max_bracket_expansions, "max_bracket_expansions")

    if q == 0.0:
        return ChannelNormalDepthResult(
            depth=0.0,
            area=0.0,
            wetted_perimeter=0.0,
            top_width=section.top_width(0.0),
            hydraulic_radius=0.0,
            velocity=0.0,
            froude_number=0.0,
            section_factor=0.0,
            conveyance=0.0,
        )
    if slope == 0.0:
        raise InvalidInputError("Normal depth is undefined for zero friction_slope with positive discharge.")

    def residual(depth: float) -> float:
        area: float = section.area(depth)
        perimeter: float = section.wetted_perimeter(depth)
        radius: float = 0.0 if area == 0.0 else area / perimeter
        return manning_discharge(area=area, hydraulic_radius=radius, slope=slope, roughness=n) - q

    expansions = 0
    while residual(upper) < 0.0:
        upper *= 2.0
        expansions += 1
        if not math.isfinite(upper) or expansions >= expansion_limit:
            raise ConvergenceError(
                "Unable to bracket open-channel normal depth.",
                bracket=(0.0, upper),
                iterations=expansions,
            )

    root_result: RootResult = solve_brent(
        function=residual,
        lower=0.0,
        upper=upper,
        tolerances=tolerances,
    )
    depth: float = root_result.root
    area: float = section.area(depth)
    perimeter: float = section.wetted_perimeter(depth)
    radius: float = area / perimeter
    width: float = section.top_width(depth)
    section_factor: float = area * radius ** (2.0 / 3.0)
    return ChannelNormalDepthResult(
        depth=depth,
        area=area,
        wetted_perimeter=perimeter,
        top_width=width,
        hydraulic_radius=radius,
        velocity=cross_section_velocity(q, area),
        froude_number=froude_number(discharge=q, area=area, top_width=width, g=accel),
        section_factor=section_factor,
        conveyance=section_factor / n,
        convergence=root_result,
    )
