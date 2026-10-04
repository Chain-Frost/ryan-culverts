# External validation handoff: advanced roadway overtopping

Date: 2026-10-05

Branch: `validation/roadway-overtopping-external`

Baseline: `main` at `0b79a83a83d195df39f055d173725e1ebc73aa19`

Status: Awaiting `run-hy8` input-contract updates. Owner: Unassigned.
Claimed and handed back by Codex desktop agent: 2026-10-05.

## Desktop investigation and dependency handoff

The user agreed to hand required wrapper changes back to `run-hy8` and resume this task
afterwards. The validation definition of done below is **not satisfied**. No hydraulic
equations, coefficients, applicability limits or existing comparison baselines were changed.

### Environment actually inspected

- `ryan-culverts` branch head: `ce5988b78350c58908e340048d0eadf81eefdb5e`.
- Python: `3.14.6`; Windows 10 Pro `10.0.19045`, build `19045`.
- HY-8 file/product version: `8.0.1.2`; executable SHA-256:
  `0b1c5e7fb6b48be9c675b5486ae9a84346f436c5c649aa5ed09a1552267ee806`.
- Installed `run-hy8` distribution reports `2026.9.8.1`. The retained wheel hash is
  `efacb82b13f0fc07fa239a9db91a3e329e87f6622e53e3c5d92525848ca70a1e`. Five installed
  Python files differ bytewise from that wheel: `hydraulics.py`, `models/__init__.py`,
  `models/base.py`, `models/project.py`, and `models/tailwater_definition.py`.
  A follow-up UTF-8 comparison confirmed these are line-ending differences only; all
  23 installed Python files match the wheel's source text. Installed file hashes are retained in
  [the package fingerprint](../validation_data/hy8_roadway_input_probe_package_hashes.json).
  Its source commit is unverified. The separate source checkout was at
  `9d578a3a7045f0aa84698964f0fb64e7347fe309`; that checkout was not used to execute HY-8.
- HEC-RAS `7.0.1` is installed; `Ras.exe` file/product version is `7.00.0001`, SHA-256
  `ce2ca395c68c4ee17387376ea3a7152c24db483488dced4eb96a59e85fd72985`.
  The controller was not invoked and no HEC-RAS hydraulic comparison was run.

PR [#13](https://github.com/Chain-Frost/ryan-culverts/pull/13) and its acceptance record were
read: they explicitly leave new roadway executable comparison outstanding.

### Input-contract findings

The tracked HY-8 manual, Section 3.3.1, printed page 41, distinguishes paved/gravel
automatic coefficient selection from the input-discharge-coefficient option. The installed
wrapper's `RoadwayProfile` has no coefficient field; its writer emits no `WEIRCOEFF` card,
and its reader drops that card. Selecting `USER_DEFINED` alone therefore does not prove
coefficient parity.

Six exploratory executable runs used the same constant crest and varied the surface
option and `WEIRCOEFF` card. Geometry was crest stations `(0, 20) m`, elevations
`(12, 12) m`, top width `10 m`; total flow `20 m3/s`, tailwater `9.7 m`. The single concrete
circular barrel was `1.2 m` diameter, `30 m` long, inverts `10/9.7 m`, Manning `0.012`,
square-edge headwall, one barrel, default profile and exit-loss settings.

With `SURFACE=3`, the card uses the US coefficient even when project display units are SI:
`C_SI = C_US sqrt(0.3048)`. A target `1.6 m^0.5/s` therefore needs card value
`2.898094224008874`, saved by HY-8 as `2.898094`. Entering `1.6` directly gave displayed
headwater `12.91 m` and roadway flow `15.44 m3/s`; the converted card gave `12.62 m` and
`15.76 m3/s`. This is input-unit evidence, not solver calibration.

For paved and gravel modes, changing that card from `1.6` to `2.898094224008874` left the
displayed results unchanged within each surface mode: headwater `12.61 m`, roadway flow
`15.78 m3/s` paved and `15.77 m3/s` gravel. The surface modes do not provide the requested
explicit-coefficient parity. A wrapper update cannot be assumed to change executable
semantics or independently select a physical surface and a fixed coefficient.

The wrapper also rejects constant tailwater at or above the lowest roadway crest before
execution. Three additional exploratory runs changed only the generated constant-tailwater
rating cards to `12.9 m`, retaining the converted coefficient card and each surface mode.
HY-8 returned finite flows; its saved files read back at `12.900000108 m`. These raw-card
probes establish that executable submerged runs are possible, but do not establish the
submergence law for `USER_DEFINED` mode.

All nine probe summaries, reported culvert flows/velocities/states and raw report hashes are
retained in [the input-probe CSV](../validation_data/hy8_8_0_1_2_roadway_input_probes.csv).
Each is classified `unsupported comparison`: these are adapter investigations, not paired
local-solver validation cases. The inferred free coefficient in the CSV uses rounded
headwater and flow and must not be treated as an exact selected coefficient.

An initial discarded probe used three points with constant-profile mode. That mode did
not represent the intended full station span; subsequent constant probes use exactly two
points. The irregular mode and its point-count requirements must be explicit before the
sloping/sag matrix is constructed.

### Concrete request for the `run-hy8` agent

Make the following changes in `run-hy8`, with its own task ownership and checks:

1. Add a typed, explicit SI roadway discharge-coefficient field for `USER_DEFINED` mode.
   Require it in that mode; reject missing, non-finite or out-of-range values. Serialize
   and read `WEIRCOEFF` using its demonstrated US-unit storage contract independently of
   project display units. Preserve it through dictionaries/configuration and round trips.
   Verify the executable/manual coefficient range rather than treating this one probe as
   a full contract. Do not silently replace it with a paved/gravel coefficient.
2. Model/document constant versus irregular roadway profiles and validate their respective
   station counts and extents. The manual specifies 3-15 points for an irregular profile;
   represent a two-point linear slope with an explicitly collinear middle point if required.
3. Replace the blanket `constant_elevation >= crest` rejection with a documented supported
   submerged-roadway input path. Retain invalid-input checks; verify the actual saved
   tailwater, roadway extent and selected surface/coefficient after executable execution.
4. Investigate and retain evidence for `USER_DEFINED` submergence semantics. Establish
   whether explicit coefficient and independently selected paved/gravel correction can
   coexist in HY-8 8.0.1.2. If they cannot, expose that limitation and classify the later
   submerged comparison accordingly; do not imply that a new API field fixes it.
5. Build an identifiable validation wheel/source revision and verify the installed package
   matches it. Add focused read/write, unit-conversion, config and executable input-parity
   tests. Keep HY-8 file adapters and parsing in `run-hy8`.

No `run-hy8` files were changed and no issue/comment/message was sent externally. This is
a reviewable request for the next agent, not a claim that those updates have been made.

### Validation limits and resumption

HY-8 reports these quantities to two decimal places. No local/external acceptance tolerance
was selected, and no maximum local/external difference or state agreement can be reported:
paired solver comparisons have not run. Displayed flow closure in the nine probes is
within `0.01 m3/s`; this records rounding, not engineering acceptance. Crest activation,
irregular profiles, supported ratios near `0.99`, equal stage, the unsupported gap, reverse
head and missing-surface boundaries remain outstanding in the required matrix.

HEC-RAS comparison is deferred while the primary HY-8 input contract is resolved. Its
roadway formulation also uses upstream **energy** head; equivalent approach-section and
velocity-head treatment must be demonstrated before comparing it to the local stage-based
input. See the official
[HEC-RAS weir coefficient reference](https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.5/modeling-culverts/culvert-data-and-coefficients/weir-flow-coefficient).
This is an outstanding supplementary comparison, not a permanent exclusion.

Resume on this branch using the verified updated wrapper. Run the small constant/free case
first, then the sloping/sag, submerged and combined sequences below. Retain local Gaussian
segment evidence and discrepancy dispositions; choose quantity-specific tolerances from
output precision and documented method differences. Add external regression tests only
once matched, version-pinned evidence exists. No regression assertion should enshrine the
exploratory probes as hydraulic truth.

### Commands executed during investigation

The generated projects, reports and temporary exploratory drivers remain ignored under
`validation_artifacts/roadway-probe/`. The three drivers used the installed wrapper and
`HY864.exe -OpenRunSave`; they injected the known `WEIRCOEFF` card into wrapper-generated
files before execution. The submerged driver additionally replaced the constant rating
stage cards. They are exploratory local artifacts, not a maintained comparison harness.

```powershell
$env:PYTHONPATH='src'
python validation_artifacts/roadway-probe/probe.py
python validation_artifacts/roadway-probe/probes.py
python validation_artifacts/roadway-probe/subprobe.py
```

All three completed with exit code 0. Inline Python commands extracted retained summaries
through `run_hy8.parse_rst` / `Hy8Results`, read saved projects with
`load_project_from_hy8`, and compared installed Python files to the retained wheel.
`python --version`, `python -m pip show run-hy8`, executable `VersionInfo`, `Get-FileHash`,
and `Get-CimInstance Win32_OperatingSystem` supplied the environment evidence above.

Repository checks after the documentation/evidence changes:

- `python -m pytest -q`: **398 passed**, 17.07 seconds.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 128 files already formatted.
- `python -m pyright`: passed, 0 errors / 0 warnings.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`: passed.
- `python -m mkdocs build --strict`: initially failed because this branch's new handoff
  page was absent from navigation; passed after adding it to `mkdocs.yml`.
- `git diff --check`: passed.

Packaging checks were not run: no packaging or Python-code changes were made. No files
were staged, committed, pushed or published. The task owner is returned to `Unassigned`.

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
