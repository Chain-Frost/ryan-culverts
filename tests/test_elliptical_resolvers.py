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
    InletSelectionBasis,
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
def test_ellipse_defaults_are_shape_specific(
    geometry: HorizontalEllipseGeometry | VerticalEllipseGeometry,
    expected_inlet: InletCoefficients,
    expected_loss: EntranceLossCoefficient,
) -> None:
    barrel = _barrel(geometry)

    inlet = resolve_inlet_coefficients(barrel)
    loss = resolve_entrance_loss_coefficient(barrel)

    assert inlet.basis is InletSelectionBasis.GEOMETRY_MATERIAL_DEFAULT
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


def test_ellipse_unsupported_material_fails_closed() -> None:
    barrel = _barrel(
        VerticalEllipseGeometry(span=1.2, rise=2.4),
        material=CORRUGATED_STEEL,
    )

    with pytest.raises(InvalidInputError, match="vertical ellipse material"):
        resolve_inlet_coefficients(barrel)
    with pytest.raises(InvalidInputError, match="vertical ellipse"):
        resolve_entrance_loss_coefficient(barrel)
