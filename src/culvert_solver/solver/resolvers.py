"""Provenance-bearing resolvers for inlet and entrance-loss coefficients.

Each resolver follows the same design as ``resolve_manning_roughness`` in
``models.materials``: the resolved value is wrapped in a frozen result that
records *how* it was selected (user override, barrel-attached, or library
default), which source reference applies, and the concrete value.

The precedence is:

1. An explicit user value passed to the resolver.
2. A value already attached to the ``CulvertBarrel``.
3. A library default inferred from barrel geometry and material.
4. An explicit error when no applicable default exists.
"""

from dataclasses import dataclass

from .._validation import finite
from ..exceptions import InvalidInputError
from ..geometry.circular import CircularGeometry
from ..geometry.filleted_rectangular import FilletedRectangularGeometry
from ..geometry.rectangular import RectangularGeometry
from ..inlet_control.coefficients import InletCoefficients
from ..models.barrel import CulvertBarrel
from ..models.enums import EntranceLossSelectionBasis, GeometryShape, InletSelectionBasis
from ..models.materials import (
    CONCRETE,
    CONCRETE_BOX,
    CONCRETE_PIPE,
    CORRUGATED_STEEL,
)
from ..outlet_control.losses import (
    EntranceLossCoefficient,
    validate_entrance_loss_shape,
)
from ..references.models import SourceReference
from .config import DEFAULT_SOLVER_CONFIGURATION, SolverConfiguration

# ---------------------------------------------------------------------------
# Inlet-control coefficient selection
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InletCoefficientSelection:
    """Resolved inlet-control coefficient set with its selection basis and source."""

    coefficients: InletCoefficients
    basis: InletSelectionBasis
    source: SourceReference

    @property
    def used_default(self) -> bool:
        """Return whether the value came from a geometry/material library default."""
        return self.basis is InletSelectionBasis.GEOMETRY_MATERIAL_DEFAULT


def _validate_inlet_shape(barrel: CulvertBarrel, coefficients: InletCoefficients) -> None:
    """Reject inlet coefficients for a different geometry family."""
    if isinstance(barrel.geometry, CircularGeometry):
        barrel_shape = GeometryShape.CIRCULAR
    elif isinstance(barrel.geometry, (RectangularGeometry, FilletedRectangularGeometry)):
        barrel_shape = GeometryShape.RECTANGULAR
    else:
        barrel_shape = GeometryShape.ANY
    if coefficients.shape not in (GeometryShape.ANY, barrel_shape):
        raise InvalidInputError(
            f"Inlet coefficients for {coefficients.shape.value!r} geometry cannot be used "
            f"with {barrel_shape.value!r} geometry."
        )


def _default_inlet_coefficients(barrel: CulvertBarrel, config: SolverConfiguration) -> InletCoefficients:
    """Select standard default inlet coefficients from geometry and material."""
    if isinstance(barrel.geometry, CircularGeometry):
        if barrel.material == CORRUGATED_STEEL:
            return config.default_circular_cmp_inlet
        if barrel.material in {CONCRETE, CONCRETE_PIPE}:
            return config.default_circular_concrete_inlet
        raise InvalidInputError(
            "No default inlet coefficients exist for this circular barrel material; "
            "provide inlet_coefficients explicitly."
        )
    if isinstance(barrel.geometry, (RectangularGeometry, FilletedRectangularGeometry)):
        if barrel.material in {CONCRETE, CONCRETE_BOX}:
            return config.default_rectangular_inlet
        raise InvalidInputError(
            "No default inlet coefficients exist for this rectangular barrel material; "
            "provide inlet_coefficients explicitly."
        )
    raise InvalidInputError("No default inlet coefficients exist for this geometry; provide them explicitly.")


def resolve_inlet_coefficients(
    barrel: CulvertBarrel,
    *,
    override: InletCoefficients | None = None,
    configuration: SolverConfiguration | None = None,
) -> InletCoefficientSelection:
    """Resolve inlet-control coefficients using override > barrel > geometry/material default.

    Parameters
    ----------
    barrel : CulvertBarrel
        Culvert barrel domain model.
    override : InletCoefficients | None, optional
        Explicit user-supplied coefficient set. Always wins when provided.
    configuration : SolverConfiguration | None, optional
        Project configuration supplying defaults. Uses library defaults if None.

    Returns
    -------
    InletCoefficientSelection
        Resolved coefficients with selection basis and source provenance.
    """
    config = configuration if configuration is not None else DEFAULT_SOLVER_CONFIGURATION

    if override is not None:
        _validate_inlet_shape(barrel, override)
        return InletCoefficientSelection(
            coefficients=override,
            basis=InletSelectionBasis.USER_OVERRIDE,
            source=override.reference,
        )

    if barrel.inlet_coefficients is not None:
        _validate_inlet_shape(barrel, barrel.inlet_coefficients)
        return InletCoefficientSelection(
            coefficients=barrel.inlet_coefficients,
            basis=InletSelectionBasis.BARREL_ATTACHED,
            source=barrel.inlet_coefficients.reference,
        )

    default = _default_inlet_coefficients(barrel, config)
    _validate_inlet_shape(barrel, default)
    return InletCoefficientSelection(
        coefficients=default,
        basis=InletSelectionBasis.GEOMETRY_MATERIAL_DEFAULT,
        source=default.reference,
    )


# ---------------------------------------------------------------------------
# Entrance-loss coefficient selection
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EntranceLossSelection:
    """Resolved entrance-loss coefficient with its selection basis and source."""

    ke: float
    name: str
    basis: EntranceLossSelectionBasis
    source: SourceReference | None
    shape: GeometryShape

    def __post_init__(self) -> None:
        ke_val: float = finite(self.ke, "ke")
        if ke_val < 0:
            raise InvalidInputError("ke must be nonnegative.")
        if not self.name.strip():
            raise InvalidInputError("name must be nonempty text.")
        if self.basis is EntranceLossSelectionBasis.GEOMETRY_DEFAULT and self.source is None:
            raise InvalidInputError("A geometry default must identify its source.")
        object.__setattr__(self, "ke", ke_val)

    @property
    def used_default(self) -> bool:
        """Return whether the value came from a geometry/material library default."""
        return self.basis is EntranceLossSelectionBasis.GEOMETRY_DEFAULT


def resolve_entrance_loss_coefficient(
    barrel: CulvertBarrel,
    *,
    override: float | EntranceLossCoefficient | None = None,
    override_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
) -> EntranceLossSelection:
    """Resolve entrance-loss coefficient using override > barrel > geometry default.

    Parameters
    ----------
    barrel : CulvertBarrel
        Culvert barrel domain model.
    override : float | EntranceLossCoefficient | None, optional
        Explicit user-supplied Ke value or typed coefficient. Always wins.
    override_source : SourceReference | None, optional
        Source provenance for a numeric override. Only valid with a numeric override.
    configuration : SolverConfiguration | None, optional
        Project configuration supplying defaults. Uses library defaults if None.

    Returns
    -------
    EntranceLossSelection
        Resolved Ke with selection basis and source provenance.
    """
    config: SolverConfiguration = configuration if configuration is not None else DEFAULT_SOLVER_CONFIGURATION
    # 1. Explicit user override
    if override is not None:
        if isinstance(override, EntranceLossCoefficient):
            if override_source is not None:
                raise InvalidInputError(
                    "override_source is not used when override is an EntranceLossCoefficient "
                    "(it carries its own reference)."
                )
            validate_entrance_loss_shape(barrel, override)
            return EntranceLossSelection(
                ke=override.ke,
                name=override.name,
                basis=EntranceLossSelectionBasis.USER_OVERRIDE,
                source=override.reference,
                shape=override.shape,
            )
        ke_val: float = finite(override, "override")
        if ke_val < 0:
            raise InvalidInputError("entrance_loss_coefficient must be nonnegative.")
        return EntranceLossSelection(
            ke=ke_val,
            name="User-specified Ke",
            basis=EntranceLossSelectionBasis.USER_OVERRIDE,
            source=override_source,
            shape=GeometryShape.ANY,
        )

    if override_source is not None:
        raise InvalidInputError("override_source requires an override value.")

    # 2. Barrel-attached coefficient
    barrel_ke: EntranceLossCoefficient | float | None = barrel.entrance_loss_coefficient
    if barrel_ke is not None:
        if isinstance(barrel_ke, EntranceLossCoefficient):
            validate_entrance_loss_shape(barrel, barrel_ke)
            return EntranceLossSelection(
                ke=barrel_ke.ke,
                name=barrel_ke.name,
                basis=EntranceLossSelectionBasis.BARREL_ATTACHED,
                source=barrel_ke.reference,
                shape=barrel_ke.shape,
            )
        # Numeric value attached to barrel
        return EntranceLossSelection(
            ke=float(barrel_ke),
            name="Barrel-attached Ke",
            basis=EntranceLossSelectionBasis.BARREL_ATTACHED,
            source=None,
            shape=GeometryShape.ANY,
        )

    # 3. Geometry/material-based library default
    if isinstance(barrel.geometry, CircularGeometry):
        if barrel.material == CORRUGATED_STEEL:
            default_coeff: EntranceLossCoefficient = config.default_circular_cmp_loss
        elif barrel.material in {CONCRETE, CONCRETE_PIPE}:
            default_coeff = config.default_circular_concrete_loss
        else:
            raise InvalidInputError(
                "No default entrance-loss coefficient exists for this circular barrel material; provide one explicitly."
            )
    elif isinstance(barrel.geometry, (RectangularGeometry, FilletedRectangularGeometry)):
        if barrel.material in {CONCRETE, CONCRETE_BOX}:
            default_coeff = config.default_rectangular_loss
        else:
            raise InvalidInputError(
                "No default entrance-loss coefficient exists for this rectangular barrel "
                "material; provide one explicitly."
            )
    else:
        raise InvalidInputError(
            "No default entrance-loss coefficient exists for this geometry; provide one explicitly."
        )

    validate_entrance_loss_shape(barrel, default_coeff)
    return EntranceLossSelection(
        ke=default_coeff.ke,
        name=default_coeff.name,
        basis=EntranceLossSelectionBasis.GEOMETRY_DEFAULT,
        source=default_coeff.reference,
        shape=default_coeff.shape,
    )
