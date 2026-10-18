# CS-025 elliptical culvert implementation slice

Status: implemented on `feat/issue-3-elliptical-culverts`, 2026-10-07.

This note records the first implementation slice of
[issue #3](https://github.com/Chain-Frost/ryan-culverts/issues/3). It does not close the
broader additional-shapes/materials issue.

Current validation: the [18 October executable assessment](#local-six-case-executable-assessment-2026-10-18)
supersedes the historical statements below that the six-case comparison has not run.

## Shape priority

1. **Horizontal and vertical ellipses — implemented.** Span and rise define an exact ellipse,
   the depth-dependent area and top width are analytical, and the wetted perimeter can be
   evaluated directly from the ellipse arc-length integral. HDS-5 Third Edition Appendix A,
   Table A.2 retains concrete inlet constants for discontinued Charts 29 and 30.
2. **Pipe arches — deferred.** HDS-5 distinguishes multiple corner-radius/profile families.
   Span and rise alone are therefore not enough to identify the physical section without a
   sourced standard-profile definition or manufacturer geometry.
3. **Arches — deferred.** The same profile-identity problem applies; a nominal "arch" label
   is not a hydraulic geometry.
4. **Other closed shapes — deferred until project demand supplies a source-backed geometry
   definition and applicable inlet/loss evidence.**

This ordering follows the issue requirement to add hydraulic geometry rather than labels.

## Implemented hydraulic contract

`HorizontalEllipseGeometry` requires `span > rise`;
`VerticalEllipseGeometry` requires `rise > span`; equality is rejected in favour of
`CircularGeometry`. Both expose the common closed-section contract: span, rise, full area,
full wetted perimeter, depth-dependent area/perimeter/top width, hydraulic radius/depth,
and crown/full behaviour.

Partial area and top width use exact ellipse identities. Incomplete perimeter uses the exact
arc-length integrand evaluated with fixed composite Simpson quadrature. Tests use independent
high-precision perimeter ordinates at quarter depth and analytical area/symmetry identities.

Closed ellipses, like circular conduits, reach maximum Manning conveyance below the crown.
The normal-depth solver therefore locates the ellipse conveyance maximum and solves only on
the rising branch. The geometry-only peak search is cached by ellipse span/rise so repeated
rating-curve and inverse-solver evaluations do not rerun the numerical maximisation. A
regression constructs discharge from a 0.90-rise target depth, where conveyance is already
greater than the full-section value, to prevent regression to the previous full-capacity
shortcut.

## Empirical applicability

FHWA HDS-5 Third Edition Appendix A Table A.2 supplies separate concrete inlet-control
records for horizontal Chart 29 and vertical Chart 30. These are encoded as separate
`GeometryShape` categories; circular, horizontal-ellipse, vertical-ellipse and rectangular
coefficients cannot be interchanged silently.

HDS-5 Appendix C Table C.2 groups outlet-control entrance losses under "Pipe, Concrete".
The square-edge headwall value is represented by separate horizontal- and vertical-ellipse
records rather than broadening the existing circular record. The existing source-traceable
`CONCRETE_PIPE` material remains applicable; this slice does not invent new material
records simply to satisfy the issue heading.

Ellipse coefficient resolution deliberately has no geometry/material default. HDS-5
catalogues several inlet treatments with different empirical constants, so selecting
square-edge/headwall merely because a culvert is a concrete ellipse would be ambiguous.
Callers must explicitly attach or override the applicable inlet-control coefficient set and
entrance-loss coefficient. This is stricter than the legacy circular/box default behaviour
and follows the repository fail-closed policy.

## External validation boundary (updated 2026-10-08)

The companion [run-hy8 PR #7](https://github.com/Chain-Frost/run-hy8/pull/7)
was merged on 8 October 2026. The source ShapeDB catalogue is traced to
the merged `run-hy8` commit `28e7909afd5ae53c4357380ef70c5f2e482c917d`.
The optional `external-validation` extra now specifies `run-hy8>=2026.10.5.1`
from PyPI, not a Git commit pin. Record the **installed** `run-hy8` version
and the HY-8 executable version when producing comparison evidence.
The HY-8 v8.0.1.2
ShapeDB-backed adapter supports 23 concrete and 40 steel-or-aluminum
**catalogue sizes** and rejects arbitrary/reversed dimension pairs.
Its ellipse catalogue does not expose a generic vertical-orientation switch.
Consequently, the `VerticalEllipseGeometry` mathematical geometry introduced
here does not currently have an equivalent runnable HY-8 catalogue case.

### Critical distinction: nominal size is not identical geometry

`HorizontalEllipseGeometry` and `VerticalEllipseGeometry` in this PR
represent **mathematically exact ellipses**. HY-8's v8.0.1.2 ShapeDB
represents its nominal elliptical products using a standard-profile record
(`Br/Tr/Cr/B`) with a separate authoritative area. Even when nominal
span/rise agree, full-section areas do not necessarily agree:

| Concrete catalogue (inch) | Exact ellipse area (ft²) | ShapeDB area (ft²) | ShapeDB vs exact |
| --- | ---: | ---: | ---: |
| 23 × 14 | 1.756238 | 1.820000 | +3.63% |
| 60 × 38 | 12.435471 | 12.850000 | +3.33% |
| 68 × 43 | 15.947946 | 16.490000 | +3.40% |
| 121 × 77 | 50.816352 | 52.470001 | +3.25% |

The complete retained audit is
[`hy8_8_0_1_2_concrete_ellipse_area_audit.csv`](../validation_data/hy8_8_0_1_2_concrete_ellipse_area_audit.csv),
checked by `tests/test_hy8_ellipse_geometry_audit.py` without requiring
HY-8 or the optional `run-hy8` dependency. This regression checks the
provenance and arithmetic; it is **not** an executable parity test.

The full 23-entry concrete catalogue has a nonzero area discrepancy at
every size; observed differences range from approximately +0.50% to +4.14%.
Calculation: `A_exact = pi * span_in * rise_in / (4 * 144)` ft²,
compared with `run_hy8.CONCRETE_ELLIPSE_CATALOGUE[*].area_ft2` at the pinned commit.
The source of the ShapeDB data is HY-8 8.0.1.2 `ShapeDB.dat` with SHA-256
`2479e9444feaff529313e18a1b26fc2de4f6b6c541db58477da6bebc602164a7`.

This is a **model-geometry difference**, not a permissible calibration
residual. Exact mathematical ellipses remain useful independent geometries.
Do not silently replace their mathematics or tune empirical inlet coefficients
to conceal the difference.

### Four-arc HY-8 profile reconstruction (2026-10-08)

The new `Hy8ConcreteOvalGeometry` represents a **separate, explicit**
catalogued concrete oval rather than changing `HorizontalEllipseGeometry`.
The source-pinned, dependency-free catalogue is
`src/culvert_solver/geometry/hy8_oval_catalogue.py`. It retains ShapeDB
top/bottom/corner radii, half rise, nominal dimensions, tabulated full area,
and Manning roughness. Source: HY-8 8.0.1.2 / `run-hy8` merge commit
`28e7909afd5ae53c4357380ef70c5f2e482c917d` plus FHWA HEC-10
Section VII.C (the standard oval is constructed from two pairs of arcs,
not a mathematical ellipse).

`Hy8ConcreteOvalGeometry.from_mm(span_mm, rise_mm)` selects an exact nominal
catalogue row; arbitrary sizes, orientation reversal and interpolation are
rejected. The unscaled source radii join at tangent circular arcs, and all
partial-area and perimeter calculations retain this circular-arc geometry.
No affine horizontal stretch is permitted.

The reconstructed *actual* span must agree with nominal ShapeDB span
within 0.5%, and independently calculated full flow area must agree with
the ShapeDB reported area within 0.5%. These **two fail-closed source
reconciliation gates** are not a claim of HY-8 numeric parity or an
engineering design accuracy tolerance. `oval.span` returns actual
reconstructed maximum width; `oval.catalogue_size.span_in` is the nominal
selection width in inches.

**Eight of 23 concrete sizes** pass both gates (zero-based rows 3, 7, 11,
12, 17, 18, 19, 20); the other 15 sizes reject construction. The formerly
accepted **60 × 38** and **68 × 43 inch** entries do not pass unscaled
reconciliation. The previous horizontal stretch reduced area residuals
but converted the four source *circles* to elliptical arcs and is removed.

The six-case comparison now uses **83 × 53** and **128 × 82 inch** concrete
ShapeDB sections, each at discharges of 0.5, 1.0 and 2.0 m³/s.
The 83 × 53 reconstruction differs approximately +0.01% in span and
-0.004% in area; 128 × 82 differs approximately 0% in span and
-0.19% in area. The CSV includes source/reconstructed spans and areas
alongside headwater, velocities, controls and profile diagnostics.
Classify model-geometry discrepancies separately from numerical hydraulic
solver discrepancies. Do not adjust inlet coefficients to conceal a
geometric difference.

The exact mathematical ellipse classes are retained independently.
Steel/aluminium ovals, arch/pipe-arch shapes and reversed vertical
standard profiles are not supported by this catalogue class.

### Verification status and next validation gate

- The earlier local HY-8 run of 7 October produced zero elliptical barrel
  discharge. Its generated projects were subsequently corrected in
  `run-hy8` by populating HY-8's ShapeDB `BARRELGEOMETRY` fields; positive
  flow is now reported by its hosted executable probes. The earlier failed
  project is **historical**, not a current-head validation result.
- The 8 October `run-hy8` merge does not supply an independent
  `ryan-culverts` comparison fixture. The `ryan-culverts` ellipse geometry,
  inlet/output regimes, velocity and headwater are not yet HY-8-validated.
The existing `scripts/compare_hy8.py` now has an **opt-in**
`--elliptical` mode with six cases (83 × 53 and 128 × 82 inch concrete
catalogue sizes, each at 0.5, 1.0 and 2.0 m³/s). The default legacy
circular/CSP/box comparison matrix is unchanged. The mode writes
headwater, velocity, control/regime, per-culvert flow and diagnostics
and retains the native HY-8 outputs when `--workspace` is set.
Its comparison CSV must be read together with the ShapeDB catalogue and
arc-reconstruction area discrepancies; it is **quantitative comparison
instrumentation**, not a claim of HY-8 parity.

With `run-hy8` installed from PyPI using the optional
`external-validation` extra, run from the repository root on Windows
with HY-8 8.0.1.2 installed:

```powershell
py -3.14 -m pip install -e ".[dev,external-validation]"
py -3.14 -m pip show run-hy8
$env:PYTHONPATH = 'src'
py -3.14 -B scripts/compare_hy8.py `
  --elliptical `
  --hy8 'C:\Path\To\HY864.exe' `
  --workspace validation_artifacts/hy8-ellipse `
  --output docs/validation_data/hy8_8_0_1_2_ellipse_comparison.csv
```

If `py -3.14` is unavailable, replace it with the full path to
your installed Python 3.14 executable (for example,
`& 'C:\Program Files\Python314\python.exe'` in PowerShell). Do not
accidentally execute the comparison using Python 3.13.

Preserve the executable's actual version/path and the case-level
`.hy8`, `.rst`, `.rsql` alongside the resulting CSV. Run into a fresh
workspace to avoid conflating old results with the current pinned version.
The executable comparison has **not been run from this GitHub-only
environment**; no numerical findings are yet claimed.

- Retain **version-pinned local Windows HY-8 8.0.1.2** concrete cases at
  exact catalogue sizes, multiple flows and physical inlets, with raw
  `.hy8`, `.rst`, `.rsql`, measured executable version/path, and
  a quantitative comparison CSV.
- Record discharge partition, headwater, outlet velocity, control state,
  nominal geometry and both full-section areas. Reject unrequested
  roadway overtopping and incomplete/zero barrel discharge.
- Classify geometry mismatch separately from inlet/profile/control-method
  discrepancies. Seek independent shape/profile evidence for vertical
  ellipses; do not invent a reversed HY-8 catalogue size.
- Verify Ruff, strict Pyright, pytest, documentation, wheel smoke checks
  and CI on the final PR head. Hosted CI does **not** substitute for the
  independent HY-8 executable.
- If the numerical results disagree, preserve raw files and distinguish
  catalogue area/radius discrepancies from inlet polynomial, outlet
  profile and control-state differences. Reject invalid fixtures with
  unexpected roadway flow or zero culvert discharge.
- Keep the PR as draft until the executable comparison is reviewed against
  documented quantitative acceptance criteria.

## Verification status (historical)

The original implementation was reviewed structurally in a GitHub-only
environment without a locally executed suite. Subsequent local repair and
hosted CI ran after that review; see the section below. The historical
checks do not establish HY-8 engineering parity.

## Local validation repair, 2026-10-07

Owner: Unassigned. Status: verified locally on Python 3.14.6; uncommitted and unpushed.
The initial full suite had 525 passing tests and two failures: missing ellipse API
documentation and a nonmonotonic vertical-ellipse projecting-inlet transition.

Checked Chart 30 Scale 3 against tracked `reference_docs/HDS-5.pdf`, Table A.2,
PDF page 198: `K=0.0095`, `M=2.0`, `c=0.0317`, `Y=0.69` are correctly transcribed.
The fixed cubic bridge is unsupported for the tested 1.2 m span and 2.4 m rise.
The transition now checks its quadratic derivative's exact minimum and fails closed
when negative. Published coefficients and endpoint tangents are preserved; a sourced
alternative transition remains future work. Bounding empirical branches remain usable.

Added the missing public API entries and MkDocs navigation. Resolved lint and formatting
issues, combined the existing circular/ellipse normal-depth branches without changing
their capacity or root contracts, and extracted entrance-loss default selection.
Ellipse value equality remains explicitly unhashable.

Verification:

- `python -m pytest -q`: 530 passed.
- `python -m pytest -q tests/test_inlet_control.py tests/test_elliptical_geometry.py tests/test_elliptical_resolvers.py tests/test_normal.py tests/test_resolvers.py tests/test_public_api.py`: 118 passed.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 142 files already formatted.
- `python -m pyright`: zero errors, warnings or information messages.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`: passed.
- `python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.

An initial focused command used nonexistent `tests/test_normal_depth.py` and collected
no tests; the corrected command above passed. No package build, installed-wheel test,
or HY-8 executable comparison was run. These are local regression checks, not independent
engineering acceptance or completion of the broader issue.

## Remaining CS-025 work

Naming follow-up: renamed the shared circular/ellipse normal-depth residual to
`f_conveyance_closed`. No equation or control-flow change. Verification:
`python -m pytest -q tests/test_normal.py tests/test_elliptical_geometry.py` passed
26 tests; focused Ruff check and format check passed for
`src/culvert_solver/hydraulics/normal.py`. Markdown lint and `git diff --check` passed.
The full suite, Pyright, MkDocs, packaging, and HY-8 were not rerun for this rename.

- research a source-backed standard profile representation for pipe-arch families before
  implementing their depth-dependent section properties;
- do the same for arch families;
- add new material/roughness records only when a primary or manufacturer source provides
  values and applicability not already represented by the current material catalogue;
- review and resolve the retained ellipse discrepancies described below before claiming
  bounded external hydraulic acceptance.

## Local six-case executable assessment, 2026-10-18

Owner: Unassigned. Status: comparison evidence captured; engineering acceptance open.
Boundary: PR #29 comparison and evidence review, not new geometry or calibrated equations.

The branch already incorporates main through `55f912c8f7f9d3f5683bf34ced2dd675a97b8db3`;
GitHub reports it mergeable. No additional conflict resolution was necessary.

Executed all six requested cases on Python 3.14.6 with HY-8 file version **8.0.1.2**
at `C:/Program Files/HY-8 8.00/HY864.exe`, using the public **run-hy8 2026.10.18.2**
wheel in an isolated environment with system site packages enabled. The global
adapter was not changed by this task. Executable and ShapeDB hashes, exact source head,
working-tree harness changes, and all retained artifact hashes are recorded in
[`manifest.json`](../validation_data/hy8_8_0_1_2_ellipse/manifest.json).

The first attempt failed adapter input validation before execution: the harness supplied
three points for a constant roadway. Corrected this to the required two equal-elevation
endpoints, preserving width, crest and non-overtopping intent. The completed final run
returned exit code 0 in a fresh
`validation_artifacts/ellipse-2026-10-18/run-04-adapter-2026.10.18.2` workspace.
The ellipse CSV now explicitly retains crossing, barrel and roadway discharge.
The initial completed run used 2026.10.16.1. After the user updated run-hy8, installed
2026.10.18.2 into the isolated environment and reran all six cases. The comparison CSV
is byte-identical across both adapter versions. Retained native files are from the final
installed-wheel rerun after the provenance fix, also using 2026.10.18.2. Earlier runs
remain separately preserved in ignored workspaces.

Retained evidence:

- [Six-case comparison CSV](../validation_data/hy8_8_0_1_2_ellipse_comparison.csv).
- Native `.hy8`, `.rst`, `.rsql` and `.plt` files for every case in
  `docs/validation_data/hy8_8_0_1_2_ellipse/`, alongside the hash manifest.
- Byte-preserving Git attributes protect these checksum inputs from line-ending conversion.
  Native files retain HY-8's generated whitespace and use binary diffs; the CSV and
  provenance manifest remain directly reviewable text.
- Offline tests verify hashes and compare CSV flow/headwater/velocity/type with native
  report columns. These are evidence-integrity checks, not new executable runs in CI.

### Quantitative assessment criteria

Use the existing source-reconciliation limits and report-precision checks; do not choose
a larger tolerance to encompass the observed differences. These are diagnostic gates,
not design tolerances or an assertion that HY-8 defines correctness.

1. Fixture validity: finite positive barrel flow equal to requested crossing flow within
   the existing `0.0051 m3/s` report tolerance; roadway flow zero within that tolerance;
   full/free lengths nonnegative and summing to 30 m within `0.011 m`. All six pass.
2. Source geometry: independently reconstructed span and area each within the established
   0.5% ShapeDB reconciliation gates. Both sizes pass; this does not establish identical
   depth-dependent section properties inside HY-8.
3. Rounding-only hydraulic agreement: absolute headwater difference at most `0.0051 m`
   and velocity difference at most `0.0051 m/s`, reflecting two-decimal native reports.
   Differences above this need method/geometry explanation, not automatic acceptance.
4. Regime evidence: consistent inlet control, S2 profile and zero full-flow length.
   All six agree. HY-8's `0.0*` outlet-control depth is qualified, not an independent
   physical outlet-control depth or a value against which to calibrate the core.
5. Final engineering review: assess independent equation/profile evidence and explain
   residual differences before accepting this bounded comparison. Vertical mathematical
   ellipses and other regimes remain outside its coverage.

Signed differences below are local minus HY-8:

| Case | HW difference (m) | Velocity difference (m/s) | Rounding-only agreement |
| --- | ---: | ---: | --- |
| 83 x 53 inch, 0.5 m3/s | -0.001188 | +0.011830 | Velocity exceeds |
| 83 x 53 inch, 1.0 m3/s | +0.002976 | +0.013830 | Velocity exceeds |
| 83 x 53 inch, 2.0 m3/s | +0.007268 | +0.005062 | Headwater exceeds |
| 128 x 82 inch, 0.5 m3/s | -0.022632 | +0.006101 | Both exceed |
| 128 x 82 inch, 1.0 m3/s | -0.009647 | +0.024171 | Both exceed |
| 128 x 82 inch, 2.0 m3/s | -0.007162 | +0.020660 | Both exceed |

Two of six headwater values and one of six velocities meet the rounding-only gate;
no case meets both. All requested barrel flows are exactly 0.5, 1.0 or 2.0 m3/s in the
reports, with zero roadway flow. All local cases are unsubmerged inlet control with S2
profiles; HY-8 reports `1-S2n`, 0 m full and 30 m free length.

### Difference classification and disposition

The 83 x 53 profile reconstructs nominal span at +0.009636% and area at -0.003694%;
128 x 82 has approximately zero span discrepancy and area -0.185753%. The CSV retains
exact values. These source-geometry residuals are separate from hydraulic residuals;
full-area agreement cannot establish partial-depth area/perimeter equivalence.

The local inlet calculation uses HDS-5 Table A.2 Chart 29 Scale 1 and Equation A.1
with computed critical specific energy. The retained reports establish that the
headwater differences occur on the unsubmerged inlet-control branch, so they are not
evidence of a submerged transition or full-flow outlet-loss error. Outlet velocity
also depends on partial-depth geometry and the normal/outlet profile. A quantitative
attribution between HY-8's internal geometry and inlet/profile implementation remains
unresolved; do not claim the area residual alone explains the discrepancy.

No hydraulic equations, coefficients, source-reconciliation gates or historical
comparison baselines were adjusted. This new fixture records discrepancies faithfully.
The six-case execution requirement is satisfied; numerical equivalence and engineering
acceptance are not. Keep PR #29 draft and defer the requested final acceptance review
until the residuals have independent evidence and a reviewed disposition. Do not merge.

### Verification and delivery

Checks on the final implementation and retained evidence, Python 3.14.6:

- `python -m pytest -q`: **643 passed** in 20.12 s, no skips or deselections.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 157 files already formatted.
- `python -m pyright`: zero errors, warnings or information messages.
- `python -m pyright scripts/compare_hy8.py`: zero diagnostics with the updated adapter.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`: passed.
- `python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- `python scripts/build_package.py --no-bump` and `python scripts/verify_wheel.py`:
  passed; wheel version unchanged at 26.10.16.1, 121,661 bytes, SHA-256
  `1a769421147a8c26d5d5ba855601d67c27d53d758f9e8c7086398b7ef99b4594`.
- Installed that wheel in the isolated environment; `python -I
  scripts/smoke_test_installed_wheel.py` passed. The first isolated external comparison
  found that `-I` excludes dependencies inherited from user site packages. Installed
  adapter dependencies inside the environment and repeated successfully.
- Repeated the full six-case executable matrix against the installed wheel using `-I`,
  with run-hy8 2026.10.18.2, in fresh workspace
  `validation_artifacts/ellipse-2026-10-18/run-07-final-wheel`. Exit code 0;
  CSV SHA-256 matches the source-tree run exactly:
  `6a6c527907e7b440b53689ddd57be02f45ed52b4135d35b1431fca3483f42361`.

PR #29 was restored to draft because the independent acceptance gate remains open.
The new P2 review finding about mutable catalogue identity was repaired: the index is
stored privately and exposed through a read-only property. Reassignment/deletion now
raise `AttributeError`, preserving the source row and precomputed profile together.
A regression checks this contract. The final rebuilt wheel's full matrix reproduces
the earlier CSV exactly, so the provenance repair did not change these hydraulics.
The four jobs in hosted [run 39106984351](https://github.com/Chain-Frost/ryan-culverts/actions/runs/39106984351)
passed at base head `55f912c`; that run does not verify these subsequent evidence changes.
Fresh hosted CI must be checked after delivery. No merge, release or publication is
part of this work. No new Linux/macOS local execution or GUI inspection was performed.
The owner is returned to Unassigned; final acceptance review remains deferred until
the hydraulic discrepancies have a defensible disposition.
