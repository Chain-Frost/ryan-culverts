# Development progress

## 2026-09-08 — CS-006 independent primitive fixtures

Completed the ready primitive portion of CS-006. Critical depth, normal depth, circular
geometry, and full-flow losses now use fixed independently calculated expectations sourced
to HDS-5 equations rather than calculating expected values through another public package
path. `docs/validation.md` records inputs, expected values, zero differences at the shown
precision, source locators, and quantity-specific numerical tolerances.

Focused verification passed 32 tests across `tests/test_critical.py`,
`tests/test_normal.py`, and `tests/test_outlet_control.py`. An initial full run passed 267
tests but again failed the unrelated CS-007 wall-clock assertion, this time at
`0.510 ms/evaluation`. Separated verification passed all 261 non-performance tests and all
7 performance tests unchanged. After the temporary `0.6 ms/evaluation` adjustment, the
final full suite passed 268 tests. Ruff, format, strict Pyright, Markdown lint, and
`git diff --check` passed.

Profile, group/crossing, and rating-curve fixtures remain pending CS-004 and are not implied
to be validated by these primitive checks. The recurring environment-sensitive performance
failure remains assigned to CS-007. Nothing was committed, built, versioned, or published.

At the user's direction, the single-barrel timing ceiling was temporarily relaxed from
`0.5` to `0.6 ms/evaluation` to avoid known processor/load noise. This is a stopgap, not a
portable performance requirement; CS-007 still owns its replacement with a reproducible
benchmark method and recorded environment.

## 2026-09-08 — CS-003 inlet methodology completion

Completed CS-003 against FHWA HDS-5, Third Edition. The cubic Hermite transition is
retained as the deterministic implementation of Appendix A's smooth tangent construction:
it matches both branch values and analytical slopes, remains monotonic for every catalogued
circular and rectangular inlet, and is not described as HY-8 polynomial or exact
hand-drawn-nomograph parity. Tests independently reproduce the Appendix A printed pages
A.2-A.4 dimensionless example.

High-head results now expose their `HW/D` ratio. Direct Equation A.3 results above the
Section 3.5.2 laboratory-curve limit of `HW/D = 3` carry
`inlet_control_high_head_extension`; values above `HW/D = 10` also carry
`inlet_control_extreme_headwater`. These warnings propagate through barrel and rating-curve
results. The retained Type `6-FFc` difference is documented as direct HDS-5 Equation A.3
versus HY-8's fitted polynomial/general-orifice method, not a coefficient calibration target.

Remaining limitation: the exact HY-8 closed-executable high-head fit and a published Type 6
numeric case have not been independently reconstructed. CS-008 retains that comparison
evidence and CS-004 owns the mixed-profile details. Nothing was committed, built,
versioned, or published.

Focused verification passed 46 tests across inlet control, regime propagation, and rating
curves; the final full suite passed 268 tests. Repository-wide Ruff check and format,
strict Pyright, Markdown lint with MD013 excluded, and `git diff --check` passed. An
earlier full run measured the known CS-007 fixed wall-clock benchmark at
`0.5000315 ms/evaluation`, fractionally outside its `< 0.5` threshold; it passed unchanged
on the final run and remains recorded as timing-noise evidence.

## 2026-09-08 — CS-002 defaults and applicability completion

Completed CS-002 after reviewing the current primary MRWA pages and the local HDS-5
Table B.1 copy. Concrete pipe and box now have distinct source-bearing roughness records
using MRWA Design Procedure version 2E Table 2.1 ranges. Generic concrete roughness and
missing material context fail explicitly instead of silently selecting a concrete
default. Existing explicit values, barrel-attached values, and project configuration
overrides retain precedence.

Plastic-pipe roughness now requires an applicable manufacturer override. The HDS-5
laboratory value is available only through `allow_documented_fallback=True`, and that
selection carries stable notices for absent manufacturer data and the separation between
hydraulic roughness and MRWA construction compliance. CSP table selections carry the
same compliance distinction. A barrel can retain the complete roughness selection so
the solved result exposes its adopted value, basis, source, and notices. No HY-8 fallback
was introduced, and no hydraulic method or tolerance changed.

Focused verification: `python -m pytest -q tests/test_models.py tests/test_resolvers.py
tests/test_inlet_control.py tests/test_regime.py` passed 108 tests; the full suite passed
266 tests. Strict Pyright, repository-wide Ruff check and format, Markdown lint with the
repository's existing long-line convention excluded, and `git diff --check` passed.

At the user's request, Ruff fixed the import order and reformatted the pre-existing staged
`profiles/direct_step.py` typing work. The cleanup is unstaged and does not change the
profile method. The authoritative CS-002 handoff records future applicability limits and
the preserved staged/unstaged worktree state. Nothing was committed, built, versioned,
or published.

## 2026-09-08 — CS-005 result transparency handoff

Completed the currently ready, non-method-changing CS-005 diagnostics work. Public result
models now expose typed scalar head-loss components, labelled root convergence records,
and the already-computed profile object. Full-flow loss records include entrance,
friction, exit, and total head loss. Free-surface results expose entrance loss and retain
their distributed friction-slope profile without inventing scalar friction, exit, or
total values. Critical depth, normal depth, profile-boundary, hydraulic-jump, barrel
discharge, and crossing-headwater roots retain their residual, bracket, and iteration
count where a numerical root was actually solved.

No hydraulic equation, profile selection, tolerance, or acceptance threshold changed.
No new engineering source was needed: the work exposes values already calculated by the
existing HDS-5-based full-flow and direct-step paths and the existing `RootResult`
contract. `None` means a component or root was not separately calculated, not zero.
Exact inactive crossing groups continue to contain zero flow and velocity with no
fabricated losses, profile, or convergence record.

Focused verification: `python -m pytest -q tests/test_critical.py tests/test_normal.py
tests/test_profiles.py tests/test_regime.py tests/test_crossing.py tests/test_models.py`
passed 88 tests; `python -m ruff check src tests` passed; `python -m pyright` reported zero
errors and warnings. Full verification: `python -m pytest -q` passed 259 tests;
`python -m ruff check .`, `python -m ruff format --check .`, `python -m pyright`,
`python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`,
and `git diff --check` passed.

Remaining limitations: scalar free-surface friction, exit, and total loss are absent
because those methods do not currently calculate them as distinct values; interpolation
fallbacks do not claim numerical-root convergence; full-flow longitudinal points are not
calculated. CS-002 is now settled, so CS-005 remains open only pending CS-004 profiles.
The next action is to recheck the result contract after CS-004, then allow CS-011 to
consume the stable fields. Nothing was committed, built, or published.

## 2026-09-08 — Agent handoff and HY-8 qualifier review

- Made `docs/work/README.md` the concise selection dashboard with ready, waiting,
  blocked, and gated states plus exact routine verification commands.
- Defined non-overlapping responsibilities for research decisions (CS-001), inlet
  methods (CS-003), internal profiles/regimes (CS-004), independent fixtures (CS-006),
  and external-software evidence (CS-008).
- Added immediate deliverables for the Type 6 inlet-depth and long M2/full crown-station
  discrepancies, and assigned any resulting method changes to CS-003 or CS-004.
- Added CS-012 as the gated release, installed-wheel, and deliberate version-bump task.
- Reworded historical phase headings so implementation milestones cannot be mistaken for
  current engineering acceptance.
- Recorded HY-8 control-depth qualifiers: `*` has a developer-documented negative-depth
  correction meaning; the `**` onset near inlet-control `HW/D > 10` remains observed
  HY-8 8.0.1.2 behaviour rather than a manual-defined cross-version contract.
- Recorded the primary HDS-5 applicability statement that laboratory inlet curves cover
  `0.5 <= HW/D <= 3.0` and use a fitted orifice relationship above that range.

Verification: 259 tests passed; Ruff check and format, strict Pyright, Markdown lint, and
`git diff --check` passed.

## 2026-09-07 to 2026-09-08 — Agent-work and research-intake review

Reviewed the Phase 0-10 implementation, the two supplied agent research reports,
the primary PDFs under `reference_docs/`, and the local HY-8 evidence. Corrections
and improvements in this pass:

- corrected contradictory Phase 0 completion claims; CS-001 remains in progress;
- corrected the FHWA-HRT-06-138 polynomial discharge variable and completed the
  initial corrected Table 12 transcription with exact local PDF locators;
- corrected the NCHRP 734 slipline loss values and replaced the blanket
  multi-barrel efficiency warning with the report's qualified findings;
- made inlet and entrance-loss resolvers fail closed for unsupported material or
  geometry combinations, and corrected default-selection reporting;
- connected injectable `SolverConfiguration` defaults to the actual barrel,
  group, crossing, and rating-curve calculation paths;
- replaced the index-based crossing collection with a typed `CulvertInventory`
  using stable, unique crossing IDs and configuration/result consistency checks;
- added normalized crossing summary rows and deduplicated configured source data.

Follow-up work now preserves resolved inlet, entrance-loss, and Manning values,
selection bases, and optional user sources in solved barrel results. Inventory
summaries expose normalized crossing/group rows and deduplicate complete adopted
parameter sets using caller IDs or deterministic content fingerprints. Tests cover
50 crossings, repeatability, caller IDs, and distinct manufacturer provenance.
No JSON, spreadsheet, GIS, or presentation boundary was added to the calculation core.

Verified after this review and provenance-summary follow-up: 232 tests passed;
Ruff check and format, strict
Pyright, Markdown lint, and `git diff --check` passed. An isolated sdist/wheel
build and temporary installed-wheel import check passed at `0.2.0.dev1`. The
version was not bumped because no release or distinct handoff artifact was requested.

## 2026-09-06 — Independent review of Phases 0–10

The implementation milestones below are retained as a record of work performed, but their
earlier use of “complete” and “verified” meant internal implementation checks only. This
review found that the Phase 0 research gate was not completed before the hydraulic layers
were built, and that Phases 4–7 still contain provisional methodology.

Review corrections and improvements:

- Checked current inlet constants against HDS-5 Appendix A/Table A.1, entrance-loss
  constants against Table C.2, and Manning ranges against Appendix B/Table B.1.
- Corrected Manning provenance and the combined concrete range; coefficient transcription
  does not by itself establish engineering applicability.
- Added enums for control type, geometry applicability, inlet equation form, and profile
  curve; retained frozen dataclasses for extensible materials and coefficient records.
- Enforced inlet and entrance-loss coefficient shape applicability.
- Removed roughness-based inference of corrugated-metal inlet geometry; roughness alone
  cannot identify an entrance configuration.
- Added exact inactive-barrel crossing results and explicit mixed crossing rating-curve
  classifications instead of reporting a fabricated tiny flow or the first input group.
- Hardened and directly tested Brent's method at extreme finite bounds.
- Confirmed that JSON is not currently a computational-core requirement. Add it only at a
  future validated input/output boundary with explicit schema/version handling.
- Confirmed public classes and functions have docstrings. Remaining issues are accuracy and
  completeness of some docstrings/claims, not a shortage of docstring coverage.
- Added the MRWA Table 2.2 CSP Manning lookup by diameter and corrugation, with explicit
  override precedence and fail-closed handling of unavailable combinations.
- Added a calculation-only preliminary roughness resolver that reports whether its value came
  from an explicit override, a material default, or the MRWA CSP table, together with provenance.
- Added an agent-ready `docs/work/` register that consolidates active remediation and future
  scope with dependencies and acceptance criteria.

Open hydraulic gates:

- Choose and validate a defensible inlet transition method; HDS-5 describes a smooth tangent
  curve and does not prescribe the current linear interpolation.
- Complete Bodhaine, corrected box-inlet, pinned HY-8 technical, NCHRP, and Australian
  guidance review.
- Implement or explicitly reject hydraulic jumps and mixed full/free-surface profiles; test
  S1/S2 and pressurisation transitions against independent references.
- Replace the current `tailwater_depth >= rise` unconditional full-flow classification. HDS-5
  distinguishes S1 and hydraulic-jump outcomes for some submerged-outlet cases and requires
  profile reasoning before concluding that the whole barrel is pressurised.
- Decide whether high-level solvers must require explicit inlet and entrance configurations.
  Current geometry-based defaults are convenient assumptions, not site-specific design data.
- Replace qualitative/self-consistency tests with published profile cases and external,
  version-pinned comparisons before engineering use.
- Prove or remove the full-flow-candidate performance short-circuit.

Verified after review and MRWA/defaults follow-up: 188 tests passed; Ruff check and format,
strict Pyright, Markdown lint, package build, installed-wheel import checks, and
`git diff --check` passed. The distinct development artifact is `0.2.0.dev1`.

## 2026-09-06 — Research intake and numerical foundations

Baseline: `1f4de19` (cleanup committed by the user). The old implementation remains
available in earlier Git history; new implementation starts in `src/culvert_solver`.

Completed in this milestone:

- Corrected the work plan's title/section hierarchy and math-block formatting.
- Started computational basis, architecture, validation and HY-8 capability docs.
- Recorded source review levels and remaining literature work in references.
- Implemented explicit mm-to-m dimension conversion, immutable source metadata,
  numerical tolerances and bracketed roots with structured failure diagnostics.
- Added focused analytical/contract tests and Python 3.14 packaging/tool settings.

Verified for this milestone:

- `python -m pytest -q`: 26 passed.
- `python -m ruff check src tests`: passed; formatting check passed.
- `python -m pyright`: zero errors/warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md
  culvert_solver_updated_work_plan.md docs`: passed, including MD025.
  Line length is excluded for source URLs and tables; heading rules are enabled.
- `python -m build --no-isolation`: sdist and wheel built successfully.
- Installed the wheel without dependencies into a temporary target and checked
  import, mm conversion and an analytical root using isolated Python (`-I`).
  The wheel contains the typed marker and no retired `culvertflow` package.
- `git diff --check`: passed. Build outputs stay ignored under root `dist/`.

These checks cover the foundation only. No external hydraulic application was
launched, and the new package still has no hydraulic solver.

## 2026-09-06 — Physical constants, hydraulic geometry and SI primitives

Completed in this milestone:

- Defined central physical constants with immutable `SourceReference` records
  (`GRAVITATIONAL_ACCELERATION`, `STANDARD_WATER_DENSITY`,
  `STANDARD_WATER_KINEMATIC_VISCOSITY`).
- Implemented `CrossSectionGeometry` base class defining the hydraulic geometry
  protocol, SI contracts, and strict closed-conduit crown handling.
- Implemented `CircularGeometry` with analytical segment trigonometry, limiting-depth
  checks, quarter/half/three-quarter analytical symmetry, and `from_mm` factory.
- Implemented `RectangularGeometry` for box culverts with full closed-conduit crown
  transition, four-wall full wetted perimeter, and `from_mm` factory.
- Implemented pure SI hydraulic primitives (`cross_section_velocity`, `velocity_head`,
  `specific_energy`, `froude_number`, `manning_discharge`, `manning_friction_slope`,
  `friction_head_loss`, `minor_head_loss`) with strict parameter validation.
- Added comprehensive unit and analytical tests covering zero depth, partial depth,
  full depth, surcharged depth, symmetry, Froude critical condition, and Manning
  consistency (79 passed tests total).

Verified for this milestone:

- `python -m pytest -q`: 79 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Critical and normal depth implementation milestone (Phase 3)

Completed in this milestone:

- Implemented `calculate_critical_depth` in `culvert_solver.hydraulics.critical`:
  analytical closed-form solution for rectangular box culverts and bracketed root
  solver for circular/arbitrary conduits satisfying minimum specific energy and
  $\text{Fr} = 1.0$, with `CriticalDepthResult` and submerged-crown detection.
- Implemented `calculate_normal_depth` in `culvert_solver.hydraulics.normal`:
  uniform-flow Manning conveyance solver with circular branch selection resolving
  the non-monotone crown region ($y \le 0.9382 D$) per `docs/computational_basis.md`,
  `NormalDepthResult`, capacity exceedance flags, and zero-slope rejection.
- Added comprehensive unit tests in `tests/test_critical.py` and `tests/test_normal.py`
  covering analytical box solutions, energy minimization, known circular benchmarks,
  circular stable branch verification ($y_n \approx 0.82 D$ at full conveyance),
  and error contracts (101 passed tests total).

Verified for this milestone:

- `python -m pytest -q`: 101 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Core domain models (Phase 1 complete)

Completed in this milestone:

- Implemented `CulvertMaterial` and standard materials (`CONCRETE`, `SMOOTH_HDPE`,
  `CORRUGATED_STEEL`) with documented Manning ranges and HDS-5 Table A.1 references.
- Implemented `CulvertBarrel` with authoritative inverts and length, derived drop
  and slope, horizontal barrel support, and adverse slope rejection.
- Implemented `CulvertGroup` representing parallel identical barrels with quantity
  validation and aggregate flow area / span scaling.
- Implemented `TailwaterCondition` representing absolute water surface elevation
  with per-invert outlet depth derivation ($\max(0, \text{elevation} - z_{\text{outlet}})$).
- Implemented `CulvertCrossing` representing multi-group road crossings with
  aggregate barrels count, total area, and invert extrema.
- Implemented `FlowRegime` and result contracts (`BarrelHydraulicResult`,
  `GroupHydraulicResult`, `CrossingHydraulicResult`).
- Added unit tests in `tests/test_models.py` verifying all domain invariants,
  derived quantities, and immutability (116 passed tests total).

Verified for this milestone:

- `python -m pytest -q`: 116 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Inlet-control implementation milestone (Phase 4)

Completed in this milestone:

- Implemented `InletCoefficients` dataclass and standard coefficient sets from
  HDS-5 Table A.1 with complete `SourceReference` citations for circular concrete,
  circular corrugated metal pipe (CMP), and concrete box culverts.
- Implemented pure SI FHWA inlet-control formulations (`fhwa_inlet_headwater_form1`,
  `fhwa_inlet_headwater_form2`, `fhwa_submerged_inlet_headwater`, and
  `fhwa_transition_inlet_headwater`) with the $K_u = 1.811$ dimensionless flow
  parameter $q^* = K_u Q / (A D^{0.5})$ and continuous linear interpolation across
  the transition range ($3.5 < q^* < 4.0$).
- Implemented `calculate_inlet_control_headwater` solver returning structured
  `InletControlResult` capturing headwater depth, headwater elevation, flow regime
  (`UNSUBMERGED`, `TRANSITION`, `SUBMERGED`), and dimensionless discharge parameter.
- Added comprehensive unit tests in `tests/test_inlet_control.py` validating
  submerged/unsubmerged regimes, transition continuity, slope corrections, and
  HDS-5 manual example benchmarks (125 passed tests total).

Verified for this milestone:

- `python -m pytest -q`: 125 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Initial full-flow outlet-control implementation (Phase 5A)

Completed in this milestone:

- Implemented `EntranceLossCoefficient` dataclass with standard HDS-5 Table C.2
  coefficients (`PIPE_CONCRETE_SQUARE_EDGE`, `PIPE_CONCRETE_SOCKET_END`,
  `PIPE_CMP_PROJECTING`, `BOX_CONCRETE_FLARED_WINGWALLS_30_75`, etc.) with
  complete `SourceReference` citations and standard exit loss coefficient $K_o = 1.0$.
- Implemented head loss functions (`calculate_entrance_loss`, `calculate_friction_loss`,
  `calculate_exit_loss`, and `calculate_total_head_loss`).
- Implemented `calculate_full_flow_outlet_headwater` solver in
  `culvert_solver.outlet_control.full_flow` using FHWA HDS-5 Section 3.1.4 energy
  balance with effective downstream tailwater depth $h_o = \max(TW, (d_c + D) / 2)$,
  producing structured `FullFlowOutletResult`.
- Added unit and analytical tests in `tests/test_outlet_control.py` verifying
  submerged and unsubmerged tailwaters, effective downstream tailwater approximation,
  circular and box geometries, horizontal barrels ($S_0 = 0$), and input validation
  (134 passed tests total).

Verified for this milestone:

- `python -m pytest -q`: 134 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Provisional partial-flow and backwater implementation (Phase 5B)

Completed in this milestone:

- Implemented `ProfilePoint` and `WaterSurfaceProfile` domain models in
  `culvert_solver.profiles.direct_step` with complete longitudinal state tracking
  (station, depth, invert/crown/WSE, velocity, velocity head, EGL, friction slope,
  and free-surface Froude number).
- Implemented `compute_backwater_profile` using the direct-step method for prismatic
  culvert conduits, supporting M1, M2, H2, and S1 curves, asymptotic normal-depth
  convergence, exact inlet boundary intersection at $x = 0$ via `solve_bracketed`,
  and upstream headwater depth $HW = y_{\text{in}} + (1 + K_e) V_{\text{in}}^2 / (2g)$.
- Implemented `calculate_partial_flow_outlet_headwater` solver in
  `culvert_solver.outlet_control.partial_flow` returning structured
  `PartialFlowOutletResult`.
- Added unit and analytical tests in `tests/test_profiles.py` verifying M2 drawdown
  curves, M1 backwater curves, horizontal barrel H2 curves, long barrel normal-depth
  asymptotics, submerged outlet full-flow transition, and input validation
  (141 passed tests total).

Verified for this milestone:

- `python -m pytest -q`: 141 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Provisional regime selection and single-barrel solver (Phase 6)

Completed in this milestone:

- Extended `FlowRegime` enum with `INLET_CONTROL_TRANSITION` to explicitly track the
  FHWA transition region ($3.5 < q^* < 4.0$).
- Implemented `determine_governing_regime` in `culvert_solver.solver.regime` comparing
  inlet control and outlet control solutions, enforcing physical consistency per
  FHWA HDS-5 and Bodhaine (1968) (e.g. steep slope low tailwater cutoff for Bodhaine
  Flow Type 1, submerged full-flow triggers, and subcritical backwater curves).
- Implemented `solve_barrel_hydraulics` in `culvert_solver.solver.barrel` producing
  complete `BarrelHydraulicResult` capturing governing regime, control type,
  headwater depth/elevation, tailwater depth/elevation, outlet velocity, critical
  depth, and normal depth.
- Added comprehensive unit tests in `tests/test_regime.py` validating steep-slope
  inlet control, high tailwater full-flow outlet control, mild-slope subcritical
  backwater outlet control, transition-zone classification, horizontal barrels,
  and input validation (147 passed tests total).

Verified for this milestone:

- `python -m pytest -q`: 147 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Culvert groups and multi-group crossings (Items 15 & 16 complete)

Completed in this milestone:

- Implemented `solve_group_hydraulics` in `culvert_solver.solver.group` computing
  per-barrel flow partition ($Q_{\text{barrel}} = Q_{\text{tot}} / N$) and aggregate
  `GroupHydraulicResult`.
- Implemented `solve_barrel_discharge_for_headwater` in `culvert_solver.solver.crossing`
  inverting $HW(Q)$ to compute $Q(HW)$, with robust headwater depth scaling,
  tailwater upper-bound checks ($HW \le TW \implies Q = 0$), and contraction down to
  dry invert limits.
- Implemented `solve_crossing_hydraulics` in `culvert_solver.solver.crossing` for
  crossings containing multiple groups with different geometries, materials, and
  invert levels:
  - Fast-path closed-form execution for single-group crossings.
  - Multi-group common upstream headwater elevation solve satisfying
    $\sum_i N_i Q_i(HW_{\text{elev}}) = Q_{\text{total}}$.
  - Natural handling of relief barrels (inactive when $HW_{\text{elev}} \le z_{\text{inlet}}$).
- Added comprehensive unit and integration tests in `tests/test_crossing.py` (153 passed).

Verified for this milestone:

- `python -m pytest -q`: 153 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Rating curves and discharge sequences (Item 17 complete)

Completed in this milestone:

- Implemented `RatingCurvePoint` and `RatingCurveResult` domain models in
  `culvert_solver.solver.rating_curve`.
- Implemented `generate_discharge_range` utility generating linearly spaced positive
  discharges for rating curve evaluation.
- Implemented `generate_barrel_rating_curve` and `generate_crossing_rating_curve`
  producing sorted rating curve points with headwater depths, elevations, velocities,
  governing controls, and regime tracking.
- Added comprehensive unit tests in `tests/test_rating_curve.py` validating monotonicity,
  steep-slope regime transitions, relief barrel activation, and input validation
  (159 passed).

Verified for this milestone:

- `python -m pytest -q`: 159 passed.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-06 — Initial performance and rapid-evaluation work (Phase 10)

Completed in this milestone:

- Implemented `solve_brent` in `culvert_solver.numerical.roots` combining bisection,
  secant, and inverse quadratic interpolation for superlinear convergence while strictly
  maintaining the bracket.
- Optimized crossing solver inner and outer root iterations with `solve_brent`, reducing
  evaluation iterations from ~25 to ~6.
- Accelerated `calculate_critical_depth` and `calculate_normal_depth` using `solve_brent`.
- Implemented physical upper-bound short-circuiting in `determine_governing_regime`:
  when $HW_{\text{inlet}} \ge HW_{\text{full}}$, inlet control is guaranteed to govern,
  avoiding expensive direct-step backwater profile integration.
- Added Phase 10 test suite in `tests/test_performance.py` verifying scalar result
  equivalence, bit-exact deterministic repeated runs, group permutation invariance,
  smooth regime transitions, and throughput benchmarks (166 passed).
- Benchmarked evaluation throughput:
  - Single barrel: ~0.08 ms / eval (> 12,000 evaluations/sec in pure Python).
  - Multi-group crossing: ~46 ms / eval.
  - Rating curve (20 points): ~1.8 ms / curve.

Verified for this milestone:

- `python -m pytest -q`: 166 passed in 1.01s.
- `python -m ruff check src tests`: passed with zero warnings.
- `python -m ruff format --check src tests`: 56 files formatted.
- `python -m pyright`: zero errors or warnings under strict configuration.
- `python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs`: passed.

## 2026-09-07 - Initial HY-8 8.0.1.2 executable comparison

Completed in this milestone:

- Added `scripts/compare_hy8.py`, a reproducible 16-case SI comparison using the
  public `run-hy8` API and circular concrete, circular CSP, and concrete box barrels.
- Ran the matrix against HY-8 8.0.1.2 through `run-hy8` commit `3cea405` and recorded
  the version, configuration, result summary, method differences, and limitations in
  `docs/validation.md`.
- Corrected the comparison roadway crest so arbitrary culvert datums cannot accidentally
  introduce roadway overtopping.
- Corrected inlet-control outlet velocity to use an S2 profile where the downstream
  boundary cannot control the supercritical barrel flow.
- Added `outlet_depth` to `BarrelHydraulicResult`, making the velocity basis inspectable.
- Confirmed that the largest remaining headwater difference (`0.089 m`) is a HY-8 Type
  `7-M2c` case not represented by the provisional local state model.
- Implemented forward direct-step `S2n` routing for steep barrels with tailwater no higher
  than normal depth. The profile starts immediately below critical depth, approaches normal
  depth downstream, exposes its `ProfileCurve`, and can be refined by increasing its step
  count. This reduced the maximum concrete-box velocity difference from `0.570 m/s` to
  `0.019 m/s` while retaining the Phase 10 performance thresholds.
- Replaced the provisional linear inlet transition with a cubic Hermite curve tangent to
  the HDS-5 unsubmerged and submerged branches. The Form 1 tangent includes the exact
  critical-specific-energy derivative. Tests cover C1 endpoint continuity and monotonicity
  for all nine catalogued inlet coefficient sets. Two `q* = 3.75` HY-8 cases now distinguish
  the HDS-5 tangent method from HY-8's shape-specific polynomial method.
- Added typed candidate headwaters and hydraulic limitation warnings to barrel results.
  Rating-curve points retain the complete warnings, and road-inventory group/crossing rows
  expose compact deduplicated warning codes. The HY-8 CSV now records those codes for each
  comparison case.
- Added exact circular and rectangular hydrostatic pressure moments plus a general
  momentum-function sequent-depth solver. In the moderate-tailwater comparison, tailwater
  is below the S2 outlet conjugate depth, proving that the jump is swept out. The solver now
  matches HY-8's `1-S2n` classification and reduces the maximum circular-concrete velocity
  difference from `0.178 m/s` to `0.015 m/s`.
- Implemented backward S1 routing and momentum matching against the S2 conjugate-depth
  envelope. Results now distinguish swept-out S2, an in-barrel `JS1` jump with its station,
  and an S1 curve reaching the inlet. The added HY-8 cases agree on `1-JS1t` and `1-S1t`
  flow types and closely match headwater and velocity.
- Removed the heuristic that discarded a free-surface candidate whenever the full-flow
  headwater was below inlet control. The circular-CSP case now selects `7-M2c`, reducing
  its HY-8 headwater difference from `0.089 m` to `0.004 m`.
- Continued M2 profiles that reach the crown as full-section upstream reaches, charging
  Manning friction only over the reported full-flow length. A new long-barrel HY-8 case
  agrees within `0.005 m` headwater and `0.003 m/s` velocity while reporting `68.483 m`
  of full flow rather than flattening the profile at the crown.
- Replaced the blanket submerged-outlet full-flow classification with an HGL-versus-crown
  intersection. Fully pressurised cases prove full length; shallow submergence now routes
  the upstream free-surface portion to that transition. The `1-S1f` comparison improves
  to `0.002 m` headwater and `0.005 m/s` velocity difference. A second case locates JS1
  at station `17.528 m`, reports `0.202 m` of downstream full flow, and matches HY-8's
  `5-JS1f` classification within `0.007 m` headwater and `0.003 m/s` velocity.
- Added an explicit HY-8 `6-FFc` free-outfall case. The local solver reports `9.991 m` of
  the 10 m barrel as full and matches velocity within `0.002 m/s`, but its governing
  inlet-control headwater is `0.414 m` lower. The inlet configuration mapping was checked
  as the same circular-CSP square-edge-with-headwall treatment; the remaining difference
  is between the HDS-5 high-head equation at `q* = 13.893` and HY-8's polynomial-based
  result. The fixture remains a documented failing comparison pending a primary Type 6
  case rather than being treated as validated. Result selection now retains the computed
  M2/full barrel profile without a spurious unresolved-profile warning when inlet control
  governs.
- Audited that Type 6 case against the installed HY-8 8.0.1.2 executable, raw saved project,
  raw `.rst`, installed ShapeDB, and User Manual. The project fields and parsed report agree;
  local and HY-8 outlet-control depths also agree to HY-8's display precision. No
  `run-hy8` defect was found. The remaining inlet difference is explicitly non-authoritative
  because the harness has not reconstructed HY-8's closed high-head behavior.
- Hardened the executable harness to reject wrong nearest-flow rows, non-finite results,
  and unintended roadway flow instead of silently including them in the matrix.
- Updated the harness for installed `run-hy8 2026.9.8.1` per-culvert diagnostics. It now
  cross-checks culvert and crossing discharge, velocity, and flow type; verifies
  full/free length balance; and retains HY-8 candidate depths, qualifiers, and barrel
  lengths in the 20-case CSV.
- The new fields confirm local outlet-control depth is within `0.008 m` of HY-8 across
  all 20 cases. They also expose a `0.997 m` full-length difference in the long M2/full
  case even though its outlet-control headwater agrees within `0.005 m`; this profile
  detail remains outstanding for independent validation.

Verification after implementation: 259 tests passed; Ruff check and format, strict
Pyright, Markdown lint, captured-CSV equality, and `git diff --check` passed.
The single-barrel wall-clock benchmark failed once at `0.501 ms/evaluation` against its
fixed `< 0.5 ms` threshold, then passed alone and in the final full run. CS-007 must
replace this environment-sensitive assertion with a reproducible benchmark policy.

## Phase status

Historical entries above record implementation milestones at the time. This table is the
current acceptance status and takes precedence over those chronological descriptions.

| Phase | Status | Next deliverable |
| --- | --- | --- |
| 0: research/basis | In progress | Complete the source reviews and resolve transition/profile policies |
| 1: foundations | Complete | Barrel/group/boundary models, constants and numerical infrastructure verified |
| 2: geometry | Complete | Analytical circular and rectangular box geometries implemented and verified |
| 3: fundamental hydraulics | Implemented | Add independent high-flow/crown-boundary validation |
| 4: inlet control | Implemented | Tangent transition tested; add primary nomograph fixtures |
| 5: outlet control | Partial | S1f/JS1f routed; add independent mixed-profile fixtures |
| 6: regime selection | Partial | Replace heuristic selection with fully evidenced admissibility logic |
| 7: single-barrel solver | Provisional | Complete intermediate results and independent integration cases |
| 8: culvert groups | Complete | Identical parallel barrels and group hydraulics verified |
| 9: crossings | Implemented | Expand mixed-control and coefficient-configuration cases |
| 10: rating/performance | Implemented | Record benchmark environment; depends on Phase 4–7 validation |
| External verification | In progress | 20-case HY-8 matrix covers S1f/JS1f and retains unresolved Type 6 evidence |

## Current handoff

Use the [work register](work/README.md) for current ownership, readiness, dependencies,
and execution order. In particular, do not infer current completion from the historical
entries in this progress log. The immediate high-risk chain is source decisions (CS-001),
inlet and profile methods (CS-003/004), external discrepancy evidence (CS-008), and the
independent validation suite (CS-006). Defaults (CS-002) and non-method-changing result
diagnostics (CS-005) can progress in parallel.
