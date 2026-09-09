"""Culvert crossing model for multi-group road crossings."""

from collections.abc import Sequence
from dataclasses import dataclass

from ..exceptions import InvalidInputError
from .group import CulvertGroup


@dataclass(frozen=True, slots=True)
class CulvertCrossing:
    """A multi-barrel or multi-group culvert crossing sharing upstream headwater.

    A crossing consists of one or more culvert groups, each with its own size,
    shape, material, inverts, and quantity of parallel barrels.
    """

    groups: tuple[CulvertGroup, ...]

    def __init__(self, groups: Sequence[CulvertGroup]) -> None:
        if not groups:
            raise InvalidInputError("A crossing must contain at least one culvert group.")
        object.__setattr__(self, "groups", tuple(groups))

    @property
    def num_groups(self) -> int:
        """Total number of culvert groups in the crossing."""
        return len(self.groups)

    @property
    def total_barrels(self) -> int:
        """Total number of individual culvert barrels across all groups."""
        return sum(g.quantity for g in self.groups)

    @property
    def total_full_area(self) -> float:
        """Total full cross-sectional flow area of all barrels in square metres."""
        return sum(g.total_full_area for g in self.groups)

    @property
    def min_inlet_invert(self) -> float:
        """Lowest inlet invert elevation among all groups in metres."""
        return min(g.barrel.inlet_invert for g in self.groups)

    @property
    def max_inlet_invert(self) -> float:
        """Highest inlet invert elevation among all groups in metres."""
        return max(g.barrel.inlet_invert for g in self.groups)

    @property
    def min_outlet_invert(self) -> float:
        """Lowest outlet invert elevation among all groups in metres."""
        return min(g.barrel.outlet_invert for g in self.groups)

    @property
    def max_outlet_invert(self) -> float:
        """Highest outlet invert elevation among all groups in metres."""
        return max(g.barrel.outlet_invert for g in self.groups)
