# Phase 0-10 remediation and forward plan

Status: authoritative agent handoff, updated 2026-09-08.

## Purpose and current baseline

This record converts the review findings into bounded tasks that another agent
can execute. Phases 1-10 have substantial implementations and internal tests,
but Phase 0 research is incomplete and combined hydraulic behaviour remains
provisional. Passing tests must not be described as engineering validation.

Read these files before changing hydraulics:

1. `docs/work/long-term-development-plan.md` for intended scope and order;
2. `docs/progress.md` for what was implemented and reviewed;
3. `docs/references.md` for source-review status;
4. `docs/computational_basis.md` and `docs/architecture.md` for current methods;
5. `docs/validation.md` and `docs/hy8_feature_parity.md` for evidence gaps.

Preserve unrelated Git state. Use focused tests for every edited module, then run
the full test, Ruff, strict Pyright, Markdown, build, and installed-wheel checks
before a release handoff. Do not commit or publish unless requested.

## Decisions already made

### Defaults and overrides

Defaults are conveniences, not hidden design assumptions. Use this precedence:

1. an explicit user value;
2. project-specific or manufacturer data supplied by the user;
3. an applicable MRWA value;
4. a version-pinned HY-8 default when MRWA has no applicable value;
5. an explicit error when the context is insufficient or unsupported.

Every default must be inspectable and carry source/applicability metadata. Every
default must be replaceable at the public input boundary. Partial overrides must
preserve supplied values and resolve only missing fields. Never infer an inlet
shape, corrugation, material condition, or entrance treatment from Manning roughness.
User overrides may include their own `SourceReference`, such as a manufacturer
specification or project design basis; provenance is optional for an override but
must never be discarded when supplied.

MRWA Table 2.2 CSP values are implemented by diameter and corrugation through
`resolve_csp_manning_roughness`. Unsupported combinations fail closed. An explicit
positive override always wins. `CORRUGATED_STEEL.contextual_roughness_required` is
true; its retained `typical_n` catalog value is not a substitute for the typed lookup.

### Enums, records, and JSON

Use enums for genuinely closed categories, frozen records for extensible
engineering data, and ordinary user values for overrides. Do not turn materials
or coefficient sets into enums: users need custom instances. JSON is not a better
home for computational constants. Add JSON only at a versioned I/O boundary with
schema validation, unit declarations, enum handling, provenance, and round-trip tests.
The current priority is the computational library; wrappers and ingestion formats
remain deferred until a concrete downstream consumer exists.

### Formatting and versioning

Ruff is the sole formatter and linter. Do not add Black alongside it. The package
version changes when a distinct wheel is deliberately built for handoff; development
work increments the development suffix and does not imply engineering readiness.

## Execution order and task boundaries

The task register is intentionally split by responsibility:

- CS-001 reviews sources and records engineering decisions and candidate fixture inputs;
  it does not make solver behaviour authoritative merely by documenting it.
- CS-003 owns inlet-control algorithms and focused inlet tests, including the C1
  transition and the high-head/orifice extension.
- CS-004 owns internal water-surface profiles, pressurisation transitions, hydraulic
  jumps, and regime admissibility.
- CS-006 owns the independent cross-phase fixture suite and acceptance evidence. It may
  consume source cases identified by CS-001 and focused tests produced by CS-003/004.
- CS-008 owns external-software execution, configuration parity, captured diagnostics,
  and discrepancy reports. HY-8 results do not define the equations implemented by
  CS-003/004.
- CS-005 owns result transparency without changing the underlying hydraulic methods;
  CS-011 consumes those stable result fields for inventory summaries.

Recommended execution order is CS-001, then CS-003/004 with CS-008 comparison support,
then CS-006. CS-002 and the non-method-changing portion of CS-005 can proceed in
parallel. Finish CS-011 after CS-005, CS-007 after CS-004/006, and CS-012 last.

## Active tasks

| ID | Status | Owner | Updated | Next review | Next action |
| --- | --- | --- | --- | --- | --- |
| CS-001 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Reopen only for a corrected source edition or evidence that changes a recorded decision |
| CS-002 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Monitor source revisions; reopen only for a supported new material or fallback |
| CS-003 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen only for primary evidence supporting a different transition or high-head extension |
| CS-004 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen only for a new supported profile family, geometry, or contrary primary evidence |
| CS-005 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen when a supported method calculates an additional diagnostic or adopted value |
| CS-006 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen for a new method or stronger independent combined-system evidence |
| CS-007 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Rebenchmark on target hardware or reopen for an evidenced algorithmic regression |
| CS-008 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Reopen only for contrary primary evidence or a version-pinned comparison that changes a disposition |
| CS-011 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Reopen only when a new result or notice field requires inventory representation |
| CS-012 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Use the current verified wheel for integration tests; packaging now increments the calendar version |
| CS-017 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Use `package.bat`; reopen only for a packaging failure or changed version policy |

### CS-001 - Close the Phase 0 research gate

Scope:

- complete the Bodhaine flow-type and worked-example review;
- complete the applicability review and select fixture inputs from the corrected
  FHWA-HRT-06-138 box-inlet material;
- review a pinned HY-8 technical-method version, NCHRP 734, and applicable
  Australian guidance;
- pin mutable source-code references to revisions;
- record exact pages, equations, tables, applicability, and unresolved conflicts.

Acceptance:

- `docs/references.md` identifies each source as reviewed, rejected, or pending;
- adopted methods are reflected in `docs/computational_basis.md`;
- no secondary implementation is treated as the authority;
- unresolved engineering choices become explicit tasks rather than implicit code.

Deliverable boundary: record a fixture-ready source locator, inputs, expected quantity,
published precision, and applicability for each selected case. CS-003/004 own method
implementation and focused tests; CS-006 owns the accepted cross-phase fixture suite.

Handoff (2026-09-09): local primary and HY-8 evidence originally found across
`reference_docs/` and `hy8/` was inventoried and hash-pinned, then consolidated under
`reference_docs/` during release cleanup. All ten Bodhaine examples were
reviewed; four representative input/output records, the corrected FHWA Appendix D
FC-D-30 cases, and the Austroads design-workflow case are recorded in
`docs/research/fixture_candidates.md` with source precision and applicability.

The method decisions in `docs/computational_basis.md` retain HDS-5 as the hydraulic
baseline, use Bodhaine for physical classification, keep HY-8 as a pinned comparison,
and use Austroads for Australian application context. Corrected box coefficients require
typed fillet/bevel/skew/barrel-count context (CS-013). NCHRP 734 Borda-Carnot outlet loss,
slipline, buried-invert, and composite-roughness work require richer boundary/material
models (CS-030 through CS-033); the original embedded coefficients are rejected because the bundled HY-8
correction documents flawed dimensionless flow and false beveled-case data. The Austroads
Section 3.15.1 full-flow velocity inconsistency is isolated as CS-015 rather than embedded
in a fixture.

Verification and remaining limitations: `python -m pymarkdown -d MD013 scan` passed for
the edited Markdown files, all 16 recorded PDF path/hash records matched the local files,
and `git diff --check` passed. No tests were run because this documentation-only task changed
no solver code, fixture code, or tests. At that handoff the corrected FHWA box fixtures
were not executable with the then-current sharp-corner rectangular geometry; CS-013
subsequently added the bounded filleted case. Bodhaine values remain historical-method
comparisons. Nothing was
committed, built, versioned, or published.

### CS-002 - Complete the defaults and configuration policy

Current evidence: MRWA CSP Table 2.2 is transcribed and tested. The public
roughness, inlet-coefficient, and entrance-loss resolvers apply explicit override,
barrel-attached value, and applicable default precedence with typed selection
bases and source metadata. `SolverConfiguration` is injectable through barrel,
group, crossing, and rating-curve calculations. Solved results retain these
selections and optional user sources. CS-002 completed the remaining supported
material defaults, applicability notices, and construction-compliance distinctions
on 2026-09-08.

Future extension boundary:

- audit typed inlet and entrance-loss selections for any unsupported or silently
  inferred combinations;
- refine concrete pipe, concrete box, and smooth-interior plastic defaults if the
  Phase 0 research changes their applicability or preferred source;
- use manufacturer data ahead of tabulated values when supplied;
- use MRWA before HY-8, with HY-8 version recorded for fallback values;
- emit a structured warning or error when a fallback is outside validated context.

Acceptance:

- explicit values always win, including partial overrides;
- CSP varies by diameter and corrugation and rejects unavailable combinations;
- plastic guidance requests manufacturer data before using a documented fallback;
- result objects expose the selected values and provenance;
- focused tests cover precedence, unsupported contexts, and serialization-ready enums.

No additional user decision is needed to begin. Ask only if a primary source and
the precedence above genuinely conflict for a supported design case.

Handoff (2026-09-08): complete. Live primary-source review confirmed MRWA Design
Procedure version 2E Table 2.1 concrete ranges, the Part 5B manufacturer-first plastic
policy, and Specification 404's separate construction/product requirements. Added
specific concrete-pipe and concrete-box roughness records, made generic concrete
roughness and absent material context fail explicitly, and made the HDS-5 plastic value
an opt-in fallback with stable source-bearing notices. MRWA CSP selections now also
state that a hydraulic lookup is not construction compliance. No HY-8 fallback was
introduced.

Explicit and partial overrides retain precedence. A typed roughness selection can be
attached to a barrel so its adopted value, basis, source, and notices survive into the
solved result. Focused tests cover precedence, missing and mismatched context, plastic
fallback opt-in, CSP availability, notice-code serialization, and end-to-end provenance.
The implementation changes configuration and result transparency only; no hydraulic
equation, regime/profile selection, tolerance, or acceptance threshold changed.

Verification: `python -m pytest -q tests/test_models.py tests/test_resolvers.py
tests/test_inlet_control.py tests/test_regime.py` passed 108 tests; the full suite passed
266 tests. `python -m pyright`, `python -m ruff check .`, `python -m ruff format
--check .`, `python -m pymarkdown -d MD013 scan` on all changed Markdown files, and
`git diff --check` passed. At the user's request, Ruff fixed the import order and
reformatted the pre-existing staged `profiles/direct_step.py` typing work; those cleanup
changes are unstaged and do not change the profile method.

Remaining limitations and next action: no HY-8 roughness fallback is defined, and no
unsupported plastic or other material is inferred. Add a new material/default only after
recording a supported source, applicability, precedence, and tests. The previously staged
CS-005/type-annotation content remains staged; CS-002 and requested formatting changes
are unstaged on top where files overlap. Nothing was committed, built, versioned, or
published.

### CS-003 - Resolve inlet-control methodology

Scope: validate the implemented smooth tangent interpretation between the HDS-5
unsubmerged and submerged equations, or replace it with a better-supported method. Check
continuity, derivative behaviour, applicability limits, and both implemented geometries.
Also establish the adopted high-head behaviour above the published inlet-curve range,
including whether the HDS-5 orifice equation is sufficient and how extreme `HW/D` results
are warned or rejected. HY-8's fitted polynomial/orifice implementation is comparison
evidence, not automatically the adopted method.

Acceptance: equation/page citations, primary nomograph or independently reproduced
cases, transition-boundary tests, a high-head fixture or explicit unsupported boundary,
and removal of provisional claims from code and docs. The retained Type 6 case must have
an explained method difference or a supported implementation change.

Depends on: CS-001.

Handoff (2026-09-08): complete. HDS-5 Appendix A printed pages A.1 and A.6 establish
that the transition is drawn smooth and tangent to both equation branches and that the
nomograph transition was drawn by hand; no unique digital interpolation algorithm is
specified. The adopted cubic Hermite bridge is C1 continuous, matches the analytical
endpoint derivatives, and is monotonic for every catalogued circular and rectangular
coefficient set. It is explicitly a deterministic implementation of the source requirement,
not HY-8 polynomial or exact hand-drawn-nomograph parity.

The Appendix A printed pages A.2-A.4 example has been independently reproduced in tests.
HDS-5 Section 3.5.2, printed page 3.39, limits the laboratory inlet curves to
`0.5 <= HW/D <= 3.0` and describes a fitted general-orifice extension above that range.
The project retains its direct Equation A.3 calculation above `HW/D = 3` but attaches the
stable `inlet_control_high_head_extension` warning; above `HW/D = 10` it also attaches
`inlet_control_extreme_headwater`. Both warnings propagate through barrel and rating-curve
results.

The retained Type `6-FFc` case now reports the high-head warning. Its `0.414 m` HY-8
difference is explained by direct HDS-5 Equation A.3 versus HY-8's documented fitted
polynomial/general-orifice method; no coefficient was tuned to the executable. The local
numeric extension remains useful comparison output but is not presented as ordinarily
validated above the primary `HW/D = 3` boundary.

Verification and remaining limitations are recorded in `docs/progress.md`. The exact HY-8
closed-executable high-head fit and a published Type 6 numeric case have not been
independently reconstructed; CS-008 retains that external-comparison evidence, while
CS-004 owns only mixed-profile details. Nothing was committed, built, versioned, or
published.

Verification: `python -m pytest -q tests/test_inlet_control.py tests/test_regime.py
tests/test_rating_curve.py` passed 46 tests and `python -m pytest -q` passed 268 tests.
Repository-wide Ruff check and format, strict Pyright, Markdown lint with MD013 excluded,
and `git diff --check` passed. An earlier full-suite run hit the already tracked CS-007
wall-clock assertion at `0.5000315 ms/evaluation` against a strict `< 0.5` threshold; the
unchanged test passed on the final full run. This remains timing-noise evidence, not a
CS-003 hydraulic failure.

### CS-004 - Correct outlet profiles and regime selection

Scope:

- remove the unconditional `tailwater_depth >= rise` full-flow assumption;
- implement or explicitly reject S1/S2 profiles, mixed free/full flow, and hydraulic jumps;
- verify pressurisation transitions and physical candidate selection;
- decide and document direct-step versus standard-step for each supported profile;
- test low/adverse-limit slopes only within explicitly supported scope.

Acceptance: every supported regime has a forcing test and independent reference
case; unsupported states fail clearly; no solver chooses a headwater solely by
taking the larger of two physically unchecked candidates.

Implemented so far: S2 routing covers unambiguous low-tailwater cases. Exact built-in
section pressure moments and a generic momentum-function sequent-depth solver test the S2
profile against tailwater. A backward S1 profile and its intersection with the conjugate
S2 envelope distinguish swept-out, `JS1`, and inlet-reaching S1 states. Removing the old
full-flow shortcut also admits the HY-8 `7-M2c` free-surface candidate. When M2 reaches
the crown, the solver now continues the remaining upstream length as full flow and charges
its friction explicitly. An HGL-versus-crown test now distinguishes fully pressurised
submerged barrels from a downstream-only pressurised segment and reports the segment
length. The upstream reach is now routed as S1f or JS1f, including momentum-based jump
location, with both branches checked against HY-8. An explicit HY-8 `6-FFc` comparison
fixture is recorded, but its headwater discrepancy still requires investigation before
Type 6 is considered supported.

Immediate deliverables:

1. independently reproduce at least one S2, S1/JS1, and mixed M2/full profile;
2. explain or correct the long-case crown station (`68.463 m` local versus `69.4755 m`
   in the HY-8 plot), including a documented step-refinement check;
3. convert remaining physically unsupported profile combinations into explicit errors or
   structured limitation warnings;
4. leave the high-head inlet equation itself to CS-003.

Depends on: CS-001 and CS-003 where transition behaviour affects selection.

Handoff (2026-09-08): CS-004 is complete within its stated prismatic circular/rectangular
boundary. The old integration stopped at `D - 0.0001 m`; it now targets the exact crown and
forces the final depth increment to land on its target instead of occasionally skipping it
through floating-point accumulation. The default 50-step crown station is `68.463 m`, the
800-step result is `68.44519 m`, and an independent composite-Simpson evaluation of
`dx/dy = (1 - Fr²) / (S0 - Sf)` gives `68.4449163 m`. The remaining approximately
`1.031 m` difference from HY-8's `69.4755 m` plot value is therefore not a step-resolution
error and was not used for tuning.

Direct step is adopted for monotonic profiles in the supported prismatic built-in geometries;
standard/continuous energy integration is the independent validation method, and momentum
matching handles hydraulic jumps. `compute_backwater_profile` now rejects a submerged
outlet rather than inferring whole-barrel full flow from that condition alone; the regime
solver owns pressurised and mixed classification.

Fixed independent continuous-energy references now cover S2, S1, M2, M1, and H2 profiles;
an independent momentum-function calculation covers JS1; and the refined mixed M2/full
case covers the crown transition. Each supported family has a forcing test. The unsupported
audit confirms that adverse slopes fail at `CulvertBarrel` construction, direct S2 routing
rejects non-steep slopes, invalid numerical inputs fail explicitly, and the direct backwater
API rejects submerged-outlet inference. Governing selection compares only the routed inlet
candidate with a physically classified outlet candidate; inadmissible steep S2/JS1 outlet
candidates are excluded rather than selected by magnitude.

Remaining limitations are outside CS-004 acceptance: non-prismatic barrels have no claimed
profile validation, adverse slopes remain unsupported, and the approximately `1.031 m`
HY-8 crown-location difference remains external-method evidence under CS-008. Nothing was
committed, built, versioned, or published.

Verification: 38 focused profile/regime/outlet tests and all 268 repository tests passed.
Repository-wide Ruff check and format, strict Pyright, Markdown lint with MD013 excluded,
and `git diff --check` passed. Ruff mechanically reformatted four overlength lines in the
already-modified inlet solver without changing its logic.

### CS-005 - Complete public results and diagnostics

Status: Complete. Owner: Unassigned. Updated: 2026-09-13. Next review: 2026-09-20.

Scope: preserve each adopted calculation value as a typed value plus selection basis,
source, applicability, and override/default status. Expose those adopted values alongside
candidate headwaters, depths, velocities, losses, convergence data, profile state, and
structured warnings needed for engineering review. Preserve zero-flow and inactive-group
exactness. Do not discard provenance by copying only `selection.value` into a result.

Implemented: barrel results retain adopted values and provenance, all available
headwater candidates, profile classification, and typed limitation warnings. Rating-curve
points retain the full structured warnings, while inventory group and crossing rows expose
deduplicated warning codes. Loss components, convergence records, and selected profile
objects are exposed through typed public results.

Boundary: expose computations already performed by the selected hydraulic methods. Do
not change equations, profile selection, or acceptance thresholds under CS-005.

Acceptance: fields are documented and typed, end-to-end tests verify their meaning,
future plotting can consume results without rerunning private solver internals, and a
caller can audit every adopted empirical/default value without inspecting package globals.

Depends on: CS-002 and CS-004.

Handoff (2026-09-08): the ready non-method-changing portion is implemented. Typed
`HeadLossComponents` records expose full-flow component losses and the entrance loss
separately calculated by free-surface paths. Labelled `ConvergenceRecord` values retain
applicable depth, profile-boundary, jump, barrel-discharge, and crossing-headwater
`RootResult` evidence. The profile already selected by the solver is retained for future
plotting. No equations, regime/profile choices, tolerances, or engineering acceptance
thresholds changed, and no new source assumption was introduced.

Focused verification passed 88 tests across critical depth, normal depth, profiles,
regimes, crossings, and model contracts. The full suite passed 259 tests; Ruff check and
format, strict Pyright, Markdown lint, and `git diff --check` passed. Remaining limitations
are intentionally explicit: free-surface methods do not separately calculate scalar
friction, exit, or total loss; interpolation fallbacks have no root result; and full-flow
longitudinal points are not calculated. CS-002 is now settled; recheck the public fields
after CS-004 settles before marking CS-005 complete or starting CS-011. Nothing was
committed, built, or published.

Completion handoff (2026-09-08): the post-CS-004 audit found and closed one remaining
provenance gap. `ExitLossSelection` now preserves the adopted `Ko`, selection basis, and
HDS-5 Equation 3.4c source for the standard reservoir/pool assumption; numeric overrides
are explicitly labelled as user supplied. Both `FullFlowOutletResult` and
`BarrelHydraulicResult` expose the selection, and inventory `AdoptedParameterSet` records
retain it and register its source. End-to-end tests also confirm that accepted M2/full,
S1/full, and JS1/full results retain their selected profile objects and transition details
for plotting without rerunning private solver code.

CS-005 acceptance is complete without changing equations, profile selection, or numerical
tolerances. Remaining limitations are method-shaped rather than missing diagnostics:
free-surface paths do not calculate separate scalar friction, exit, or total losses;
interpolation fallbacks have no fabricated root record; and the full-flow method does not
calculate longitudinal profile points. Nothing was committed, built, versioned, or
published.

Verification: `python -m pytest -q tests/test_outlet_control.py tests/test_regime.py
tests/test_models.py tests/test_collection.py tests/test_crossing.py tests/test_rating_curve.py`
passed 87 tests; `python -m pytest -q` passed all 270 tests. Repository-wide Ruff check and
format, strict Pyright, Markdown lint with MD013 excluded, and `git diff --check` passed.

Maintenance handoff (2026-09-13): resolved GitHub issue #10 without changing discharge,
headwater, regime, or loss calculations. Multi-barrel `GroupHydraulicResult` values now
carry the stable `representative_barrel_equal_flow` notice with NCHRP 734 Chapter 5
provenance. `CrossingHydraulicResult` aggregates it, and inventory group/crossing summaries
retain its code and register its source. The message distinguishes suitability for total
flow from uncertainty in barrel-specific discharge and velocity under nonuniform approach
or depressed-barrel conditions. Single-barrel groups do not receive the notice, and no
efficiency factor was introduced. Focused model, crossing, collection, and public API tests
passed (`69 passed`); the full suite passed (`345 passed`). Ruff check and format (`115
files already formatted`), strict Pyright (`0 errors`), Markdown lint, strict MkDocs,
retained-wheel verification, and `git diff --check` also passed. HY-8 was not run because
the task exposes an existing literature-backed applicability limit and changes no hydraulic
method. Nothing was built, versioned, published, committed, or pushed.

Maintenance handoff (2026-09-13): resolved GitHub issue #7 with the public
`HydraulicResultStatus` values `valid`, `valid_with_advisory`, `approximate`, and
`unresolved`. Status is derived from stable warning codes: high-head inlet-control warnings
remain advisories, the explicit outlet-depth fallback is approximate, and unresolved mixed
flow remains unresolved. The most conservative active child governs group/crossing status;
inactive groups are excluded. Rating-curve points and inventory group/crossing rows retain
the computed status. Documentation explicitly states that this is computational/hydraulic
resolution, not regulatory or design approval. Focused result/regime/crossing/rating/
inventory/API tests passed (`92 passed`); the full suite passed (`345 passed`). Ruff check
and format (`115 files already formatted`), strict Pyright (`0 errors`), Markdown lint,
strict MkDocs, retained-wheel verification, and `git diff --check` passed. No hydraulic
equation or acceptance threshold changed. Nothing was built, versioned, published,
committed, or pushed.

### CS-006 - Independent validation for Phases 1-10

Status: Complete. Owner: Unassigned. Updated: 2026-09-13. Next review: 2026-09-20.

Scope: retain analytical unit tests, but add published geometry/hydraulic examples,
profile cases, group/crossing conservation cases, and rating curves spanning regime
changes. Separate equation transcription, numerical convergence, and method validity.

Acceptance: `docs/validation.md` records inputs, expected results, source locator,
absolute/relative differences, regime agreement, and quantity-specific tolerances.

Immediate deliverables: add primary or independently calculated fixtures first for
geometry, critical/normal depth, and full-flow losses. Add combined inlet/profile and
rating-curve fixtures only after the corresponding CS-003/004 method is accepted. Do not
use one public package entry point as the oracle for another entry point.

Depends on: CS-001, CS-003, and CS-004.

Handoff (2026-09-08): the immediate primitive-fixture portion is complete. Existing
rectangular critical depth, rectangular Manning normal depth, circular full geometry, and
circular full-flow loss tests now compare against fixed independently calculated values
rather than recomputing their expectations alongside the assertions. `docs/validation.md`
records every input, expected result, observed difference, source locator, and
quantity-specific numerical tolerance.

Focused verification with `python -m pytest -q tests/test_critical.py tests/test_normal.py
tests/test_outlet_control.py` passed 32 tests. An initial full run passed 267 tests but failed
the unrelated CS-007 fixed wall-clock assertion at `0.510 ms/evaluation`; separated runs
passed all 261 non-performance tests and all 7 performance tests unchanged. After the user
temporarily relaxed that ceiling to `0.6 ms/evaluation`, the final full run passed all 268
tests. Ruff check and format, strict Pyright, Markdown lint with MD013 excluded, and
`git diff --check` passed.

Remaining acceptance work is intentionally limited to published profile cases,
group/crossing conservation fixtures, and rating curves after CS-004 settles. The new
fixtures do not claim that internal equation agreement proves combined-method validity.
The recurring environment-sensitive timing failure remains assigned to CS-007. Nothing
was committed, built, versioned, or published.

Completion handoff (2026-09-08): CS-006 is complete for the currently supported methods.
Fixed independent references now cover the hydraulic primitives and every accepted
prismatic profile family. New system fixtures verify a three-barrel group and a two-group
crossing against an independently evaluated HDS-5 full-flow headwater and the exact
equal-barrel conservation split. A fixed four-point performance curve independently
reproduces unsubmerged, transition, and submerged inlet-control headwaters.

The source and method locators, inputs, expected results, observed differences, regime
agreement, and quantity-specific tolerances are recorded in `docs/validation.md`. The
fixtures do not call one public package entry point to generate expectations for another.
Remaining limitations are stronger evidence for unequal barrels, tailwater rating
relationships, storage routing, and roadway overtopping; these are future validation or
deferred-feature work rather than failures of the accepted scope. Nothing was committed,
built, versioned, or published.

Verification: `python -m pytest -q tests/test_crossing.py tests/test_rating_curve.py`
passed 15 tests; `python -m pytest -q` passed all 272 tests. Repository-wide Ruff check and
format, strict Pyright, Markdown lint with MD013 excluded, and `git diff --check` passed.

Issue #8 follow-up (2026-09-13): a version-pinned six-point comparison against FHWA HY-8
`8.0.1.2` now covers a heterogeneous circular/box crossing, raised-group activation,
unequal flow allocation, differing active-group regimes, and a rating transition. The
tracked CSV records headwater, group flow, outlet velocity, classification, and
conservation evidence. Source-tree and installed-package reproductions were byte-identical;
ordinary tests consume the fixture without executing HY-8.

Maximum differences from HY-8 were `0.023668 m` common headwater, `0.017134 m3/s`
per-group discharge, and `0.028003 m/s` per-barrel outlet velocity, all within the explicit
quantity-specific tolerances documented in `docs/validation.md`. This remains external
software-comparison evidence, not equation authority or field validation. Tailwater rating
relationships, storage routing, irregular road crests, and submerged roadway overtopping
remain outside this fixture.

Verification: `python -m pytest -q` passed all 371 tests. Repository-wide Ruff check and
format (`118 files already formatted`), strict Pyright, Markdown lint with MD013 excluded,
strict MkDocs, and `git diff --check` passed. No hydraulic equation, public API, package
version, or release artifact changed.

### CS-007 - Validate Phase 10 performance behaviour

Scope: benchmark repeated scalar and crossing evaluations on fixed cases. Prove the
full-flow candidate short-circuit cannot suppress a valid free-surface solution, or
remove it. Optimisation must not alter classifications or numerical results.

Acceptance: correctness comparison with optimisation enabled/removed, reproducible
benchmark method, recorded environment, and non-flaky performance thresholds.

Depends on: CS-004 and CS-006.

Handoff (2026-09-08): CS-007 is complete. The fixed `< 0.6 ms/evaluation` assertion was
removed because wall time depends on processor, interpreter, power state, and concurrent
load. Ordinary tests now enforce non-flaky algorithmic budgets: no more than 20 recorded
root iterations for a fixed M2 barrel, no more than 10 for each exposed root in the fixed
two-group crossing, and exactly one scalar hydraulic solve per rating-curve point.

The former full-flow-candidate shortcut remains removed. Its fixed regression case has
`HW_inlet=11.211267 m` and approximate `HW_full=11.115085 m`, satisfying the old shortcut
premise, but the validated M2 outlet candidate is higher at `11.275562 m`. Re-enabling the
shortcut would therefore change both the adopted headwater and control classification.

`benchmarks/benchmark_solver.py` provides the separate reproducible timing method with
warm-up batches, repeated samples, garbage collection disabled during measurement,
nanosecond monotonic timing, robust summary statistics, deterministic-result checks, and
JSON environment metadata. On CPython 3.14.6, Windows 10 build 19045, AMD64 Family 25
Model 97 Stepping 2 with 16 logical CPUs, seven samples measured medians of
`0.8851 ms` per fixed single-barrel evaluation and `94.2260 ms` per fixed two-group
crossing evaluation. These values are observations, not portable thresholds.

Remaining limitations: the benchmark does not pin CPU affinity or power state, does not
cover a multi-machine CI matrix, and algorithmic iteration budgets cannot detect a slower
implementation with unchanged iteration counts. Compare wall times only on equivalently
configured target hardware. Nothing was committed, built, versioned, or published.

Verification: `python -m pytest -q tests/test_performance.py` passed 7 tests and
`python -m pytest -q` passed all 272 tests. Repository-wide Ruff check and format, strict
Pyright for `src`, `tests`, and the benchmark script, Markdown lint with MD013 excluded,
and `git diff --check` passed.

### CS-008 - External verification and discrepancy evidence

Scope: operate version-pinned external software, prove configuration parity, retain
diagnostic outputs, and report differences without treating external agreement as the
definition of correctness. Do not modify solver equations under this task.

Current evidence: the 20-case HY-8 8.0.1.2 matrix covers S2, swept-out jumps, `JS1`, S1,
M2c, mixed M2/full, S1f/JS1f, fully submerged flow, and a Type `6-FFc` case. Installed
`run-hy8 2026.9.8.1` exposes inlet/outlet candidates, qualifiers, and full/free lengths.
The harness checks their internal consistency. It identifies:

- a `0.414 m` Type 6 inlet-depth difference, assigned to CS-003 for any method decision;
- a `0.997 m` long-case crown-transition difference, assigned to CS-004 for any method
  decision;
- outlet-control depth agreement within `0.008 m` across the matrix.

Immediate deliverables:

1. reproduce both differences from retained inputs and raw reports;
2. test nearby discharges to establish whether each difference is smooth or a branch
   transition;
3. record version, inputs, qualifiers, output precision, and investigated explanation;
4. hand evidence to CS-003 or CS-004 without tuning coefficients to HY-8.

Acceptance: the two discrepancies have reproducible evidence and an explicit disposition
of explained method difference, confirmed local defect, confirmed external-tool defect,
or unresolved limitation. Later HEC-RAS, SWMM, and STREAM-1D cases remain optional until
the internal methods stabilize.

Handoff (2026-09-09): the 20-case matrix was reproduced from the current solver and HY-8
8.0.1.2, then refreshed to include the settled CS-003/004 diagnostics. A new reproducible
comparison mode and 27-row CSV retain nearby-discharge evidence for both discrepancies.
Across nine Type 6 flows, the inlet-depth gap changes smoothly while all HY-8 results
remain `6-FFc`; this confirms the already warned high-head inlet-method difference. Across
18 long-barrel flows, both crown locations change continuously, all HY-8 results remain
`7-M2c`, and governing headwaters remain close; this confirms a profile-method detail
rather than a classification or parser defect. No solver equation, coefficient, selection
rule, or numerical tolerance changed.

Verification and remaining limitations: Python 3.14.6 executed the installed, hash-pinned
`run-hy8 2026.9.8.1` wheel with `PYTHONPATH` cleared and bytecode generation disabled.
Its 20-row matrix and 27-row sweep matched the retained CSVs byte-for-byte. The harness
retained and cross-checked HY-8 flow, velocity, type, inlet/outlet candidates, qualifiers,
and full/free length balance; raw ignored workspaces contain the generated project, result,
query, and plot reports. `docs/validation.md` records the fixed inputs, executable/report
precision, numeric ranges, and explicit dispositions. The 20-row and 27-row artifact assertions,
all 274 tests, strict Pyright, Markdown lint with MD013 excluded, and `git diff --check`
passed. Ruff check and format could not execute because Windows denied access to the
user-site `ruff.exe`; the edited Python was reviewed directly, and this environment issue
is recorded rather than reported as a pass. HY-8's closed high-head and profile algorithms
remain unavailable for independent reconstruction, and optional HEC-RAS, SWMM, and
STREAM-1D comparisons remain future work. Pip built only a transient editable wheel while
installing the documented user-level development tools; no release distribution was
retained. Nothing was committed, versioned, or published.

Depends on: no task for evidence collection; interpretation feeds CS-003/004 and final
acceptance feeds CS-006.

### CS-011 - Add a road-level culvert inventory and compact summaries

Use `CulvertInventory` for a collection of independent road crossings. Do not call it a
hydraulic network unless future work explicitly models hydraulic connectivity between
crossings. Each inventory item needs a stable crossing identifier and may later carry road
chainage or other caller-defined metadata without making GIS a core dependency.

The calculation/report model should expose normalized, typed records for:

- one summary row per crossing;
- optional group/barrel result rows;
- a deduplicated adopted-parameter-set catalogue;
- a deduplicated source-reference catalogue;
- warnings and unsupported/applicability notices.

Crossing and group rows should reference stable parameter-set identifiers rather than repeat
the same roughness, inlet coefficients, loss coefficients, source metadata, and assumptions
for every crossing. Deduplication must use canonical typed values, units, and provenance,
not Python object identity or formatted display text. Preserve an optional caller-supplied
parameter-set ID; otherwise generate a deterministic content fingerprint.

Acceptance:

- 50 independent crossings can be evaluated and summarized deterministically;
- repeated parameter sets and sources appear once in their catalogues;
- genuinely different values or provenance never collapse into one entry;
- input order and stable crossing IDs are preserved;
- duplicate crossing IDs fail explicitly;
- summary records contain ordinary Python values and remain independent of pandas, JSON,
  spreadsheets, GIS, and presentation formatting;
- focused tests cover empty inventory, one/many crossings, deduplication, ordering, mixed
  regimes, warnings, and repeated execution.

Depends on: CS-005. File/JSON/spreadsheet renderers remain deferred under CS-009.

Handoff (2026-09-09): the road-level inventory now preserves compact crossing and group
rows for mixed regimes and unresolved calculated results. Hydraulic warning codes and
roughness applicability-notice codes are deduplicated in encounter order at both levels;
the full typed roughness notices and their sources remain attached to adopted parameter
sets. Notice content is part of the canonical parameter-set identity, so different
assumptions cannot collapse into the same generated identifier. No calculation equation,
selection rule, or numerical tolerance changed.

Verification and remaining limitations: `python -m pytest -q tests/test_collection.py`
passed 12 tests and `python -m pytest -q` passed all 274 tests. Repository-wide Ruff check
and format, strict Pyright, Markdown lint with MD013 excluded, and `git diff --check`
passed. The model remains an ordered collection of hydraulically independent crossings,
not a connected network. Persistence, JSON/spreadsheet/GIS renderers, road chainage and
other caller metadata remain CS-009 or future consumer work. Group rows describe the
identical-barrel calculation unit and do not expand into repeated per-barrel presentation
rows. Nothing was committed, built, versioned, or published.

### CS-012 - Release readiness and wheel handoff

Scope: perform release work only after the requested calculation milestone has satisfied
its validation gates. This task does not expand hydraulic scope.

Acceptance:

- task/status documents agree and no provisional method is described as validated;
- focused and full tests, Ruff, strict Pyright, Markdown lint, package build, and
  `git diff --check` pass;
- the universal wheel installs into an isolated target and passes a public-API smoke test;
- the package version is deliberately bumped from `0.2.0.dev1` for the handoff artifact;
- release notes identify supported calculations, evidence boundaries, and known limits;
- no commit, tag, publication, or upload occurs without explicit user instruction.

Depends on: CS-003, CS-004, CS-005, CS-006, CS-007, CS-011, and whichever portion of
CS-002 is claimed as supported by the release.

Handoff (2026-09-09): version `26.9.9.1` is the first packaged alpha milestone for local
integration testing. The metadata, README, packaging guide, and release notes consistently
retain the provisional engineering boundary. Thin Windows wrappers based on the proven
`ryan-tools` workflow now build, verify, select, and optionally install the latest local
wheel while preserving failure exit codes. Wheel verification checks the version, SPDX
licence expression, declared and byte-equivalent packaged licence, typed marker, required
package content, and excluded development/reference inputs.

The repository cleanup removed the superseded root research prompt, an incomplete raw
report, and an older report with non-durable tool citations. Their reviewed findings remain
in the source-pinned `docs/research/` records; the raw files and obsolete history were
intentionally discarded. The current work plan, legacy scenario evidence, primary PDFs, and HY-8
comparison evidence were retained because current documentation still relies on them.

Follow-up layout cleanup moved the long-term plan from the repository root to `docs/work/`,
where its planning role is distinct from the active register. `scripts/compare_hy8.py`
remains correctly isolated as optional external-validation tooling. All 17 test modules
exercise current numerical, hydraulic, model, solver, inventory, or performance contracts;
none depends on the retired implementation or HY-8. Unique release-note, HEC-14, HEC-26,
and `ShapeDB.dat` evidence was moved into `reference_docs/`; three duplicate PDFs, the
superseded January 2012 HDS-5 copy, and the rejected v7.6 tutorial were removed with the
now-empty `hy8/` directory.

Verification and limitations: `python -m pytest -q` passed 274 tests. Repository-wide Ruff
check and format, strict Pyright including `scripts/`, Markdown lint with MD013 excluded,
and `git diff --check` passed. `package_and_install.bat --dry-run` built and verified the
`26.9.9.1` universal wheel without altering the user installation. The wheel installed into
an isolated temporary target; its import was proven to originate there, package metadata
reported `26.9.9.1`, and a public circular critical-depth calculation succeeded. This handoff
creates a local artifact only: nothing was committed, tagged, uploaded, or published.
Hydraulic and product limitations are listed in
the maintained release notes; this packaging milestone does not expand engineering acceptance.

Release follow-up (2026-09-09): the package now uses the `yy.m.d.vv` calendar-version
scheme and the first release is `26.9.9.1`. The retained wheel is 77,379 bytes with SHA-256
`29880984ad4f40f808d993193729287c57e34107a900e96c676ba19af8d3b7d6`. A Windows GitHub
Actions workflow runs the repository checks and wheel build on pushes and pull requests.

Final wheel-only verification: `package_and_force_install.bat --dry-run` exercised the
build, archive checks, latest-wheel selection, and `--force-reinstall --no-deps` command
without changing the user installation. The wheel installed into a fresh isolated target
and passed the public smoke calculation. Its SHA-256 is
`50728cf4efd013c034de87b914d5ef6a556f3c961f8d93605eacd67b325b50d5`; no `.tar.gz`
artifact remains. The final 274-test suite, Ruff check/format without cache, strict Pyright,
Markdown lint, wheel verification, and `git diff --check` all passed.

Evidence-directory follow-up: `hec14.pdf`, `hec26.pdf`, `HY-8 7.6 Release Notes.pdf`,
and `ShapeDB.dat` moved into `reference_docs/`; the empty `hy8/` directory and its ignore
rule were removed. SHA-256 checks confirmed every retained reference file against
`docs/research/local_evidence_inventory.md`, and Git attributes confirmed LFS handling for
the three PDFs and binary data file. The full 274-test suite and every repository/package
gate remained green after the move.

## CS-017 - Transactional calendar-version packaging

Status: Complete. Owner: Unassigned. Updated: 2026-09-13. Next review: 2026-09-20.

Boundary: make the existing local wheel workflow increment the normalized `yy.m.d.vv`
version automatically, build and verify away from `dist/`, and replace prior project
artifacts only after the new wheel passes verification. Preserve an explicit-version
override and a no-bump mode for CI. Do not add package-index publication, GitHub Releases,
CI artifacts, or office-network synchronization.

Acceptance criteria:

- same-day builds increment `vv`, while a new local date resets it to `1`;
- invalid or non-increasing explicit versions fail before changing files;
- build or verification failure restores `pyproject.toml` and retains the prior wheel;
- successful promotion leaves exactly one current `ryan_culverts-*.whl` in `dist/`;
- CI builds the declared version without modifying it; and
- focused packaging tests and all repository/package checks pass.

Handoff (2026-09-09): complete. The default `package.bat` path advanced `26.9.9.1` to
`26.9.9.2`, staged and verified the wheel before promotion, and left exactly one current
project wheel. The CI `--no-bump` path rebuilt `26.9.9.2` without changing metadata.
Thirteen focused packaging tests cover increments, rollover, validation, rollback, and
promotion. The full 287-test suite, Ruff, strict Pyright, Markdown, whitespace, wheel, and
isolated zip-import checks passed. The final wheel is 77,413 bytes with SHA-256
`974df027cea6c74d4e2f2083261fed4e4e528c10da56797c6c41eba813e7cb82`.

The build uses the packaging machine's local date and deliberately performs no network
copy, commit, push, tag, or publication. Pull the repository and verify the system date
before packaging from another location.

Maintenance handoff (2026-09-13): resolved GitHub issue #5 locally. Current-version prose
now points to authoritative `pyproject.toml` and the sole retained wheel instead of
duplicating a value; the changelog records packaged version `26.9.10.2`. Retained-wheel
verification now rejects zero, multiple, or incorrectly named project wheels before
checking embedded metadata, and CI performs that check before rebuilding. Two focused
regression tests bring `tests/test_packaging.py` to 15 passing tests. The full suite passed
with 335 tests, Ruff check and format (`115 files already formatted`), strict Pyright (`0
errors`), Markdown lint, strict MkDocs, and `git diff --check`. A fresh isolated wheel build
also passed verification (`94,627` bytes; SHA-256
`1c26023545d08e2b170ca6c37feb0f04c3b72d50093cef2603390763d96e3aee`). The tracked wheel
was verified unchanged; nothing was published.

## Deferred and future scope

### CS-009 - Versioned JSON/configuration boundary

Add only for a concrete CLI, service, or project-file consumer. Define schema version,
SI units, enum representation, user-default overrides, source provenance, unknown-field
policy, migration behaviour, and round-trip tests. Keep JSON parsing out of the
hydraulic equations.

### CS-010 - Constant-crest roadway overtopping

Status: Complete. Owner: Unassigned. Updated: 2026-09-10. Next review: 2026-09-20.

Boundary: add a typed constant-elevation roadway crest, evaluate unsubmerged broad-crested
weir flow using FHWA HDS-5 Equation 3.9, and solve a common headwater that conserves total
flow between culvert groups and the roadway. Require an explicit SI discharge coefficient;
do not imply that one coefficient fits every roadway. Fail closed when tailwater exceeds
the crest because the HDS-5 Figure 3.11C submergence correction is not yet digitised.

Acceptance evidence: `RoadwayWeir`, `calculate_roadway_overtopping`, and the crossing result's
separate culvert/roadway discharge properties are public and typed; analytical equation,
inactive-flow, unsupported-submergence, roadway-only, and combined-flow tests pass; inventory
summaries retain roadway crest and flow; and the method and limitations are documented.

The formerly bundled design search, plotting, shapes/materials, blockage, uncertainty, and
advanced roadway behaviour are now CS-023 through CS-028.

### CS-013 - Modern box inlet configurations

Status: Complete. Owner: Unassigned. Updated: 2026-09-10. Next review: 2026-09-20.

Boundary: model wingwall flare, crown treatment, corner-fillet size, skew, barrel count,
span-to-rise applicability, and net area before selecting corrected FHWA-HRT-06-138
Tables 11 and 12. Reject unsupported combinations and polynomial results outside the
report's approximately `0.4 < HW/D < 2.3` useful range. Keep these coefficients separate
from HY-8's recomputed South Dakota-box polynomial.

Acceptance evidence: `FilletedRectangularGeometry` represents all four 45-degree corner
fillets and supplies net area and depth-dependent section properties. `ModernBoxInlet`
resolves only supported Figure 93 identities to source-bearing Table 11 and 12 records.
The direct polynomial uses `Q/(A*sqrt(g*D))`. The Appendix D FC-D-30 Q25 test reproduces
the published critical depth and final pool water level using Sketch 2, `Ke = 0.32`, the
filleted section, and the published approach area; no sharp-corner substitution is made.

### CS-014 - Context-rich NCHRP 734 refinements

Status: Split without implementation. Owner: Unassigned. Updated: 2026-09-10.

This umbrella was too broad. Its independent deliverables are CS-030 (slipline host/liner
geometry and composite roughness), CS-031 (receiving section and Borda-Carnot exit loss),
CS-032 (buried-invert geometry and coefficient disposition), and CS-033 (depth-dependent
roughness). No NCHRP equation or coefficient was added while performing the split.

### CS-029 - Discharge-dependent tailwater boundaries

Status: Partial. Owner: Unassigned. Updated: 2026-09-13. Next review: 2026-09-20.

Add a typed, monotonic discharge/elevation rating curve with defined interpolation and
out-of-range policy, then consider supported rectangular/trapezoidal/irregular channel
normal-depth boundaries separately. Do not import HY-8 project-card semantics into the
hydraulic core.

Handoff (2026-09-10): the supplied bundle's Manning increment is integrated without
replacing newer roadway or inverse-solver work. Rectangular and asymmetric trapezoidal
(including triangular) open-channel sections feed a generic Brent-solved normal-depth
calculation. Standalone barrels use barrel flow, standalone groups use total group flow,
and crossings resolve one receiving stage from total crossing flow before allocation.
Results retain the resolved method, distinct method and project-parameter sources,
normal-depth calculation, and convergence. The ambiguous `source` field was removed in
favour of the breaking, explicit `method_source` contract; channel-normal depth is
documented separately from culvert-relative tailwater depth. Hand-calculated fixtures
cover four section configurations and crossing/rating flow basis. A reusable
`hydraulic_radius()` utility keeps `A/P` outside the minimal open-channel protocol.

Handoff (2026-09-13): `TailwaterRatingPoint` and `TailwaterRatingCurve` provide the planned
user-supplied boundary. Construction requires at least two finite points, nonnegative and
strictly increasing discharge, nondecreasing absolute water-surface elevation, and an
explicit project `rating_curve_source`. Resolution returns exact tabulated elevations or
linear interpolation inside the closed range and rejects both extrapolation directions.
`TailwaterResolution` retains the full curve, its source, requested discharge, resolved
elevation, and an exact-point or linear interpolation classification. Public exports, API
reference, computational basis, architecture, changelog, and validation evidence were
updated. Tests cover all specified validation failures plus barrel, group, total-crossing,
and independently recalculated crossing-rating flow bases.

Remaining before completion: record an independent external comparison for the Manning
boundary. Irregular sections, compound roughness, and downstream gradually varied flow
remain separately scoped future work.

Acceptance criteria for the rating boundary:

- expose a typed boundary containing at least two finite `(Q, WSE)` points;
- require strictly increasing discharge and nondecreasing water-surface elevation;
- return the supplied elevation exactly at a curve point and use linear interpolation
  only between the two bracketing points;
- reject discharge below or above the supplied range by default rather than silently
  clamping or extrapolating;
- retain the curve, its source, interpolation method, requested discharge, and resolved
  elevation in `TailwaterResolution`;
- test exact points, interpolation, nonfinite values, too few points, duplicate or
  decreasing discharge, decreasing elevation, and both out-of-range directions; and
- prove that crossings resolve the curve from total crossing flow before allocation and
  that crossing rating curves resolve it independently at every discharge point.

Acceptance criteria for independent Manning validation: compare several normal-depth
cases spanning rectangular, symmetric/asymmetric trapezoidal, and triangular sections and
more than one flow scale with HEC-RAS or another identified trusted calculation. Record
the external tool and version, complete SI inputs, expected and observed depths, numeric
differences, tolerances, and any modelling assumptions in `docs/validation.md`. This is
external comparison evidence, not permission to tune the Manning equation to software.

Verification (2026-09-13): `python -m pytest -q` passed 358 tests. `python -m ruff check .`,
`python -m ruff format --check .` (116 files), strict Pyright (0 errors), Markdown lint with
MD013 excluded, strict MkDocs build, and `git diff --check` passed. No HY-8 executable
comparison was required or run; the remaining external Manning comparison was not run.

### CS-030 - Slipline host/liner geometry and composite roughness

Represent the host barrel, liner opening, annulus/placement context, and the source and
applicability of any composite roughness relationship. Do not infer one composite Manning
value from two material labels.

### CS-031 - Receiving section and Borda-Carnot exit loss

Represent downstream flow area and the sudden-expansion context before implementing the
NCHRP Borda-Carnot refinement. Preserve the current explicit HDS-5 reservoir/pool
`Ko = 1.0` method as a separate option.

### CS-032 - Buried-invert geometry and evidence disposition

Represent the reduced opening, natural bottom, embedment depth, and wetted geometry.
Do not implement NCHRP's original embedded coefficients; the documented dimensionless-flow
error and false 50-percent embedded beveled data remain disqualifying. Treat the HY-8
synthetic high-flow extension only as implementation-comparison evidence.

### CS-033 - Depth-dependent roughness

Define the vertical/material zones, conveyance combination method, and supported hydraulic
states before adding variable roughness. Keep it independent of CS-030 so either method can
be reviewed and validated without adopting the other.

### CS-034 - Inverse capacity helpers

Status: Complete. Owner: Unassigned. Updated: 2026-09-13. Next review: 2026-09-20.

Expose discharge for a target absolute headwater for one barrel, an identical-barrel group,
or a complete crossing including roadway flow. Provide HW/D only for a single barrel where
the reference invert and rise are unambiguous. Preserve zero capacity below activation and
round-trip the crossing result through the forward common-headwater solver.

Maintenance handoff (2026-09-13): GitHub issue #1 is implemented locally. All four public
inverse helpers now accept `TailwaterInput`. Fixed-stage inputs retain their established
direct inverse path. A discharge-dependent boundary instead uses a coupled Brent solve whose
residual calls the authoritative forward barrel, group, or crossing solver and resolves
tailwater at every candidate discharge. Standalone groups use total group flow; mixed-group
crossings use total crossing flow before allocation and preserve supported unsubmerged
roadway overtopping. `TailwaterRatingCurve` exposes its closed discharge bounds to the
inverse bracket, with explicit failures when a target would require clamping or
extrapolation. Tests cover Manning forward/inverse round trips for a barrel, HW/D, a
three-barrel group, a heterogeneous circular/rectangular crossing, and a combined
culvert/roadway crossing, plus bounded rating-curve success and both range failures.

Verification: `python -m pytest -q` passed 369 tests. `python -m ruff check .`,
`python -m ruff format --check .` (117 files), strict Pyright (0 errors), Markdown lint with
MD013 excluded, strict MkDocs build, and `git diff --check` passed. No new HY-8 comparison
was required or run. The coupled inverse checks are consistency and boundary-contract
tests, not independent combined-method hydraulic validation.

### CS-015 - Austroads worked-example clarification

Resolve AGRD05B-23 edition 1.2 Section 3.15.1's full-flow velocity inconsistency before
using it as a numerical fixture: printed page 105 states `2.5 m/s`, then tabulates `2.75
m/s` and uses the latter to obtain `3.08 m/s`. Seek an erratum or corrected edition; until
then use the case only as a workflow and reporting checklist.

## CS-016 - Documentation site and Pages publication

Status: Complete. Owner: Unassigned. Updated: 2026-09-13. Next review: 2026-09-20.

Boundary: design a navigable MkDocs information architecture for the existing maintained
documentation, add an intentional landing page and API reference, and validate the site
strictly before enabling GitHub Pages. Do not copy `run-hy8` navigation blindly or publish
legacy/research material without deciding whether it belongs in the public site.

Acceptance evidence:

- MkDocs and its selected theme/API plugins are declared directly in the development extra;
- `mkdocs.yml` deliberately navigates every maintained page with strict link validation;
- `mkdocs build --strict` passes locally, in ordinary CI, and before deployment; and
- the workflow follows the established `run-hy8` build/deploy split with deployment
  permissions confined to the dependent deploy job.

Handoff (2026-09-10): refined the Material site with tabbed top-level navigation, light and
dark palettes, improved search behaviour, and a shorter landing-page path into the main user
tasks. The former single long API document is now an overview plus focused pages for inputs,
results, solvers, hydraulic methods, and built-ins. An explicit inventory check confirmed that
the split documents all 167 public names in `culvert_solver.__all__`, excluding only the version
attribute described on the overview page. Local verification passed: `python -m pytest -q`
(`333 passed`), `python -m ruff check .`, `python -m ruff format --check .`,
`python -m pyright` (`0 errors`),
`python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`,
`python -m mkdocs build --strict --site-dir site`, and `git diff --check`. GitHub CI and Pages
deployment were not run for the uncommitted documentation changes.

Maintenance handoff (2026-09-12): repaired the work-register issue references that strict
Markdown lint interpreted as malformed ATX headings by making them explicit GitHub issue
links. Local verification passed: `python -m pytest -q` (`333 passed`),
`python -m ruff check .`, `python -m ruff format --check .` (`115 files already formatted`),
`python -m pyright` (`0 errors`),
`python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`,
`python -m mkdocs build --strict --site-dir site`, and `git diff --check`. GitHub CI was not
rerun because the repair remains uncommitted.

Maintenance handoff (2026-09-13): resolved GitHub issue #6 locally without changing
hydraulic equations or thresholds. Audited the 169-name `culvert_solver.__all__` surface:
all 168 names other than separately documented `__version__` appear exactly once across the
API pages, and all 128 callable exports have docstrings. `TailwaterInput` is now an explicit
top-level export and API input contract. The six public forward functions annotated with it
name it in their documentation; barrel, group, crossing, and rating-curve descriptions now
state the applicable discharge basis. The stale claim that hydraulic jumps and mixed
free/full states are unsupported was replaced with the current bounded support statement.
Regression tests enforce callable documentation, exact API-page coverage, and the six
tailwater annotations/docstrings. Focused public API validation passed with 10 tests and a
strict MkDocs build. Combined full-repository validation passed with 343 tests, Ruff check
and format (`115 files already formatted`), strict Pyright (`0 errors`), Markdown lint,
strict MkDocs, retained-wheel verification, and `git diff --check`.

## CS-019 - Compatibility metadata and installed-wheel CI

Status: Complete. Owner: Unassigned. Updated: 2026-09-10. Next review: 2026-09-20.

Boundary: reconcile `requires-python` with the versions actually supported, then test the
pure-Python wheel on intended Windows, Linux, and macOS interpreters. Keep HY-8 comparison
work Windows-only and separate from portable solver tests. Do not claim support from a
successful build alone. CI verifies the wheel but does not publish a second copy.

Acceptance evidence: `requires-python >=3.14,<3.15` matches the sole supported baseline and a
Windows/Linux/macOS Python 3.14 matrix builds, installs, imports, checks metadata version,
and runs a public geometry calculation outside the source tree without publishing.

## CS-020 - Public API and package presentation

Status: Complete. Owner: Unassigned. Updated: 2026-09-10. Next review: 2026-09-20.

Boundary: define stable public imports, package-version discovery, compatibility and
deprecation policy, a concise changelog, and well-known documentation/release-note project
URLs that do not require GitHub Releases. Do not broaden hydraulic support or promote
provisional calculations as stable.

Acceptance evidence: `culvert_solver.__all__` defines the supported import surface,
`culvert_solver.__version__` reads installed metadata, public API tests and the portable
wheel smoke test cover both, the alpha compatibility policy and changelog are navigable,
and package metadata links documentation and the changelog.

## CS-021 - Repository maintenance guidance

Status: Deferred. Owner: Unassigned. Updated: 2026-09-12. Next review: 2026-09-20.

Boundary: add concise contribution and security-reporting guidance, dependency-update
configuration, and documented branch-protection expectations appropriate to a small
maintained repository. Avoid enterprise process that does not reduce an identified risk.

Acceptance criteria: contributors can reproduce checks, hydraulic defects have a private
reporting path where necessary, automated dependency changes run the normal CI, and the
documented main-branch rules match GitHub settings.

Lint-baseline handoff (2026-09-11): Ruff is pinned to 0.16.6 for both the development
extra and `required-version`, and the expanded rule set passes repository-wide. Ruff's
safe fixes and narrow manual cleanups sorted public exports, normalized annotations and
docstring headings, used `pairwise` for adjacent values, and clarified tests without
changing hydraulic equations. A follow-up review exposed 678 unsafe candidates. Six
locally equivalent simplifications were applied: five single-assignment conditional
expressions and one float equality membership check. Five safe `cast` annotation quoting
fixes found during the same review were also applied. The other 672 unsafe candidates were
reviewed again against the repository policy. The 315 absolute package-import rewrites
were rejected and the `TID` selector removed because internal imports should remain
package-relative where possible. The 75 type-only import moves were rejected and the `TC`
selector removed because runtime import reduction is not a repository requirement. All
282 exception-message rewrites were applied, retaining each exception type and text while
moving its message into a local `msg` variable. Explicit policy exclusions still retain
existing unhashable geometry, trusted fixed subprocess commands, cycle-breaking local
imports, invariant assertions, and auditable decision-table complexity.

Verification: `python -m pytest -q` passed 333 tests; `python -m ruff check .` passed;
`python -m ruff format --check .` reported 115 files already formatted; `python -m
pyright` reported zero errors, warnings, or information; `python -m pymarkdown -d MD013
scan -r README.md docs AGENTS.md`, `python -m mkdocs build --strict`, `git diff --check`,
and `git diff --cached --check` passed. The remaining contribution, private security
reporting, dependency-update, and branch-protection work stays deferred.

VS Code and Ruff pinning decision (2026-09-11): keep the Ruff engine pinned to `0.16.6`
in both the development extra and `tool.ruff.required-version`. The office workflow does
not use a virtual environment. Workspace settings must not hard-code
`python.defaultInterpreterPath` or `ruff.interpreter`; developers select their installed
Python interpreter in VS Code, while the Ruff extension uses `fromEnvironment`, gives the
filesystem configuration precedence, and enables Ruff formatting on save. The
Marketplace extension is a separate, administratively installed component whose exact
approved version is selected in VS Code; the locally inspected version was
`charliermarsh.ruff@2026.78.0`. A repository extension recommendation cannot enforce that
Marketplace version.

Corporate application control must approve the user-site Ruff executable, currently
`C:\Users\Ryan.Brook\AppData\Roaming\Python\Python314\Scripts\ruff.exe`. Environment
discovery can fall back to the extension-bundled executable if Ruff is unavailable, but
the repository `required-version` check fails closed when that executable is not version
`0.16.6`; it does not install or switch versions. Both the user-site and bundled Ruff
executables were denied by the current Windows policy during this review, so no Ruff
execution is claimed. No hydraulic code or equations changed, and the test suite and HY-8
executable comparison were not run. `python -m pymarkdown -d MD013 scan
docs/work/2026-09-06-phase-0-to-10-remediation.md` and `git diff --check` passed.

Ruff policy extraction (2026-09-12): the lint and formatting configuration moved from
`pyproject.toml` to the repository-level `ruff.toml`; `pyproject.toml` remains the dependency
authority and continues to pin Ruff 0.16.6 in the development extra. The `W`, `SLOT`, `INP`,
`FBT`, and `SLF` families are now enforced. Explicit `INP001` exclusions preserve the
intentional non-package status of `benchmarks/`, `scripts/`, and `tests/`. The only active
`FBT` finding was resolved by making the private wheel-installer helper's boolean option
keyword-only. `TID`, `TC`, and `DTZ` remain outside policy; no hydraulic behaviour changed.

Verification: `python -m pytest -q tests/test_packaging.py` passed 13 tests; `python -m
pytest -q` passed 333 tests; `python -m ruff check .` passed; `python -m ruff format --check
.` reported 115 files already formatted; `python -m pyright` reported zero diagnostics;
`python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`, `python -m mkdocs build
--strict`, `git diff --check`, and `git diff --cached --check` passed.

## CS-022 - Optional GitHub Release distribution

Status: Optional. Owner: Unassigned. Updated: 2026-09-09. Next review: 2026-12-01.

Boundary: reconsider tag-driven GitHub Releases only if the Git-pulled office network
checkout becomes insufficient for remote users, traceability, or rollback. CI artifacts
are temporary build evidence, not an office installation channel, and the tracked `dist/`
wheel remains the artifact of record.

Acceptance criteria if activated: a version tag matches `pyproject.toml`, the already
verified tracked wheel is attached with a checksum, and the workflow does not create a
second different build, update the office checkout, or require office-network credentials.

## CS-023 - Design-option and minimum-size search

Status: Deferred. Owner: Unassigned. Updated: 2026-09-09. Next review: 2026-09-20.

Boundary: enumerate explicit candidate configurations and select feasible options against
typed hydraulic constraints. Keep optimisation policy outside the hydraulic equations and
retain every rejected option with its governing constraint.

## CS-024 - Optional plotting

Status: Deferred. Owner: Unassigned. Updated: 2026-09-09. Next review: 2026-09-20.

Boundary: add HGL/EGL, profile, rating-curve, and alternative-comparison plots as an optional
presentation layer over existing result objects. Do not add plotting dependencies to the
computational core.

## CS-025 - Additional shapes and materials

Status: Deferred. Owner: Unassigned. Updated: 2026-09-09. Next review: 2026-09-20.

Boundary: prioritise additional standard shapes and material records from actual project
needs, with geometry identities, coefficient applicability, source provenance, and
analytical tests completed independently of design automation.

## CS-026 - Debris and blockage scenarios

Status: Deferred. Owner: Unassigned. Updated: 2026-09-09. Next review: 2026-09-20.

Boundary: research supported blockage representations before altering effective opening
geometry or losses. Scenario assumptions must remain explicit in inputs and results.

## CS-027 - Uncertainty and sensitivity analysis

Status: Deferred. Owner: Unassigned. Updated: 2026-09-09. Next review: 2026-09-20.

Boundary: evaluate the deterministic solver over explicit parameter distributions or
bounded scenarios. Do not hide empirical uncertainty inside solver tolerances.

## CS-028 - Advanced roadway overtopping

Status: Deferred. Owner: Unassigned. Updated: 2026-09-09. Next review: 2026-09-20.

Boundary: extend CS-010 with segmented irregular/sag crest profiles and an evidenced
downstream-submergence correction. Preserve segment-level flow and correction provenance;
do not silently extrapolate digitised figures beyond their published ranges.

## Handoff template

An agent completing a task must record:

- task ID and status;
- files changed and decisions made;
- source locators and assumptions;
- focused and full verification commands with results;
- remaining limitations and the next concrete action;
- whether anything was committed, built, or published.
