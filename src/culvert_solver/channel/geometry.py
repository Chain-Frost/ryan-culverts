"""Prismatic open-channel geometry for uniform-flow calculations."""

import math
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .._validation import finite
from ..exceptions import InvalidInputError


@runtime_checkable
class OpenChannelSection(Protocol):
    """SI geometry contract for a prismatic open channel."""

    def area(self, depth: float) -> float:
        """Return wetted flow area in square metres."""
        ...

    def wetted_perimeter(self, depth: float) -> float:
        """Return wetted perimeter in metres."""
        ...

    def top_width(self, depth: float) -> float:
        """Return free-surface top width in metres."""
        ...


@dataclass(frozen=True, slots=True)
class RectangularChannel:
    """Open rectangular channel with vertical side walls."""

    bottom_width: float

    def __post_init__(self) -> None:
        width: float = finite(self.bottom_width, "bottom_width")
        if width <= 0.0:
            raise InvalidInputError("bottom_width must be strictly positive.")
        object.__setattr__(self, "bottom_width", width)

    def area(self, depth: float) -> float:
        return self.bottom_width * _depth(depth)

    def wetted_perimeter(self, depth: float) -> float:
        y: float = _depth(depth)
        return 0.0 if y == 0.0 else self.bottom_width + 2.0 * y

    def top_width(self, depth: float) -> float:
        _depth(depth)
        return self.bottom_width


@dataclass(frozen=True, slots=True)
class TrapezoidalChannel:
    """Open trapezoid with independent horizontal-to-vertical side slopes.

    A zero bottom width represents a triangular section when at least one side
    slope is positive.
    """

    bottom_width: float
    left_side_slope: float
    right_side_slope: float

    def __post_init__(self) -> None:
        width: float = finite(self.bottom_width, "bottom_width")
        left: float = finite(self.left_side_slope, "left_side_slope")
        right: float = finite(self.right_side_slope, "right_side_slope")
        if width < 0.0:
            raise InvalidInputError("bottom_width must be nonnegative.")
        if left < 0.0:
            raise InvalidInputError("left_side_slope must be nonnegative.")
        if right < 0.0:
            raise InvalidInputError("right_side_slope must be nonnegative.")
        if width == 0.0 and left == 0.0 and right == 0.0:
            raise InvalidInputError("A zero-width channel requires at least one positive side slope.")
        object.__setattr__(self, "bottom_width", width)
        object.__setattr__(self, "left_side_slope", left)
        object.__setattr__(self, "right_side_slope", right)

    def area(self, depth: float) -> float:
        y: float = _depth(depth)
        return self.bottom_width * y + 0.5 * (self.left_side_slope + self.right_side_slope) * y * y

    def wetted_perimeter(self, depth: float) -> float:
        y: float = _depth(depth)
        if y == 0.0:
            return 0.0
        return (
            self.bottom_width + y * math.hypot(1.0, self.left_side_slope) + y * math.hypot(1.0, self.right_side_slope)
        )

    def top_width(self, depth: float) -> float:
        y: float = _depth(depth)
        return self.bottom_width + (self.left_side_slope + self.right_side_slope) * y


def _depth(depth: float) -> float:
    value: float = finite(depth, "depth")
    if value < 0.0:
        raise InvalidInputError("depth must be nonnegative.")
    return value
