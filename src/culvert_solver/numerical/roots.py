"""Bracket-preserving bisection and Brent scalar root solvers."""

import math
from collections.abc import Callable
from dataclasses import dataclass

from .._validation import finite, positive_integer
from ..exceptions import ConvergenceError, InvalidInputError
from .tolerances import RootTolerances

_DEFAULT_TOLERANCES = RootTolerances()


def _safe_midpoint(a: float, b: float) -> float:
    """Return the midpoint without overflowing opposite-sign finite bounds."""
    return a + (b - a) / 2.0 if (a < 0) == (b < 0) else a / 2.0 + b / 2.0


@dataclass(frozen=True, slots=True)
class RootResult:
    """Converged root and signed residual, in the caller's canonical units.

    Iterations count midpoint evaluations; endpoint evaluation is excluded.
    The bracket contains the root for a continuous supplied function.
    """

    root: float
    residual: float
    bracket: tuple[float, float]
    iterations: int


def solve_bracketed(
    function: Callable[[float], float],
    lower: float,
    upper: float,
    *,
    tolerances: RootTolerances = _DEFAULT_TOLERANCES,
    max_iterations: int = 200,
) -> RootResult:
    """Solve a continuous scalar function with opposite signs at finite bounds.

    Caller owns continuity and hydraulic branch selection. This routine neither
    expands the bracket nor infers a physically admissible flow regime. Nonfinite
    function values fail immediately. User exceptions propagate unchanged.
    """
    a, b = finite(value=lower, name="lower"), finite(value=upper, name="upper")
    if a >= b:
        raise InvalidInputError("lower must be less than upper.")
    max_iterations = positive_integer(value=max_iterations, name="max_iterations")
    fa: float = finite(value=function(a), name="function(lower)")
    if fa == 0:
        return RootResult(root=a, residual=fa, bracket=(a, a), iterations=0)
    fb: float = finite(value=function(b), name="function(upper)")
    if fb == 0:
        return RootResult(root=b, residual=fb, bracket=(b, b), iterations=0)
    # Compare signs without products, which can underflow or overflow.
    if (fa < 0) == (fb < 0):
        raise InvalidInputError("Function must change sign across the bracket.")

    for iteration in range(1, max_iterations + 1):
        # Same-sign subtraction is safe; opposite-sign bounds need a split sum.
        mid: float = _safe_midpoint(a, b)
        fm: float = finite(value=function(mid), name="function(midpoint)")
        if fm == 0:
            return RootResult(mid, fm, (mid, mid), iteration)
        error_bound: float = max(mid - a, b - mid)
        x_limit: float = tolerances.x_abs + tolerances.x_rel * abs(mid)
        residual_ok: bool = tolerances.residual_abs is None or abs(fm) <= tolerances.residual_abs
        if error_bound <= x_limit and residual_ok:
            return RootResult(root=mid, residual=fm, bracket=(a, b), iterations=iteration)
        if mid == a or mid == b:
            raise ConvergenceError(
                "Floating-point resolution prevents the requested convergence.",
                bracket=(a, b),
                iterations=iteration,
            )
        if (fa < 0) == (fm < 0):
            a, fa = mid, fm
        else:
            b: float = mid
    raise ConvergenceError(
        message="Root solver exhausted its iteration limit.",
        bracket=(a, b),
        iterations=max_iterations,
    )


def solve_brent(
    function: Callable[[float], float],
    lower: float,
    upper: float,
    *,
    tolerances: RootTolerances = _DEFAULT_TOLERANCES,
    max_iterations: int = 100,
) -> RootResult:
    """Solve a continuous scalar function using Brent's method with guaranteed bracketing.

    Combines bisection, secant, and inverse quadratic interpolation for superlinear
    convergence while strictly confining the solution within the bracket.

    Parameters
    ----------
    function : Callable[[float], float]
        Continuous scalar function f(x).
    lower : float
        Lower bound of the bracket.
    upper : float
        Upper bound of the bracket, strictly greater than lower.
    tolerances : RootTolerances, default=_DEFAULT_TOLERANCES
        Convergence criteria for bracket width and residual.
    max_iterations : int, default=100
        Maximum allowed iterations, strictly positive.

    Returns
    -------
    RootResult
        Converged root, residual, enclosing bracket, and iteration count.
    """
    a, b = finite(value=lower, name="lower"), finite(value=upper, name="upper")
    if a >= b:
        raise InvalidInputError("lower must be less than upper.")
    max_iter: int = positive_integer(value=max_iterations, name="max_iterations")

    fa: float = finite(value=function(a), name="function(lower)")
    if fa == 0:
        return RootResult(root=a, residual=fa, bracket=(a, a), iterations=0)
    fb: float = finite(value=function(b), name="function(upper)")
    if fb == 0:
        return RootResult(root=b, residual=fb, bracket=(b, b), iterations=0)
    if (fa < 0) == (fb < 0):
        raise InvalidInputError("Function must change sign across the bracket.")

    if abs(fa) < abs(fb):
        a, b = b, a
        fa, fb = fb, fa

    c: float = a
    fc: float = fa
    mflag: bool = True
    d: float = 0.0

    for iteration in range(1, max_iter + 1):
        tol = tolerances.x_abs + tolerances.x_rel * abs(b)
        half_bracket = abs(b - a) / 2.0
        residual_ok = tolerances.residual_abs is None or abs(fb) <= tolerances.residual_abs

        if half_bracket <= tol and residual_ok:
            brk = (min(a, b), max(a, b))
            return RootResult(
                root=b,
                residual=fb,
                bracket=brk,
                iterations=max(1, iteration - 1),
            )

        if fa != fc and fb != fc:
            # Inverse quadratic interpolation
            s = (
                a * fb * fc / ((fa - fb) * (fa - fc))
                + b * fa * fc / ((fb - fa) * (fb - fc))
                + c * fa * fb / ((fc - fa) * (fc - fb))
            )
        else:
            # Secant method
            denominator = fb - fa
            s = a * (fb / denominator) - b * (fa / denominator)

        if not math.isfinite(s):
            s = _safe_midpoint(a, b)
            mflag = True

        # Brent's conditions to force bisection when interpolation is slow or out of bounds
        interpolation_bound = 0.75 * a + 0.25 * b
        cond1 = not (min(interpolation_bound, b) <= s <= max(interpolation_bound, b))
        cond2 = mflag and abs(s - b) >= abs(b - c) / 2.0
        cond3 = (not mflag) and abs(s - b) >= abs(c - d) / 2.0
        cond4 = mflag and abs(b - c) < tol
        cond5 = (not mflag) and abs(c - d) < tol

        if cond1 or cond2 or cond3 or cond4 or cond5:
            s = _safe_midpoint(a, b)
            mflag = True
        else:
            mflag = False

        fs = finite(value=function(s), name="function(evaluation)")
        if fs == 0:
            brk = (min(a, b), max(a, b))
            return RootResult(root=s, residual=fs, bracket=brk, iterations=iteration)

        d = c
        c = b
        fc = fb

        if (fa < 0) == (fs < 0):
            a, fa = s, fs
        else:
            b, fb = s, fs

        if abs(fa) < abs(fb):
            a, b = b, a
            fa, fb = fb, fa

        if a == b or abs(b - a) == 0.0:
            raise ConvergenceError(
                "Floating-point resolution prevents the requested convergence.",
                bracket=(min(a, b), max(a, b)),
                iterations=iteration,
            )

    raise ConvergenceError(
        message="Root solver exhausted its iteration limit.",
        bracket=(min(a, b), max(a, b)),
        iterations=max_iter,
    )
