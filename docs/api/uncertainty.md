# Uncertainty contracts and evaluation

These reusable primitives describe explicit parameter assumptions and evaluate one
sample through the deterministic barrel solver. See the
[uncertainty guide](../uncertainty.md) for scope and provenance requirements.
Study orchestration and design acceptance remain downstream concerns.

::: culvert_solver
    options:
      members:
        - HydraulicUncertaintyParameter
        - HydraulicUncertaintyUnit
        - ParameterBounds
        - BoundedParameterSpec
        - UniformParameterSpec
        - SampledParameter
        - HydraulicSample
        - EvaluationFailureKind
        - HydraulicEvaluationFailure
        - BarrelUncertaintyEvaluation
        - sample_bounded_parameter
        - sample_uniform_parameter
        - evaluate_barrel_sample
      show_root_heading: false
      heading_level: 2
