"""Separate tolerances for the independent variable and equation residual."""

from dataclasses import dataclass

from .._validation import finite
from ..exceptions import InvalidInputError


@dataclass(frozen=True, slots=True)
class RootTolerances:
    """Numerical tolerances, not engineering acceptance limits.

    ``x_abs`` has the units of the independent variable; ``x_rel`` is dimensionless.
    Optional ``residual_abs`` has the units of the supplied function. When set,
    both interval and residual criteria must pass (an exact zero always passes).
    """

    x_abs: float = 1e-10
    x_rel: float = 1e-12
    residual_abs: float | None = None

    def __post_init__(self) -> None:
        for name in ("x_abs", "x_rel"):
            value: float = finite(getattr(self, name), name)
            if value < 0:
                msg = f"{name} must be nonnegative."
                raise InvalidInputError(msg)
            object.__setattr__(self, name, value)
        if self.x_abs == 0 and self.x_rel == 0:
            msg = "At least one independent-variable tolerance must be positive."
            raise InvalidInputError(msg)
        if self.residual_abs is not None:
            value = finite(value=self.residual_abs, name="residual_abs")
            if value < 0:
                msg = "residual_abs must be nonnegative."
                raise InvalidInputError(msg)
            object.__setattr__(self, "residual_abs", value)
