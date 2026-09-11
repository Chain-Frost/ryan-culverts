"""Full-flow outlet control hydraulic solver per FHWA HDS-5 Section 3.1.4."""

from dataclasses import dataclass

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..hydraulics.critical import calculate_critical_depth
from ..hydraulics.primitives import (
    cross_section_velocity,
    manning_friction_slope,
    velocity_head,
)
from ..models.barrel import CulvertBarrel
from ..models.tailwater import TailwaterCondition
from .losses import (
    EntranceLossCoefficient,
    ExitLossSelection,
    calculate_entrance_loss,
    calculate_exit_loss,
    calculate_friction_loss,
    calculate_total_head_loss,
    resolve_exit_loss_coefficient,
    validate_entrance_loss_shape,
)


@dataclass(frozen=True, slots=True)
class FullFlowOutletResult:
    """Hydraulic solution for a culvert barrel operating under full-flow outlet control.

    All elevations, depths, and head losses are in SI metres.
    """

    headwater_depth: float
    headwater_elevation: float
    tailwater_elevation: float
    tailwater_depth: float
    critical_depth: float
    barrel_rise: float
    effective_tailwater_depth: float
    hydraulic_grade_elevation_outlet: float
    entrance_loss: float
    friction_loss: float
    exit_loss: float
    exit_loss_selection: ExitLossSelection
    total_head_loss: float
    velocity: float
    velocity_head: float
    energy_grade_elevation_inlet: float


def calculate_downstream_full_flow_length(
    barrel: CulvertBarrel,
    discharge: float,
    tailwater: TailwaterCondition | float,
) -> float:
    """Return barrel length whose full-flow HGL is at or above the crown.

    The downstream HGL starts at tailwater and rises upstream by the full-section
    Manning friction slope. A linear intersection with the sloping crown identifies
    whether the entire barrel or only a downstream segment can remain pressurised.
    """
    q = finite(discharge, "discharge")
    if q <= 0.0:
        msg = "discharge must be strictly positive."
        raise InvalidInputError(msg)
    tw_elevation = tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")
    outlet_clearance = tw_elevation - (barrel.outlet_invert + barrel.geometry.rise)
    if outlet_clearance < 0.0:
        return 0.0
    sf = manning_friction_slope(
        q,
        barrel.geometry.area_full,
        barrel.geometry.hydraulic_radius_full,
        barrel.roughness,
    )
    inlet_clearance = tw_elevation + sf * barrel.length - (barrel.inlet_invert + barrel.geometry.rise)
    if inlet_clearance >= 0.0:
        return barrel.length
    transition_station = barrel.length * (-inlet_clearance) / (outlet_clearance - inlet_clearance)
    return barrel.length - transition_station


def calculate_full_flow_outlet_headwater(
    barrel: CulvertBarrel,
    discharge: float,
    tailwater: TailwaterCondition | float,
    entrance_loss_coefficient: float | EntranceLossCoefficient,
    exit_loss_coefficient: float | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> FullFlowOutletResult:
    """Calculate headwater elevation and losses for a culvert under full-flow outlet control.

    Uses FHWA HDS-5 Section 3.1.4 energy balance:
        H = he + hf + ho
        HW_elevation = HGL_outlet + H
        HW_depth = HW_elevation - inlet_invert

    where HGL_outlet is the hydraulic grade line elevation at the outlet invert:
        HGL_outlet = outlet_invert + h_o_eff
        h_o_eff = max(TW_depth, (dc + D) / 2)

    Parameters
    ----------
    barrel : CulvertBarrel
        Culvert barrel domain model with geometry, inverts, length, and roughness.
    discharge : float
        Volumetric flow rate Q through the barrel (m³/s), must be strictly positive.
    tailwater : TailwaterCondition | float
        Downstream boundary condition as a TailwaterCondition object or absolute elevation (m).
    entrance_loss_coefficient : float | EntranceLossCoefficient
        Entrance loss coefficient Ke.
    exit_loss_coefficient : float | None, optional
        Explicit exit loss coefficient Ko. If omitted, the sourced HDS-5 value of
        1.0 for discharge into a reservoir or pool is adopted.
    g : float, default=GRAVITATIONAL_ACCELERATION
        Gravitational acceleration (m/s²).

    Returns:
    -------
    FullFlowOutletResult
        Comprehensive hydraulic result including headwater depth, headwater elevation,
        effective tailwater depth, component head losses, and velocity.
    """
    q: float = finite(discharge, "discharge")
    if q <= 0:
        msg = "discharge must be strictly positive."
        raise InvalidInputError(msg)

    tw_elev: float
    tw_elev = tailwater.elevation if isinstance(tailwater, TailwaterCondition) else finite(tailwater, "tailwater")

    ke: float
    if isinstance(entrance_loss_coefficient, EntranceLossCoefficient):
        validate_entrance_loss_shape(barrel, entrance_loss_coefficient)
        ke = entrance_loss_coefficient.ke
    else:
        ke = finite(entrance_loss_coefficient, "entrance_loss_coefficient")
    if ke < 0:
        msg = "entrance_loss_coefficient must be nonnegative."
        raise InvalidInputError(msg)

    exit_selection = resolve_exit_loss_coefficient(exit_loss_coefficient)
    ko = exit_selection.ko

    # Tailwater depth relative to outlet invert
    tw_depth: float = max(0.0, tw_elev - barrel.outlet_invert)

    # Conduit full-flow hydraulic parameters
    full_area: float = barrel.geometry.area_full
    full_hydraulic_radius: float = barrel.geometry.hydraulic_radius_full
    d: float = barrel.geometry.rise

    v: float = cross_section_velocity(q, full_area)
    hv: float = velocity_head(v, g=g)
    sf: float = manning_friction_slope(q, full_area, full_hydraulic_radius, barrel.roughness)

    # Component head losses
    he: float = calculate_entrance_loss(hv, ke)
    hf: float = calculate_friction_loss(barrel.length, sf)
    ho: float = calculate_exit_loss(hv, ko)
    h_total: float = calculate_total_head_loss(he, hf, ho)

    # Critical depth for effective tailwater approximation
    crit_result = calculate_critical_depth(barrel.geometry, q, g=g)
    dc: float = crit_result.depth

    # Effective downstream tailwater depth per HDS-5 Section 3.1.4: max(TW, (dc + D) / 2)
    ho_eff: float = max(tw_depth, (dc + d) / 2.0)

    # Hydraulic and Energy Grade Lines
    hgl_outlet: float = barrel.outlet_invert + ho_eff
    hw_elev: float = hgl_outlet + h_total
    hw_depth: float = hw_elev - barrel.inlet_invert
    egl_inlet: float = hw_elev

    return FullFlowOutletResult(
        headwater_depth=hw_depth,
        headwater_elevation=hw_elev,
        tailwater_elevation=tw_elev,
        tailwater_depth=tw_depth,
        critical_depth=dc,
        barrel_rise=d,
        effective_tailwater_depth=ho_eff,
        hydraulic_grade_elevation_outlet=hgl_outlet,
        entrance_loss=he,
        friction_loss=hf,
        exit_loss=ho,
        exit_loss_selection=exit_selection,
        total_head_loss=h_total,
        velocity=v,
        velocity_head=hv,
        energy_grade_elevation_inlet=egl_inlet,
    )
