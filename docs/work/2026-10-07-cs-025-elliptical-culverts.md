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

## External validation boundary

The independent analytical tests do not by themselves claim HY-8 parity. The companion
`run-hy8` work is now implemented in
[run-hy8 PR #7](https://github.com/Chain-Frost/run-hy8/pull/7), with version-pinned
HY-8 8.0.1.2 shape/inlet mappings and executable probes for both ellipse orientations.
That PR is not yet merged, and this `ryan-culverts` branch has not yet retained a fresh
ellipse comparison fixture, so external parity remains a separate validation step.

## Verification status

The branch was reviewed structurally after implementation. The modified Python core files
contained no lines longer than 120 characters, and the branch was confirmed to be based
directly on `main` with no divergence at handoff.

No local Python test, Ruff, Pyright, Markdown, MkDocs, build, or installed-wheel execution
is claimed from the GitHub-only implementation environment. The repository CI workflow
runs for pull requests (and pushes to `main`), not for a standalone feature-branch push.
A draft pull request should therefore be used to obtain the authoritative hosted checks
before this implementation slice is considered ready to merge.

No local HY-8 ellipse comparison is claimed for this `ryan-culverts` branch.
The companion orchestration is available in
[run-hy8 PR #7](https://github.com/Chain-Frost/run-hy8/pull/7), but another agent with
access to an installed HY-8 8.0.1.2 environment still needs to run the local executable
validation and then generate/retain the corresponding `ryan-culverts` ellipse comparison
fixture. Hosted CI and the run-hy8 hosted probes do not replace that local validation.

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
