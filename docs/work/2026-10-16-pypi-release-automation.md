# Merge-only PyPI release policy follow-up, 2026-10-18

Status: Needs review. Owner: Unassigned. Next review: 2026-10-19.

## Current work

Port run-hy8 PR #17's verified release opt-out to this repository. Only successful
post-merge Python CI for the latest actual PR merge into main may initiate release
creation. Remove periodic, manual and release-published entry points. Preserve the
existing builder, version format, package metadata and PyPI Trusted Publisher identity.
Add skip-release label and case-insensitive [skip release] merge-message opt-outs,
plus exact main/tag SHA checks immediately before upload.

run-hy8 PR #17 merged as d34e0f047bc7a4a30a53d7353369bbb337625c33.
Post-merge CI 39104620810 and Pages 39104620894 succeeded. Release decision
39104751133 logged "PR #17: release explicitly skipped." Publisher 39104763708
skipped both build and upload; asset sync 39104773672 completed with no release.
No tag or GitHub Release points to that merge. This verifies the opt-out path;
a later eligible merge must still verify actual OIDC publication end to end.

## Delivery and next action

Worktree: `E:/Github/ryan-culverts-merge-release`, branch `ci/merge-only-release-policy`,
based on 5fca7d4. Original checkout changes are untouched.
Implementation committed as `c4cc43e` and pushed to
`origin/ci/merge-only-release-policy` with explicit user authorization on 2026-10-18.
[PR #38](https://github.com/Chain-Frost/ryan-culverts/pull/38) is open with the
skip-release and enhancement labels and [skip release] in its title.
Hosted CI is running; next action is to confirm all required checks on the latest
PR head and inspect review feedback. Merging and publication are not authorized.
Use title `[ci] [skip release] Publish only verified PR merges`, retain the
skip-release PR label, and preserve [skip release] in the squash-merge commit.
Hosted PR CI and later eligible publication remain distinct verification steps.

## Validation on 2026-10-18

Python 3.14.6, Windows, exact local tree based on 5fca7d4:

- Focused release policy, calendar allocation/stamping, and preparation tests: 46 passed.
- Full ordinary suite: 557 passed in 20.51 seconds, no skips or deselections.
- Full Ruff check passed; format: 148 files already formatted; full strict Pyright:
  zero diagnostics.
- Markdown lint including AGENTS.md and strict MkDocs build passed.
- No-bump build and verifier passed for ryan_culverts-26.10.16.1-py3-none-any.whl,
  113280 bytes, SHA-256 80395976e9ab035956862dfbec391068b69fbb93bfeda7f69c5f18e41aa7674b.
- Isolated target install and installed-wheel public-API smoke passed outside the
  source tree; verified import containment in that target.
- Hosted cross-platform installed-wheel matrix and HY-8 comparisons were not run;
  no hydraulic behavior, coefficients or comparison baselines changed.
- Checksum-verified Actionlint 1.7.12 passed across workflows.
- Every embedded PowerShell block parses; both embedded Python shell blocks compile.
- The publisher build job is text-identical to main, preserving repository-specific
  submodules, version stamping, build and installed-wheel checks.
- Diff whitespace checks passed; package metadata and declared versions are unchanged.
- The pypi environment was inspected as custom v* tag-only, then given a specific main
  branch deployment rule. Re-read confirms both main (branch) and v* (tag); no other
  settings, reviewers, branch protections or Trusted Publisher identity changed.
- Actual OIDC upload under the new workflow chain is not yet verified. run-hy8
  demonstrated the skip path only; it created no tag, Release or uploaded wheel.

## Historical release setup evidence

## Original PyPI release automation and CI consistency

| Field | Value |
| --- | --- |
| Status | Active |
| Owner | ChatGPT |
| Created | 2026-10-16 |
| Updated | 2026-10-16 |
| Next review | 2026-10-23 |
| Delivery | feature/pypi-release-automation; [PR #32](https://github.com/Chain-Frost/ryan-culverts/pull/32) |

## Scope

Set up the same reviewed release-PR, post-merge CI, stable-release and OIDC publication
process as ryan-tools. Add consistent Perth-date preparation and focused CI improvements.
Preserve package interfaces, interpreter coverage and hydraulic validation boundaries.

## Current state

Added preparation/finalization/publication workflows and the release helper. The
[publication guide](../pypi_publishing.md) owns setup, release and recovery instructions.
[PR #32](https://github.com/Chain-Frost/ryan-culverts/pull/32) owns current review status. No release or PyPI upload has been started.

## Next action

Review the new PR and its hosted checks, merge reviewed automation, then run the first
release explicitly. Publish run-hy8 first, then validate the optional ryan-culverts extra.
The user supplied screenshots confirming both pending PyPI publishers are configured.

## Validation and delivery

Local validation on Python 3.14:

- Calendar and transactional rollback tests: 16 passed.
- Ruff check and format passed; strict Pyright passed with zero diagnostics.
- Actionlint passed across all workflows; PowerShell parsing passed for every pwsh block.
- Executed workflow JavaScript locally against 13 mocked stable-release/finalization
  scenarios, including ordinary merges, two/four-digit years, retries and invalid tags.
- URL-dependency validation passed against the retained wheel, accepted a normal optional
  PyPI requirement and rejected a synthetic Git URL dependency in an extra.
- Full preparation through the real verified builder and Twine passed in an isolated
  temporary source copy. Normal checkout versions were not bumped.
- Git diff whitespace checks passed before commit.
No hydraulic coefficients, methods or retained comparison evidence changed.

HY-8 executable comparison was not run; it is not required to configure publication.
Hosted publication and OIDC remain untested until the PyPI setup and PR merge.

## Repository-specific evidence

- Full ordinary suite: 527 passed in 22.36 seconds, no skips/deselections.
- Ruff format: 142 files already formatted; full strict Pyright had zero diagnostics.
- Markdown lint (including AGENTS.md) and strict MkDocs build passed.
- Rebuilt retained 26.9.10.2 wheel without bumping after metadata changed; verifier,
  Twine and isolated installed public-API smoke passed.
- Wheel SHA-256: `7f35ffcc12272348495820be99f6196627d27e76432170a6758d630a670a804c`.
- Replaced the optional Git URL with `run-hy8>=2026.10.5.1` from PyPI at the user's
  request. The external-validation extra is preserved; ordinary CI does not install it.
  Prior executable evidence remains tied to the source commit recorded in that evidence.

## GitHub and PyPI setup

Configured and re-read the main/tag rulesets, squash-only repository merge settings,
automatic branch deletion, Actions PR creation and tag-only pypi environment. Main
requires this repository's existing CI contexts and resolved review conversations,
with zero required approvals and maintainer bypass restricted to PRs. Tags require
CI, permit creation by automation and restrict updates/deletions. No API token was stored.
Both PyPI pending publishers were confirmed by the user's screenshot. Setup workflows
are committed and pushed in PR #32; no merge, release or upload was performed.

## Retry review fix, 2026-10-16

The review correctly identified duplicate publication dispatch on finalizer retries.
Across all three repositories, finalization now checks PyPI and active publication runs
before dispatching. Already published or active revisions skip dispatch; missing versions
with no active run remain recoverable. Transient/unknown lookup failures fail closed.
All 16 mocked release/finalization/retry scenarios passed, including already published,
active, failed previous attempts and unavailable lookup service. Actionlint and touched
document checks are rerun before pushing; exact-head hosted CI must pass before merging.

The user asked to continue with first-publication validation. Complete review fixes and
required CI, then merge and publish run-hy8 first, verify its public installation, and
subsequently publish ryan-culverts and validate the optional integration.
