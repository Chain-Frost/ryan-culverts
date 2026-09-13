# Work tracking and background index

GitHub Issues are the authoritative source for current task scope, status, ownership,
dependencies, and acceptance criteria in `ryan-culverts`.

The detailed [Phase 0-10 remediation and forward plan](2026-09-06-phase-0-to-10-remediation.md)
and the [long-term development plan](long-term-development-plan.md) are retained as
engineering background, design rationale, research context, and historical execution
evidence. They are not a second live task tracker.

## Selecting work

Use the relevant GitHub issue to select, coordinate, and close current work. Do not claim a
migrated task by editing a legacy CS `Owner` field, and do not infer current issue status
from a CS table entry. If an issue links to a CS section, treat that section as background
context unless the issue explicitly says otherwise.

Before handoff, run focused tests for edited modules and record the exact commands and
results in the issue/PR or maintained engineering documentation as appropriate. The
ordinary repository checks are:

```powershell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m pyright
python -m pymarkdown -d MD013 scan -r README.md docs
python -m mkdocs build --strict
git diff --check
```

Packaging/release work adds the package build and isolated installed-wheel checks. Do not
bump a version or create a release artifact merely to complete unrelated work.

## Repository boundary

`ryan-culverts` owns reusable hydraulic-domain models, equations, solver behaviour,
result/provenance contracts, and low-level domain utilities required by multiple consumers.

Application-level culvert project configuration, design-option search, batch/reporting
policy, plotting, GUI, and project-level uncertainty-study orchestration belong in
`ryan-tools`. In particular:

- `ryan-tools` #81 owns project/scenario/alternative configuration;
- `ryan-tools` #82 owns design-option/minimum-size search and ranking;
- `ryan-tools` #83 owns CLI/reporting/export;
- `ryan-tools` #84 owns plotting/GUI;
- `ryan-tools` #87 owns floodway formation assessment/reporting; and
- `ryan-tools` #91 owns project-level culvert uncertainty/sensitivity studies.

Core hydraulic prerequisites and reusable classes used by those workflows remain in
`ryan-culverts`.

## Legacy CS mapping

The CS identifiers below remain useful references into the detailed remediation record.
Their current implementation status is determined by the linked GitHub issue, not by this
table.

| Legacy ID | Current tracking | Boundary / disposition |
| --- | --- | --- |
| CS-009 | `ryan-tools` #81; core work only if later required | Keep project/scenario configuration downstream. Add core serialization only if a stable hydraulic-object interchange contract becomes necessary. |
| CS-014 | Split background umbrella | Do not implement as one task. Its former hydraulic scope is separated into issues #20 through #23. |
| CS-015 | `ryan-culverts` #15 | Resolve the Austroads worked-example velocity inconsistency before numerical use. |
| CS-021 | `ryan-culverts` #16 | GitHub issue is authoritative; currently closed/not planned unless reopened. |
| CS-022 | `ryan-culverts` #17 | GitHub issue is authoritative; currently closed/not planned because the release-distribution activation trigger is not met. |
| CS-023 | `ryan-tools` #82 | Design-option enumeration, feasibility and ranking remain downstream. |
| CS-024 | `ryan-tools` #84; core result support in `ryan-culverts` #9 | Plotting dependencies stay out of the hydraulic core. |
| CS-025 | `ryan-culverts` #3 | Additional supported shapes and source-traceable materials. |
| CS-026 | `ryan-culverts` #18 | Explicit debris/blockage hydraulic scenarios. |
| CS-027 | `ryan-culverts` #19 plus `ryan-tools` #91 | Core owns reusable uncertainty contracts/primitives; downstream owns study orchestration, aggregation and reporting. |
| CS-028 | `ryan-culverts` #4 and #14; PR #13 | Core owns advanced roadway overtopping and the downstream-consumable roadway hydraulic state. |
| CS-029 | `ryan-culverts` #2 | Implemented/closed issue; retain the CS section as background validation history. |
| CS-030 | `ryan-culverts` #20 | Slipline host/liner geometry and sourced roughness treatment. |
| CS-031 | `ryan-culverts` #21 | Receiving-section model and Borda-Carnot exit-loss refinement. |
| CS-032 | `ryan-culverts` #22 | Buried-invert geometry and coefficient disposition. |
| CS-033 | `ryan-culverts` #23 | Depth-dependent roughness with explicit material zones. |
| CS-034 | `ryan-culverts` #1 | Implemented/closed issue; retain the CS section as background inverse-capacity history. |

Completed CS-001 through CS-013, CS-016, CS-017, CS-019, and CS-020 remain historical
records of bounded work already delivered. Reopen or create a GitHub issue if new evidence
requires additional work rather than silently changing their historical status.

## Repository-review issues

The repository review and subsequent integration work are tracked directly as GitHub
issues:

- #5 synchronises packaged version, wheel and release documentation;
- #6 reconciles public API documentation with implemented capabilities;
- #7 provides machine-readable hydraulic result validity/severity;
- #8 covers independent heterogeneous-crossing and rating-curve validation;
- #9 provides longitudinal HGL/EGL data for full and pressurised reaches;
- #10 exposes representative-barrel/equal-flow applicability limits;
- #11 makes version reporting truthful for standalone and vendored layouts;
- #14 exposes roadway segment hydraulic state for downstream floodway analysis;
- #15 through #23 carry the migrated remaining CS work where applicable.

Always use the GitHub issue itself for current status and acceptance criteria.
