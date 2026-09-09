"""Reproducible, non-gating wall-clock benchmark for fixed hydraulic cases."""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import statistics
import time
from collections.abc import Callable
from typing import Any

from culvert_solver.geometry.circular import CircularGeometry
from culvert_solver.geometry.rectangular import RectangularGeometry
from culvert_solver.models.barrel import CulvertBarrel
from culvert_solver.models.crossing import CulvertCrossing
from culvert_solver.models.group import CulvertGroup
from culvert_solver.models.materials import CONCRETE
from culvert_solver.solver.barrel import solve_barrel_hydraulics
from culvert_solver.solver.crossing import solve_crossing_hydraulics


def _measure(
    operation: Callable[[], object], *, iterations: int, samples: int, warmup_batches: int
) -> dict[str, float | int]:
    """Measure independent batches and return robust per-operation statistics."""
    for _ in range(warmup_batches):
        for _ in range(iterations):
            operation()

    timings: list[float] = []
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        for _ in range(samples):
            start = time.perf_counter_ns()
            for _ in range(iterations):
                operation()
            timings.append((time.perf_counter_ns() - start) / iterations / 1_000_000.0)
    finally:
        if gc_was_enabled:
            gc.enable()

    ordered = sorted(timings)
    p95_index = min(len(ordered) - 1, int(0.95 * len(ordered)))
    return {
        "iterations_per_sample": iterations,
        "samples": samples,
        "min_ms": ordered[0],
        "median_ms": statistics.median(ordered),
        "p95_ms": ordered[p95_index],
    }


def _cases() -> tuple[Callable[[], object], Callable[[], object]]:
    """Return fixed single-barrel and two-group crossing operations."""
    single_barrel = CulvertBarrel(
        geometry=CircularGeometry(diameter=1.2),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.020,
        material=CONCRETE,
    )
    circular = CulvertBarrel(
        geometry=CircularGeometry(diameter=0.9),
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.7,
        roughness=0.013,
        material=CONCRETE,
    )
    box = CulvertBarrel(
        geometry=RectangularGeometry(span=1.8, rise=1.2),
        length=30.0,
        inlet_invert=10.4,
        outlet_invert=10.1,
        roughness=0.013,
        material=CONCRETE,
    )
    crossing = CulvertCrossing([CulvertGroup(circular, quantity=2), CulvertGroup(box, quantity=1)])

    def single_operation() -> object:
        return solve_barrel_hydraulics(single_barrel, 2.0, 9.7)

    def crossing_operation() -> object:
        return solve_crossing_hydraulics(crossing, 4.5, 9.7)

    return single_operation, crossing_operation


def main() -> None:
    """Run fixed benchmarks and print machine-readable environment and timing data."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=7)
    parser.add_argument("--single-iterations", type=int, default=500)
    parser.add_argument("--crossing-iterations", type=int, default=10)
    parser.add_argument("--warmup-batches", type=int, default=2)
    args = parser.parse_args()
    if (
        min(
            args.samples,
            args.single_iterations,
            args.crossing_iterations,
            args.warmup_batches,
        )
        <= 0
    ):
        parser.error("all benchmark counts must be positive")

    single_operation, crossing_operation = _cases()
    single_before = single_operation()
    crossing_before = crossing_operation()

    results: dict[str, Any] = {
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
            "logical_cpu_count": os.cpu_count(),
            "perf_counter_resolution_seconds": time.get_clock_info("perf_counter").resolution,
        },
        "method": {
            "clock": "time.perf_counter_ns",
            "garbage_collection_during_samples": False,
            "warmup_batches": args.warmup_batches,
            "interpretation": "observational; deterministic algorithmic budgets gate tests",
        },
        "single_barrel": _measure(
            single_operation,
            iterations=args.single_iterations,
            samples=args.samples,
            warmup_batches=args.warmup_batches,
        ),
        "two_group_crossing": _measure(
            crossing_operation,
            iterations=args.crossing_iterations,
            samples=args.samples,
            warmup_batches=args.warmup_batches,
        ),
    }

    if single_operation() != single_before or crossing_operation() != crossing_before:
        raise RuntimeError("Benchmark operations changed their deterministic hydraulic results.")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
