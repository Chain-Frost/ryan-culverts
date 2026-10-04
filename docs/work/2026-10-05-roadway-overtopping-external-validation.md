# External validation handoff: advanced roadway overtopping

Date: 2026-10-05

Branch: `validation/roadway-overtopping-external`

Baseline: `main` at `0b79a83a83d195df39f055d173725e1ebc73aa19`

## Purpose

Externally validate the advanced roadway-overtopping implementation merged by PR #13 using a
Windows desktop environment with FHWA HY-8 and HEC-RAS available.

This task is validation-first. HY-8 and HEC-RAS are comparison evidence, not hydraulic
authority. Do not alter equations, coefficients, tolerances, or supported applicability merely
to improve agreement with an external executable.

The implementation under test already includes:

- constant and irregular roadway crest profiles;
- four-point Gaussian integration over roadway profile intervals;
- free roadway overflow;
- paved and gravel downstream-submergence correction;
- common-headwater culvert/roadway coupling;
- public per-segment roadway hydraulic state including local unit discharge, physical
  interval length, integration/effective length, free/submerged state, submergence ratio and
  factor, and source provenance.

The current CS-028 handoff explicitly records that HY-8 executable comparison has **not** yet
been run for the new roadway cases. Closing that evidence gap is the primary objective.

## Repository and branch instructions

Repository:

`Chain-Frost/ryan-culverts`

Work only from this branch:

`validation/roadway-overtopping-external`

Do not base new work on the historical branches:

- `cs-028-advanced-roadway-overtopping`
- `feature/issue-9-longitudinal-profile`

Their associated PRs (#13 and #12) are already merged into `main`.

Before changing code, read:

- `AGENTS.md`
- `docs/validation.md`
- `docs/computational_basis.md`
- `docs/hy8_feature_parity.md`
- `docs/work/2026-09-13-cs-028-handoff.md`
- PR #13 and its review/acceptance evidence

## Environment provenance

Record the exact environment before running comparisons:

- current `ryan-culverts` commit SHA;
- Python version;
- HY-8 executable file/product version;
- HY-8 executable SHA-256 if practical;
- `run-hy8` installed version, wheel hash and source commit if used;
- HEC-RAS executable/controller version;
- HEC-RAS executable SHA-256 if practical;
- Windows version where useful for reproducibility.

Prefer the already documented validation environment where available:

- HY-8 8.0.1.2;
- `run-hy8 2026.9.8.1` using the repository's documented pin;
- HEC-RAS 7.0.1;
- Python 3.14.

If the installed software differs, use the actual installed version and make the retained
evidence explicitly version-specific. Do not present results from one version as evidence
for another.

## Primary task: HY-8 roadway validation matrix

Construct a deliberately small, traceable matrix. Do not start with a large random sweep.

### Free roadway overflow

At minimum include:

1. constant-level roadway crest;
2. simple two-point sloping crest;
3. irregular/sag profile with several station/elevation points;
4. a profile where only part of the crest is active;
5. a discharge series spanning roadway activation and increasing overflow.

### Submerged roadway flow

At minimum include:

1. paved roadway;
2. gravel roadway;
3. multiple downstream-head/upstream-head ratios through the supported range;
4. points approaching, but not exceeding, the local solver's supported ratio of `0.99`;
5. equal-stage and unsupported near-equal-stage boundary behaviour.

Do not extrapolate the local solver beyond its documented applicability to obtain a prettier
comparison.

### Combined culvert plus roadway

At minimum include:

1. one simple culvert plus a constant roadway;
2. one culvert plus an irregular roadway profile;
3. a discharge sequence spanning:
   - culvert-only flow;
   - first roadway activation;
   - substantial culvert plus roadway flow;
   - supported submerged roadway flow.

Where possible, include one heterogeneous or multi-group crossing only after the simple
cases are understood.

## Input parity

For each compared case, prove that the programs are using equivalent inputs as far as their
data models allow.

Match and retain:

- roadway station/elevation coordinates;
- crest/profile extent;
- roadway surface type;
- explicit SI roadway discharge coefficient;
- culvert dimensions and number of barrels;
- culvert inverts and length;
- Manning roughness;
- entrance/inlet configuration;
- discharge;
- tailwater/boundary condition;
- any profile/default option that materially changes the external calculation.

The same explicit roadway discharge coefficient must be used in each program. Do not let
HY-8 silently select a coefficient while `ryan-culverts` uses a user-supplied value and
then interpret the resulting difference as a solver discrepancy.

## Quantities to retain and compare

At minimum retain:

- requested total discharge;
- tailwater elevation;
- common/upstream headwater elevation;
- total roadway discharge;
- total culvert discharge;
- per-group and per-barrel discharge where available;
- outlet velocity where relevant;
- HY-8 reported flow type/state;
- local roadway free/submerged state;
- local submergence ratio and factor.

For irregular roadway profiles also retain the local `ryan-culverts` segment evidence:

- source interval index;
- interval station limits;
- integration station;
- physical interval length;
- Gaussian/effective integration length;
- local unit discharge;
- local discharge contribution;
- local upstream/downstream heads;
- submergence factor/state;
- source/provenance fields.

Do not invent direct HY-8 equivalents for Gaussian quadrature segment quantities if HY-8
does not expose them. Those fields are local diagnostic evidence.

## Boundary and failure cases

Explicitly exercise and document:

- headwater exactly at crest;
- equal upstream/downstream stage;
- supported submergence ratios close to `0.99`;
- the unsupported local interval `0.99 < downstream_head/upstream_head < 1.00`;
- reverse roadway head;
- missing/unsupported roadway surface for submerged flow where applicable.

For each boundary, record what HY-8 actually does:

- returns a value;
- clamps;
- extrapolates;
- reports zero;
- reports an error/warning;
- fails;
- or exhibits behaviour that cannot be confidently interpreted.

Do not change the local fail-closed policy merely because HY-8 computes through an
unsupported range.

## Supplementary HEC-RAS comparison

Use HEC-RAS as independent supplementary evidence where the model formulations can be made
meaningfully equivalent.

Create a small 1D steady-flow model using an inline structure/roadway crossing or other
appropriate equivalent setup.

Prioritise:

1. constant roadway free overflow;
2. irregular roadway free overflow;
3. one combined culvert plus roadway case;
4. optionally a submerged case only if the HEC-RAS submergence formulation can be shown to
   be sufficiently comparable.

Match geometry, coefficient, flow and boundary conditions explicitly.

Compare:

- upstream water level;
- downstream water level;
- roadway/weir flow;
- culvert flow;
- total flow closure.

If HEC-RAS uses a materially different weir or submergence relationship, classify the
difference as a method difference rather than a local-solver defect.

Do not tune `ryan-culverts` to HEC-RAS.

## Automation and retained evidence

Prefer extending the repository's existing validation pattern rather than relying on
manual screenshots or GUI notes.

Existing examples include:

- `scripts/compare_hy8.py`
- `scripts/compare_hecras_normal_depth.py`
- `docs/validation_data/`
- `tests/test_external_crossing_validation.py`
- `tests/test_external_manning_validation.py`

Suggested deliverables:

- `scripts/compare_hy8_roadway.py`
- `docs/validation_data/hy8_8_0_1_2_roadway_overtopping.csv`
- `tests/test_external_roadway_validation.py`

If HEC-RAS automation is practical, also consider:

- `scripts/compare_hecras_roadway.py`
- `docs/validation_data/hecras_<version>_roadway.csv`

Generated HY-8/HEC-RAS project, result and workspace files should normally remain ignored
and reproducible. Commit compact CSV evidence plus enough provenance to reproduce it.

Do not commit machine-specific absolute paths.

## Comparison tolerances

Do not choose comparison tolerances merely to make tests pass.

Before setting tolerances, establish:

- HY-8 report/display precision;
- precision available in HY-8 machine-readable outputs;
- HEC-RAS reported/machine-readable precision;
- local numerical precision;
- known published-method differences.

Then define quantity-specific tolerances.

Keep external-software comparison tolerances explicitly separate from:

- numerical root tolerances;
- solver convergence tolerances;
- field/design tolerances;
- regulatory/design acceptance criteria.

If two programs implement different legitimate methods, preserve the discrepancy and explain
it instead of widening a tolerance or calibrating the local solver.

## Defect handling

If a potential genuine solver defect is found:

1. reduce it to the smallest reproducible case;
2. prove input parity;
3. inspect the primary method/source basis;
4. add a failing focused regression test;
5. only then change production code;
6. rerun the surrounding matrix to check for unintended effects.

Do not treat HY-8 or HEC-RAS as automatically correct.

## Required result classification

Classify every important case or discrepancy as one of:

- `externally corroborated`
- `explained method difference`
- `unsupported comparison`
- `genuine solver defect`
- `external-software behaviour unresolved`

Do not reduce the validation record to one overall pass/fail label.

## Scope controls

Do not use this task to:

- add floodway pavement/batter/toe/scour design calculations to `ryan-culverts`;
- add HY-8 or HEC-RAS as runtime dependencies;
- add arbitrary calibration factors;
- implement debris or blockage;
- implement project/reporting policy that belongs in `ryan-tools`;
- redesign the public roadway API without evidence of an actual defect;
- change the supported `0.99` submergence boundary merely to follow external executable
  behaviour;
- solve the separate roadway-only/no-culvert architecture issue unless it directly blocks
  a required validation case.

The downstream `ryan-tools` floodway workflow owns road-formation response and reporting.
This task is limited to validating the hydraulic state supplied by `ryan-culverts`.

## Required documentation updates

Before handoff, update as appropriate:

- `docs/validation.md`;
- `docs/hy8_feature_parity.md`;
- this work record with actual execution evidence;
- any source/provenance documentation affected by the findings.

The final record must state:

- exact software versions;
- exact compared cases;
- exact retained quantities;
- proposed/used tolerances and why;
- maximum observed differences;
- regime/state agreement or disagreement;
- discrepancy disposition;
- unresolved limitations;
- exact validation commands that were run.

## Repository validation before handoff

Run the normal repository checks from a clean working tree/environment where possible:

```powershell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m pyright
python -m pymarkdown -d MD013 scan -r README.md docs
python -m mkdocs build --strict
git diff --check
```

If packaging or wheel-facing code changes, also run the repository's package/wheel
verification procedure.

Record actual outputs. Do not claim any check passed if it was not run.

## Definition of done

The task is complete when:

- the merged advanced roadway functionality has reproducible HY-8 comparison evidence;
- irregular and submerged roadway cases are represented in retained validation data;
- at least one combined culvert/roadway sequence is externally compared;
- HEC-RAS evidence is included where the methods are sufficiently comparable, or the reason
  for excluding it is documented;
- all material discrepancies have explicit dispositions;
- compact evidence and regression tests are committed;
- documentation reflects the new validation boundary;
- repository validation has been run and recorded;
- no solver calibration has been performed solely to match an external executable.

## Follow-on work

After this task, return to `ryan-tools` PR #88 and continue the MRWA floodway-design
implementation using the now externally checked roadway hydraulic state.

A separate future core task may add support for a pure roadway/floodway crossing with no
culvert groups. That is not part of this validation task unless it becomes necessary to
construct a required comparison case.
