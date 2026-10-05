# Uncertainty primitives

ryan-culverts provides low-level, reusable contracts for describing and evaluating
hydraulic parameter uncertainty. Project study orchestration, Monte Carlo policy,
aggregation, percentiles, ranking, plots and design acceptance remain downstream concerns.

## Separation of concerns

Four distinct concepts must not be collapsed into one setting:

1. **Parameter uncertainty** describes uncertainty in an explicit hydraulic input such as
   Manning roughness, discharge, fixed tailwater elevation or entrance-loss coefficient.
2. **Model applicability** is represented by the solver's structured warnings and
   applicability records. Sampling a parameter does not expand the validated method range.
3. **Numerical convergence** is retained from the deterministic solver. Root tolerances are
   numerical controls and are deliberately not uncertainty parameters.
4. **Design or regulatory acceptance** is project policy and is not decided by these
   primitives.

## Public contracts

BoundedParameterSpec records deterministic engineering bounds without implying a
probability distribution. UniformParameterSpec records an explicit uniform distribution.
Both preserve the parameter identity, canonical SI unit and a SourceReference describing
the basis for the uncertainty assumption.

sample_bounded_parameter produces an inclusive deterministic sweep. A one-point sweep
uses the midpoint; sweeps with two or more points include both bounds.

sample_uniform_parameter requires an explicit integer seed and uses a local random
generator, so repeated calls with the same specification, count and seed are reproducible
without mutating global random state.

HydraulicSample may contain multiple distinct sampled inputs. The initial supported
parameter identities are:

- Manning roughness, dimensionless;
- discharge, m³/s;
- fixed tailwater elevation, m;
- entrance-loss coefficient, dimensionless.

Geometry and invert tolerances are intentionally not included until each sampled geometry
mutation can be passed through the deterministic domain model without bypassing its
validation and provenance rules.

## Evaluation

evaluate_barrel_sample applies one HydraulicSample and then calls the public
solve_barrel_hydraulics entry point. It does not implement uncertainty-specific
hydraulic equations.

Successful evaluations retain the complete BarrelHydraulicResult, including structured
hydraulic status, warnings, provenance and convergence records. Expected
InvalidInputError and ConvergenceError failures are returned as
HydraulicEvaluationFailure data so unsupported or failed samples are not silently
discarded. Unexpected programming errors still propagate.

The module does not decide whether a distribution is justified for a project. Bounds,
distribution choice and their source remain explicit inputs supplied by the caller.
