# Changelog

This file records user-visible changes. Detailed validation evidence remains in
[progress](progress.md) and the maintained [release notes](releases/README.md).

## Unreleased

Source-only maintenance may exist above the retained wheel without requiring a release
entry. User-visible package changes must be listed here before the next wheel is built.

- Exported the `TailwaterInput` contract, corrected forward-solver tailwater and supported
  profile documentation, and added public API documentation drift checks.
- Synchronized packaged-release documentation with authoritative project metadata and
  strengthened retained-wheel consistency verification.
- Added a source-backed representative-barrel/equal-flow applicability notice to
  multi-barrel group and crossing results and propagated it through inventory summaries.
- Added machine-readable hydraulic result status with conservative group/crossing
  aggregation and propagation into rating-curve points and inventory summaries.
- Added a typed, source-traceable user-supplied tailwater rating curve with monotonic point
  validation, exact or linear in-range resolution, fail-closed extrapolation, and forward
  barrel/group/crossing integration.
- Extended barrel, HW/D, group, and crossing inverse-capacity helpers to solve against the
  public `TailwaterInput` contract, including total-flow coupling for mixed crossings and
  supported roadway overtopping.

## 26.9.10.2 - 2026-09-10

- Added rectangular and asymmetric trapezoidal/triangular open-channel geometry and a
  source-traceable Manning normal-depth tailwater boundary that uses receiving flow at the
  barrel, group, or crossing boundary and recalculates stage at each rating point.
- Replaced the ambiguous Manning `source` field with explicit method and project-parameter
  provenance, documented the two tailwater depth datums, and added a public open-channel
  `hydraulic_radius()` utility.
- Added public barrel, group, and crossing discharge-for-headwater helpers, including a
  single-barrel HW/D convenience and forward/inverse round-trip coverage.
- Added filleted rectangular box geometry and a fail-closed corrected FHWA-HRT-06-138
  modern-box inlet catalogue with bounded Table 12 evaluation and an Appendix D fixture.
- Added constant-elevation, unsubmerged roadway overtopping using FHWA HDS-5 Equation 3.9
  and combined culvert-roadway flow allocation.
- Added `culvert_solver.__version__` and documented the top-level public API boundary.
- Restricted package metadata to the tested Python 3.14 baseline and added portable
  installed-wheel CI on Windows, Linux, and macOS.
- Added a strictly validated MkDocs site and gated GitHub Pages workflow.

## 26.9.9.2 - 2026-09-09

- Added fail-safe calendar-version packaging and retained a single verified wheel.

## 26.9.9.1 - 2026-09-09

- Created the first packaged alpha handoff for integration testing.
