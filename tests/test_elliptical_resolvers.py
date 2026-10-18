"""Source-backed inlet and loss resolution tests for elliptical culverts."""

import pytest

from culvert_solver import (
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    CONCRETE,
    CONCRETE_BOX,
    CONCRETE_PIPE,
    CORRUGATED_STEEL,
    HORIZONTAL_ELLIPSE_CONCRETE_GROOVE_END,
    HORIZONTAL_ELLIPSE_CONCRETE_GROOVE_PROJECTING,
    HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
    HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE,
    VERTICAL_ELLIPSE_CONCRETE_GROOVE_END,
    VERTICAL_ELLIPSE_CONCRETE_GROOVE_PROJECTING,
    VERTICAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
    VERTICAL_ELLIPSE_LOSS_SQUARE_EDGE,
    CulvertBarrel,
    CulvertMaterial,
    EntranceLossCoefficient,
    GeometryShape,
    HorizontalEllipseGeometry,
    Hy8ConcreteOvalGeometry,
    InletCoefficients,
    InvalidInputError,
    VerticalEllipseGeometry,
    calculate_inlet_control_headwater,
)
from culvert_solver.solver.resolvers import (
    resolve_entrance_loss_coefficient,
    resolve_inlet_coefficients,
)


def _barrel(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
    *,
    material: CulvertMaterial = CONCRETE_PIPE,
) -> CulvertBarrel:
    return CulvertBarrel(
        geometry=geometry,
        length=30.0,
        inlet_invert=100.0,
        outlet_invert=99.5,
        roughness=0.012,
        material=material,
    )


@pytest.mark.parametrize(
    ("coefficient", "shape", "chart", "scale", "k", "m", "c", "y"),
    [
        (
            HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
            GeometryShape.HORIZONTAL_ELLIPSE,
            29,
            1,
            0.0100,
            2.0,
            0.0398,
            0.67,
        ),
        (
            HORIZONTAL_ELLIPSE_CONCRETE_GROOVE_END,
            GeometryShape.HORIZONTAL_ELLIPSE,
            29,
            2,
            0.0018,
            2.5,
            0.0292,
            0.74,
        ),
        (
            HORIZONTAL_ELLIPSE_CONCRETE_GROOVE_PROJECTING,
            GeometryShape.HORIZONTAL_ELLIPSE,
            29,
            3,
            0.0045,
            2.0,
            0.0317,
            0.69,
        ),
        (
            VERTICAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
            GeometryShape.VERTICAL_ELLIPSE,
            30,
            1,
            0.0100,
            2.0,
            0.0398,
            0.67,
        ),
        (
            VERTICAL_ELLIPSE_CONCRETE_GROOVE_END,
            GeometryShape.VERTICAL_ELLIPSE,
            30,
            2,
            0.0018,
            2.5,
            0.0292,
            0.74,
        ),
        (
            VERTICAL_ELLIPSE_CONCRETE_GROOVE_PROJECTING,
            GeometryShape.VERTICAL_ELLIPSE,
            30,
            3,
            0.0095,
            2.0,
            0.0317,
            0.69,
        ),
    ],
)
def test_hds5_table_a2_ellipse_coefficients(
    coefficient: InletCoefficients,
    shape: GeometryShape,
    chart: int,
    scale: int,
    k: float,
    m: float,
    c: float,
    y: float,
) -> None:
    assert coefficient.shape is shape
    assert (coefficient.chart, coefficient.scale) == (chart, scale)
    assert (coefficient.k, coefficient.m, coefficient.c, coefficient.y) == pytest.approx((k, m, c, y))
    assert coefficient.reference.source_id == "FHWA-HDS5-2012-TABLE-A2"


@pytest.mark.parametrize(
    "geometry",
    [
        HorizontalEllipseGeometry(span=2.4, rise=1.2),
        VerticalEllipseGeometry(span=1.2, rise=2.4),
    ],
)
def test_ellipse_requires_explicit_inlet_treatment(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
) -> None:
    barrel = _barrel(geometry)

    with pytest.raises(InvalidInputError, match="Elliptical inlet treatment is ambiguous"):
        resolve_inlet_coefficients(barrel)
    with pytest.raises(InvalidInputError, match="Elliptical entrance treatment is ambiguous"):
        resolve_entrance_loss_coefficient(barrel)


@pytest.mark.parametrize(
    ("geometry", "expected_inlet", "expected_loss"),
    [
        (
            HorizontalEllipseGeometry(span=2.4, rise=1.2),
            HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
            HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE,
        ),
        (
            VerticalEllipseGeometry(span=1.2, rise=2.4),
            VERTICAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
            VERTICAL_ELLIPSE_LOSS_SQUARE_EDGE,
        ),
    ],
)
def test_ellipse_explicit_coefficients_are_shape_specific(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
    expected_inlet: InletCoefficients,
    expected_loss: EntranceLossCoefficient,
) -> None:
    barrel = CulvertBarrel(
        geometry=geometry,
        length=30.0,
        inlet_invert=100.0,
        outlet_invert=99.5,
        roughness=0.012,
        material=CONCRETE_PIPE,
        inlet_coefficients=expected_inlet,
        entrance_loss_coefficient=expected_loss,
    )

    inlet = resolve_inlet_coefficients(barrel)
    loss = resolve_entrance_loss_coefficient(barrel)

    assert inlet.coefficients is expected_inlet
    assert loss.ke == expected_loss.ke
    assert loss.shape is expected_loss.shape


def test_ellipse_rejects_circular_inlet_coefficients() -> None:
    barrel = _barrel(HorizontalEllipseGeometry(span=2.4, rise=1.2))

    with pytest.raises(InvalidInputError, match="horizontal_ellipse"):
        resolve_inlet_coefficients(
            barrel,
            override=CIRCULAR_CONCRETE_SQUARE_EDGE,
        )


def test_ellipse_material_does_not_bypass_explicit_treatment_requirement() -> None:
    barrel = _barrel(
        VerticalEllipseGeometry(span=1.2, rise=2.4),
        material=CORRUGATED_STEEL,
    )

    with pytest.raises(InvalidInputError, match="Elliptical inlet treatment is ambiguous"):
        resolve_inlet_coefficients(barrel)
    with pytest.raises(InvalidInputError, match="Elliptical entrance treatment is ambiguous"):
        resolve_entrance_loss_coefficient(barrel)


@pytest.mark.parametrize(
    ("geometry", "inlet_coefficients", "loss_coefficients"),
    [
        (
            HorizontalEllipseGeometry(span=2.4, rise=1.2),
            HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
            HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE,
        ),
        (
            VerticalEllipseGeometry(span=1.2, rise=2.4),
            VERTICAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
            VERTICAL_ELLIPSE_LOSS_SQUARE_EDGE,
        ),
        (
            Hy8ConcreteOvalGeometry.from_mm(2108.2, 1346.2),
            HORIZONTAL_ELLIPSE_CONCRETE_GROOVE_END,
            HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE,
        ),
    ],
)
@pytest.mark.parametrize("material", [CORRUGATED_STEEL, CONCRETE_BOX])
def test_concrete_ellipse_coefficients_fail_closed_for_other_materials(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry | Hy8ConcreteOvalGeometry,
    inlet_coefficients: InletCoefficients,
    loss_coefficients: EntranceLossCoefficient,
    material: CulvertMaterial,
) -> None:
    """A shape match does not make concrete empirical data valid for steel/boxes."""
    bare = CulvertBarrel(
        geometry=geometry,
        length=30.0,
        inlet_invert=100.0,
        outlet_invert=99.5,
        roughness=0.012,
        material=material,
    )
    attached = CulvertBarrel(
        geometry=geometry,
        length=30.0,
        inlet_invert=100.0,
        outlet_invert=99.5,
        roughness=0.012,
        material=material,
        inlet_coefficients=inlet_coefficients,
        entrance_loss_coefficient=loss_coefficients,
    )
    with pytest.raises(InvalidInputError, match="concrete pipe material"):
        resolve_inlet_coefficients(bare, override=inlet_coefficients)
    with pytest.raises(InvalidInputError, match="concrete pipe material"):
        resolve_inlet_coefficients(attached)
    with pytest.raises(InvalidInputError, match="concrete pipe material"):
        resolve_entrance_loss_coefficient(bare, override=loss_coefficients)
    with pytest.raises(InvalidInputError, match="concrete pipe material"):
        resolve_entrance_loss_coefficient(attached)
    for discharge in (0.0, 1.0):
        with pytest.raises(InvalidInputError, match="concrete pipe material"):
            calculate_inlet_control_headwater(bare, discharge, coefficients=inlet_coefficients)
        with pytest.raises(InvalidInputError, match="concrete pipe material"):
            calculate_inlet_control_headwater(attached, discharge)


@pytest.mark.parametrize("material", [CONCRETE, CONCRETE_PIPE])
def test_concrete_ellipse_coefficients_accept_concrete_pipe_materials(
    material: CulvertMaterial,
) -> None:
    """Explicit published ellipse configurations retain both valid concrete options."""
    barrel = CulvertBarrel(
        geometry=HorizontalEllipseGeometry(span=2.4, rise=1.2),
        length=30.0,
        inlet_invert=100.0,
        outlet_invert=99.5,
        roughness=0.012,
        material=material,
        inlet_coefficients=HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
        entrance_loss_coefficient=HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE,
    )
    assert resolve_inlet_coefficients(barrel).coefficients is HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE
    assert resolve_entrance_loss_coefficient(barrel).ke == HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE.ke
    assert calculate_inlet_control_headwater(barrel, 1.0).headwater_depth > 0.0
