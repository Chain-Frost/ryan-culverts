"""Culvert group hydraulic solver for parallel identical barrels."""

from dataclasses import replace

from .._validation import finite
from ..constants import GRAVITATIONAL_ACCELERATION
from ..exceptions import InvalidInputError
from ..inlet_control.coefficients import InletCoefficients
from ..models.group import CulvertGroup
from ..models.results import BarrelHydraulicResult, GroupHydraulicResult
from ..models.tailwater import TailwaterInput, TailwaterResolution, resolve_tailwater
from ..outlet_control.losses import EntranceLossCoefficient
from ..references.models import SourceReference
from .barrel import solve_barrel_hydraulics
from .config import SolverConfiguration


def solve_group_hydraulics(
    group: CulvertGroup,
    total_discharge: float,
    tailwater: TailwaterInput,
    *,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> GroupHydraulicResult:
    """Solve hydraulics for a group of N identical parallel culvert barrels.

    Discharge is equally distributed across all N identical barrels:
        Q_barrel = Q_total / N

    For ``N > 1``, the result carries a structured representative-barrel applicability
    notice. The assumption supports total-flow calculation under sufficiently uniform
    approach conditions, but does not establish exact barrel-specific flow or velocity.

    Parameters
    ----------
    group : CulvertGroup
        Group domain model containing barrel definition and barrel quantity N >= 1.
    total_discharge : float
        Total volumetric discharge through the entire culvert group (m³/s), strictly positive.
    tailwater : TailwaterInput
        Absolute tailwater elevation (m) or a boundary resolved at total group discharge.
    inlet_coefficients : InletCoefficients | None, optional
        Inlet control regression constants.
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
    GroupHydraulicResult
        Hydraulic solution for the group and its representative single barrel.
    """
    if not isinstance(group, CulvertGroup):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "group must be an instance of CulvertGroup."
        raise InvalidInputError(msg)

    q_tot: float = finite(total_discharge, "total_discharge")
    if q_tot <= 0:
        msg = "total_discharge must be strictly positive."
        raise InvalidInputError(msg)

    tailwater_resolution: TailwaterResolution = resolve_tailwater(tailwater, q_tot, g=g)
    q_barrel: float = q_tot / float(group.quantity)

    barrel_res: BarrelHydraulicResult = solve_barrel_hydraulics(
        barrel=group.barrel,
        discharge=q_barrel,
        tailwater=tailwater_resolution.elevation,
        inlet_coefficients=inlet_coefficients,
        entrance_loss_coefficient=entrance_loss_coefficient,
        entrance_loss_source=entrance_loss_source,
        configuration=configuration,
        g=g,
    )
    barrel_res = replace(barrel_res, tailwater_resolution=tailwater_resolution)

    return GroupHydraulicResult(
        group=group,
        total_discharge=q_tot,
        barrel_discharge=q_barrel,
        barrel_result=barrel_res,
        tailwater_resolution=tailwater_resolution,
    )
