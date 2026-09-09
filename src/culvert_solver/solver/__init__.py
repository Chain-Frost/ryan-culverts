"""Culvert hydraulic solver modules."""

from .barrel import solve_barrel_hydraulics
from .crossing import solve_crossing_hydraulics
from .group import solve_group_hydraulics
from .rating_curve import (
    RatingCurvePoint,
    RatingCurveResult,
    generate_barrel_rating_curve,
    generate_crossing_rating_curve,
    generate_discharge_range,
)
from .regime import determine_governing_regime

__all__ = [
    "RatingCurvePoint",
    "RatingCurveResult",
    "determine_governing_regime",
    "generate_barrel_rating_curve",
    "generate_crossing_rating_curve",
    "generate_discharge_range",
    "solve_barrel_hydraulics",
    "solve_crossing_hydraulics",
    "solve_group_hydraulics",
]
