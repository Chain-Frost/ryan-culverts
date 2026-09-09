"""Fixed and Manning normal-depth tailwater boundary contracts."""

import pytest

from culvert_solver import (
    FHWA_HDS5_NORMAL_DEPTH_TAILWATER,
    ManningChannelTailwater,
    TailwaterCondition,
    TailwaterMethod,
    TrapezoidalChannel,
    resolve_tailwater,
)


def _boundary() -> ManningChannelTailwater:
    return ManningChannelTailwater(
        section=TrapezoidalChannel(4.0, 3.0, 2.0),
        channel_invert_elevation=100.0,
        roughness=0.035,
        friction_slope=0.002,
    )


def test_fixed_tailwater_behavior_is_preserved() -> None:
    fixed = TailwaterCondition(101.25)
    resolved = resolve_tailwater(fixed, discharge=8.0)
    assert resolved.elevation == 101.25
    assert resolved.method is TailwaterMethod.FIXED_ELEVATION
    assert resolved.depth is None
    assert fixed.depth_at_invert(100.75) == pytest.approx(0.5)


def test_manning_tailwater_preserves_stage_and_provenance() -> None:
    resolved = _boundary().resolve(9.26246172103823)
    assert resolved.method is TailwaterMethod.MANNING_NORMAL_DEPTH
    assert resolved.depth == pytest.approx(1.2, abs=1e-7)
    assert resolved.elevation == pytest.approx(101.2, abs=1e-7)
    assert resolved.source is FHWA_HDS5_NORMAL_DEPTH_TAILWATER
    assert resolved.channel_section is not None
    assert resolved.roughness == 0.035
    assert resolved.friction_slope == 0.002
    assert resolved.normal_depth_result is not None


def test_manning_tailwater_stage_increases_with_discharge() -> None:
    low = _boundary().resolve(2.0)
    high = _boundary().resolve(10.0)
    assert low.depth is not None and high.depth is not None
    assert high.depth > low.depth
