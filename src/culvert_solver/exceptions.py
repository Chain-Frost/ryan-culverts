"""Typed failure boundaries for numerical and model validation."""


class InvalidInputError(ValueError):
    """An input violates the documented domain of a calculation."""


class ConvergenceError(RuntimeError):
    """A bracketed calculation exhausted iterations or floating-point resolution."""

    def __init__(self, message: str, *, bracket: tuple[float, float], iterations: int) -> None:
        super().__init__(message)
        self.bracket: tuple[float, float] = bracket
        self.iterations: int = iterations


class UnvalidatedFallbackWarning(UserWarning):
    """A solver parameter fell back to a generic default outside validated bounds."""
