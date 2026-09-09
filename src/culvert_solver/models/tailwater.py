"""Downstream tailwater boundary condition model."""

from dataclasses import dataclass

from .._validation import finite


@dataclass(frozen=True, slots=True)
class TailwaterCondition:
    """Downstream tailwater boundary specified as an absolute water surface elevation."""

    elevation: float

    def __post_init__(self) -> None:
        elev: float = finite(self.elevation, "elevation")
        object.__setattr__(self, "elevation", elev)

    def depth_at_invert(self, outlet_invert: float) -> float:
        """Derive tailwater depth at a specific barrel outlet invert (metres).

        Returns 0.0 if the tailwater elevation is at or below the outlet invert.
        """
        z_out: float = finite(outlet_invert, "outlet_invert")
        return max(0.0, self.elevation - z_out)
