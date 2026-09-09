"""Tests for culvert group and multi-group crossing solvers."""

import pytest

from culvert_solver.exceptions import InvalidInputError
from culvert_solver.geometry.circular import CircularGeometry
from culvert_solver.geometry.rectangular import RectangularGeometry
from culvert_solver.inlet_control.coefficients import CIRCULAR_CONCRETE_SQUARE_EDGE
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.crossing import CulvertCrossing
from culvert_solver.models.enums import ConvergenceCalculation
from culvert_solver.models.group import CulvertGroup
from culvert_solver.models.materials import CONCRETE
from culvert_solver.models.results import FlowRegime
from culvert_solver.models.tailwater import TailwaterCondition
from culvert_solver.solver.crossing import (
    solve_barrel_discharge_for_headwater,
    solve_crossing_hydraulics,
)
from culvert_solver.solver.group import solve_group_hydraulics


def test_solve_group_hydraulics() -> None:
    """Verify solve_group_hydraulics divides flow equally across N barrels."""
    geom = CircularGeometry.from_mm(diameter_mm=1200.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )
    group = CulvertGroup(barrel=barrel, quantity=3)
    total_q = 6.0

    res = solve_group_hydraulics(
        group=group,
        total_discharge=total_q,
        tailwater=10.0,
    )

    assert res.total_discharge == pytest.approx(6.0)
    assert res.barrel_discharge == pytest.approx(2.0)
    assert res.barrel_result.discharge == pytest.approx(2.0)
    assert res.barrel_result.headwater_elevation > 10.0


def test_solve_barrel_discharge_for_headwater() -> None:
    """Verify single barrel discharge solver from target headwater elevation."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=20.0,
        outlet_invert=19.0,
        roughness=0.013,
        material=CONCRETE,
    )
    target_hw = 21.2
    tw = 19.0

    q_solved = solve_barrel_discharge_for_headwater(
        barrel=barrel,
        headwater_elevation=target_hw,
        tailwater=tw,
    )
    assert q_solved > 0

    # Invert back to confirm headwater matches target
    group = CulvertGroup(barrel=barrel, quantity=1)
    g_res = solve_group_hydraulics(group=group, total_discharge=q_solved, tailwater=tw)
    assert g_res.barrel_result.headwater_elevation == pytest.approx(target_hw, abs=1e-4)


def test_single_group_crossing() -> None:
    """Verify single-group crossing uses fast-path and matches group solver."""
    geom = RectangularGeometry.from_mm(span_mm=2400.0, rise_mm=1800.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=30.0,
        inlet_invert=50.0,
        outlet_invert=49.5,
        roughness=0.013,
        material=CONCRETE,
    )
    group = CulvertGroup(barrel=barrel, quantity=2)
    crossing = CulvertCrossing(groups=[group])

    total_q = 8.0
    tw = 49.5

    c_res = solve_crossing_hydraulics(crossing=crossing, total_discharge=total_q, tailwater=tw)
    g_res = solve_group_hydraulics(group=group, total_discharge=total_q, tailwater=tw)

    assert c_res.headwater_elevation == pytest.approx(
        g_res.barrel_result.headwater_elevation, abs=1e-6
    )
    assert c_res.total_discharge == pytest.approx(total_q)
    assert len(c_res.group_results) == 1
    assert c_res.group_results[0].barrel_discharge == pytest.approx(4.0)


def test_multi_group_crossing_equal_sharing() -> None:
    """Verify crossing with two identical groups splits flow 50/50."""
    geom = CircularGeometry.from_mm(diameter_mm=1200.0)
    b1 = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=100.0,
        outlet_invert=99.0,
        roughness=0.012,
        material=CONCRETE,
        inlet_coefficients=CIRCULAR_CONCRETE_SQUARE_EDGE,
    )
    g1 = CulvertGroup(barrel=b1, quantity=2)
    g2 = CulvertGroup(barrel=b1, quantity=2)
    crossing = CulvertCrossing(groups=[g1, g2])

    total_q = 8.0
    tw = 99.0

    c_res = solve_crossing_hydraulics(crossing=crossing, total_discharge=total_q, tailwater=tw)

    assert c_res.total_discharge == pytest.approx(total_q)
    assert len(c_res.group_results) == 2
    # Each group has 2 barrels, total 4 identical barrels, each carrying 2.0 m3/s
    assert c_res.group_results[0].total_discharge == pytest.approx(4.0, abs=1e-3)
    assert c_res.group_results[1].total_discharge == pytest.approx(4.0, abs=1e-3)
    assert c_res.group_results[0].barrel_discharge == pytest.approx(2.0, abs=1e-3)
    assert c_res.group_results[1].barrel_discharge == pytest.approx(2.0, abs=1e-3)
    assert c_res.headwater_convergence is not None
    assert c_res.headwater_convergence.calculation is ConvergenceCalculation.CROSSING_HEADWATER
    assert c_res.headwater_convergence.result.root == c_res.headwater_elevation
    for group_result in c_res.group_results:
        assert group_result.discharge_convergence is not None
        assert (
            group_result.discharge_convergence.calculation
            is ConvergenceCalculation.BARREL_DISCHARGE
        )
        assert group_result.discharge_convergence.result.root == pytest.approx(
            group_result.barrel_discharge
        )


def test_multi_group_crossing_different_inverts() -> None:
    """Verify multi-group crossing where one group has a higher relief invert."""
    geom1 = CircularGeometry.from_mm(diameter_mm=1000.0)
    # Primary low-flow barrel: invert = 10.0 m
    b1 = CulvertBarrel(
        geometry=geom1,
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )
    g1 = CulvertGroup(barrel=b1, quantity=1)

    geom2 = RectangularGeometry.from_mm(span_mm=2000.0, rise_mm=1500.0)
    # Overflow relief box: invert = 11.2 m
    b2 = CulvertBarrel(
        geometry=geom2,
        length=40.0,
        inlet_invert=11.2,
        outlet_invert=10.7,
        roughness=0.013,
        material=CONCRETE,
    )
    g2 = CulvertGroup(barrel=b2, quantity=1)

    crossing = CulvertCrossing(groups=[g1, g2])
    tw = TailwaterCondition(elevation=9.5)

    # 1. Very low flow: should not reach relief culvert invert (11.2 m)
    low_q = 0.5
    c_res_low = solve_crossing_hydraulics(crossing=crossing, total_discharge=low_q, tailwater=tw)
    assert c_res_low.headwater_elevation < 11.2
    assert c_res_low.group_results[0].total_discharge == pytest.approx(low_q, abs=1e-4)
    assert c_res_low.group_results[1].total_discharge == pytest.approx(0.0, abs=1e-4)
    inactive = c_res_low.group_results[1].barrel_result
    assert inactive.discharge == 0.0
    assert inactive.velocity_outlet == 0.0
    assert inactive.regime == FlowRegime.INACTIVE
    assert inactive.outlet_control_losses is None
    assert inactive.full_flow_losses is None
    assert inactive.profile is None
    assert not inactive.convergence
    assert c_res_low.group_results[1].discharge_convergence is None

    # 2. High flow: headwater rises above 11.2 m and activates relief box
    high_q = 6.0
    c_res_high = solve_crossing_hydraulics(crossing=crossing, total_discharge=high_q, tailwater=tw)
    assert c_res_high.headwater_elevation > 11.2
    q1 = c_res_high.group_results[0].total_discharge
    q2 = c_res_high.group_results[1].total_discharge
    assert q1 > 0
    assert q2 > 0
    assert (q1 + q2) == pytest.approx(high_q, abs=1e-3)


def test_crossing_validation_errors() -> None:
    """Verify input validation on crossing solver."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )
    group = CulvertGroup(barrel=barrel, quantity=1)
    crossing = CulvertCrossing(groups=[group])

    with pytest.raises(InvalidInputError, match="crossing must be an instance"):
        solve_crossing_hydraulics(
            crossing="not a crossing",  # type: ignore[arg-type]
            total_discharge=1.0,
            tailwater=9.5,
        )

    with pytest.raises(InvalidInputError, match="total_discharge must be strictly positive"):
        solve_crossing_hydraulics(crossing=crossing, total_discharge=0.0, tailwater=9.5)
