"""Typed longitudinal HGL/EGL profiles for free-surface and pressurised reaches."""

from dataclasses import dataclass
from enum import StrEnum

from ..models.barrel import CulvertBarrel
from .direct_step import InletControlProfile, ProfilePoint, WaterSurfaceProfile


class HydraulicProfileState(StrEnum):
    """Hydraulic meaning of a longitudinal profile point."""

    FREE_SURFACE = "free_surface"
    PRESSURISED = "pressurised"


@dataclass(frozen=True, slots=True)
class HydraulicProfilePoint:
    """Station-based hydraulic state for downstream plotting and reporting.

    ``water_surface_elevation`` is populated only for free-surface flow. For a
    pressurised point the piezometric level is represented solely by
    ``hydraulic_grade_elevation`` so consumers do not confuse HGL with a physical
    free surface.
    """

    station: float
    invert_elevation: float
    crown_elevation: float
    state: HydraulicProfileState
    water_surface_elevation: float | None
    hydraulic_grade_elevation: float
    energy_grade_elevation: float
    velocity: float
    velocity_head: float
    friction_slope: float
    cumulative_friction_loss: float


@dataclass(frozen=True, slots=True)
class LongitudinalHydraulicProfile:
    """Ordered barrel profile combining free-surface and pressurised reaches.

    Station is measured from the culvert inlet (0 m) to outlet (barrel length).
    Boundary losses are retained separately from the station-wise barrel friction
    accumulation to avoid double counting entrance or exit losses.
    """

    points: tuple[HydraulicProfilePoint, ...]
    transition_stations: tuple[float, ...] = ()
    entrance_loss: float | None = None
    friction_loss: float | None = None
    exit_loss: float | None = None

    @property
    def is_mixed(self) -> bool:
        """Return whether both free-surface and pressurised states are present."""
        states = {point.state for point in self.points}
        return len(states) > 1


def _free_surface_points(
    points: tuple[ProfilePoint, ...],
    *,
    initial_friction_loss: float = 0.0,
) -> tuple[HydraulicProfilePoint, ...]:
    """Convert existing free-surface points without changing their semantics."""
    if not points:
        return ()

    cumulative = initial_friction_loss
    converted: list[HydraulicProfilePoint] = []
    previous: ProfilePoint | None = None
    for point in points:
        if previous is not None:
            dx = point.station - previous.station
            if dx > 0.0:
                cumulative += 0.5 * (previous.friction_slope + point.friction_slope) * dx
        converted.append(
            HydraulicProfilePoint(
                station=point.station,
                invert_elevation=point.invert_elevation,
                crown_elevation=point.crown_elevation,
                state=HydraulicProfileState.FREE_SURFACE,
                water_surface_elevation=point.water_surface_elevation,
                hydraulic_grade_elevation=point.water_surface_elevation,
                energy_grade_elevation=point.energy_grade_elevation,
                velocity=point.velocity,
                velocity_head=point.velocity_head,
                friction_slope=point.friction_slope,
                cumulative_friction_loss=cumulative,
            )
        )
        previous = point
    return tuple(converted)


def _pressurised_point(
    barrel: CulvertBarrel,
    *,
    station: float,
    hydraulic_grade_elevation: float,
    velocity: float,
    velocity_head: float,
    friction_slope: float,
    cumulative_friction_loss: float,
) -> HydraulicProfilePoint:
    invert = barrel.inlet_invert - barrel.slope * station
    return HydraulicProfilePoint(
        station=station,
        invert_elevation=invert,
        crown_elevation=invert + barrel.geometry.rise,
        state=HydraulicProfileState.PRESSURISED,
        water_surface_elevation=None,
        hydraulic_grade_elevation=hydraulic_grade_elevation,
        energy_grade_elevation=hydraulic_grade_elevation + velocity_head,
        velocity=velocity,
        velocity_head=velocity_head,
        friction_slope=friction_slope,
        cumulative_friction_loss=cumulative_friction_loss,
    )


def build_free_surface_longitudinal_profile(
    profile: WaterSurfaceProfile | InletControlProfile,
    *,
    entrance_loss: float | None = None,
) -> LongitudinalHydraulicProfile:
    """Expose an existing free-surface profile through the unified contract."""
    points = _free_surface_points(profile.points)
    friction_loss = points[-1].cumulative_friction_loss if points else 0.0
    return LongitudinalHydraulicProfile(
        points=points,
        entrance_loss=entrance_loss,
        friction_loss=friction_loss,
    )


def build_full_flow_longitudinal_profile(
    barrel: CulvertBarrel,
    *,
    headwater_elevation: float,
    entrance_loss: float,
    friction_loss: float,
    exit_loss: float,
    velocity: float,
    velocity_head: float,
) -> LongitudinalHydraulicProfile:
    """Build the internal barrel HGL/EGL from retained full-flow scalar evidence.

    The first station is immediately downstream of the entrance loss. The final
    station is immediately upstream of the exit loss. Consequently the EGL drop
    between profile endpoints is exactly the scalar full-barrel friction loss.
    """
    friction_slope = friction_loss / barrel.length
    inlet_egl = headwater_elevation - entrance_loss
    inlet_hgl = inlet_egl - velocity_head
    outlet_egl = inlet_egl - friction_loss
    outlet_hgl = outlet_egl - velocity_head
    points = (
        _pressurised_point(
            barrel,
            station=0.0,
            hydraulic_grade_elevation=inlet_hgl,
            velocity=velocity,
            velocity_head=velocity_head,
            friction_slope=friction_slope,
            cumulative_friction_loss=0.0,
        ),
        _pressurised_point(
            barrel,
            station=barrel.length,
            hydraulic_grade_elevation=outlet_hgl,
            velocity=velocity,
            velocity_head=velocity_head,
            friction_slope=friction_slope,
            cumulative_friction_loss=friction_loss,
        ),
    )
    return LongitudinalHydraulicProfile(
        points=points,
        entrance_loss=entrance_loss,
        friction_loss=friction_loss,
        exit_loss=exit_loss,
    )


def build_mixed_longitudinal_profile(
    barrel: CulvertBarrel,
    free_surface_profile: WaterSurfaceProfile | InletControlProfile,
    *,
    friction_loss: float,
    velocity: float,
    velocity_head: float,
    upstream_full_length: float = 0.0,
    downstream_full_length: float = 0.0,
    entrance_loss: float | None = None,
    exit_loss: float | None = None,
) -> LongitudinalHydraulicProfile:
    """Combine one existing free-surface path with a supported full-flow reach."""
    if upstream_full_length > 0.0 and downstream_full_length > 0.0:
        msg = "A mixed profile cannot have both upstream and downstream full reaches."
        raise ValueError(msg)
    if upstream_full_length <= 0.0 and downstream_full_length <= 0.0:
        return build_free_surface_longitudinal_profile(free_surface_profile, entrance_loss=entrance_loss)

    sf = friction_loss / barrel.length
    tolerance = max(1e-9, barrel.length * 1e-10)

    if upstream_full_length > 0.0:
        transition = upstream_full_length
        free_points = tuple(point for point in free_surface_profile.points if point.station >= transition - tolerance)
        if not free_points:
            msg_0 = "Free-surface profile does not contain the upstream full-flow transition."
            raise ValueError(msg_0)
        transition_hgl = free_points[0].water_surface_elevation
        inlet_hgl = transition_hgl + sf * transition
        pressurised = (
            _pressurised_point(
                barrel,
                station=0.0,
                hydraulic_grade_elevation=inlet_hgl,
                velocity=velocity,
                velocity_head=velocity_head,
                friction_slope=sf,
                cumulative_friction_loss=0.0,
            ),
            _pressurised_point(
                barrel,
                station=transition,
                hydraulic_grade_elevation=transition_hgl,
                velocity=velocity,
                velocity_head=velocity_head,
                friction_slope=sf,
                cumulative_friction_loss=sf * transition,
            ),
        )
        free = _free_surface_points(free_points, initial_friction_loss=sf * transition)
        points = (*pressurised, *free)
        profile_exit_loss = None
    else:
        transition = barrel.length - downstream_full_length
        free_points = tuple(point for point in free_surface_profile.points if point.station <= transition + tolerance)
        if not free_points:
            msg_1 = "Free-surface profile does not contain the downstream full-flow transition."
            raise ValueError(msg_1)
        free = _free_surface_points(free_points)
        initial_friction = free[-1].cumulative_friction_loss
        transition_invert = barrel.inlet_invert - barrel.slope * transition
        transition_hgl = transition_invert + barrel.geometry.rise
        pressurised = (
            _pressurised_point(
                barrel,
                station=transition,
                hydraulic_grade_elevation=transition_hgl,
                velocity=velocity,
                velocity_head=velocity_head,
                friction_slope=sf,
                cumulative_friction_loss=initial_friction,
            ),
            _pressurised_point(
                barrel,
                station=barrel.length,
                hydraulic_grade_elevation=transition_hgl - sf * downstream_full_length,
                velocity=velocity,
                velocity_head=velocity_head,
                friction_slope=sf,
                cumulative_friction_loss=initial_friction + sf * downstream_full_length,
            ),
        )
        points = (*free, *pressurised)
        profile_exit_loss = exit_loss

    return LongitudinalHydraulicProfile(
        points=points,
        transition_stations=(transition,),
        entrance_loss=entrance_loss,
        friction_loss=points[-1].cumulative_friction_loss,
        exit_loss=profile_exit_loss,
    )
