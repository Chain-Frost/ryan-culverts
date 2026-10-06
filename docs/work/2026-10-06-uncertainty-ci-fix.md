# Uncertainty PR verification and review follow-up

Task: verify PR #25 within issue #19's uncertainty-primitives boundary.
Owner: Unassigned. Status: implementation and reviewer follow-up complete; PR #25 merged
to `main` as commit `0213eac2bf10b5751feb13ae7d88d00026eeb9f1`.

The GitHub issue remains the authoritative feature tracker. The implementation preserves
runtime integer validation for sampling counts and seeds, exposes all public uncertainty
contracts in the API reference, and leaves hydraulic equations and comparison baselines
unchanged.

## CI repair history

An earlier GitHub Actions run failed only at type checking because Pyright reported
`reportUnnecessaryIsInstance` for runtime seed and count validation. Targeted annotations
were added to match existing runtime-validation conventions. Local full testing also
identified missing public API reference entries for the uncertainty exports; the dedicated
API reference page now documents them and is included in navigation.

A subsequent full CI run, #79, passed before automated review follow-up, including the
repository verification job and installed-wheel jobs on Windows, Ubuntu and macOS.

## Automated review follow-up

The PR reviewer identified two substantive issues, both addressed with regression tests:

- Manning roughness now carries its dimensional SI unit, `s/m^(1/3)`, rather than being
  incorrectly labelled dimensionless.
- Sampling Manning roughness clears any baseline `parameter_set_id` so a modified adopted
  parameter set cannot retain stale identity/provenance.

The hardening pass also adds a real high-head advisory case proving that uncertainty
evaluation preserves the deterministic solver's structured hydraulic warning, resulting
`HydraulicResultStatus`, and convergence evidence.

A subsequent Codex review found no major issues. Final PR-head CI run #90 passed before
PR #25 was merged. The merged implementation therefore completes the `ryan-culverts`
scope of CS-027.

## Verification scope

The ordinary repository gate includes:

- `python -m pytest -q`;
- `python -m ruff check .`;
- `python -m ruff format --check .`;
- `python -m pyright`;
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`;
- `python -m mkdocs build --strict`;
- `git diff --check`;
- package build and installed-wheel smoke tests on Windows, Ubuntu and macOS.

HY-8 executable comparison is not required for this task because the uncertainty layer
calls the existing authoritative deterministic solver and does not change hydraulic
equations, empirical coefficient methods, or comparison baselines.

No version bump or release publication is part of CS-027. Project-level Monte Carlo study
orchestration, aggregation, reporting, ranking and design acceptance remain downstream in
`ryan-tools` issue #91.
