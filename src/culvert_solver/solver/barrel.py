"""Single-barrel culvert hydraulic solver."""

from dataclasses import replace

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..inlet_control.coefficients import InletCoefficients
from ..models.barrel import CulvertBarrel
from ..models.results import BarrelHydraulicResult
from ..models.tailwater import TailwaterInput, TailwaterResolution, resolve_tailwater
from ..outlet_control.losses import EntranceLossCoefficient
from ..references.models import SourceReference
from .config import SolverConfiguration
from .regime import determine_governing_regime


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
    tailwater : TailwaterCondition | float
        Tailwater boundary condition or elevation (m).
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

    Returns
    -------
    BarrelHydraulicResult
        Hydraulic result including the selected regime, headwater, and outlet velocity.

    Notes
    -----
    Hydraulic jumps and mixed free-surface/pressurised profiles are not yet supported.
    """
    q: float = finite(discharge, "discharge")
    if q <= 0.0:
        raise InvalidInputError("discharge must be strictly positive.")
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
    return replace(result, tailwater_resolution=tailwater_resolution)
