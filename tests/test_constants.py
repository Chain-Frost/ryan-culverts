"""Tests for central physical constants and provenance records."""

import pytest

from culvert_solver.constants import (
    GRAVITATIONAL_ACCELERATION,
    GRAVITATIONAL_ACCELERATION_REFERENCE,
    STANDARD_WATER_DENSITY,
    STANDARD_WATER_KINEMATIC_VISCOSITY,
    STANDARD_WATER_PROPERTIES_REFERENCE,
)
from culvert_solver.references.models import SourceReference


def test_standard_gravitational_acceleration_value() -> None:
    assert pytest.approx(9.80665) == GRAVITATIONAL_ACCELERATION
    assert isinstance(GRAVITATIONAL_ACCELERATION_REFERENCE, SourceReference)
    assert "ISO-80000-3" in GRAVITATIONAL_ACCELERATION_REFERENCE.source_id
    assert GRAVITATIONAL_ACCELERATION_REFERENCE.url is not None
    assert GRAVITATIONAL_ACCELERATION_REFERENCE.url.startswith("https://")


def test_standard_water_properties_values() -> None:
    assert pytest.approx(998.2) == STANDARD_WATER_DENSITY
    assert pytest.approx(1.004e-6) == STANDARD_WATER_KINEMATIC_VISCOSITY
    assert isinstance(STANDARD_WATER_PROPERTIES_REFERENCE, SourceReference)
    assert STANDARD_WATER_PROPERTIES_REFERENCE.url is not None
    assert STANDARD_WATER_PROPERTIES_REFERENCE.url.startswith("https://")
