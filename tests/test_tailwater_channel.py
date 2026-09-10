"""Fixed and Manning normal-depth tailwater boundary contracts."""

import pytest

from culvert_solver import (
    FHWA_HDS5_NORMAL_DEPTH_TAILWATER,
    ManningChannelTailwater,
    SourceReference,
    TailwaterCondition,
    TailwaterMethod,
    TrapezoidalChannel,
    resolve_tailwater,
)

PROJECT_SOURCE = SourceReference(
    source_id="TEST-PROJECT-DRAINAGE",
    publication="Project drainage report",
    edition="Revision A",
    locator="Receiving channel parameters",
    url=None,
    applicability="Test fixture only.",
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
    boundary = ManningChannelTailwater(
        section=TrapezoidalChannel(4.0, 3.0, 2.0),
        channel_invert_elevation=100.0,
        roughness=0.035,
        friction_slope=0.002,
        roughness_source=PROJECT_SOURCE,
        slope_source=PROJECT_SOURCE,
        geometry_source=PROJECT_SOURCE,
        channel_invert_source=PROJECT_SOURCE,
    )
    resolved = boundary.resolve(9.26246172103823)
    assert resolved.method is TailwaterMethod.MANNING_NORMAL_DEPTH
    assert resolved.depth == pytest.approx(1.2, abs=1e-7)
    assert resolved.elevation == pytest.approx(101.2, abs=1e-7)
    assert resolved.method_source is FHWA_HDS5_NORMAL_DEPTH_TAILWATER
    assert resolved.roughness_source is PROJECT_SOURCE
    assert resolved.slope_source is PROJECT_SOURCE
    assert resolved.geometry_source is PROJECT_SOURCE
    assert resolved.channel_invert_source is PROJECT_SOURCE
    assert resolved.channel_section is not None
    assert resolved.roughness == 0.035
    assert resolved.friction_slope == 0.002
    assert resolved.normal_depth_result is not None


def test_explicit_method_source_is_retained() -> None:
    boundary = ManningChannelTailwater(
        section=TrapezoidalChannel(4.0, 3.0, 2.0),
        channel_invert_elevation=100.0,
        roughness=0.035,
        friction_slope=0.002,
        method_source=PROJECT_SOURCE,
    )
    assert boundary.method_source is PROJECT_SOURCE
    assert boundary.resolve(2.0).method_source is PROJECT_SOURCE


def test_manning_tailwater_stage_increases_with_discharge() -> None:
    low = _boundary().resolve(2.0)
    high = _boundary().resolve(10.0)
    assert low.depth is not None and high.depth is not None
    assert high.depth > low.depth
