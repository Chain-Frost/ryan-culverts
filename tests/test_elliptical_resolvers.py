"""Source-backed inlet and loss resolution tests for elliptical culverts."""

import pytest

from culvert_solver import (
    CIRCULAR_CONCRETE_SQUARE_EDGE,
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
    InletCoefficients,
    InvalidInputError,
    VerticalEllipseGeometry,
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
