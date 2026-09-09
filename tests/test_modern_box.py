"""Corrected FHWA modern-box configuration and filleted-geometry tests."""

import math

import pytest

from culvert_solver import (
    BoxCrownTreatment,
    BoxWingwallTreatment,
    FilletedRectangularGeometry,
    InvalidInputError,
    ModernBoxInlet,
    RectangularGeometry,
    calculate_critical_depth,
    calculate_modern_box_inlet_headwater,
    resolve_modern_box_inlet_coefficients,
    solve_barrel_hydraulics,
    water_surface_elevation_from_energy_grade,
)
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.materials import CONCRETE


def test_filleted_geometry_uses_net_area_and_piecewise_width() -> None:
    geometry = FilletedRectangularGeometry(span=3.0, rise=2.0, fillet=0.2)

    assert geometry.area_full == pytest.approx(6.0 - 2.0 * 0.2**2)
    assert geometry.top_width(0.1) == pytest.approx(2.8)
    assert geometry.top_width(1.0) == pytest.approx(3.0)
    assert geometry.top_width(1.9) == pytest.approx(2.8)
    assert geometry.wetted_perimeter_full == pytest.approx(
        2.0 * (3.0 + 2.0) + 4.0 * (math.sqrt(2.0) - 2.0) * 0.2
    )


def test_appendix_d_six_inch_fillet_critical_depth() -> None:
    """Reproduce Appendix D Table 22's Q25 FC-D critical-depth intermediate."""
    geometry = FilletedRectangularGeometry(
        span=9.0 * 0.3048,
        rise=8.0 * 0.3048,
        fillet=6.0 * 0.0254,
    )
    per_barrel_discharge = 773.0 * 0.028316846592 / 2.0

    result = calculate_critical_depth(geometry, per_barrel_discharge)

    assert result.depth / 0.3048 == pytest.approx(3.88, abs=0.005)


def test_appendix_d_physical_identity_resolves_sketch_2() -> None:
    inlet = ModernBoxInlet(
        geometry=FilletedRectangularGeometry(
            span=9.0 * 0.3048,
            rise=8.0 * 0.3048,
            fillet=6.0 * 0.0254,
        ),
        wingwall_treatment=BoxWingwallTreatment.FLARED_30,
        crown_treatment=BoxCrownTreatment.BEVEL_45,
        barrel_count=2,
    )

    coefficients = resolve_modern_box_inlet_coefficients(inlet)

    assert coefficients.sketch == 2
    assert coefficients.ke == pytest.approx(0.32)
    assert inlet.net_opening_area == pytest.approx(2.0 * inlet.geometry.area_full)


def test_appendix_d_q25_headwater_case() -> None:
    """Reproduce Appendix D Table 25 using its customary-unit governing inputs."""
    geometry = FilletedRectangularGeometry(
        span=9.0 * 0.3048,
        rise=8.0 * 0.3048,
        fillet=6.0 * 0.0254,
    )
    inlet = ModernBoxInlet(
        geometry=geometry,
        wingwall_treatment=BoxWingwallTreatment.FLARED_30,
        crown_treatment=BoxCrownTreatment.BEVEL_45,
        barrel_count=2,
    )
    coefficients = resolve_modern_box_inlet_coefficients(inlet)
    barrel = CulvertBarrel(
        geometry=geometry,
        length=84.0 * 0.3048,
        inlet_invert=78.81 * 0.3048,
        outlet_invert=78.79 * 0.3048,
        roughness=0.012,
        material=CONCRETE,
    )
    total_discharge = 773.0 * 0.028316846592
    barrel_result = solve_barrel_hydraulics(
        barrel,
        total_discharge / 2.0,
        84.78 * 0.3048,
        inlet_coefficients=coefficients.form_2_inlet_coefficients(),
        entrance_loss_coefficient=coefficients.entrance_loss_coefficient(),
        g=32.2 * 0.3048,
    )
    pool_level = water_surface_elevation_from_energy_grade(
        barrel_result.headwater_elevation,
        total_discharge,
        1265.0 * 0.3048**2,
        g=32.2 * 0.3048,
    )

    assert pool_level / 0.3048 == pytest.approx(85.907, abs=0.001)


def test_table_12_polynomial_uses_dimensionless_discharge() -> None:
    inlet = ModernBoxInlet(
        geometry=RectangularGeometry(span=2.0, rise=2.0),
        wingwall_treatment=BoxWingwallTreatment.FLARED_30,
        crown_treatment=BoxCrownTreatment.BEVEL_45,
        barrel_count=2,
    )
    discharge_at_x_one = inlet.net_opening_area * math.sqrt(9.80665 * inlet.geometry.rise)

    result = calculate_modern_box_inlet_headwater(inlet, discharge_at_x_one)

    expected_ratio = sum(result.coefficients.polynomial)
    assert result.flow_parameter == pytest.approx(1.0)
    assert result.headwater_ratio == pytest.approx(expected_ratio)
    assert result.headwater_depth == pytest.approx(expected_ratio * 2.0)


def test_modern_box_resolver_rejects_visual_fallback() -> None:
    inlet = ModernBoxInlet(
        geometry=RectangularGeometry(span=2.0, rise=2.0),
        wingwall_treatment=BoxWingwallTreatment.FLARED_30,
        crown_treatment=BoxCrownTreatment.SQUARE_EDGE,
    )

    with pytest.raises(InvalidInputError, match="require a 45-degree crown bevel"):
        resolve_modern_box_inlet_coefficients(inlet)


def test_table_12_polynomial_fails_outside_useful_range() -> None:
    inlet = ModernBoxInlet(
        geometry=RectangularGeometry(span=2.0, rise=2.0),
        wingwall_treatment=BoxWingwallTreatment.FLARED_30,
        crown_treatment=BoxCrownTreatment.BEVEL_45,
    )

    with pytest.raises(InvalidInputError, match="outside its documented useful range"):
        calculate_modern_box_inlet_headwater(inlet, 1e-9)
