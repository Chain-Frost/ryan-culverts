"""Phase 10: Performance benchmarks, scalar equivalence, and rapid evaluation tests.

Validates the Phase 10 requirements from Section 10 and Section 17, item 18 of the
work plan:
- Scalar result equivalence
- Monotonicity where physically expected
- Deterministic repeated runs
- Correct handling of regime changes over rating curves
- Reproducibility across crossing group permutations
- Performance benchmarks without weakening numerical correctness.
"""

import time

import pytest

from culvert_solver.geometry.circular import CircularGeometry
from culvert_solver.geometry.rectangular import RectangularGeometry
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.crossing import CulvertCrossing
from culvert_solver.models.group import CulvertGroup
from culvert_solver.models.materials import CONCRETE
from culvert_solver.models.results import FlowRegime
from culvert_solver.models.tailwater import TailwaterCondition
from culvert_solver.solver.barrel import solve_barrel_hydraulics
from culvert_solver.solver.crossing import solve_crossing_hydraulics
from culvert_solver.solver.rating_curve import (
    generate_barrel_rating_curve,
    generate_crossing_rating_curve,
    generate_discharge_range,
)


def test_scalar_result_equivalence() -> None:
    """Verify rating curve points are equivalent to independent scalar solver calls."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=25.0,
        inlet_invert=10.0,
        outlet_invert=9.75,
        roughness=0.013,
        material=CONCRETE,
    )
    tw = TailwaterCondition(elevation=9.75)
    discharges = generate_discharge_range(0.2, 3.0, num_points=10)

    # 1. Batch rating curve
    rc = generate_barrel_rating_curve(barrel=barrel, discharges=discharges, tailwater=tw)

    # 2. Individual scalar calls
    for pt in rc.points:
        scalar = solve_barrel_hydraulics(barrel=barrel, discharge=pt.discharge, tailwater=tw)
        assert pt.headwater_elevation == pytest.approx(scalar.headwater_elevation, rel=1e-12)
        assert pt.headwater_depth == pytest.approx(scalar.headwater_depth, rel=1e-12)
        assert pt.tailwater_elevation == pytest.approx(scalar.tailwater_elevation, rel=1e-12)
        assert pt.outlet_velocity == pytest.approx(scalar.velocity_outlet, rel=1e-12)
        assert pt.control_type == scalar.control_type
        assert pt.regime == scalar.regime


def test_crossing_scalar_equivalence() -> None:
    """Verify crossing rating curve points match independent crossing solver calls."""
    geom1 = CircularGeometry.from_mm(diameter_mm=900.0)
    b1 = CulvertBarrel(
        geometry=geom1,
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.013,
        material=CONCRETE,
    )
    g1 = CulvertGroup(barrel=b1, quantity=2)

    geom2 = RectangularGeometry.from_mm(span_mm=1800.0, rise_mm=1200.0)
    b2 = CulvertBarrel(
        geometry=geom2,
        length=30.0,
        inlet_invert=10.4,
        outlet_invert=10.1,
        roughness=0.013,
        material=CONCRETE,
    )
    g2 = CulvertGroup(barrel=b2, quantity=1)

    crossing = CulvertCrossing(groups=[g1, g2])
    tw = TailwaterCondition(elevation=9.7)
    discharges = (0.5, 2.0, 4.5)

    rc = generate_crossing_rating_curve(crossing=crossing, discharges=discharges, tailwater=tw)

    for pt in rc.points:
        scalar = solve_crossing_hydraulics(
            crossing=crossing, total_discharge=pt.discharge, tailwater=tw
        )
        assert pt.headwater_elevation == pytest.approx(scalar.headwater_elevation, rel=1e-9)
        assert pt.headwater_depth == pytest.approx(
            scalar.headwater_elevation - crossing.min_inlet_invert, rel=1e-9
        )


def test_deterministic_repeated_runs() -> None:
    """Verify repeated runs produce bit-exact identical numerical results without state drift."""
    geom = CircularGeometry.from_mm(diameter_mm=1200.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=20.0,
        outlet_invert=19.5,
        roughness=0.012,
        material=CONCRETE,
    )
    tw = 19.5
    q = 2.5

    baseline = solve_barrel_hydraulics(barrel, q, tw)
    for _ in range(30):
        run = solve_barrel_hydraulics(barrel, q, tw)
        assert run.headwater_elevation == baseline.headwater_elevation
        assert run.headwater_depth == baseline.headwater_depth
        assert run.velocity_outlet == baseline.velocity_outlet
        assert run.regime == baseline.regime
        assert run.control_type == baseline.control_type


def test_reproducibility_across_group_permutations() -> None:
    """Verify crossing headwater solution is invariant under permutation of culvert groups."""
    geom1 = CircularGeometry.from_mm(diameter_mm=900.0)
    b1 = CulvertBarrel(
        geometry=geom1,
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.013,
        material=CONCRETE,
    )
    g1 = CulvertGroup(barrel=b1, quantity=2)

    geom2 = RectangularGeometry.from_mm(span_mm=1500.0, rise_mm=1000.0)
    b2 = CulvertBarrel(
        geometry=geom2,
        length=30.0,
        inlet_invert=10.5,
        outlet_invert=10.2,
        roughness=0.013,
        material=CONCRETE,
    )
    g2 = CulvertGroup(barrel=b2, quantity=1)

    cr_forward = CulvertCrossing(groups=[g1, g2])
    cr_reverse = CulvertCrossing(groups=[g2, g1])

    tw = 9.7
    for q in (1.0, 3.0, 5.0):
        res_fwd = solve_crossing_hydraulics(cr_forward, q, tw)
        res_rev = solve_crossing_hydraulics(cr_reverse, q, tw)
        assert res_fwd.headwater_elevation == pytest.approx(res_rev.headwater_elevation, abs=1e-5)


def test_rating_curve_regime_changes_continuity() -> None:
    """Verify smooth monotonic headwater progression across regimes.

    Spans unsubmerged, transition, and submerged regimes without discontinuities.
    """
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=20.0,
        inlet_invert=100.0,
        outlet_invert=99.6,
        roughness=0.013,
        material=CONCRETE,
    )
    tw = 99.6
    # Broad discharge sweep spanning unsubmerged (q* < 3.5) to submerged (q* > 4.0)
    discharges = generate_discharge_range(0.2, 5.0, num_points=25)

    rc = generate_barrel_rating_curve(barrel, discharges, tw)
    regimes_encountered = {pt.regime for pt in rc.points}

    # Verify that multiple regimes are traversed
    assert FlowRegime.INLET_CONTROL_UNSUBMERGED in regimes_encountered
    assert FlowRegime.INLET_CONTROL_SUBMERGED in regimes_encountered

    # Verify strictly monotonic headwater elevation across regime boundaries
    for i in range(len(rc.points) - 1):
        assert rc.points[i].headwater_elevation < rc.points[i + 1].headwater_elevation


def test_single_barrel_performance_benchmark() -> None:
    """Benchmark single barrel evaluation throughput (< 0.6 ms per evaluation)."""
    geom = CircularGeometry.from_mm(diameter_mm=1000.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.013,
        material=CONCRETE,
    )
    tw = 9.7

    n_evals = 200
    t0 = time.perf_counter()
    for _ in range(n_evals):
        solve_barrel_hydraulics(barrel, 2.0, tw)
    elapsed = time.perf_counter() - t0
    ms_per_eval = (elapsed / n_evals) * 1000.0

    # Temporary environment-sensitive ceiling pending the reproducible CS-007 benchmark.
    assert ms_per_eval < 0.6, f"Single barrel evaluation too slow: {ms_per_eval:.3f} ms/eval"


def test_rating_curve_performance_benchmark() -> None:
    """Benchmark rating curve generation (< 15 ms for 30 points)."""
    geom = RectangularGeometry.from_mm(span_mm=2000.0, rise_mm=1200.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=25.0,
        inlet_invert=50.0,
        outlet_invert=49.75,
        roughness=0.013,
        material=CONCRETE,
    )
    discharges = generate_discharge_range(0.5, 6.0, num_points=30)
    tw = 49.75

    t0 = time.perf_counter()
    rc = generate_barrel_rating_curve(barrel, discharges, tw)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert len(rc.points) == 30
    assert elapsed_ms < 15.0, f"Rating curve generation too slow: {elapsed_ms:.2f} ms"
