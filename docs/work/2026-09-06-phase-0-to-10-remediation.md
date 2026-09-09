# Phase 0-10 remediation and forward plan

Status: authoritative agent handoff, updated 2026-09-08.

## Purpose and current baseline

This record converts the review findings into bounded tasks that another agent
can execute. Phases 1-10 have substantial implementations and internal tests,
but Phase 0 research is incomplete and combined hydraulic behaviour remains
provisional. Passing tests must not be described as engineering validation.

Read these files before changing hydraulics:

1. `culvert_solver_updated_work_plan.md` for intended scope and order;
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
| CS-001 | Ready, in progress | Unassigned | 2026-09-08 | 2026-09-14 | Finish source reviews and publish explicit method decisions and fixture inputs |
| CS-002 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Monitor source revisions; reopen only for a supported new material or fallback |
| CS-003 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen only for primary evidence supporting a different transition or high-head extension |
| CS-004 | Ready, high risk | Unassigned | 2026-09-08 | 2026-09-14 | Validate mixed profiles and resolve the long-case crown-transition method |
| CS-005 | Ready, diagnostics implemented | Unassigned | 2026-09-08 | 2026-09-14 | Recheck result fields after CS-004, then unblock CS-011 |
| CS-006 | Ready in part, primitives added | Unassigned | 2026-09-08 | 2026-09-14 | Add profile, group/crossing, and rating fixtures after CS-004 settles |
| CS-007 | Blocked by CS-004/006 | Unassigned | 2026-09-08 | 2026-09-14 | Replace the temporary 0.6 ms wall-clock ceiling and rebenchmark after validation |
| CS-008 | Ready, in progress | Unassigned | 2026-09-08 | 2026-09-14 | Reproduce and explain Type 6 and crown-transition differences without tuning to HY-8 |
| CS-011 | Waiting for CS-005 | Unassigned | 2026-09-08 | 2026-09-14 | Add mixed-regime and unsupported-result inventory tests after result fields settle |
| CS-012 | Gated release task | Unassigned | 2026-09-08 | 2026-09-20 | Run the release gate and bump the version only for a deliberate wheel handoff |

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
2. explain or correct the long-case crown station (`68.483 m` local versus `69.4755 m`
   in the HY-8 plot), including a documented step-refinement check;
3. convert remaining physically unsupported profile combinations into explicit errors or
   structured limitation warnings;
4. leave the high-head inlet equation itself to CS-003.

Depends on: CS-001 and CS-003 where transition behaviour affects selection.

### CS-005 - Complete public results and diagnostics

Scope: preserve each adopted calculation value as a typed value plus selection basis,
source, applicability, and override/default status. Expose those adopted values alongside
candidate headwaters, depths, velocities, losses, convergence data, profile state, and
structured warnings needed for engineering review. Preserve zero-flow and inactive-group
exactness. Do not discard provenance by copying only `selection.value` into a result.

Implemented so far: barrel results retain adopted values and provenance, all available
headwater candidates, profile classification, and typed limitation warnings. Rating-curve
points retain the full structured warnings, while inventory group and crossing rows expose
deduplicated warning codes. Loss components and convergence records remain outstanding.

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

### CS-006 - Independent validation for Phases 1-10

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

### CS-007 - Validate Phase 10 performance behaviour

Scope: benchmark repeated scalar and crossing evaluations on fixed cases. Prove the
full-flow candidate short-circuit cannot suppress a valid free-surface solution, or
remove it. Optimisation must not alter classifications or numerical results.

Acceptance: correctness comparison with optimisation enabled/removed, reproducible
benchmark method, recorded environment, and non-flaky performance thresholds.

Depends on: CS-004 and CS-006.

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

### CS-012 - Release readiness and wheel handoff

Scope: perform release work only after the requested calculation milestone has satisfied
its validation gates. This task does not expand hydraulic scope.

Acceptance:

- task/status documents agree and no provisional method is described as validated;
- focused and full tests, Ruff, strict Pyright, Markdown lint, package build, and
  `git diff --check` pass;
- the sdist and wheel install into an isolated target and pass a public-API smoke test;
- the package version is deliberately bumped from `0.2.0.dev1` for the handoff artifact;
- release notes identify supported calculations, evidence boundaries, and known limits;
- no commit, tag, publication, or upload occurs without explicit user instruction.

Depends on: CS-003, CS-004, CS-005, CS-006, CS-007, CS-011, and whichever portion of
CS-002 is claimed as supported by the release.

## Deferred and future scope

### CS-009 - Versioned JSON/configuration boundary

Add only for a concrete CLI, service, or project-file consumer. Define schema version,
SI units, enum representation, user-default overrides, source provenance, unknown-field
policy, migration behaviour, and round-trip tests. Keep JSON parsing out of the
hydraulic equations.

### CS-010 - Broader product features

Future work includes design-option enumeration, minimum-size search, plotting/HGL/EGL
views, additional shapes and materials, roadway overtopping, debris/blockage scenarios,
and uncertainty/sensitivity analysis. Begin only after their prerequisite result fields
and hydraulic validation are complete; create separate dated work records when activated.

## Handoff template

An agent completing a task must record:

- task ID and status;
- files changed and decisions made;
- source locators and assumptions;
- focused and full verification commands with results;
- remaining limitations and the next concrete action;
- whether anything was committed, built, or published.
