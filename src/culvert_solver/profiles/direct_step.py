"""Direct-step method for free-surface water profile computation in prismatic culverts."""

from dataclasses import dataclass
from itertools import pairwise

from .._validation import finite, positive_integer
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import ConvergenceError, InvalidInputError
from ..geometry.base import CrossSectionGeometry
from ..hydraulics.critical import CriticalDepthResult, calculate_critical_depth
from ..hydraulics.momentum import calculate_sequent_depth
from ..hydraulics.normal import NormalDepthResult, calculate_normal_depth
from ..hydraulics.primitives import (
    cross_section_velocity,
    froude_number,
    manning_friction_slope,
    minor_head_loss,
    specific_energy,
    velocity_head,
)
from ..models.barrel import CulvertBarrel
from ..models.enums import ConvergenceCalculation, ProfileCurve
from ..models.results import ConvergenceRecord
from ..models.tailwater import TailwaterCondition
from ..numerical.roots import RootResult, solve_bracketed
from ..numerical.tolerances import RootTolerances
from ..outlet_control.losses import (
    EntranceLossCoefficient,
)

_PROFILE_ROOT_TOLERANCES = RootTolerances(x_abs=1e-6, x_rel=1e-8)


@dataclass(frozen=True, slots=True)
class ProfilePoint:
    """Hydraulic state at a discrete longitudinal station along the culvert barrel.

    All lengths, depths, and elevations are in SI metres.
    Station is measured from the culvert inlet (station = 0.0) to the outlet (station = length).
    """

    station: float
    invert_elevation: float
    crown_elevation: float
    water_depth: float
    water_surface_elevation: float
    velocity: float
    velocity_head: float
    energy_grade_elevation: float
    friction_slope: float
    froude_number: float | None


@dataclass(frozen=True, slots=True)
class WaterSurfaceProfile:
    """Complete water surface profile computed along the culvert barrel."""

    curve_type: ProfileCurve
    points: tuple[ProfilePoint, ...]
    inlet_depth: float
    inlet_velocity: float
    inlet_headwater_depth: float
    inlet_headwater_elevation: float
    outlet_depth: float
    reaches_normal_depth: bool
    is_full_flow: bool
    profile_limit_station: float | None = None
    full_flow_length: float = 0.0
    convergence: tuple[ConvergenceRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class InletControlProfile:
    """Forward free-surface profile downstream from an inlet control section."""

    curve_type: ProfileCurve
    points: tuple[ProfilePoint, ...]
    inlet_depth: float
    outlet_depth: float
    reaches_normal_depth: bool
    outlet_sequent_depth: float | None = None
    hydraulic_jump_station: float | None = None
    hydraulic_jump_swept_out: bool = True
    convergence: tuple[ConvergenceRecord, ...] = ()


def _make_point(
    station: float,
    depth: float,
    barrel: CulvertBarrel,
    discharge: float,
    g: float,
) -> ProfilePoint:
    """Create a ProfilePoint at the specified station and depth."""
    geom: CrossSectionGeometry = barrel.geometry
    rise: float = geom.rise
    s0: float = barrel.slope
    z_inv: float = barrel.inlet_invert - s0 * station
    z_crown: float = z_inv + rise

    if depth >= rise:
        # Full / pressurized section
        a: float = geom.area_full
        r: float = geom.hydraulic_radius_full
        v: float = cross_section_velocity(discharge=discharge, area=a)
        hv: float = velocity_head(velocity=v, g=g)
        sf: float = manning_friction_slope(discharge=discharge, area=a, hydraulic_radius=r, roughness=barrel.roughness)
        return ProfilePoint(
            station=station,
            invert_elevation=z_inv,
            crown_elevation=z_crown,
            water_depth=depth,
            water_surface_elevation=z_inv + depth,
            velocity=v,
            velocity_head=hv,
            energy_grade_elevation=z_inv + depth + hv,
            friction_slope=sf,
            froude_number=None,
        )

    # Free surface section
    a = geom.area(depth)
    r = geom.hydraulic_radius(depth)
    t: float = geom.top_width(depth)
    v = cross_section_velocity(discharge=discharge, area=a)
    hv = velocity_head(velocity=v, g=g)
    e: float = specific_energy(depth=depth, velocity_head=hv)
    sf = manning_friction_slope(discharge=discharge, area=a, hydraulic_radius=r, roughness=barrel.roughness)
    fr: float | None
    fr = froude_number(discharge=discharge, area=a, top_width=t, g=g) if t > 0 and a > 0 else None

    return ProfilePoint(
        station=station,
        invert_elevation=z_inv,
        crown_elevation=z_crown,
        water_depth=depth,
        water_surface_elevation=z_inv + depth,
        velocity=v,
        velocity_head=hv,
        energy_grade_elevation=z_inv + e,
        friction_slope=sf,
        froude_number=fr,
    )


def _energy_and_friction_slope(
    geom: CrossSectionGeometry,
    q: float,
    roughness: float,
    y: float,
    g: float,
) -> tuple[float, float]:
    """Compute specific energy and Manning friction slope at specified depth."""
    a: float = geom.area(depth=y)
    r: float = geom.hydraulic_radius(depth=y)
    v: float = cross_section_velocity(discharge=q, area=a)
    hv: float = velocity_head(velocity=v, g=g)
    e: float = specific_energy(depth=y, velocity_head=hv)
    sf: float = manning_friction_slope(discharge=q, area=a, hydraulic_radius=r, roughness=roughness)
    return e, sf


def _inlet_station_residual(
    y: float,
    step_x: float,
    step_e: float,
    step_sf: float,
    s0: float,
    geom: CrossSectionGeometry,
    q: float,
    roughness: float,
    g: float,
) -> float:
    """Compute station offset residual from current step to inlet x = 0."""
    ey, sfy = _energy_and_friction_slope(geom, q, roughness, y, g)
    s_avg: float = 0.5 * (step_sf + sfy)
    den: float = s0 - s_avg
    if abs(den) < 1e-12:
        return step_x
    return step_x + (ey - step_e) / den


def compute_inlet_control_s2_profile(
    barrel: CulvertBarrel,
    discharge: float,
    num_steps: int = 25,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> InletControlProfile:
    """Route an S2 profile downstream from critical depth toward normal depth.

    This routine is limited to a positive, hydraulically steep, prismatic barrel
    where normal depth is below critical depth. It does not determine whether a
    downstream S1 profile or hydraulic jump intrudes into the barrel; the governing
    solver therefore uses it only for the unambiguous low-tailwater ``S2n`` case.
    The default depth discretisation is intended for rapid rating calculations;
    callers can increase ``num_steps`` for profile plotting or refinement checks.
    """
    q: float = finite(discharge, "discharge")
    if q <= 0:
        msg = "discharge must be strictly positive."
        raise InvalidInputError(msg)
    steps: int = positive_integer(num_steps, "num_steps")
    if steps < 5:
        msg = "num_steps must be at least 5."
        raise InvalidInputError(msg)
    if barrel.is_horizontal:
        msg = "an S2 profile requires a positive barrel slope."
        raise InvalidInputError(msg)

    geom: CrossSectionGeometry = barrel.geometry
    rise: float = geom.rise
    yc: float = calculate_critical_depth(geometry=geom, discharge=q, g=g).depth
    normal: NormalDepthResult = calculate_normal_depth(
        geometry=geom, discharge=q, slope=barrel.slope, roughness=barrel.roughness, g=g
    )
    if normal.capacity_exceeded or normal.depth >= yc:
        msg = "an S2 profile requires normal depth below critical depth."
        raise InvalidInputError(msg)
    yn: float = normal.depth

    # Starting infinitesimally below critical depth avoids the zero gradient at
    # the control section while preserving the critical-depth boundary physically.
    depth_epsilon: float = max(1e-8, rise * 1e-7)
    curr_y: float = max(yn + depth_epsilon, yc - depth_epsilon)
    target_y: float = yn + depth_epsilon
    curr_x = 0.0
    points: list[ProfilePoint] = [_make_point(station=curr_x, depth=curr_y, barrel=barrel, discharge=q, g=g)]
    dy: float = (target_y - curr_y) / float(steps)
    reaches_normal = False
    convergence: list[ConvergenceRecord] = []

    for _ in range(steps):
        next_y: float = curr_y + dy
        e_curr, sf_curr = _energy_and_friction_slope(geom=geom, q=q, roughness=barrel.roughness, y=curr_y, g=g)
        e_next, sf_next = _energy_and_friction_slope(geom=geom, q=q, roughness=barrel.roughness, y=next_y, g=g)
        denominator: float = barrel.slope - 0.5 * (sf_curr + sf_next)
        if denominator <= 0.0:
            reaches_normal = True
            break
        next_x: float = curr_x + (e_next - e_curr) / denominator
        if next_x >= barrel.length:
            step_x: float = curr_x
            step_energy: float = e_curr
            step_friction_slope: float = sf_curr

            def outlet_residual(
                y: float,
                x0: float = step_x,
                energy0: float = step_energy,
                friction0: float = step_friction_slope,
            ) -> float:
                energy, friction_slope = _energy_and_friction_slope(
                    geom=geom, q=q, roughness=barrel.roughness, y=y, g=g
                )
                average_slope: float = 0.5 * (friction0 + friction_slope)
                return x0 + (energy - energy0) / (barrel.slope - average_slope) - barrel.length

            try:
                outlet_root: RootResult = solve_bracketed(
                    function=outlet_residual,
                    lower=next_y,
                    upper=curr_y,
                    tolerances=_PROFILE_ROOT_TOLERANCES,
                )
                outlet_y: float = outlet_root.root
                convergence.append(
                    ConvergenceRecord(
                        calculation=ConvergenceCalculation.PROFILE_OUTLET_BOUNDARY,
                        result=outlet_root,
                    )
                )
            except ConvergenceError, InvalidInputError:
                fraction: float = (barrel.length - curr_x) / (next_x - curr_x)
                outlet_y = curr_y + fraction * (next_y - curr_y)
            points.append(_make_point(station=barrel.length, depth=outlet_y, barrel=barrel, discharge=q, g=g))
            curr_x: float = barrel.length
            curr_y = outlet_y
            break

        curr_x = next_x
        curr_y = next_y
        points.append(_make_point(station=curr_x, depth=curr_y, barrel=barrel, discharge=q, g=g))

    if curr_x < barrel.length:
        reaches_normal = True
        curr_y = yn
        points.append(_make_point(station=barrel.length, depth=curr_y, barrel=barrel, discharge=q, g=g))

    return InletControlProfile(
        curve_type=ProfileCurve.S2,
        points=tuple(points),
        inlet_depth=points[0].water_depth,
        outlet_depth=curr_y,
        reaches_normal_depth=reaches_normal,
        convergence=tuple(convergence),
    )


def _interpolate_profile_depth(points: tuple[ProfilePoint, ...], station: float) -> float:
    """Linearly interpolate water depth between ordered profile stations."""
    if station <= points[0].station:
        return points[0].water_depth
    if station >= points[-1].station:
        return points[-1].water_depth
    for first, second in pairwise(points):
        if first.station <= station <= second.station:
            fraction: float = (station - first.station) / (second.station - first.station)
            return first.water_depth + fraction * (second.water_depth - first.water_depth)
    msg = "Profile interpolation could not bracket the requested station."
    raise ConvergenceError(
        msg,
        bracket=(points[0].station, points[-1].station),
        iterations=len(points) - 1,
    )


def compute_steep_inlet_control_profile(
    barrel: CulvertBarrel,
    discharge: float,
    tailwater: TailwaterCondition | float,
    num_steps: int = 25,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> InletControlProfile:
    """Resolve S2, swept-out-jump, in-barrel JS1, or inlet-reaching S1 flow.

    The S2 profile is routed downstream and compared with the backward S1 profile
    using conjugate depths from equal momentum. A duplicated station at an
    identified jump records the pre- and post-jump depths explicitly.
    """
    q: float = finite(discharge, "discharge")
    if q <= 0.0:
        msg = "discharge must be strictly positive."
        raise InvalidInputError(msg)
    steps: int = positive_integer(num_steps, "num_steps")
    if steps < 5:
        msg = "num_steps must be at least 5."
        raise InvalidInputError(msg)
    tw_elevation: float = (
        tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")
    )
    tw_depth: float = max(0.0, tw_elevation - barrel.outlet_invert)
    if tw_depth >= barrel.geometry.rise:
        msg = "steep inlet-control profile requires sub-crown tailwater."
        raise InvalidInputError(msg)

    s2: InletControlProfile = compute_inlet_control_s2_profile(barrel=barrel, discharge=q, num_steps=steps, g=g)
    normal: float = calculate_normal_depth(
        geometry=barrel.geometry,
        discharge=q,
        slope=barrel.slope,
        roughness=barrel.roughness,
        g=g,
    ).depth
    if tw_depth <= normal:
        return s2

    outlet_sequent: float | None = calculate_sequent_depth(
        geometry=barrel.geometry,
        discharge=q,
        supercritical_depth=s2.outlet_depth,
        g=g,
    )
    if outlet_sequent is None or tw_depth <= outlet_sequent:
        return InletControlProfile(
            curve_type=ProfileCurve.S2,
            points=s2.points,
            inlet_depth=s2.inlet_depth,
            outlet_depth=s2.outlet_depth,
            reaches_normal_depth=s2.reaches_normal_depth,
            outlet_sequent_depth=outlet_sequent,
            convergence=s2.convergence,
        )

    s1: WaterSurfaceProfile = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elevation,
        entrance_loss_coefficient=0.0,
        num_steps=steps,
        g=g,
    )
    if s1.curve_type is not ProfileCurve.S1:
        msg = "Expected an S1 profile for the steep tailwater boundary."
        raise ConvergenceError(
            msg,
            bracket=(0.0, barrel.length),
            iterations=steps,
        )
    if s1.profile_limit_station is None:
        return InletControlProfile(
            curve_type=ProfileCurve.S1,
            points=s1.points,
            inlet_depth=s1.inlet_depth,
            outlet_depth=s1.outlet_depth,
            reaches_normal_depth=False,
            outlet_sequent_depth=outlet_sequent,
            hydraulic_jump_swept_out=False,
            convergence=(*s2.convergence, *s1.convergence),
        )

    limit_station: float = s1.profile_limit_station
    physical_s1_points: tuple[ProfilePoint, ...] = tuple(
        point for point in s1.points if point.station >= limit_station - 1e-9
    )

    def jump_residual(station: float) -> float:
        s2_depth: float = _interpolate_profile_depth(s2.points, station)
        conjugate_depth: float | None = calculate_sequent_depth(
            geometry=barrel.geometry, discharge=q, supercritical_depth=s2_depth, g=g
        )
        if conjugate_depth is None:
            conjugate_depth = barrel.geometry.rise
        return _interpolate_profile_depth(physical_s1_points, station) - conjugate_depth

    lower_residual: float = jump_residual(limit_station)
    upper_residual: float = jump_residual(barrel.length)
    if lower_residual > 0.0 or upper_residual < 0.0:
        msg = "S1 and S2 conjugate-depth profiles did not bracket a jump."
        raise ConvergenceError(
            msg,
            bracket=(limit_station, barrel.length),
            iterations=steps,
        )
    jump_root: RootResult = solve_bracketed(
        function=jump_residual,
        lower=limit_station,
        upper=barrel.length,
        tolerances=_PROFILE_ROOT_TOLERANCES,
    )
    jump_station: float = jump_root.root
    pre_jump_depth: float = _interpolate_profile_depth(s2.points, jump_station)
    post_jump_depth: float = _interpolate_profile_depth(physical_s1_points, jump_station)
    combined_points: tuple[ProfilePoint, ...] = (
        *(point for point in s2.points if point.station < jump_station),
        _make_point(jump_station, pre_jump_depth, barrel, q, g),
        _make_point(jump_station, post_jump_depth, barrel, q, g),
        *(point for point in physical_s1_points if point.station > jump_station),
    )
    return InletControlProfile(
        curve_type=ProfileCurve.JS1,
        points=combined_points,
        inlet_depth=s2.inlet_depth,
        outlet_depth=s1.outlet_depth,
        reaches_normal_depth=s2.reaches_normal_depth,
        outlet_sequent_depth=outlet_sequent,
        hydraulic_jump_station=jump_station,
        hydraulic_jump_swept_out=False,
        convergence=(
            *s2.convergence,
            *s1.convergence,
            ConvergenceRecord(
                calculation=ConvergenceCalculation.HYDRAULIC_JUMP,
                result=jump_root,
            ),
        ),
    )


def compute_backwater_profile(
    barrel: CulvertBarrel,
    discharge: float,
    tailwater: TailwaterCondition | float,
    entrance_loss_coefficient: float | EntranceLossCoefficient,
    num_steps: int = 50,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> WaterSurfaceProfile:
    """Compute backwater free-surface profile along a culvert barrel via the direct-step method.

    Integrates from downstream outlet (station = length) upstream towards the inlet (station = 0)
    for subcritical or drawdown profiles (M1, M2, H2, S1).

    Parameters
    ----------
    barrel : CulvertBarrel
        Culvert barrel domain model.
    discharge : float
        Volumetric flow rate Q (m³/s), strictly positive.
    tailwater : TailwaterCondition | float
        Downstream tailwater condition or elevation (m).
    entrance_loss_coefficient : float | EntranceLossCoefficient
        Inlet entrance loss coefficient Ke.
    num_steps : int, default=50
        Number of direct-step depth increments.
    g : float, default=GRAVITATIONAL_ACCELERATION
        Gravitational acceleration (m/s²).

    Returns:
    -------
    WaterSurfaceProfile
        Computed profile points ordered from inlet (station 0.0) to outlet (station L),
        governing curve type, and upstream headwater elevation.

    Notes:
    -----
    This routine supports free-surface backwater curves and an upstream full-flow
    continuation when an M2 profile reaches the crown. A submerged outlet alone does
    not prove that the whole barrel is full; use the regime solver for that state.
    """
    q: float = finite(discharge, "discharge")
    if q <= 0:
        msg = "discharge must be strictly positive."
        raise InvalidInputError(msg)

    steps: int = positive_integer(num_steps, "num_steps")
    if steps < 5:
        msg = "num_steps must be at least 5."
        raise InvalidInputError(msg)

    tw_elev: float
    tw_elev = tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")

    ke: float
    if isinstance(entrance_loss_coefficient, EntranceLossCoefficient):
        ke = entrance_loss_coefficient.ke
    else:
        ke = finite(entrance_loss_coefficient, "entrance_loss_coefficient")
    if ke < 0:
        msg = "entrance_loss_coefficient must be nonnegative."
        raise InvalidInputError(msg)

    convergence: list[ConvergenceRecord] = []

    geom: CrossSectionGeometry = barrel.geometry
    rise: float = geom.rise
    s0: float = barrel.slope
    length: float = barrel.length

    # Critical depth
    crit_res: CriticalDepthResult = calculate_critical_depth(geometry=geom, discharge=q, g=g)
    yc: float = crit_res.depth

    # Downstream boundary depth at outlet invert
    tw_depth: float = max(0.0, tw_elev - barrel.outlet_invert)

    # A submerged outlet does not by itself establish full flow along the barrel.
    if tw_depth >= rise:
        msg = (
            "compute_backwater_profile does not infer full-barrel flow from a "
            "submerged outlet; use determine_governing_regime for pressurised or "
            "mixed-flow classification."
        )
        raise InvalidInputError(msg)

    # Free surface starting depth at outlet
    y_start: float = max(tw_depth, yc)

    # Normal depth and curve classification
    curve_type: ProfileCurve
    yn: float | None = None
    y_target: float
    normal_capacity_exceeded = False

    if barrel.is_horizontal:
        curve_type = ProfileCurve.H2
        # On horizontal slope, target depth is crown (approaching full flow)
        y_target = min(rise - 1e-4, y_start + 0.3 * rise)
    else:
        norm_res: NormalDepthResult = calculate_normal_depth(
            geometry=geom, discharge=q, slope=s0, roughness=barrel.roughness, g=g
        )
        if norm_res.capacity_exceeded:
            yn = rise
            normal_capacity_exceeded = True
        else:
            yn = norm_res.depth

        if yn > yc:
            # Mild slope
            if y_start > yn:
                curve_type = ProfileCurve.M1
                # Target depth decreases towards normal depth
                y_target = yn + 1e-4
            else:
                curve_type = ProfileCurve.M2
                # A capacity-exceeded M2 curve reaches the crown at a finite station.
                y_target = rise if normal_capacity_exceeded else yn - 1e-4
        else:
            # Steep slope
            if y_start > yc:
                curve_type = ProfileCurve.S1
                y_target = yc + 1e-4
            else:
                curve_type = ProfileCurve.S2
                y_target = yn + 1e-4

    # Integrate upstream from outlet (x = length, y = y_start)
    raw_points: list[ProfilePoint] = []
    curr_x: float = length
    curr_y: float = y_start

    raw_points.append(_make_point(curr_x, curr_y, barrel, q, g))

    reaches_normal: bool = False
    profile_limit_station: float | None = None
    dy: float = (y_target - y_start) / float(steps)

    if abs(dy) < 1e-6:
        # Flow is already virtually at normal depth
        reaches_normal = True
        p_inlet: ProfilePoint = _make_point(0.0, curr_y, barrel, q, g)
        raw_points.append(p_inlet)
    else:
        for step_index in range(steps):
            # Avoid accumulated floating-point error skipping an exact crown target.
            next_y: float = y_target if step_index == steps - 1 else curr_y + dy
            if next_y <= 0 or next_y > rise:
                break

            e_curr, sf_curr = _energy_and_friction_slope(geom, q, barrel.roughness, curr_y, g)
            e_next, sf_next = _energy_and_friction_slope(geom, q, barrel.roughness, next_y, g)

            sf_avg: float = 0.5 * (sf_curr + sf_next)
            denom: float = s0 - sf_avg

            if abs(denom) < 1e-9:
                # Reached normal depth (Sf == S0)
                reaches_normal = True
                break

            dx: float = (e_next - e_curr) / denom
            next_x: float = curr_x + dx

            if next_x <= 0.0:
                # The profile crossed the inlet (x = 0) during this step
                # Solve exact depth at x = 0 between curr_y and next_y
                y_bracket_lo: float = min(curr_y, next_y)
                y_bracket_hi: float = max(curr_y, next_y)

                cur_x_val: float = curr_x
                e_cur_val: float = e_curr
                sf_cur_val: float = sf_curr

                def res_func(
                    y_val: float,
                    cx: float = cur_x_val,
                    ec: float = e_cur_val,
                    sfc: float = sf_cur_val,
                ) -> float:
                    return _inlet_station_residual(y_val, cx, ec, sfc, s0, geom, q, barrel.roughness, g)

                try:
                    root_res: RootResult = solve_bracketed(
                        function=res_func,
                        lower=y_bracket_lo,
                        upper=y_bracket_hi,
                        tolerances=_PROFILE_ROOT_TOLERANCES,
                    )
                    y_inlet: float = root_res.root
                    convergence.append(
                        ConvergenceRecord(
                            calculation=ConvergenceCalculation.PROFILE_INLET_BOUNDARY,
                            result=root_res,
                        )
                    )
                except ConvergenceError, InvalidInputError:
                    # Linear fallback interpolation if boundary stagnation occurs
                    frac: float = (0.0 - curr_x) / (next_x - curr_x)
                    y_inlet = curr_y + frac * (next_y - curr_y)

                raw_points.append(_make_point(0.0, y_inlet, barrel, q, g))
                curr_x = 0.0
                curr_y = y_inlet
                break

            curr_x = next_x
            curr_y = next_y
            raw_points.append(_make_point(curr_x, curr_y, barrel, q, g))

        if curr_x > 0.0:
            reached_crown = curve_type is ProfileCurve.M2 and normal_capacity_exceeded and curr_y >= rise - 1e-12
            # Otherwise, the profile reached its normal-depth asymptote before the inlet.
            reaches_normal = not reached_crown
            profile_limit_station = curr_x
            raw_points.append(_make_point(0.0, curr_y, barrel, q, g))

    # Order points strictly from inlet (station = 0.0) to outlet (station = length)
    sorted_points: tuple[ProfilePoint, ...] = tuple(sorted(raw_points, key=lambda p: p.station))

    full_flow_length = 0.0
    if curve_type is ProfileCurve.M2 and normal_capacity_exceeded and profile_limit_station is not None:
        full_flow_length: float = profile_limit_station
        sorted_points = (
            _make_point(0.0, rise, barrel, q, g),
            *(point for point in sorted_points if point.station > 0.0),
        )

    inlet_pt: ProfilePoint = sorted_points[0]
    outlet_pt: ProfilePoint = sorted_points[-1]

    # Inlet headwater accounting: HW = y_in + (1 + Ke) * hv_in
    vin: float = inlet_pt.velocity
    hv_in: float = inlet_pt.velocity_head
    he_in: float = minor_head_loss(ke, hv_in)
    if full_flow_length > 0.0:
        transition_invert: float = barrel.inlet_invert - s0 * full_flow_length
        transition_energy: float = transition_invert + rise + hv_in
        full_friction_slope: float = manning_friction_slope(
            discharge=q,
            area=geom.area_full,
            hydraulic_radius=geom.hydraulic_radius_full,
            roughness=barrel.roughness,
        )
        hw_elev = transition_energy + full_friction_slope * full_flow_length + he_in
        hw_depth: float = hw_elev - barrel.inlet_invert
    else:
        hw_depth = inlet_pt.water_depth + hv_in + he_in
        hw_elev = barrel.inlet_invert + hw_depth

    return WaterSurfaceProfile(
        curve_type=curve_type,
        points=sorted_points,
        inlet_depth=inlet_pt.water_depth,
        inlet_velocity=vin,
        inlet_headwater_depth=hw_depth,
        inlet_headwater_elevation=hw_elev,
        outlet_depth=outlet_pt.water_depth,
        reaches_normal_depth=reaches_normal,
        is_full_flow=False,
        profile_limit_station=profile_limit_station,
        full_flow_length=full_flow_length,
        convergence=tuple(convergence),
    )
