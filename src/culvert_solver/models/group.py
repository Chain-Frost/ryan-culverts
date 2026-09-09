"""Culvert group domain model for parallel identical barrels."""

from dataclasses import dataclass

from .._validation import positive_integer
from .barrel import CulvertBarrel


@dataclass(frozen=True, slots=True)
class CulvertGroup:
    """A collection of hydraulically identical parallel barrels."""

    barrel: CulvertBarrel
    quantity: int = 1

    def __post_init__(self) -> None:
        q_val: int = positive_integer(self.quantity, "quantity")
        object.__setattr__(self, "quantity", q_val)

    @property
    def total_full_area(self) -> float:
        """Total cross-sectional flow area of all barrels in the group in square metres."""
        return self.barrel.geometry.area_full * self.quantity

    @property
    def total_span(self) -> float:
        """Combined nominal horizontal span of all barrels in the group in metres."""
        return self.barrel.geometry.span * self.quantity
