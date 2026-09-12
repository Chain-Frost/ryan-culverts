"""Culvert group domain model for parallel identical barrels."""

from dataclasses import dataclass

from .._validation import positive_integer
from .barrel import CulvertBarrel


@dataclass(frozen=True, slots=True)
class CulvertGroup:
    """Hydraulically identical parallel barrels represented with equal barrel flow.

    For ``quantity > 1``, solvers divide total group discharge equally between barrels.
    This representative-barrel model is intended for total-flow calculations under
    sufficiently uniform approach conditions; it does not establish exact barrel-specific
    discharge or velocity under nonuniform approach flow or depressed-barrel conditions.
    """

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
