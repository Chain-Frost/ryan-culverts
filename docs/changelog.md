# Changelog

This file records user-visible changes. Detailed validation evidence remains in
[progress](progress.md) and the maintained [release notes](releases/README.md).

## Unreleased

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
