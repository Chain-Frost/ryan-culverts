"""Single-barrel culvert hydraulic solver."""

from dataclasses import replace

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..inlet_control.coefficients import InletCoefficients
from ..models.barrel import CulvertBarrel
from ..models.results import BarrelHydraulicResult
from ..models.tailwater import TailwaterInput, TailwaterResolution, resolve_tailwater
from ..outlet_control.full_flow import calculate_full_flow_outlet_headwater
from ..outlet_control.losses import EntranceLossCoefficient
from ..profiles.direct_step import WaterSurfaceProfile
from ..profiles.longitudinal import (
    LongitudinalHydraulicProfile,
    build_free_surface_longitudinal_profile,
    build_full_flow_longitudinal_profile,
    build_mixed_longitudinal_profile,
)
from ..references.models import SourceReference
from .config import SolverConfiguration
from .regime import determine_governing_regime


def _build_longitudinal_profile(
    result: BarrelHydraulicResult,
    *,
    g: float,
) -> LongitudinalHydraulicProfile | None:
    """Build a plotting-ready profile from authoritative scalar/profile results."""
    entrance_selection = result.entrance_loss_selection
    if entrance_selection is None:
        return None

    full_flow = calculate_full_flow_outlet_headwater(
        barrel=result.barrel,
        discharge=result.discharge,
        tailwater=result.tailwater_elevation,
        entrance_loss_coefficient=entrance_selection.ke,
        g=g,
    )
    profile = result.profile
    length_tolerance = max(1e-9, result.barrel.length * 1e-10)

    if profile is None:
        if result.full_flow_length >= result.barrel.length - length_tolerance:
            return build_full_flow_longitudinal_profile(result.barrel, full_flow)
        return None

    if isinstance(profile, WaterSurfaceProfile) and profile.full_flow_length > length_tolerance:
        return build_mixed_longitudinal_profile(
            result.barrel,
            profile,
            full_flow,
            upstream_full_length=profile.full_flow_length,
            entrance_loss=(None if result.outlet_control_losses is None else result.outlet_control_losses.entrance),
        )

    if result.full_flow_length > length_tolerance:
        return build_mixed_longitudinal_profile(
            result.barrel,
            profile,
            full_flow,
            downstream_full_length=result.full_flow_length,
            entrance_loss=(None if result.outlet_control_losses is None else result.outlet_control_losses.entrance),
        )

    return build_free_surface_longitudinal_profile(
        profile,
        entrance_loss=None if result.outlet_control_losses is None else result.outlet_control_losses.entrance,
    )


def solve_barrel_hydraulics(
    barrel: CulvertBarrel,
    discharge: float,
    tailwater: TailwaterInput,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> BarrelHydraulicResult:
    """Solve the currently supported provisional single-barrel regimes.

    Parameters
    ----------
    barrel : CulvertBarrel
        Culvert barrel domain model.
    discharge : float
        Discharge Q (m³/s), strictly positive.
    tailwater : TailwaterInput
        Absolute tailwater elevation (m) or a boundary resolved at this barrel discharge.
    inlet_coefficients : InletCoefficients | None, optional
        Empirical inlet control coefficients.
    entrance_loss_coefficient : float | EntranceLossCoefficient | None, optional
        Entrance loss coefficient Ke for outlet control.
    entrance_loss_source : SourceReference | None, optional
        Provenance for a numeric entrance-loss override.
    configuration : SolverConfiguration | None, optional
        Injectable project defaults used only when explicit and barrel values are absent.
    g : float, default=GRAVITATIONAL_ACCELERATION
        Gravitational acceleration (m/s²).

    Returns:
    -------
    BarrelHydraulicResult
        Hydraulic result including the selected regime, headwater, outlet velocity,
        and a typed longitudinal HGL/EGL profile where the hydraulic path is resolved.

    Notes:
    -----
    Supported outlet-control profile paths include S1/S2 profiles, hydraulic jumps, and
    selected mixed free-surface/full-flow states. Unsupported or unresolved transitions
    remain explicit in the result warnings.
    """
    q: float = finite(discharge, "discharge")
    if q <= 0.0:
        msg = "discharge must be strictly positive."
        raise InvalidInputError(msg)
    tailwater_resolution: TailwaterResolution = resolve_tailwater(tailwater=tailwater, discharge=q, g=g)
    result: BarrelHydraulicResult = determine_governing_regime(
        barrel=barrel,
        discharge=q,
        tailwater=tailwater_resolution.elevation,
        inlet_coefficients=inlet_coefficients,
        entrance_loss_coefficient=entrance_loss_coefficient,
        entrance_loss_source=entrance_loss_source,
        configuration=configuration,
        g=g,
    )
    longitudinal_profile = _build_longitudinal_profile(result, g=g)
    return replace(
        result,
        longitudinal_profile=longitudinal_profile,
        tailwater_resolution=tailwater_resolution,
    )
