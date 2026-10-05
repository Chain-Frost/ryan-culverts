"""Tests for reusable uncertainty contracts and deterministic evaluation primitives."""

import pytest

from culvert_solver import (
    CONCRETE,
    BoundedParameterSpec,
    CircularGeometry,
    CulvertBarrel,
    EvaluationFailureKind,
    HydraulicResultStatus,
    HydraulicSample,
    HydraulicUncertaintyParameter,
    HydraulicUncertaintyUnit,
    InvalidInputError,
    ParameterBounds,
    SampledParameter,
    SourceReference,
    TailwaterRatingCurve,
    TailwaterRatingPoint,
    UniformParameterSpec,
    evaluate_barrel_sample,
    sample_bounded_parameter,
    sample_uniform_parameter,
)


@pytest.fixture
def uncertainty_source() -> SourceReference:
    return SourceReference(
        source_id="project-uncertainty-basis",
        publication="Project hydraulic uncertainty basis",
        edition="2026",
        locator="Table U-1",
        url=None,
        applicability="Illustrative uncertainty test inputs.",
    )


@pytest.fixture
def barrel() -> CulvertBarrel:
    return CulvertBarrel(
        geometry=CircularGeometry(diameter=1.0),
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.013,
        material=CONCRETE,
    )


def test_bounded_sampling_includes_bounds_without_probability_assumption(
    uncertainty_source: SourceReference,
) -> None:
    spec = BoundedParameterSpec(
        parameter=HydraulicUncertaintyParameter.MANNING_ROUGHNESS,
        bounds=ParameterBounds(
            lower=0.011,
            upper=0.015,
            unit=HydraulicUncertaintyUnit.DIMENSIONLESS,
        ),
        source=uncertainty_source,
    )

    samples = sample_bounded_parameter(spec, count=3)

    assert tuple(sample.parameters[0].value for sample in samples) == pytest.approx((0.011, 0.013, 0.015))
    assert all(sample.parameters[0].source is uncertainty_source for sample in samples)


def test_uniform_sampling_is_seeded_and_reproducible(
    uncertainty_source: SourceReference,
) -> None:
    spec = UniformParameterSpec(
        parameter=HydraulicUncertaintyParameter.DISCHARGE,
        bounds=ParameterBounds(
            lower=1.0,
            upper=2.0,
            unit=HydraulicUncertaintyUnit.CUBIC_METRE_PER_SECOND,
        ),
        source=uncertainty_source,
    )

    first = sample_uniform_parameter(spec, count=5, seed=2718)
    repeated = sample_uniform_parameter(spec, count=5, seed=2718)
    different = sample_uniform_parameter(spec, count=5, seed=3141)

    first_values = tuple(sample.parameters[0].value for sample in first)
    assert first_values == tuple(sample.parameters[0].value for sample in repeated)
    assert first_values != tuple(sample.parameters[0].value for sample in different)
    assert all(1.0 <= value <= 2.0 for value in first_values)


def test_parameter_unit_mismatch_is_rejected(
    uncertainty_source: SourceReference,
) -> None:
    with pytest.raises(InvalidInputError, match="manning_roughness bounds must use unit"):
        BoundedParameterSpec(
            parameter=HydraulicUncertaintyParameter.MANNING_ROUGHNESS,
            bounds=ParameterBounds(
                lower=0.011,
                upper=0.015,
                unit=HydraulicUncertaintyUnit.METRE,
            ),
            source=uncertainty_source,
        )


def test_evaluation_retains_expected_failure_instead_of_dropping_sample(
    barrel: CulvertBarrel,
    uncertainty_source: SourceReference,
) -> None:
    rating_curve = TailwaterRatingCurve(
        points=(
            TailwaterRatingPoint(discharge=0.5, elevation=9.6),
            TailwaterRatingPoint(discharge=1.0, elevation=9.8),
        ),
        rating_curve_source=uncertainty_source,
    )
    sample = HydraulicSample(
        parameters=(
            SampledParameter(
                parameter=HydraulicUncertaintyParameter.DISCHARGE,
                value=1.5,
                unit=HydraulicUncertaintyUnit.CUBIC_METRE_PER_SECOND,
                source=uncertainty_source,
            ),
        ),
        sample_id="outside-tailwater-range",
    )

    evaluation = evaluate_barrel_sample(
        sample,
        barrel=barrel,
        discharge=0.75,
        tailwater=rating_curve,
    )

    assert evaluation.result is None
    assert evaluation.failure is not None
    assert evaluation.failure.kind is EvaluationFailureKind.INVALID_INPUT
    assert "outside the tailwater rating-curve range" in evaluation.failure.message
    assert evaluation.status is None
    assert not evaluation.warnings
    assert not evaluation.convergence


def test_increasing_roughness_increases_full_flow_headwater(
    barrel: CulvertBarrel,
    uncertainty_source: SourceReference,
) -> None:
    low = HydraulicSample(
        parameters=(
            SampledParameter(
                parameter=HydraulicUncertaintyParameter.MANNING_ROUGHNESS,
                value=0.011,
                unit=HydraulicUncertaintyUnit.DIMENSIONLESS,
                source=uncertainty_source,
            ),
        ),
    )
    high = HydraulicSample(
        parameters=(
            SampledParameter(
                parameter=HydraulicUncertaintyParameter.MANNING_ROUGHNESS,
                value=0.018,
                unit=HydraulicUncertaintyUnit.DIMENSIONLESS,
                source=uncertainty_source,
            ),
        ),
    )

    low_result = evaluate_barrel_sample(low, barrel=barrel, discharge=1.5, tailwater=12.0)
    high_result = evaluate_barrel_sample(high, barrel=barrel, discharge=1.5, tailwater=12.0)

    assert low_result.result is not None
    assert high_result.result is not None
    assert high_result.result.headwater_elevation > low_result.result.headwater_elevation
    assert low_result.result.roughness_source is uncertainty_source
    assert high_result.result.roughness_source is uncertainty_source


def test_successful_evaluation_exposes_result_status_warnings_and_convergence(
    barrel: CulvertBarrel,
    uncertainty_source: SourceReference,
) -> None:
    sample = HydraulicSample(
        parameters=(
            SampledParameter(
                parameter=HydraulicUncertaintyParameter.ENTRANCE_LOSS_COEFFICIENT,
                value=0.5,
                unit=HydraulicUncertaintyUnit.DIMENSIONLESS,
                source=uncertainty_source,
            ),
        ),
        sample_id="loss-override",
    )

    evaluation = evaluate_barrel_sample(
        sample,
        barrel=barrel,
        discharge=1.5,
        tailwater=12.0,
    )

    assert evaluation.result is not None
    assert evaluation.failure is None
    assert evaluation.status is HydraulicResultStatus.VALID
    assert evaluation.warnings == evaluation.result.warnings
    assert evaluation.convergence == evaluation.result.convergence
    assert evaluation.result.entrance_loss_selection is not None
    assert evaluation.result.entrance_loss_selection.source is uncertainty_source
