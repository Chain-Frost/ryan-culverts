"""Source-backed four-arc concrete oval geometry and solver integration."""

import math

import pytest

from culvert_solver import (
    CONCRETE_PIPE,
    HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
    HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE,
    HY8_CONCRETE_OVALS,
    CulvertBarrel,
    HorizontalEllipseGeometry,
    Hy8ConcreteOvalGeometry,
    InvalidInputError,
    calculate_critical_depth,
    calculate_normal_depth,
    solve_barrel_hydraulics,
)
from culvert_solver.solver.resolvers import (
    resolve_entrance_loss_coefficient,
    resolve_inlet_coefficients,
)


@pytest.mark.parametrize("span_mm,rise_mm", [(1524, 965.2), (1727.2, 1092.2)])
def test_hy8_source_oval_matches_nominal_dimensions_and_area(
    span_mm: float, rise_mm: float
) -> None:
    """The catalogue-based section is not interchangeable with an exact ellipse."""
    oval = Hy8ConcreteOvalGeometry.from_mm(span_mm, rise_mm)
    exact_ellipse = HorizontalEllipseGeometry.from_mm(span_mm, rise_mm)
    assert oval.span == pytest.approx(span_mm / 1000.0)
    assert oval.rise == pytest.approx(rise_mm / 1000.0)
    assert oval.top_width(oval.rise / 2) == pytest.approx(oval.span, abs=1e-12)
    assert oval.area_full > exact_ellipse.area_full
    assert abs(oval.shape_db_area_difference_percent) < 0.1
    assert oval.area_full == pytest.approx(2 * oval.area(oval.rise / 2), rel=1e-12)
    assert oval.wetted_perimeter_full == pytest.approx(
        2 * oval.wetted_perimeter(oval.rise / 2), rel=1e-12
    )


@pytest.mark.parametrize("row_index", [0, 1, 7, 8, 9, 16, 21])
def test_oval_area_depth_perimeter_and_width_consistency(row_index: int) -> None:
    """Partial profile derivatives satisfy the basic cross-section identities."""
    oval = Hy8ConcreteOvalGeometry(row_index)
    rise = oval.rise
    assert oval.area(0) == 0
    assert oval.top_width(0) == 0
    assert oval.wetted_perimeter(0) == 0
    assert oval.area(2 * rise) == pytest.approx(oval.area_full)
    assert oval.wetted_perimeter(2 * rise) == pytest.approx(oval.wetted_perimeter_full)
    for fraction in (0.05, 0.20, 0.40, 0.50, 0.70, 0.85, 0.95):
        y = fraction * rise
        small = 1e-5 * rise
        numerical_width = (oval.area(y + small) - oval.area(y - small)) / (2 * small)
        assert oval.top_width(y) == pytest.approx(numerical_width, rel=3e-5)
        assert oval.area(y) + oval.area(rise - y) == pytest.approx(oval.area_full, rel=1e-11)
        assert oval.wetted_perimeter(y) + oval.wetted_perimeter(rise - y) == pytest.approx(
            oval.wetted_perimeter_full, rel=1e-10
        )


def test_catalogue_selection_and_area_reconciliation_fail_closed() -> None:
    """No substitution, rotation or knowingly inconsistent catalogue geometry."""
    assert len(HY8_CONCRETE_OVALS) == 23
    with pytest.raises(InvalidInputError, match="exact ShapeDB catalogue size"):
        Hy8ConcreteOvalGeometry.from_mm(1500, 1000)
    with pytest.raises(InvalidInputError, match="exact ShapeDB catalogue size"):
        Hy8ConcreteOvalGeometry.from_mm(965.2, 1524)
    with pytest.raises(InvalidInputError, match="area reconciliation failed"):
        Hy8ConcreteOvalGeometry.from_mm(34 * 25.4, 22 * 25.4)
    with pytest.raises(InvalidInputError, match="area reconciliation failed"):
        Hy8ConcreteOvalGeometry.from_mm(180 * 25.4, 116 * 25.4)


def test_hy8_oval_critical_and_normal_depth() -> None:
    """Standard profiles participate in the existing hydraulic primitives."""
    oval = Hy8ConcreteOvalGeometry.from_mm(1524, 965.2)
    critical = calculate_critical_depth(oval, discharge=0.5)
    assert 0 < critical.depth < oval.rise
    assert critical.froude_number == pytest.approx(1.0, rel=1e-6)
    y = 0.50 * oval.rise
    slope = 0.01
    roughness = 0.012
    flow = oval.area(y) * oval.hydraulic_radius(y) ** (2 / 3) * math.sqrt(slope) / roughness
    normal = calculate_normal_depth(oval, flow, slope, roughness)
    assert normal.depth == pytest.approx(y, abs=2e-6)
    assert not normal.is_full


def test_hy8_oval_inlet_and_loss_are_explicit_and_shape_checked() -> None:
    """Catalogue identity must never imply a physical inlet/entrance configuration."""
    oval = Hy8ConcreteOvalGeometry.from_mm(1524, 965.2)
    bare = CulvertBarrel(
        geometry=oval, length=30, inlet_invert=10, outlet_invert=9.5,
        roughness=0.012, material=CONCRETE_PIPE
    )
    with pytest.raises(InvalidInputError, match="Elliptical inlet treatment is ambiguous"):
        resolve_inlet_coefficients(bare)
    with pytest.raises(InvalidInputError, match="Elliptical entrance treatment is ambiguous"):
        resolve_entrance_loss_coefficient(bare)

    barrel = CulvertBarrel(
        geometry=oval, length=30, inlet_invert=10, outlet_invert=9.5,
        roughness=0.012, material=CONCRETE_PIPE,
        inlet_coefficients=HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE,
        entrance_loss_coefficient=HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE,
    )
    assert resolve_inlet_coefficients(barrel).coefficients is HORIZONTAL_ELLIPSE_CONCRETE_SQUARE_EDGE
    assert resolve_entrance_loss_coefficient(barrel).ke == HORIZONTAL_ELLIPSE_LOSS_SQUARE_EDGE.ke
    result = solve_barrel_hydraulics(barrel, 0.5, tailwater=9.7)
    assert math.isfinite(result.headwater_elevation)
