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

## Active validation handoff

Issue #3 / PR #29 hydraulic review (2026-10-18): Owner: Unassigned.
Status: **Current review round complete**; numerical parity and design acceptance
are separate decisions. No additional HY-8 cases or solver adjustments are
requested for this review round. Findings and limits are recorded in the
[standalone PR review](2026-10-18-pr29-hydraulic-review.md).
No merge or release was performed in this review.

Issue #3 / PR #29 critical-depth diagnostic (2026-10-18): Owner: Unassigned. Status: executed; independent review required.
Boundary: execute five new high-flow cases, retain native curves, compare critical
and profile depths with unchanged geometry/equations, and report independent-review limits.
Five fresh runs and the 25/35 m3/s anchors are retained separately with full native curves.
See [the targeted assessment](2026-10-07-cs-025-elliptical-culverts.md#targeted-high-flow-critical-depth-investigation-2026-10-18).
All 658 tests and ordinary quality checks pass on Python 3.14.6 after repairing
a missing test-decorator parenthesis from the concurrently advanced branch.

Issue #3 / PR #29 higher-flow executable sweep (2026-10-18): Owner: Unassigned. Status: executed; engineering review outstanding.
Boundary: execute the requested 18-case diagnostic matrix in a fresh workspace,
preserve native/version/hash evidence, and assess discrepancies without changing
solver equations, coefficients, existing baselines, or acceptance criteria.
All 18 cases completed with HY-8 8.0.1.2 and run-hy8 2026.10.18.2. Native reports,
CSV and manifest are retained separately; repeated baseline rows are unchanged.
See [the sweep assessment](2026-10-07-cs-025-elliptical-culverts.md#local-18-case-executable-sweep-2026-10-18).
PR remains draft. Changes are uncommitted and unpushed.

Main integration (2026-10-18): Owner: Unassigned. Status: validated locally.
Merged `origin/main` at `8d442e6` into `feat/issue-3-elliptical-culverts`.
Resolved the sole conflict in this index by retaining both branches' handoff records.
Validation on Python 3.14.6: `python -m pytest -q` (648 passed),
`python -m ruff check .`, `python -m ruff format --check .` (158 files),
`python -m pyright` (zero diagnostics),
`python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`,
`python -m mkdocs build --strict`, and `git diff --check` passed.
Python 3.13.15 pytest could not run because that interpreter lacks pytest.
No new HY-8 executable comparison, wheel build/install verification, or hosted CI
was run for this merge. Existing engineering acceptance limits remain in force.
Local merge only; no push or publication performed.

Issue #3 / PR #29 six-case executable validation (2026-10-18): Owner: Unassigned. Status: Needs review.
Boundary: preserve fresh HY-8 ellipse evidence, assess hydraulic discrepancies against
explicit comparison criteria, and record validation and review readiness.
The six positive-flow cases are retained; hydraulic differences exceed report rounding.
See [the current assessment](2026-10-07-cs-025-elliptical-culverts.md#local-six-case-executable-assessment-2026-10-18).
Engineering acceptance and final review remain gated; next review: 2026-10-19.

Issue #3 ellipse validation repair (2026-10-07): Owner: Unassigned. Status: verified locally.
Boundary: repair local test and quality-check failures in the ellipse implementation
slice without changing sourced coefficients or HY-8 baselines.
See [the implementation note](2026-10-07-cs-025-elliptical-culverts.md) for exact checks
and the remaining Chart 30 Scale 3 transition applicability limit. Changes are uncommitted
and unpushed; the broader issue remains open.
PyPI release automation (2026-10-16): Owner: ChatGPT. Status: Active.
User-selected task: consistent release preparation, verified publication and focused
CI improvements, delivered as a new PR. No hydraulic methods or comparison baselines
will change. [PR #32](https://github.com/Chain-Frost/ryan-culverts/pull/32) owns current review status; see the
[release setup handoff](2026-10-16-pypi-release-automation.md) for validation and next actions.

Python 3.13 support (2026-10-18): Owner: Unassigned. Status: CI simplification validated locally.
User-selected compatibility task within the CS-019 packaging boundary. Installation
requires Python `>=3.13`, with no upper bound. CI runs full checks once on 3.13 under the required name `verify`, plus lightweight
installed/vendored wheel checks on 3.14 across Windows, Linux, and macOS.
This reduces eight jobs to four and preserves all existing required check names.
Ruff and Pyright target 3.13. Restored exception tuple parentheses and deferred barrel
annotations for 3.13 imports; hydraulic equations and comparison baselines are unchanged.
Adjusted the invalid-date test for the different standard-library error wording on 3.13.

Verification on Windows, Python 3.13.15 and 3.14.6:

- Full `python -m pytest -q`: 560 passed on each version, no skips or deselections.
- Python 3.13: `python -m ruff check .`, `python -m ruff format --check .`
  (148 files), and `python -m pyright` (zero diagnostics) passed.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`,
  `python -m mkdocs build --strict`, and `git diff --check` passed.
- Python 3.13: `python scripts/build_package.py --no-bump` and
  `python scripts/verify_wheel.py` passed. Rebuilt local version `26.10.16.1`,
  113181 bytes, SHA-256
  `8de9b889e79bb5af8046b24bcbdaf12187caf0c7c9f2ac5c46a7d26a0534523c`.
- Rebuilt wheel installed and passed `scripts/smoke_test_installed_wheel.py`
  outside the checkout in separate clean 3.13 and 3.14 virtual environments.
- Python 3.13 vendored fixture built, installed into a temporary target, and passed
  `scripts/smoke_test_vendored_wheel.py` outside the checkout with unrelated stale
  distribution metadata present.

The initial eight-job hosted CI run 39131100873 passed on head `fc20229`, including
Linux/macOS wheel checks. The subsequent four-job CI simplification is tracked in
[PR #39](https://github.com/Chain-Frost/ryan-culverts/pull/39). Actionlint, Markdown lint,
strict MkDocs, and whitespace were rerun locally for the workflow/documentation edits.
HY-8 executable comparisons and Python 3.15 or later were not run. Actionlint 1.7.12 passed after checksum verification. Newer interpreters are permitted by metadata;
local compatibility evidence covers 3.13/3.14. This is regression evidence, not
engineering acceptance. The compatibility change is committed on `feat/python-313-support`; no publication
was performed. The latest `main` was merged before PR validation. Its removal of the
tracked wheel is preserved; build artifacts are local validation evidence only.

PyPI release policy (2026-10-18): Owner: Unassigned. Status: Needs review.
Port run-hy8 PR #17's verified merge-only release opt-out, preserving repository-specific
builds and publisher identity. Local validation passes, including 561 tests and isolated
wheel smoke. [PR #38](https://github.com/Chain-Frost/ryan-culverts/pull/38) is open
on `ci/merge-only-release-policy`; the PR owns live CI status. No merge authorized. Next review: 2026-10-19. See the
[release handoff](2026-10-16-pypi-release-automation.md) for scope and validation.

Local and CI validation (2026-10-08): Owner: Unassigned. Status: local checks passed;
hosted CI needs the local repair committed and pushed.
Validated `fix/issue-30-csp-defaults` at `3debf677` on Python 3.14.6.
Removed one extra blank line in `docs/api/inputs.md` that caused MD012/MD022.

- `python -m pytest -q`: 511 passed in 25.12 seconds, no skips or deselections.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 138 files already formatted.
- `python -m pyright`: zero errors, warnings or information messages.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`: passed after repair.
- `python -m mkdocs build --strict`: passed after repair.
- `git diff --check`: passed.
- `python scripts/verify_wheel.py`: passed before and after rebuild.
- `python scripts/build_package.py --no-bump`: passed, version unchanged.
- `python scripts/smoke_test_installed_wheel.py`: passed using a temporary virtual
  environment with the rebuilt wheel installed and execution outside the checkout;
  confirmed the import resolved inside that environment.
- Vendored fixture: `python -m build --wheel --outdir <temporary-wheelhouse>
  <fixture>` and isolated installation passed.
  `python scripts/smoke_test_vendored_wheel.py --expected-root <temporary-install>
  --expected-version 26.9.10.2 --unrelated-version 1.2.3` passed outside the checkout.

Retained wheel SHA-256 after rebuild:
`a141a620a472ebfc0411f87525a7041ff7c887af818814151500cc2b4ca90734`.
The retained artifact changed from 94,209 to 112,782 bytes.

Retried failed jobs in [Python CI run 37717359615](https://github.com/Chain-Frost/ryan-culverts/actions/runs/37717359615).
All four jobs are terminal: three installed-wheel platform jobs passed; `verify`
passed lint, formatting, typing and all 511 tests on Python 3.14.7, then failed
on the same Markdown blank line in the committed PR #31 merge checkout.
Strict docs, whitespace and retained-wheel build/verification steps were skipped
in that hosted job; their local equivalents passed above.
The local fix is absent from hosted CI until committed and pushed.

HY-8 executable comparison and optional external-harness typing were not run;
ordinary CI excludes those local integration checks. GitHub Pages deployment
was not triggered. No hydraulic behaviour or tracked comparison baseline changed.
These checks provide regression evidence, not engineering acceptance.
The documentation fix, validation record and rebuilt retained wheel remain unstaged
and uncommitted; no push or publication was performed.

PR #27 review and CI repair (2026-10-06): Owner: Unassigned. Status: verified locally.
Clarified the source regression's inlet-velocity basis and its conversion to the
full-barrel velocity basis. Checked Sellevold et al. Equations 4/5 (page
04023038-3), Equations 10/11 and Table 4 (page 04023038-8) in the
[author-uploaded full text](https://www.researchgate.net/publication/377473974).
An independent algebra check confirmed equal head loss on both velocity bases
and the conversion factor of 16 at 75% blockage. No solver code was changed.

Actions run 37351762892 failed Markdown checking on an extra blank line.
Removed it and added the missing research-page navigation entry, which also
caused a local strict-build failure. All three installed-wheel CI jobs passed.

Verification on Python 3.14.6:

- `python -m pytest -q`: 488 passed.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 133 files formatted.
- `python -m pyright`: zero errors, warnings or information messages.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`: passed.
- `python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.

No new package build, local installed-wheel test or HY-8 executable comparison
was run for this documentation repair. Changes are uncommitted and unpushed;
no publication was performed. Implementation and experimental validation remain
future work under issue #18. Next action: commit and push, then verify fresh CI.

PR #26 CI repair (2026-10-06): Owner: Unassigned. Status: verified locally.
Added the Austroads worked-example research page to MkDocs navigation, resolving
the strict-build failure in Actions run 37349719931. The remaining checks in that
job were skipped after the documentation failure; all three installed-wheel jobs
passed. No hydraulic behaviour or source interpretation changed.

Verification on Python 3.14.6:

- `python -m pytest -q`: 488 passed.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 132 files formatted.
- `python -m pyright`: zero errors, warnings or information messages.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`: passed.
- `python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- `python scripts/verify_wheel.py`: existing retained wheel integrity passed.

No new package build or local installed-wheel test was run for this navigation-only
repair. HY-8 executable comparison was not run. The repair is committed locally;
next action is to push the branch and confirm the new CI run completes. No release
or publication was performed.

- [External validation of advanced roadway overtopping](2026-10-05-roadway-overtopping-external-validation.md) â€” [47 discharge cases and seven boundary investigations recorded](2026-10-06-roadway-overtopping-comparison-results.md); irregular differences and submerged-method parity remain unresolved.

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

- [`ryan-tools` issue #81](https://github.com/Chain-Frost/ryan-tools/issues/81) owns project/scenario/alternative configuration;
- [`ryan-tools` issue #82](https://github.com/Chain-Frost/ryan-tools/issues/82) owns design-option/minimum-size search and ranking;
- [`ryan-tools` issue #83](https://github.com/Chain-Frost/ryan-tools/issues/83) owns CLI/reporting/export;
- [`ryan-tools` issue #84](https://github.com/Chain-Frost/ryan-tools/issues/84) owns plotting/GUI;
- [`ryan-tools` issue #87](https://github.com/Chain-Frost/ryan-tools/issues/87) owns floodway formation assessment/reporting; and
- [`ryan-tools` issue #91](https://github.com/Chain-Frost/ryan-tools/issues/91) owns project-level culvert uncertainty/sensitivity studies.

Core hydraulic prerequisites and reusable classes used by those workflows remain in
`ryan-culverts`.

## Legacy CS mapping

The CS identifiers below remain useful references into the detailed remediation record.
Their current implementation status is determined by the linked GitHub issue, not by this
table.

| Legacy ID | Current tracking | Boundary / disposition |
| --- | --- | --- |
| CS-009 | [`ryan-tools` #81](https://github.com/Chain-Frost/ryan-tools/issues/81); core work only if later required | Keep project/scenario configuration downstream. Add core serialization only if a stable hydraulic-object interchange contract becomes necessary. |
| CS-014 | Split background umbrella | Do not implement as one task. Its former hydraulic scope is separated into issues [#20](https://github.com/Chain-Frost/ryan-culverts/issues/20) through [#23](https://github.com/Chain-Frost/ryan-culverts/issues/23). |
| CS-015 | [`ryan-culverts` #15](https://github.com/Chain-Frost/ryan-culverts/issues/15) | Resolve the Austroads worked-example velocity inconsistency before numerical use. |
| CS-021 | [`ryan-culverts` #16](https://github.com/Chain-Frost/ryan-culverts/issues/16) | GitHub issue is authoritative; currently closed/not planned unless reopened. |
| CS-022 | [`ryan-culverts` #17](https://github.com/Chain-Frost/ryan-culverts/issues/17) | GitHub issue is authoritative; currently closed/not planned because the release-distribution activation trigger is not met. |
| CS-023 | [`ryan-tools` #82](https://github.com/Chain-Frost/ryan-tools/issues/82) | Design-option enumeration, feasibility and ranking remain downstream. |
| CS-024 | [`ryan-tools` #84](https://github.com/Chain-Frost/ryan-tools/issues/84); core result support in [`ryan-culverts` #9](https://github.com/Chain-Frost/ryan-culverts/issues/9) | Plotting dependencies stay out of the hydraulic core. |
| CS-025 | [`ryan-culverts` #3](https://github.com/Chain-Frost/ryan-culverts/issues/3) | Additional supported shapes and source-traceable materials. |
| CS-026 | [`ryan-culverts` #18](https://github.com/Chain-Frost/ryan-culverts/issues/18) | Explicit debris/blockage hydraulic scenarios. |
| CS-027 | [`ryan-culverts` #19](https://github.com/Chain-Frost/ryan-culverts/issues/19) plus [`ryan-tools` #91](https://github.com/Chain-Frost/ryan-tools/issues/91) | Core owns reusable uncertainty contracts/primitives; downstream owns study orchestration, aggregation and reporting. |
| CS-028 | [`ryan-culverts` #4](https://github.com/Chain-Frost/ryan-culverts/issues/4) and [#14](https://github.com/Chain-Frost/ryan-culverts/issues/14); PR [#13](https://github.com/Chain-Frost/ryan-culverts/pull/13) | Core owns advanced roadway overtopping and the downstream-consumable roadway hydraulic state. |
| CS-029 | [`ryan-culverts` #2](https://github.com/Chain-Frost/ryan-culverts/issues/2) | Implemented/closed issue; retain the CS section as background validation history. |
| CS-030 | [`ryan-culverts` #20](https://github.com/Chain-Frost/ryan-culverts/issues/20) | Slipline host/liner geometry and sourced roughness treatment. |
| CS-031 | [`ryan-culverts` #21](https://github.com/Chain-Frost/ryan-culverts/issues/21) | Receiving-section model and Borda-Carnot exit-loss refinement. |
| CS-032 | [`ryan-culverts` #22](https://github.com/Chain-Frost/ryan-culverts/issues/22) | Buried-invert geometry and coefficient disposition. |
| CS-033 | [`ryan-culverts` #23](https://github.com/Chain-Frost/ryan-culverts/issues/23) | Depth-dependent roughness with explicit material zones. |
| CS-034 | [`ryan-culverts` #1](https://github.com/Chain-Frost/ryan-culverts/issues/1) | Implemented/closed issue; retain the CS section as background inverse-capacity history. |

Completed CS-001 through CS-013, CS-016, CS-017, CS-019, and CS-020 remain historical
records of bounded work already delivered. Reopen or create a GitHub issue if new evidence
requires additional work rather than silently changing their historical status.

## Repository-review issues

The repository review and subsequent integration work are tracked directly as GitHub
issues:

- [#5](https://github.com/Chain-Frost/ryan-culverts/issues/5) synchronises packaged version, wheel and release documentation;
- [#6](https://github.com/Chain-Frost/ryan-culverts/issues/6) reconciles public API documentation with implemented capabilities;
- [#7](https://github.com/Chain-Frost/ryan-culverts/issues/7) provides machine-readable hydraulic result validity/severity;
- [#8](https://github.com/Chain-Frost/ryan-culverts/issues/8) covers independent heterogeneous-crossing and rating-curve validation;
- [#9](https://github.com/Chain-Frost/ryan-culverts/issues/9) provides longitudinal HGL/EGL data for full and pressurised reaches;
- [#10](https://github.com/Chain-Frost/ryan-culverts/issues/10) exposes representative-barrel/equal-flow applicability limits;
- [#11](https://github.com/Chain-Frost/ryan-culverts/issues/11) makes version reporting truthful for standalone and vendored layouts;
- [#14](https://github.com/Chain-Frost/ryan-culverts/issues/14) exposes roadway segment hydraulic state for downstream floodway analysis;
- [#15](https://github.com/Chain-Frost/ryan-culverts/issues/15) through [#23](https://github.com/Chain-Frost/ryan-culverts/issues/23) carry the migrated remaining CS work where applicable.

Always use the GitHub issue itself for current status and acceptance criteria.
