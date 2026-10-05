"""Reusable hydraulic uncertainty contracts and low-level evaluation primitives."""

from dataclasses import dataclass, replace
from enum import StrEnum
from random import Random

from ._validation import finite
from .constants import GRAVITATIONAL_ACCELERATION
from .exceptions import ConvergenceError, InvalidInputError
from .inlet_control.coefficients import InletCoefficients
from .models.barrel import CulvertBarrel
from .models.enums import HydraulicResultStatus, RoughnessSelectionBasis
from .models.results import BarrelHydraulicResult, ConvergenceRecord, HydraulicWarning
from .models.tailwater import TailwaterInput
from .outlet_control.losses import EntranceLossCoefficient
from .references.models import SourceReference
from .solver.barrel import solve_barrel_hydraulics
from .solver.config import SolverConfiguration


class HydraulicUncertaintyParameter(StrEnum):
    """Hydraulic inputs currently supported by the uncertainty evaluation primitive."""

    MANNING_ROUGHNESS = "manning_roughness"
    DISCHARGE = "discharge"
    TAILWATER_ELEVATION = "tailwater_elevation"
    ENTRANCE_LOSS_COEFFICIENT = "entrance_loss_coefficient"

    @property
    def unit(self) -> "HydraulicUncertaintyUnit":
        """Return the canonical SI unit for this parameter."""
        return _PARAMETER_UNITS[self]


class HydraulicUncertaintyUnit(StrEnum):
    """Canonical units carried by public uncertainty values."""

    DIMENSIONLESS = "1"
    METRE = "m"
    CUBIC_METRE_PER_SECOND = "m3/s"


_PARAMETER_UNITS: dict[HydraulicUncertaintyParameter, HydraulicUncertaintyUnit] = {
    HydraulicUncertaintyParameter.MANNING_ROUGHNESS: HydraulicUncertaintyUnit.DIMENSIONLESS,
    HydraulicUncertaintyParameter.DISCHARGE: HydraulicUncertaintyUnit.CUBIC_METRE_PER_SECOND,
    HydraulicUncertaintyParameter.TAILWATER_ELEVATION: HydraulicUncertaintyUnit.METRE,
    HydraulicUncertaintyParameter.ENTRANCE_LOSS_COEFFICIENT: HydraulicUncertaintyUnit.DIMENSIONLESS,
}


@dataclass(frozen=True, slots=True)
class ParameterBounds:
    """Inclusive finite lower and upper bounds in an explicit unit."""

    lower: float
    upper: float
    unit: HydraulicUncertaintyUnit

    def __post_init__(self) -> None:
        lower = finite(self.lower, "lower")
        upper = finite(self.upper, "upper")
        try:
            unit = HydraulicUncertaintyUnit(self.unit)
        except (TypeError, ValueError) as exc:
            msg = "unit must be a HydraulicUncertaintyUnit."
            raise InvalidInputError(msg) from exc
        if upper < lower:
            msg = "upper must be greater than or equal to lower."
            raise InvalidInputError(msg)
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)
        object.__setattr__(self, "unit", unit)


@dataclass(frozen=True, slots=True)
class BoundedParameterSpec:
    """Deterministic bounded uncertainty specification without a probability model."""

    parameter: HydraulicUncertaintyParameter
    bounds: ParameterBounds
    source: SourceReference

    def __post_init__(self) -> None:
        parameter = _validated_parameter(self.parameter)
        _validate_bounds(parameter, self.bounds)
        _validate_source(self.source)
        object.__setattr__(self, "parameter", parameter)


@dataclass(frozen=True, slots=True)
class UniformParameterSpec:
    """Uniform probability specification with explicit bounds and provenance."""

    parameter: HydraulicUncertaintyParameter
    bounds: ParameterBounds
    source: SourceReference

    def __post_init__(self) -> None:
        parameter = _validated_parameter(self.parameter)
        _validate_bounds(parameter, self.bounds)
        _validate_source(self.source)
        object.__setattr__(self, "parameter", parameter)


@dataclass(frozen=True, slots=True)
class SampledParameter:
    """One sampled hydraulic input with identity, SI unit and uncertainty source."""

    parameter: HydraulicUncertaintyParameter
    value: float
    unit: HydraulicUncertaintyUnit
    source: SourceReference

    def __post_init__(self) -> None:
        parameter = _validated_parameter(self.parameter)
        value = finite(self.value, "value")
        try:
            unit = HydraulicUncertaintyUnit(self.unit)
        except (TypeError, ValueError) as exc:
            msg = "unit must be a HydraulicUncertaintyUnit."
            raise InvalidInputError(msg) from exc
        if unit is not parameter.unit:
            msg = f"{parameter.value} uncertainty values must use unit {parameter.unit.value!r}."
            raise InvalidInputError(msg)
        _validate_parameter_value(parameter, value)
        _validate_source(self.source)
        object.__setattr__(self, "parameter", parameter)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "unit", unit)


@dataclass(frozen=True, slots=True)
class HydraulicSample:
    """One low-level evaluation sample containing unique hydraulic parameters."""

    parameters: tuple[SampledParameter, ...]
    sample_id: str | None = None

    def __post_init__(self) -> None:
        parameters = tuple(self.parameters)
        for item in parameters:
            if not isinstance(item, SampledParameter):  # pyright: ignore[reportUnnecessaryIsInstance]
                msg = "parameters must contain only SampledParameter values."
                raise InvalidInputError(msg)
        identities = tuple(item.parameter for item in parameters)
        if len(set(identities)) != len(identities):
            msg = "A HydraulicSample cannot contain the same parameter more than once."
            raise InvalidInputError(msg)
        if self.sample_id is not None and not self.sample_id.strip():
            msg = "sample_id must be nonempty text when provided."
            raise InvalidInputError(msg)
        object.__setattr__(self, "parameters", parameters)


class EvaluationFailureKind(StrEnum):
    """Expected deterministic solver failure categories retained by an evaluation."""

    INVALID_INPUT = "invalid_input"
    CONVERGENCE = "convergence"


@dataclass(frozen=True, slots=True)
class HydraulicEvaluationFailure:
    """Expected solver failure retained instead of silently dropping the sample."""

    kind: EvaluationFailureKind
    exception_type: str
    message: str
    bracket: tuple[float, float] | None = None
    iterations: int | None = None


@dataclass(frozen=True, slots=True)
class BarrelUncertaintyEvaluation:
    """Outcome of evaluating one sample through the public barrel solver."""

    sample: HydraulicSample
    result: BarrelHydraulicResult | None = None
    failure: HydraulicEvaluationFailure | None = None

    def __post_init__(self) -> None:
        if (self.result is None) == (self.failure is None):
            msg = "Exactly one of result or failure must be supplied."
            raise InvalidInputError(msg)

    @property
    def status(self) -> HydraulicResultStatus | None:
        """Hydraulic result status, or None when the deterministic solve failed."""
        return None if self.result is None else self.result.status

    @property
    def warnings(self) -> tuple[HydraulicWarning, ...]:
        """Structured hydraulic warnings retained from a successful solve."""
        return () if self.result is None else self.result.warnings

    @property
    def convergence(self) -> tuple[ConvergenceRecord, ...]:
        """Numerical convergence evidence retained from a successful solve."""
        return () if self.result is None else self.result.convergence


def sample_bounded_parameter(
    spec: BoundedParameterSpec,
    *,
    count: int,
) -> tuple[HydraulicSample, ...]:
    """Return an inclusive evenly spaced deterministic sweep over the stated bounds.

    A single requested sample is placed at the midpoint. Two or more samples include
    both stated bounds exactly. No probability distribution is implied.
    """
    sample_count = _positive_count(count)
    lower = spec.bounds.lower
    upper = spec.bounds.upper
    if sample_count == 1:
        values = ((lower + upper) / 2.0,)
    else:
        step = (upper - lower) / (sample_count - 1)
        values = tuple(lower + step * index for index in range(sample_count))
        values = (*values[:-1], upper)
    return tuple(
        HydraulicSample(
            parameters=(
                SampledParameter(
                    parameter=spec.parameter,
                    value=value,
                    unit=spec.bounds.unit,
                    source=spec.source,
                ),
            ),
            sample_id=f"{spec.parameter.value}:bounded:{index}",
        )
        for index, value in enumerate(values)
    )


def sample_uniform_parameter(
    spec: UniformParameterSpec,
    *,
    count: int,
    seed: int,
) -> tuple[HydraulicSample, ...]:
    """Return reproducible uniform samples using an explicit local random seed."""
    sample_count = _positive_count(count)
    if not isinstance(seed, int) or isinstance(seed, bool):
        msg = "seed must be an integer."
        raise InvalidInputError(msg)
    generator = Random(seed)  # noqa: S311 - deterministic engineering sampling, not cryptography.
    return tuple(
        HydraulicSample(
            parameters=(
                SampledParameter(
                    parameter=spec.parameter,
                    value=generator.uniform(spec.bounds.lower, spec.bounds.upper),
                    unit=spec.bounds.unit,
                    source=spec.source,
                ),
            ),
            sample_id=f"{spec.parameter.value}:uniform:{index}",
        )
        for index in range(sample_count)
    )


def evaluate_barrel_sample(
    sample: HydraulicSample,
    *,
    barrel: CulvertBarrel,
    discharge: float,
    tailwater: TailwaterInput,
    inlet_coefficients: InletCoefficients | None = None,
    entrance_loss_coefficient: float | EntranceLossCoefficient | None = None,
    entrance_loss_source: SourceReference | None = None,
    configuration: SolverConfiguration | None = None,
    g: float = GRAVITATIONAL_ACCELERATION,
) -> BarrelUncertaintyEvaluation:
    """Evaluate one uncertainty sample through the public barrel solver.

    Only explicit deterministic hydraulic inputs are varied. Numerical tolerances are
    intentionally absent from the uncertainty parameter vocabulary. Expected input-domain
    and convergence failures are returned as data; unexpected programming errors propagate.
    """
    evaluated_barrel = barrel
    evaluated_discharge = discharge
    evaluated_tailwater = tailwater
    evaluated_entrance_loss = entrance_loss_coefficient
    evaluated_entrance_loss_source = entrance_loss_source

    for sampled in sample.parameters:
        if sampled.parameter is HydraulicUncertaintyParameter.MANNING_ROUGHNESS:
            evaluated_barrel = replace(
                evaluated_barrel,
                roughness=sampled.value,
                roughness_selection_basis=RoughnessSelectionBasis.USER_OVERRIDE,
                roughness_source=sampled.source,
                roughness_selection=None,
            )
        elif sampled.parameter is HydraulicUncertaintyParameter.DISCHARGE:
            evaluated_discharge = sampled.value
        elif sampled.parameter is HydraulicUncertaintyParameter.TAILWATER_ELEVATION:
            evaluated_tailwater = sampled.value
        elif sampled.parameter is HydraulicUncertaintyParameter.ENTRANCE_LOSS_COEFFICIENT:
            evaluated_entrance_loss = sampled.value
            evaluated_entrance_loss_source = sampled.source

    try:
        result = solve_barrel_hydraulics(
            barrel=evaluated_barrel,
            discharge=evaluated_discharge,
            tailwater=evaluated_tailwater,
            inlet_coefficients=inlet_coefficients,
            entrance_loss_coefficient=evaluated_entrance_loss,
            entrance_loss_source=evaluated_entrance_loss_source,
            configuration=configuration,
            g=g,
        )
    except ConvergenceError as exc:
        return BarrelUncertaintyEvaluation(
            sample=sample,
            failure=HydraulicEvaluationFailure(
                kind=EvaluationFailureKind.CONVERGENCE,
                exception_type=type(exc).__name__,
                message=str(exc),
                bracket=exc.bracket,
                iterations=exc.iterations,
            ),
        )
    except InvalidInputError as exc:
        return BarrelUncertaintyEvaluation(
            sample=sample,
            failure=HydraulicEvaluationFailure(
                kind=EvaluationFailureKind.INVALID_INPUT,
                exception_type=type(exc).__name__,
                message=str(exc),
            ),
        )
    return BarrelUncertaintyEvaluation(sample=sample, result=result)


def _validated_parameter(
    parameter: HydraulicUncertaintyParameter,
) -> HydraulicUncertaintyParameter:
    try:
        return HydraulicUncertaintyParameter(parameter)
    except (TypeError, ValueError) as exc:
        msg = "parameter must be a HydraulicUncertaintyParameter."
        raise InvalidInputError(msg) from exc


def _validate_bounds(
    parameter: HydraulicUncertaintyParameter,
    bounds: ParameterBounds,
) -> None:
    if not isinstance(bounds, ParameterBounds):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "bounds must be a ParameterBounds value."
        raise InvalidInputError(msg)
    if bounds.unit is not parameter.unit:
        msg = f"{parameter.value} bounds must use unit {parameter.unit.value!r}."
        raise InvalidInputError(msg)
    _validate_parameter_value(parameter, bounds.lower)
    _validate_parameter_value(parameter, bounds.upper)


def _validate_parameter_value(
    parameter: HydraulicUncertaintyParameter,
    value: float,
) -> None:
    if parameter in (
        HydraulicUncertaintyParameter.MANNING_ROUGHNESS,
        HydraulicUncertaintyParameter.DISCHARGE,
    ) and value <= 0.0:
        msg = f"{parameter.value} must be strictly positive."
        raise InvalidInputError(msg)
    if parameter is HydraulicUncertaintyParameter.ENTRANCE_LOSS_COEFFICIENT and value < 0.0:
        msg = "entrance_loss_coefficient must be nonnegative."
        raise InvalidInputError(msg)


def _validate_source(source: SourceReference) -> None:
    if not isinstance(source, SourceReference):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "source must be a SourceReference."
        raise InvalidInputError(msg)


def _positive_count(count: int) -> int:
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        msg = "count must be a strictly positive integer."
        raise InvalidInputError(msg)
    return count
