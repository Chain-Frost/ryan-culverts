"""Culvert barrel domain model."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .._validation import finite
from ..exceptions import InvalidInputError
from ..geometry.base import CrossSectionGeometry
from .enums import RoughnessSelectionBasis
from .materials import (
    CulvertMaterial,
    ManningRoughnessSelection,
    RoughnessApplicabilityNotice,
)

if TYPE_CHECKING:
    from ..inlet_control.coefficients import InletCoefficients
    from ..outlet_control.losses import EntranceLossCoefficient
    from ..references.models import SourceReference


@dataclass(frozen=True, slots=True)
class CulvertBarrel:
    """A physical culvert barrel defined by authoritative inverts and longitudinal length.

    All lengths, inverts, and computed elevations are in SI metres.
    Slope is derived from the drop (inlet_invert - outlet_invert) and barrel length.
    Adverse slopes (outlet_invert > inlet_invert) raise InvalidInputError.
    """

    geometry: CrossSectionGeometry
    length: float
    inlet_invert: float
    outlet_invert: float
    roughness: float
    material: CulvertMaterial | None = None
    inlet_coefficients: InletCoefficients | None = None
    entrance_loss_coefficient: EntranceLossCoefficient | float | None = None
    label: str = ""
    roughness_selection_basis: RoughnessSelectionBasis = RoughnessSelectionBasis.USER_OVERRIDE
    roughness_source: SourceReference | None = None
    parameter_set_id: str | None = None
    roughness_selection: ManningRoughnessSelection | None = None
    roughness_notices: tuple[RoughnessApplicabilityNotice, ...] = field(default=(), init=False)

    def __post_init__(self) -> None:
        l_val: float = finite(self.length, "length")
        if l_val <= 0:
            msg = "length must be strictly positive."
            raise InvalidInputError(msg)
        z_in: float = finite(self.inlet_invert, "inlet_invert")
        z_out: float = finite(self.outlet_invert, "outlet_invert")
        if z_out > z_in:
            msg = "Adverse slope is outside the initial solver release: inlet_invert must be >= outlet_invert."
            raise InvalidInputError(msg)
        roughness_selection = self.roughness_selection
        n_val: float = finite(self.roughness, "roughness")
        if n_val <= 0:
            msg = "roughness must be strictly positive."
            raise InvalidInputError(msg)
        object.__setattr__(self, "length", l_val)
        object.__setattr__(self, "inlet_invert", z_in)
        object.__setattr__(self, "outlet_invert", z_out)
        object.__setattr__(self, "roughness", n_val)
        if roughness_selection is not None:
            if n_val != roughness_selection.value:
                msg = "roughness must equal the supplied roughness_selection value."
                raise InvalidInputError(msg)
            if (
                self.roughness_selection_basis is not RoughnessSelectionBasis.USER_OVERRIDE
                and self.roughness_selection_basis is not roughness_selection.basis
            ):
                msg = "roughness_selection_basis conflicts with the supplied roughness selection."
                raise InvalidInputError(msg)
            if self.roughness_source is not None and self.roughness_source != roughness_selection.source:
                msg = "roughness_source conflicts with the supplied roughness selection."
                raise InvalidInputError(msg)
            object.__setattr__(self, "roughness_selection_basis", roughness_selection.basis)
            object.__setattr__(self, "roughness_source", roughness_selection.source)
            object.__setattr__(self, "roughness_notices", roughness_selection.notices)
        try:
            roughness_basis = RoughnessSelectionBasis(self.roughness_selection_basis)
        except (TypeError, ValueError) as exc:
            msg = "roughness_selection_basis must be a RoughnessSelectionBasis value."
            raise InvalidInputError(msg) from exc
        object.__setattr__(self, "roughness_selection_basis", roughness_basis)
        if self.parameter_set_id is not None and not self.parameter_set_id.strip():
            msg = "parameter_set_id must be nonempty text when provided."
            raise InvalidInputError(msg)
        if self.roughness_source is not None:
            from ..references.models import SourceReference

            if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                self.roughness_source, SourceReference
            ):
                msg = "roughness_source must be a SourceReference or None."
                raise InvalidInputError(msg)
        if isinstance(self.entrance_loss_coefficient, (float, int)):
            ke_val = finite(self.entrance_loss_coefficient, "entrance_loss_coefficient")
            if ke_val < 0:
                msg = "entrance_loss_coefficient must be nonnegative."
                raise InvalidInputError(msg)
            object.__setattr__(self, "entrance_loss_coefficient", ke_val)
        elif self.entrance_loss_coefficient is not None:
            from ..outlet_control.losses import EntranceLossCoefficient

            if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                self.entrance_loss_coefficient, EntranceLossCoefficient
            ):
                msg = "entrance_loss_coefficient must be a finite number or EntranceLossCoefficient."
                raise InvalidInputError(msg)

    @property
    def drop(self) -> float:
        """Total vertical fall along the barrel in metres (inlet_invert - outlet_invert)."""
        return self.inlet_invert - self.outlet_invert

    @property
    def slope(self) -> float:
        """Longitudinal barrel bed slope S0 = drop / length (dimensionless)."""
        return self.drop / self.length

    @property
    def is_horizontal(self) -> bool:
        """Return True if the barrel has zero slope (inlet_invert == outlet_invert)."""
        return self.drop == 0.0

    @property
    def inlet_crown(self) -> float:
        """Absolute elevation of the barrel crown at the inlet in metres."""
        return self.inlet_invert + self.geometry.rise

    @property
    def outlet_crown(self) -> float:
        """Absolute elevation of the barrel crown at the outlet in metres."""
        return self.outlet_invert + self.geometry.rise
