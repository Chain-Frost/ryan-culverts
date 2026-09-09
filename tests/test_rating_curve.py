"""Unit tests for rating curve generation for barrels and crossings."""

import math

import pytest

from culvert_solver.exceptions import InvalidInputError
from culvert_solver.geometry.circular import CircularGeometry
from culvert_solver.geometry.rectangular import RectangularGeometry
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.crossing import CulvertCrossing
from culvert_solver.models.enums import HydraulicWarningCode
from culvert_solver.models.group import CulvertGroup
from culvert_solver.models.materials import CONCRETE
from culvert_solver.models.results import FlowRegime
from culvert_solver.models.tailwater import TailwaterCondition
from culvert_solver.solver.rating_curve import (
    generate_barrel_rating_curve,
    generate_crossing_rating_curve,
    generate_discharge_range,
)


def test_generate_discharge_range() -> None:
    """Verify discharge range generation helper."""
    seq = generate_discharge_range(min_discharge=1.0, max_discharge=5.0, num_points=5)
    assert len(seq) == 5
    assert seq == (1.0, 2.0, 3.0, 4.0, 5.0)

    # Validation errors
    with pytest.raises(InvalidInputError, match="min_discharge must be strictly positive"):
        generate_discharge_range(min_discharge=0.0, max_discharge=5.0)

    with pytest.raises(InvalidInputError, match="strictly greater than min_discharge"):
        generate_discharge_range(min_discharge=5.0, max_discharge=2.0)

    with pytest.raises(InvalidInputError, match="num_points must be at least 2"):
        generate_discharge_range(min_discharge=1.0, max_discharge=5.0, num_points=1)


def test_barrel_rating_curve_monotonicity() -> None:
    """Verify rating curve points and monotonic headwater progression for a single barrel."""
    geom = CircularGeometry.from_mm(diameter_mm=1200.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=30.0,
        inlet_invert=100.0,
        outlet_invert=99.7,
        roughness=0.013,
        material=CONCRETE,
    )
    discharges = generate_discharge_range(0.2, 3.0, num_points=8)
    tw = TailwaterCondition(elevation=99.7)

    rc = generate_barrel_rating_curve(barrel=barrel, discharges=discharges, tailwater=tw)

    assert len(rc.points) == 8
    assert math.isclose(rc.min_discharge, 0.2)
    assert math.isclose(rc.max_discharge, 3.0)

    # Verify strictly monotonic headwater elevation
    for i in range(len(rc.points) - 1):
        p_cur = rc.points[i]
        p_next = rc.points[i + 1]
        assert p_cur.discharge < p_next.discharge
        assert p_cur.headwater_elevation < p_next.headwater_elevation
        assert p_cur.headwater_depth < p_next.headwater_depth
        assert p_cur.outlet_velocity > 0.0


def test_barrel_rating_curve_regime_progression() -> None:
    """Verify regime shifts from unsubmerged to submerged under steep inlet control."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    # Steep slope S0 = 0.02
    barrel = CulvertBarrel(
        geometry=geom,
        length=25.0,
        inlet_invert=50.0,
        outlet_invert=49.5,
        roughness=0.012,
        material=CONCRETE,
    )
    tw = TailwaterCondition(elevation=49.5)
    discharges = (0.3, 1.0, 1.626, 2.5)

    rc = generate_barrel_rating_curve(barrel=barrel, discharges=discharges, tailwater=tw)

    # Fixed values independently evaluated from HDS-5 A.1/A.3 and the documented
    # cubic-Hermite transition, using separate circular-section bisection at critical flow.
    assert [point.headwater_elevation for point in rc.points] == pytest.approx(
        [50.41129639578769, 50.85046073327805, 51.21952069304025, 51.98257475067179],
        abs=1e-9,
    )
    assert [point.regime for point in rc.points] == [
        FlowRegime.INLET_CONTROL_UNSUBMERGED,
        FlowRegime.INLET_CONTROL_UNSUBMERGED,
        FlowRegime.INLET_CONTROL_TRANSITION,
        FlowRegime.INLET_CONTROL_SUBMERGED,
    ]
    assert all(point.control_type == "inlet_control" for point in rc.points)


def test_crossing_rating_curve_single_group() -> None:
    """Verify rating curve for a crossing with a single multi-barrel group."""
    geom = CircularGeometry.from_mm(diameter_mm=900.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=20.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=0.013,
        material=CONCRETE,
    )
    group = CulvertGroup(barrel=barrel, quantity=2)
    crossing = CulvertCrossing(groups=[group])
    discharges = (0.5, 1.5, 3.0)
    tw = TailwaterCondition(elevation=9.8)

    rc = generate_crossing_rating_curve(crossing=crossing, discharges=discharges, tailwater=tw)

    assert len(rc.points) == 3
    assert rc.points[0].discharge == 0.5
    assert rc.points[-1].discharge == 3.0
    for pt in rc.points:
        assert pt.headwater_elevation > 10.0
        assert pt.outlet_velocity > 0.0


def test_rating_curve_retains_high_head_applicability_warning() -> None:
    """A resolved profile retains its relevant inlet-method review warning."""
    barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=0.9),
        length=10.0,
        inlet_invert=100.2,
        outlet_invert=100.0,
        roughness=0.020,
        material=CONCRETE,
    )

    curve = generate_barrel_rating_curve(
        barrel=barrel,
        discharges=(4.63,),
        tailwater=100.1,
    )

    point = curve.points[0]
    assert tuple(warning.code for warning in point.warnings) == (
        HydraulicWarningCode.INLET_CONTROL_HIGH_HEAD_EXTENSION,
    )


def test_crossing_rating_curve_multi_group() -> None:
    """Verify rating curve for a multi-group crossing with different inverts."""
    geom1 = CircularGeometry.from_mm(diameter_mm=1000.0)
    b1 = CulvertBarrel(
        geometry=geom1,
        length=35.0,
        inlet_invert=10.0,
        outlet_invert=9.65,
        roughness=0.013,
        material=CONCRETE,
    )
    g1 = CulvertGroup(barrel=b1, quantity=1)

    geom2 = RectangularGeometry.from_mm(span_mm=1800.0, rise_mm=1200.0)
    b2 = CulvertBarrel(
        geometry=geom2,
        length=35.0,
        inlet_invert=11.0,
        outlet_invert=10.65,
        roughness=0.013,
        material=CONCRETE,
    )
    g2 = CulvertGroup(barrel=b2, quantity=1)

    crossing = CulvertCrossing(groups=[g1, g2])
    tw = TailwaterCondition(elevation=9.65)
    discharges = (0.5, 2.0, 5.0)

    rc = generate_crossing_rating_curve(crossing=crossing, discharges=discharges, tailwater=tw)

    assert len(rc.points) == 3
    assert rc.points[0].headwater_elevation < rc.points[1].headwater_elevation
    assert rc.points[1].headwater_elevation < rc.points[2].headwater_elevation

    # At low discharge (0.5), headwater should be below relief barrel invert (11.0)
    assert rc.points[0].headwater_elevation < 11.0

    # At high discharge (5.0), headwater must activate relief barrel
    assert rc.points[2].headwater_elevation > 11.0
    assert rc.points[2].regime == FlowRegime.MIXED

    reversed_curve = generate_crossing_rating_curve(
        crossing=CulvertCrossing(groups=[g2, g1]),
        discharges=discharges,
        tailwater=tw,
    )
    assert [point.regime for point in reversed_curve.points] == [
        point.regime for point in rc.points
    ]
    assert [point.control_type for point in reversed_curve.points] == [
        point.control_type for point in rc.points
    ]


def test_rating_curve_validation_errors() -> None:
    """Verify input validation for barrel and crossing rating curves."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=20.0,
        inlet_invert=10.0,
        outlet_invert=9.8,
        roughness=0.013,
        material=CONCRETE,
    )
    group = CulvertGroup(barrel=barrel, quantity=1)
    crossing = CulvertCrossing(groups=[group])
    tw = 9.8

    # Empty discharges
    with pytest.raises(InvalidInputError, match="must contain at least one value"):
        generate_barrel_rating_curve(barrel=barrel, discharges=[], tailwater=tw)

    with pytest.raises(InvalidInputError, match="must contain at least one value"):
        generate_crossing_rating_curve(crossing=crossing, discharges=[], tailwater=tw)

    # Non-positive discharge
    with pytest.raises(InvalidInputError, match="must be strictly positive"):
        generate_barrel_rating_curve(barrel=barrel, discharges=[1.0, -0.5], tailwater=tw)

    with pytest.raises(InvalidInputError, match="must be strictly positive"):
        generate_crossing_rating_curve(crossing=crossing, discharges=[0.0], tailwater=tw)
