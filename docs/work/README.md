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
2. CS-010 now provides the bounded first roadway-overtopping increment.
3. CS-012 performs release checks only for a deliberate wheel handoff.
4. CS-013 and CS-034 have completed their bounded implementations.
5. CS-014 was split before implementation; CS-030 through CS-033 own its former scope.
6. CS-015 and CS-022 through CS-033 preserve future work.

CS-015 and the split NCHRP tasks must not be folded silently into the current equations
or release claim. Reopen CS-013 only if corrected source evidence changes its bounded
catalogue or validation.

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
| CS-010 | Complete | Unassigned | 2026-09-10 | 2026-09-20 | Use the constant-crest free-flow roadway model; CS-028 owns irregular crests and submergence. |
| CS-011 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Reopen only when a new result or notice field requires inventory representation. |
| CS-012 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Use the current verified wheel for integration tests; packaging now increments the calendar version. |
| CS-013 | Complete | Unassigned | 2026-09-10 | 2026-09-20 | Use only the typed Figure 93 configurations and keep corrected Table 12 within its documented range. |
| CS-016 | Complete | Unassigned | 2026-09-10 | 2026-09-20 | Keep navigation intentional and require strict local and CI builds before Pages deployment. |
| CS-017 | Complete | Unassigned | 2026-09-09 | 2026-09-20 | Use `package.bat` to create the next verified wheel; reopen only for a packaging failure or changed version policy. |
| CS-019 | Complete | Unassigned | 2026-09-10 | 2026-09-20 | Python 3.14 is the supported baseline; keep the installed-wheel OS matrix green. |
| CS-020 | Complete | Unassigned | 2026-09-10 | 2026-09-20 | Maintain top-level exports, version discovery, changelog entries, and project links together. |
| CS-034 | Complete | Unassigned | 2026-09-10 | 2026-09-20 | Maintain public barrel, group, and crossing discharge-for-headwater helpers and their round-trip tests. |

## Deferred work

| ID | Status | Owner | Updated | Next review | Next action |
| --- | --- | --- | --- | --- | --- |
| CS-009 | Deferred | Unassigned | 2026-09-06 | 2026-09-20 | Define a versioned JSON/configuration boundary only when a consumer requires it. |
| CS-014 | Split | Unassigned | 2026-09-10 | 2026-09-20 | Do not implement this umbrella; use CS-030 through CS-033. |
| CS-015 | Pending source clarification | Unassigned | 2026-09-09 | 2026-09-20 | Resolve the AGRD05B-23 Section 3.15.1 velocity inconsistency before numerical use. |
| CS-021 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Add only concise contribution, security-reporting, dependency-update, and branch-rule guidance. |
| CS-022 | Optional | Unassigned | 2026-09-09 | 2026-12-01 | Reconsider GitHub Releases only if the Git-pulled office checkout no longer meets user needs. |
| CS-023 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Define design-option enumeration and minimum-size search as a separate consumer of the solver. |
| CS-024 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Add optional plotting without presentation dependencies in the hydraulic core. |
| CS-025 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Prioritise and add supported shapes and materials independently of design automation. |
| CS-026 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Research and model debris and blockage scenarios with explicit applicability limits. |
| CS-027 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Add uncertainty and sensitivity analysis over explicit input distributions. |
| CS-028 | Deferred | Unassigned | 2026-09-09 | 2026-09-20 | Extend roadway flow to irregular sag profiles and evidenced downstream-submergence correction. |
| CS-029 | Partial | Unassigned | 2026-09-10 | 2026-09-20 | Add the planned user-supplied monotonic stage-discharge boundary and an external Manning-boundary comparison. |
| CS-030 | Deferred | Unassigned | 2026-09-10 | 2026-09-20 | Model host and liner geometry plus sourced composite roughness for slip-lined culverts. |
| CS-031 | Deferred | Unassigned | 2026-09-10 | 2026-09-20 | Model downstream receiving-section area before adding Borda-Carnot exit loss. |
| CS-032 | Deferred | Unassigned | 2026-09-10 | 2026-09-20 | Research and model buried-invert geometry without using rejected embedded coefficients. |
| CS-033 | Deferred | Unassigned | 2026-09-10 | 2026-09-20 | Add depth-dependent roughness only with an explicit supported applicability model. |

Agents must update the status, owner, date, next review, and next action when
taking over or handing off a task. Do not mark a task complete solely because
tests pass; satisfy its acceptance criteria and record the evidence first.
