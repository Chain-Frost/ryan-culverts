# CS-025 elliptical culvert implementation slice

Status: implemented on `feat/issue-3-elliptical-culverts`, 2026-10-07.

This note records the first implementation slice of
[issue #3](https://github.com/Chain-Frost/ryan-culverts/issues/3). It does not close the
broader additional-shapes/materials issue.

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
was merged on 8 October 2026. This branch's optional `external-validation`
dependency is now pinned to the merged `run-hy8` commit
`28e7909afd5ae53c4357380ef70c5f2e482c917d`. The HY-8 v8.0.1.2
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
residual. It prevents claiming geometric parity or treating headwater
differences as solely numerical/solver defects. Exact mathematical ellipses
remain useful independent geometries, but native HY-8 product-profile parity
requires a separate source-backed standard-profile geometry implementation.
Do not silently replace the existing mathematical geometry or tune empirical
inlet coefficients to conceal the area difference.

### Verification status and next validation gate

- The earlier local HY-8 run of 7 October produced zero elliptical barrel
  discharge. Its generated projects were subsequently corrected in
  `run-hy8` by populating HY-8's ShapeDB `BARRELGEOMETRY` fields; positive
  flow is now reported by its hosted executable probes. The earlier failed
  project is **historical**, not a current-head validation result.
- The 8 October `run-hy8` merge does not supply an independent
  `ryan-culverts` comparison fixture. The `ryan-culverts` ellipse geometry,
  inlet/output regimes, velocity and headwater are not yet HY-8-validated.
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
- The previously recorded hosted Python 3.14 CI passed on the original
  review-adjusted branch. Recheck CI on the new dependency-pin commit before
  asserting a final status. Hosted Python CI is not a substitute for the
  executable comparison.

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
- after `run-hy8` #5 is implemented, add retained ellipse comparison fixtures here.
