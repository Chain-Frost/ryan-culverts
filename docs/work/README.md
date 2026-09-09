# Work register

This is the entry point for agents continuing the culvert solver. The detailed,
authoritative execution record is the
[Phase 0-10 remediation and forward plan](2026-09-06-phase-0-to-10-remediation.md).
The [long-term development plan](long-term-development-plan.md) defines the
long-term scope; it is not a claim that its phases are complete.

## Selecting work

An agent must claim one task by replacing `Unassigned` with its name before editing.
Stay within that task's boundary in the detailed plan, record evidence in the named
documents, and return the owner to `Unassigned` at handoff. A task may be implemented
without being complete; only its acceptance criteria permit `Complete` status.

Recommended order:

1. CS-001 through CS-008 and CS-011 have completed their bounded work.
2. CS-012 performs release checks only for a deliberate wheel handoff.
3. CS-013 through CS-015 preserve research-driven future work.

CS-013 through CS-015 must not be folded silently into the current equations or release
claim.

Before handoff, run focused tests for edited modules and record their exact commands and
results. The ordinary repository checks are:

```powershell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m pyright
python -m pymarkdown -d MD013 scan -r README.md docs
git diff --check
```

CS-012 adds the package build and isolated installed-wheel checks; do not bump a version
or create a release artifact merely to complete an earlier task.

## Active work

| ID | Status | Owner | Updated | Next review | Next action |
| --- | --- | --- | --- | --- | --- |
| CS-001 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Reopen only for a corrected source edition or evidence that changes a recorded decision. |
| CS-002 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Monitor source revisions; reopen only for a supported new material or fallback. |
| CS-003 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen only if primary evidence supports a different digital transition or high-head extension. |
| CS-004 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen only for a new supported profile family, geometry, or contrary primary evidence. |
| CS-005 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen only when a supported method calculates an additional diagnostic or adopted value. |
| CS-006 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen for a new supported method or stronger independent combined-system evidence. |
| CS-007 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Rebenchmark on target hardware or reopen for an evidenced algorithmic regression. |
| CS-008 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Reopen only for contrary primary evidence or a version-pinned external comparison that changes a disposition. |
| CS-011 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Reopen only when a new result or notice field requires inventory representation. |
| CS-012 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Use the current verified wheel for integration tests; packaging now increments the calendar version. |
| CS-017 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Use `package.bat` to create the next verified wheel; reopen only for a packaging failure or changed version policy. |

## Deferred work

| ID | Status | Owner | Updated | Next review | Next action |
| --- | --- | --- | --- | --- | --- |
| CS-009 | Deferred | Unassigned | 2026-09-06 | 2026-09-20 | Define a versioned JSON/configuration boundary only when a consumer requires it. |
| CS-010 | Deferred | Unassigned | 2026-09-06 | 2026-09-20 | Add design search, plotting, and roadway-overtopping features after validation. |
| CS-013 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Add typed modern-box inlet geometry before using corrected FHWA-HRT-06-138 coefficients. |
| CS-014 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Design context-rich NCHRP slipline, exit-loss, and composite-roughness support. |
| CS-015 | Pending source clarification | Unassigned | 2026-09-09 | 2026-09-20 | Resolve the AGRD05B-23 Section 3.15.1 velocity inconsistency before numerical use. |
| CS-016 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Design and strictly validate an MkDocs site before enabling GitHub Pages deployment. |
| CS-018 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Document and test installation from the office checkout's tracked `dist/` after a manual `git pull`. |
| CS-019 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Align Python support metadata and add cross-platform installed-wheel CI without publishing another artifact. |
| CS-020 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Define public API stability, version discovery, changelog, and non-release package project URLs. |
| CS-021 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Add concise maintenance guidance, including keeping the office checkout clean and pull-only. |
| CS-022 | Optional | Unassigned | 2026-09-09 | 2026-12-01 | Reconsider GitHub Releases only if the Git-pulled office checkout no longer meets user needs. |

Agents must update the status, owner, date, next review, and next action when
taking over or handing off a task. Do not mark a task complete solely because
tests pass; satisfy its acceptance criteria and record the evidence first.
