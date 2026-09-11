"""Partial-flow outlet control hydraulic solver using backwater profiles."""

from dataclasses import dataclass

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..hydraulics.critical import calculate_critical_depth
from ..hydraulics.normal import calculate_normal_depth
from ..hydraulics.primitives import minor_head_loss, velocity_head
from ..models.barrel import CulvertBarrel
from ..models.tailwater import TailwaterCondition
from ..profiles.direct_step import WaterSurfaceProfile, compute_backwater_profile
from .losses import EntranceLossCoefficient, validate_entrance_loss_shape


@dataclass(frozen=True, slots=True)
class PartialFlowOutletResult:
    """Hydraulic outcome for a culvert barrel operating under partial-flow outlet control."""

    headwater_depth: float
    headwater_elevation: float
    tailwater_elevation: float
    tailwater_depth: float
    critical_depth: float
    normal_depth: float | None
    barrel_rise: float
    inlet_depth: float
    outlet_depth: float
    entrance_loss: float
    profile: WaterSurfaceProfile
    full_flow_length: float = 0.0


def calculate_partial_flow_outlet_headwater(
    barrel: CulvertBarrel,
    discharge: float,
    tailwater: TailwaterCondition | float,
    entrance_loss_coefficient: float | EntranceLossCoefficient,
    num_steps: int = 50,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> PartialFlowOutletResult:
    """Calculate headwater elevation for partially full culvert outlet control via backwater.

    Parameters
    ----------
    barrel : CulvertBarrel
        Culvert barrel domain model.
    discharge : float
        Discharge Q (m³/s), strictly positive.
    tailwater : TailwaterCondition | float
        Tailwater condition or elevation (m).
    entrance_loss_coefficient : float | EntranceLossCoefficient
        Entrance loss coefficient Ke.
    num_steps : int, default=50
        Number of steps for the direct-step integration.
    g : float, default=GRAVITATIONAL_ACCELERATION
        Gravitational acceleration (m/s²).

    Returns:
    -------
    PartialFlowOutletResult
        Comprehensive partial-flow outlet control result including full profile points.
    """
    q: float = finite(discharge, "discharge")
    if q <= 0:
        msg = "discharge must be strictly positive."
        raise InvalidInputError(msg)

    tw_elev: float
    tw_elev = tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")

    tw_depth: float = max(0.0, tw_elev - barrel.outlet_invert)

    ke: float
    if isinstance(entrance_loss_coefficient, EntranceLossCoefficient):
        validate_entrance_loss_shape(barrel, entrance_loss_coefficient)
        ke = entrance_loss_coefficient.ke
    else:
        ke = finite(entrance_loss_coefficient, "entrance_loss_coefficient")

    profile: WaterSurfaceProfile = compute_backwater_profile(
        barrel=barrel,
        discharge=q,
        tailwater=tw_elev,
        entrance_loss_coefficient=ke,
        num_steps=num_steps,
        g=g,
    )

    crit_res = calculate_critical_depth(barrel.geometry, q, g=g)
    dc: float = crit_res.depth

    yn: float | None = None
    if not barrel.is_horizontal:
        norm_res = calculate_normal_depth(barrel.geometry, q, barrel.slope, barrel.roughness, g=g)
        if not norm_res.capacity_exceeded:
            yn = norm_res.depth

    hv_in = velocity_head(profile.inlet_velocity, g=g)
    he = minor_head_loss(ke, hv_in)

    return PartialFlowOutletResult(
        headwater_depth=profile.inlet_headwater_depth,
        headwater_elevation=profile.inlet_headwater_elevation,
        tailwater_elevation=tw_elev,
        tailwater_depth=tw_depth,
        critical_depth=dc,
        normal_depth=yn,
        barrel_rise=barrel.geometry.rise,
        inlet_depth=profile.inlet_depth,
        outlet_depth=profile.outlet_depth,
        entrance_loss=he,
        profile=profile,
        full_flow_length=profile.full_flow_length,
    )
