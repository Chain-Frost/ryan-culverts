"""Analytical, reference-benchmark, and continuity tests for inlet-control hydraulics."""

import math
from dataclasses import FrozenInstanceError
from itertools import pairwise
from typing import cast

import pytest

from culvert_solver import (
    BOX_CONCRETE_CHAMFER_90_HEADWALL,
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    CIRCULAR_CMP_HEADWALL,
    CIRCULAR_CMP_MITERED,
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    CONCRETE_PIPE,
    EXTREME_HEADWATER_RATIO,
    HDS5_LABORATORY_HW_D_MAX,
    SMOOTH_HDPE,
    STANDARD_INLET_COEFFICIENTS,
    CircularGeometry,
    CulvertBarrel,
    FlowRegime,
    GeometryShape,
    HydraulicWarningCode,
    InletCoefficients,
    InletEquationForm,
    InvalidInputError,
    RectangularGeometry,
    calculate_inlet_control_headwater,
    flow_parameter,
    submerged_headwater,
    transition_headwater,
    unsubmerged_headwater_form_1,
    unsubmerged_headwater_form_2,
)


def test_tangent_transition_matches_endpoint_values_and_slopes() -> None:
    """The deterministic bridge is C1-continuous with its supplied branches."""
    low = 3.5
    high = 4.0
    value_low = 1.1
    value_high = 1.4
    tangent_low = 0.45
    tangent_high = 0.7
    epsilon = 1e-6

    at_low = transition_headwater(low, value_low, value_high, tangent_low, tangent_high)
    at_high = transition_headwater(high, value_low, value_high, tangent_low, tangent_high)
    slope_low = (
        transition_headwater(low + epsilon, value_low, value_high, tangent_low, tangent_high) - at_low
    ) / epsilon
    slope_high = (
        at_high - transition_headwater(high - epsilon, value_low, value_high, tangent_low, tangent_high)
    ) / epsilon

    assert at_low == pytest.approx(value_low)
    assert at_high == pytest.approx(value_high)
    assert slope_low == pytest.approx(tangent_low, rel=1e-5)
    assert slope_high == pytest.approx(tangent_high, rel=1e-5)
    with pytest.raises(InvalidInputError, match="transition interval"):
        transition_headwater(3.4, value_low, value_high, tangent_low, tangent_high)


@pytest.mark.parametrize("coefficients", STANDARD_INLET_COEFFICIENTS)
def test_standard_inlet_transitions_are_monotonic_and_tangent(
    coefficients: InletCoefficients,
) -> None:
    """All catalogued inlet transitions remain monotonic and C1 at both bounds."""
    geometry = (
        CircularGeometry(diameter=1.2)
        if coefficients.shape is GeometryShape.CIRCULAR
        else RectangularGeometry(span=2.4, rise=1.2)
    )
    barrel = CulvertBarrel(
        geometry=geometry,
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.013,
        material=CONCRETE_PIPE,
        inlet_coefficients=coefficients,
    )
    discharge_per_q_star = geometry.area_full * math.sqrt(geometry.rise) / 1.811

    def dimensionless_headwater(q_star: float) -> float:
        result = calculate_inlet_control_headwater(barrel, q_star * discharge_per_q_star)
        return result.headwater_depth / geometry.rise

    values = [dimensionless_headwater(3.5 + index * 0.01) for index in range(51)]
    assert all(first <= second for first, second in pairwise(values))

    epsilon = 1e-4
    left_low = (dimensionless_headwater(3.5) - dimensionless_headwater(3.5 - epsilon)) / epsilon
    right_low = (dimensionless_headwater(3.5 + epsilon) - dimensionless_headwater(3.5)) / epsilon
    left_high = (dimensionless_headwater(4.0) - dimensionless_headwater(4.0 - epsilon)) / epsilon
    right_high = (dimensionless_headwater(4.0 + epsilon) - dimensionless_headwater(4.0)) / epsilon
    assert right_low == pytest.approx(left_low, rel=2e-3)
    assert left_high == pytest.approx(right_high, rel=2e-3)


def test_flow_parameter_calculation() -> None:
    # Q = 2.0 m³/s, Area = 1.13097 m², D = 1.2 m
    q = 2.0
    area = math.pi * (1.2**2) / 4.0
    rise = 1.2
    # q* = 1.811 * 2.0 / (area * sqrt(1.2))
    expected = (1.811 * q) / (area * math.sqrt(rise))
    assert flow_parameter(q, area, rise) == pytest.approx(expected)
    assert flow_parameter(0.0, area, rise) == 0.0

    with pytest.raises(InvalidInputError):
        flow_parameter(-1.0, area, rise)
    with pytest.raises(InvalidInputError):
        flow_parameter(q, 0.0, rise)
    with pytest.raises(InvalidInputError):
        flow_parameter(q, area, 0.0)


def test_hds5_appendix_a_worked_example_benchmarks() -> None:
    # HDS-5 (2012) printed pages A.2-A.4 worked example for Chart 34 Scale 3:
    # K = 0.0340, M = 1.5, c = 0.0496, Y = 0.53, S = 0.02, Ks = -0.5
    coeffs = InletCoefficients(
        name="Elliptical Projecting (Chart 34 Scale 3)",
        chart=34,
        scale=3,
        form=InletEquationForm.SPECIFIC_HEAD,
        k=0.0340,
        m=1.5,
        c=0.0496,
        y=0.53,
    )
    slope = 0.02

    # Unsubmerged check at q* = 2.54 with Hc/D = 0.84:
    # HWi/D = 0.84 + 0.0340 * (2.54)^1.5 - 0.5 * 0.02 = 0.84 + 0.1376 - 0.01 = 0.9676
    hwi_d_unsub = unsubmerged_headwater_form_1(
        q_star=2.54,
        hc_over_d=0.84,
        slope=slope,
        coefficients=coeffs,
    )
    assert hwi_d_unsub == pytest.approx(0.84 + 0.0340 * (2.54**1.5) - 0.01, rel=1e-5)

    # Submerged check at q* = 4.0:
    # HWi/D = 0.0496 * (4.0)^2 + 0.53 - 0.5 * 0.02 = 0.7936 + 0.53 - 0.01 = 1.3136
    hwi_d_sub = submerged_headwater(
        q_star=4.0,
        slope=slope,
        coefficients=coeffs,
    )
    assert hwi_d_sub == pytest.approx(0.0496 * 16.0 + 0.53 - 0.01, rel=1e-5)

    # Independently reproduce the submerged design-curve values tabulated on
    # printed page A.4. The publication rounds them to 1.31, 2.31, and 3.69.
    for q_star, published_value in ((4.0, 1.31), (6.0, 2.31), (8.0, 3.69)):
        calculated = submerged_headwater(q_star, slope, coeffs)
        assert calculated == pytest.approx(published_value, abs=0.0051)


def test_high_head_extension_is_calculated_but_warned() -> None:
    """The retained Type 6 fixture exposes its direct HDS-5 extrapolation."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=0.9),
        length=10.0,
        inlet_invert=100.2,
        outlet_invert=100.0,
        roughness=0.020,
        inlet_coefficients=CIRCULAR_CMP_HEADWALL,
    )

    result = calculate_inlet_control_headwater(barrel, discharge=4.63)

    assert result.headwater_depth == pytest.approx(7.195976803967568)
    assert HDS5_LABORATORY_HW_D_MAX < result.headwater_ratio < EXTREME_HEADWATER_RATIO
    assert tuple(warning.code for warning in result.warnings) == (
        HydraulicWarningCode.INLET_CONTROL_HIGH_HEAD_EXTENSION,
    )


def test_extreme_headwater_has_additional_review_warning() -> None:
    """HW/D above ten remains numeric but cannot appear ordinarily validated."""
    geometry = CircularGeometry(diameter=1.0)
    barrel = CulvertBarrel(
        geometry=geometry,
        length=50.0,
        inlet_invert=10.0,
        outlet_invert=9.0,
        roughness=0.012,
        material=CONCRETE_PIPE,
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
    )
    q_star = 16.0
    discharge = q_star * geometry.area_full * math.sqrt(geometry.rise) / 1.811

    result = calculate_inlet_control_headwater(barrel, discharge)

    assert result.headwater_ratio > EXTREME_HEADWATER_RATIO
    assert tuple(warning.code for warning in result.warnings) == (
        HydraulicWarningCode.INLET_CONTROL_HIGH_HEAD_EXTENSION,
        HydraulicWarningCode.INLET_CONTROL_EXTREME_HEADWATER,
    )


def test_unsubmerged_form_2_box_culvert() -> None:
    # Box with 90° headwall and 3/4" chamfers (Chart 10 Scale 1)
    coeffs = BOX_CONCRETE_CHAMFER_90_HEADWALL
    assert coeffs.form == 2
    # Form 2: HWi/D = K * (q*)^M
    q_star = 2.0
    expected = 0.515 * (2.0**0.667)
    assert unsubmerged_headwater_form_2(q_star, coeffs) == pytest.approx(expected)


def test_transition_zone_continuity() -> None:
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.6,
        roughness=0.012,
        material=CONCRETE_PIPE,
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
    )

    area = barrel.geometry.area_full
    rise = barrel.geometry.rise
    # Calculate discharges corresponding to q* = 3.5 and q* = 4.0
    q_35 = (3.5 * area * math.sqrt(rise)) / 1.811
    q_40 = (4.0 * area * math.sqrt(rise)) / 1.811

    eps = 1e-6
    # Left and right around q* = 3.5
    res_below_35 = calculate_inlet_control_headwater(barrel, q_35 - eps)
    res_at_35 = calculate_inlet_control_headwater(barrel, q_35)
    res_above_35 = calculate_inlet_control_headwater(barrel, q_35 + eps)

    assert res_below_35.headwater_depth == pytest.approx(res_at_35.headwater_depth, abs=1e-4)
    assert res_above_35.headwater_depth == pytest.approx(res_at_35.headwater_depth, abs=1e-4)

    # Left and right around q* = 4.0
    res_below_40 = calculate_inlet_control_headwater(barrel, q_40 - eps)
    res_at_40 = calculate_inlet_control_headwater(barrel, q_40)
    res_above_40 = calculate_inlet_control_headwater(barrel, q_40 + eps)

    assert res_below_40.headwater_depth == pytest.approx(res_at_40.headwater_depth, abs=1e-4)
    assert res_above_40.headwater_depth == pytest.approx(res_at_40.headwater_depth, abs=1e-4)

    # Monotonicity check across transition
    assert res_at_35.headwater_depth < res_at_40.headwater_depth


def test_calculate_inlet_control_unsubmerged_and_submerged_regimes() -> None:
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.5),
        length=50.0,
        inlet_invert=100.0,
        outlet_invert=99.0,
        roughness=0.013,
        material=CONCRETE_PIPE,
    )

    # Low flow -> Unsubmerged
    res_low = calculate_inlet_control_headwater(barrel, discharge=1.5)
    assert res_low.regime == FlowRegime.INLET_CONTROL_UNSUBMERGED
    assert res_low.critical_depth is not None
    assert res_low.critical_depth > 0.0
    assert res_low.specific_energy is not None
    assert res_low.headwater_elevation == pytest.approx(100.0 + res_low.headwater_depth)

    # Very high flow -> Submerged orifice
    res_high = calculate_inlet_control_headwater(barrel, discharge=15.0)
    assert res_high.regime == FlowRegime.INLET_CONTROL_SUBMERGED
    assert res_high.headwater_depth > 1.2 * barrel.geometry.rise
    assert res_high.headwater_elevation == pytest.approx(100.0 + res_high.headwater_depth)


def test_mitered_inlet_positive_slope_correction() -> None:
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.0),
        length=20.0,
        inlet_invert=10.0,
        outlet_invert=9.0,
        roughness=0.024,
        inlet_coefficients=CIRCULAR_CMP_MITERED,
    )
    assert barrel.inlet_coefficients is not None
    assert barrel.inlet_coefficients.slope_correction == 0.7
    res = calculate_inlet_control_headwater(barrel, discharge=4.0)
    assert res.headwater_depth > 0.0


def test_box_culvert_inlet_control() -> None:
    box = CulvertBarrel(
        geometry=RectangularGeometry(span=2.4, rise=1.2),
        length=45.0,
        inlet_invert=50.0,
        outlet_invert=49.5,
        roughness=0.013,
        inlet_coefficients=BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    )
    res = calculate_inlet_control_headwater(box, discharge=3.0)
    assert res.headwater_depth > 0.0
    assert res.regime == FlowRegime.INLET_CONTROL_UNSUBMERGED


def test_inlet_coefficient_shape_mismatch_is_rejected() -> None:
    """Coefficient applicability metadata must be enforced, not merely recorded."""
    barrel = CulvertBarrel(
        geometry=RectangularGeometry(span=2.0, rise=1.0),
        length=20.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=0.013,
    )
    with pytest.raises(InvalidInputError, match="cannot be used"):
        calculate_inlet_control_headwater(barrel, 1.0, coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE)


def test_unknown_material_requires_explicit_inlet_coefficients() -> None:
    """Material roughness must not be used to invent an inlet configuration."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.0),
        length=20.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=SMOOTH_HDPE.typical_n,
        material=SMOOTH_HDPE,
    )
    with pytest.raises(InvalidInputError, match="provide inlet_coefficients"):
        calculate_inlet_control_headwater(barrel, 1.0)


def test_zero_discharge_inlet_control() -> None:
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.0),
        length=20.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=0.012,
        material=CONCRETE_PIPE,
    )
    res = calculate_inlet_control_headwater(barrel, discharge=0.0)
    assert res.headwater_depth == 0.0
    assert res.headwater_elevation == 10.0
    assert res.flow_parameter == 0.0


def test_inlet_coefficients_immutability_and_validation() -> None:
    coeffs = CIRCULAR_CONCRETE_SQUARE_EDGE
    field = "k"
    with pytest.raises(FrozenInstanceError):
        setattr(coeffs, field, 0.02)

    invalid_form = cast("InletEquationForm", 3)
    with pytest.raises(InvalidInputError):
        InletCoefficients(
            name="Bad Form",
            chart=1,
            scale=1,
            form=invalid_form,
            k=0.01,
            m=2.0,
            c=0.04,
            y=0.7,
        )

    with pytest.raises(InvalidInputError):
        InletCoefficients(
            name="Bad Shape",
            chart=1,
            scale=1,
            form=InletEquationForm.SPECIFIC_HEAD,
            k=0.01,
            m=2.0,
            c=0.04,
            y=0.7,
            shape=cast("GeometryShape", "invalid_shape"),
        )
