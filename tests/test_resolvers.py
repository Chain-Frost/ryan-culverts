"""Tests for inlet-control and entrance-loss coefficient resolvers."""

import pytest

from culvert_solver import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    CIRCULAR_CMP_HEADWALL,
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    CONCRETE,
    CONCRETE_BOX,
    CONCRETE_PIPE,
    CORRUGATED_STEEL,
    CircularGeometry,
    CulvertBarrel,
    CulvertMaterial,
    EntranceLossCoefficient,
    EntranceLossSelection,
    EntranceLossSelectionBasis,
    InletCoefficients,
    InletCoefficientSelection,
    InletSelectionBasis,
    InvalidInputError,
    RectangularGeometry,
    SourceReference,
)
from culvert_solver.geometry.base import CrossSectionGeometry
from culvert_solver.outlet_control.losses import (
    BOX_CONCRETE_FLARED_WINGWALLS_30_75 as LOSS_BOX_FLARED,
)
from culvert_solver.outlet_control.losses import (
    PIPE_CMP_PROJECTING,
    PIPE_CONCRETE_SQUARE_EDGE,
)
from culvert_solver.solver.config import SolverConfiguration
from culvert_solver.solver.resolvers import (
    resolve_entrance_loss_coefficient,
    resolve_inlet_coefficients,
)

# ---------------------------------------------------------------------------
# Barrel fixtures
# ---------------------------------------------------------------------------


def _circular_barrel(
    *,
    material: CulvertMaterial | None = CONCRETE,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: EntranceLossCoefficient | float | None = None,
) -> CulvertBarrel:
    return CulvertBarrel(
        geometry=CircularGeometry.from_mm(600),
        length=20.0,
        inlet_invert=100.0,
        outlet_invert=99.8,
        roughness=0.012,
        material=material,
        inlet_coefficients=inlet_coefficients,
        entrance_loss_coefficient=entrance_loss_coefficient,
    )


def _box_barrel(
    *,
    material: CulvertMaterial | None = CONCRETE,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: EntranceLossCoefficient | float | None = None,
) -> CulvertBarrel:
    return CulvertBarrel(
        geometry=RectangularGeometry.from_mm(1200, 600),
        length=20.0,
        inlet_invert=100.0,
        outlet_invert=99.8,
        roughness=0.012,
        material=material,
        inlet_coefficients=inlet_coefficients,
        entrance_loss_coefficient=entrance_loss_coefficient,
    )


# ===========================================================================
# Inlet coefficient resolver tests
# ===========================================================================


class TestResolveInletCoefficients:
    """Test resolve_inlet_coefficients precedence and validation."""

    def test_user_override_wins(self) -> None:
        barrel = _circular_barrel(inlet_coefficients=CIRCULAR_CMP_HEADWALL)
        result = resolve_inlet_coefficients(barrel, override=CIRCULAR_CONCRETE_SQUARE_EDGE)
        assert result.basis is InletSelectionBasis.USER_OVERRIDE
        assert result.coefficients is CIRCULAR_CONCRETE_SQUARE_EDGE
        assert not result.used_default

    def test_barrel_attached_wins_over_default(self) -> None:
        barrel = _circular_barrel(inlet_coefficients=CIRCULAR_CMP_HEADWALL)
        result = resolve_inlet_coefficients(barrel)
        assert result.basis is InletSelectionBasis.BARREL_ATTACHED
        assert result.coefficients is CIRCULAR_CMP_HEADWALL
        assert not result.used_default

    def test_geometry_material_default_circular_concrete(self) -> None:
        barrel = _circular_barrel(material=CONCRETE)
        result = resolve_inlet_coefficients(barrel)
        assert result.basis is InletSelectionBasis.GEOMETRY_MATERIAL_DEFAULT
        assert result.coefficients is CIRCULAR_CONCRETE_SQUARE_EDGE
        assert result.used_default

    def test_geometry_material_default_circular_csp(self) -> None:
        barrel = _circular_barrel(material=CORRUGATED_STEEL)
        result = resolve_inlet_coefficients(barrel)
        assert result.basis is InletSelectionBasis.GEOMETRY_MATERIAL_DEFAULT
        assert result.coefficients is CIRCULAR_CMP_HEADWALL

    def test_geometry_material_default_circular_requires_material(self) -> None:
        barrel = _circular_barrel(material=None)
        with pytest.raises(InvalidInputError, match="material"):
            resolve_inlet_coefficients(barrel)

    def test_geometry_material_default_box_concrete(self) -> None:
        barrel = _box_barrel(material=CONCRETE)
        result = resolve_inlet_coefficients(barrel)
        assert result.basis is InletSelectionBasis.GEOMETRY_MATERIAL_DEFAULT
        assert result.coefficients is BOX_CONCRETE_FLARED_WINGWALLS_30_75

    def test_geometry_material_default_box_requires_material(self) -> None:
        barrel = _box_barrel(material=None)
        with pytest.raises(InvalidInputError, match="material"):
            resolve_inlet_coefficients(barrel)

    def test_specific_concrete_materials_match_geometry(self) -> None:
        assert (
            resolve_inlet_coefficients(_circular_barrel(material=CONCRETE_PIPE)).coefficients
            is CIRCULAR_CONCRETE_SQUARE_EDGE
        )
        assert (
            resolve_inlet_coefficients(_box_barrel(material=CONCRETE_BOX)).coefficients
            is BOX_CONCRETE_FLARED_WINGWALLS_30_75
        )
        with pytest.raises(InvalidInputError, match="material"):
            resolve_inlet_coefficients(_circular_barrel(material=CONCRETE_BOX))
        with pytest.raises(InvalidInputError, match="material"):
            resolve_inlet_coefficients(_box_barrel(material=CONCRETE_PIPE))

    def test_shape_mismatch_rejects_override(self) -> None:
        barrel = _box_barrel()
        with pytest.raises(InvalidInputError, match="geometry"):
            resolve_inlet_coefficients(barrel, override=CIRCULAR_CONCRETE_SQUARE_EDGE)

    def test_shape_mismatch_rejects_barrel_attached(self) -> None:
        barrel = _box_barrel(inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE)
        with pytest.raises(InvalidInputError, match="geometry"):
            resolve_inlet_coefficients(barrel)

    def test_unsupported_material_fails(self) -> None:
        custom = CulvertMaterial(name="Custom", typical_n=0.015, range_n=(0.014, 0.016))
        barrel = _circular_barrel(material=custom)
        with pytest.raises(InvalidInputError, match="default inlet"):
            resolve_inlet_coefficients(barrel)

    def test_unsupported_box_material_fails(self) -> None:
        custom = CulvertMaterial(name="Custom", typical_n=0.015, range_n=(0.014, 0.016))
        barrel = _box_barrel(material=custom)
        with pytest.raises(InvalidInputError, match="default inlet"):
            resolve_inlet_coefficients(barrel)

    def test_source_reference_propagated(self) -> None:
        barrel = _circular_barrel()
        result = resolve_inlet_coefficients(barrel)
        assert result.source is not None
        assert "HDS5" in result.source.source_id or "HDS-5" in result.source.publication

    def test_result_is_frozen(self) -> None:
        barrel = _circular_barrel()
        result = resolve_inlet_coefficients(barrel)
        assert isinstance(result, InletCoefficientSelection)
        # Frozen dataclass
        with pytest.raises(AttributeError):
            result.basis = InletSelectionBasis.USER_OVERRIDE  # type: ignore[misc]


# ===========================================================================
# Entrance-loss coefficient resolver tests
# ===========================================================================


class TestResolveEntranceLossCoefficient:
    """Test resolve_entrance_loss_coefficient precedence and validation."""

    def test_numeric_override_wins(self) -> None:
        barrel = _circular_barrel(entrance_loss_coefficient=0.2)
        result = resolve_entrance_loss_coefficient(barrel, override=0.7)
        assert result.basis is EntranceLossSelectionBasis.USER_OVERRIDE
        assert result.ke == pytest.approx(0.7)
        assert not result.used_default

    def test_typed_override_wins(self) -> None:
        barrel = _circular_barrel()
        result = resolve_entrance_loss_coefficient(barrel, override=PIPE_CMP_PROJECTING)
        assert result.basis is EntranceLossSelectionBasis.USER_OVERRIDE
        assert result.ke == pytest.approx(PIPE_CMP_PROJECTING.ke)
        assert result.name == PIPE_CMP_PROJECTING.name

    def test_numeric_override_with_source(self) -> None:
        src = SourceReference(
            source_id="test",
            publication="Test pub",
            edition="v1",
            locator="Table 1",
            url="https://example.com/test",
            applicability="Test applicability",
        )
        barrel = _circular_barrel()
        result = resolve_entrance_loss_coefficient(barrel, override=0.3, override_source=src)
        assert result.ke == pytest.approx(0.3)
        assert result.source is src

    def test_typed_override_rejects_override_source(self) -> None:
        src = SourceReference(
            source_id="test",
            publication="Test pub",
            edition="v1",
            locator="Table 1",
            url="https://example.com/test",
            applicability="Test applicability",
        )
        barrel = _circular_barrel()
        with pytest.raises(InvalidInputError, match="override_source"):
            resolve_entrance_loss_coefficient(barrel, override=PIPE_CMP_PROJECTING, override_source=src)

    def test_override_source_without_override_fails(self) -> None:
        src = SourceReference(
            source_id="test",
            publication="Test pub",
            edition="v1",
            locator="Table 1",
            url="https://example.com/test",
            applicability="Test applicability",
        )
        barrel = _circular_barrel()
        with pytest.raises(InvalidInputError, match="override_source requires"):
            resolve_entrance_loss_coefficient(barrel, override_source=src)

    def test_barrel_attached_numeric(self) -> None:
        barrel = _circular_barrel(entrance_loss_coefficient=0.2)
        result = resolve_entrance_loss_coefficient(barrel)
        assert result.basis is EntranceLossSelectionBasis.BARREL_ATTACHED
        assert result.ke == pytest.approx(0.2)
        assert not result.used_default

    def test_barrel_attached_typed(self) -> None:
        barrel = _circular_barrel(entrance_loss_coefficient=PIPE_CMP_PROJECTING)
        result = resolve_entrance_loss_coefficient(barrel)
        assert result.basis is EntranceLossSelectionBasis.BARREL_ATTACHED
        assert result.ke == pytest.approx(PIPE_CMP_PROJECTING.ke)
        assert result.name == PIPE_CMP_PROJECTING.name

    def test_geometry_default_circular(self) -> None:
        barrel = _circular_barrel()
        result = resolve_entrance_loss_coefficient(barrel)
        assert result.basis is EntranceLossSelectionBasis.GEOMETRY_DEFAULT
        assert result.ke == pytest.approx(PIPE_CONCRETE_SQUARE_EDGE.ke)
        assert result.used_default

    def test_geometry_default_box(self) -> None:
        barrel = _box_barrel()
        result = resolve_entrance_loss_coefficient(barrel)
        assert result.basis is EntranceLossSelectionBasis.GEOMETRY_DEFAULT
        assert result.ke == pytest.approx(LOSS_BOX_FLARED.ke)

    def test_geometry_default_csp_uses_cmp_headwall(self) -> None:
        barrel = _circular_barrel(material=CORRUGATED_STEEL)
        result = resolve_entrance_loss_coefficient(barrel)
        assert result.basis is EntranceLossSelectionBasis.GEOMETRY_DEFAULT
        assert result.ke == pytest.approx(0.5)
        assert "CMP" in result.name

    def test_geometry_default_requires_explicit_material_context(self) -> None:
        with pytest.raises(InvalidInputError, match="material"):
            resolve_entrance_loss_coefficient(_circular_barrel(material=None))
        with pytest.raises(InvalidInputError, match="material"):
            resolve_entrance_loss_coefficient(_box_barrel(material=None))

    def test_specific_concrete_loss_materials_match_geometry(self) -> None:
        assert resolve_entrance_loss_coefficient(_circular_barrel(material=CONCRETE_PIPE)).ke == pytest.approx(
            PIPE_CONCRETE_SQUARE_EDGE.ke
        )
        assert resolve_entrance_loss_coefficient(_box_barrel(material=CONCRETE_BOX)).ke == pytest.approx(
            LOSS_BOX_FLARED.ke
        )
        with pytest.raises(InvalidInputError, match="material"):
            resolve_entrance_loss_coefficient(_circular_barrel(material=CONCRETE_BOX))
        with pytest.raises(InvalidInputError, match="material"):
            resolve_entrance_loss_coefficient(_box_barrel(material=CONCRETE_PIPE))

    def test_negative_override_rejected(self) -> None:
        barrel = _circular_barrel()
        with pytest.raises(InvalidInputError, match="nonnegative"):
            resolve_entrance_loss_coefficient(barrel, override=-0.1)

    def test_shape_mismatch_typed_override_rejected(self) -> None:
        barrel = _box_barrel()
        with pytest.raises(InvalidInputError, match="geometry"):
            resolve_entrance_loss_coefficient(barrel, override=PIPE_CMP_PROJECTING)

    def test_shape_mismatch_barrel_attached_rejected(self) -> None:
        barrel = _box_barrel(entrance_loss_coefficient=PIPE_CMP_PROJECTING)
        with pytest.raises(InvalidInputError, match="geometry"):
            resolve_entrance_loss_coefficient(barrel)

    def test_source_reference_propagated(self) -> None:
        barrel = _circular_barrel()
        result = resolve_entrance_loss_coefficient(barrel)
        assert result.source is not None
        assert "HDS5" in result.source.source_id or "HDS-5" in result.source.publication

    def test_result_is_frozen(self) -> None:
        barrel = _circular_barrel()
        result = resolve_entrance_loss_coefficient(barrel)
        assert isinstance(result, EntranceLossSelection)
        with pytest.raises(AttributeError):
            result.ke = 999.0  # type: ignore[misc]

    def test_zero_override_accepted(self) -> None:
        barrel = _circular_barrel()
        result = resolve_entrance_loss_coefficient(barrel, override=0.0)
        assert result.ke == pytest.approx(0.0)


# ===========================================================================
# Configuration override tests
# ===========================================================================


class TestResolverConfiguration:
    """Test injecting custom SolverConfiguration into resolvers."""

    def test_inlet_custom_configuration(self) -> None:
        # Create a custom config that replaces concrete circular with CMP
        config = SolverConfiguration(default_circular_concrete_inlet=CIRCULAR_CMP_HEADWALL)
        barrel = _circular_barrel(material=CONCRETE)

        result = resolve_inlet_coefficients(barrel, configuration=config)
        assert result.coefficients is CIRCULAR_CMP_HEADWALL

    def test_entrance_loss_custom_configuration(self) -> None:
        config = SolverConfiguration(default_circular_concrete_loss=PIPE_CMP_PROJECTING)
        barrel = _circular_barrel(material=CONCRETE)

        result = resolve_entrance_loss_coefficient(barrel, configuration=config)
        assert result.ke == pytest.approx(PIPE_CMP_PROJECTING.ke)

    def test_unknown_geometry_fails_closed(self) -> None:
        class DummyGeometry(CrossSectionGeometry):
            @property
            def area_full(self) -> float:
                return 1.0

            @property
            def wetted_perimeter_full(self) -> float:
                return 1.0

            @property
            def span(self) -> float:
                return 1.0

            @property
            def rise(self) -> float:
                return 1.0

            def area(self, depth: float) -> float:
                del depth
                return 1.0

            def wetted_perimeter(self, depth: float) -> float:
                del depth
                return 1.0

            def top_width(self, depth: float) -> float:
                del depth
                return 1.0

        barrel = CulvertBarrel(
            geometry=DummyGeometry(),
            length=10.0,
            inlet_invert=1.0,
            outlet_invert=0.0,
            roughness=0.012,
        )

        with pytest.raises(InvalidInputError, match="No default entrance-loss"):
            resolve_entrance_loss_coefficient(barrel)
