# Work register

This is the entry point for agents continuing the culvert solver. The detailed,
authoritative execution record is the
[Phase 0-10 remediation and forward plan](2026-09-06-phase-0-to-10-remediation.md).
The original [work plan](../../culvert_solver_updated_work_plan.md) defines the
long-term scope; it is not a claim that its phases are complete.

## Selecting work

An agent must claim one task by replacing `Unassigned` with its name before editing.
Stay within that task's boundary in the detailed plan, record evidence in the named
documents, and return the owner to `Unassigned` at handoff. A task may be implemented
without being complete; only its acceptance criteria permit `Complete` status.

Recommended order:

1. CS-001 establishes source decisions; CS-002 can progress independently.
2. CS-003 owns inlet-method implementation, including high-head behaviour.
3. CS-004 owns internal profile/regime implementation; CS-008 independently compares it.
4. CS-006 turns accepted source cases into the cross-phase validation suite.
5. CS-005 completes auditable outputs, then CS-011 completes inventory summaries.
6. CS-007 benchmarks the validated calculations; CS-012 performs release checks.

CS-001, CS-002, CS-003, CS-004, CS-005, CS-006, and CS-008 all have bounded work that
can start now. Coordinate CS-004 and CS-008 so comparison evidence is not mistaken for
the definition of correctness.

Before handoff, run focused tests for edited modules and record their exact commands and
results. The ordinary repository checks are:

```powershell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m pyright
python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs
git diff --check
```

CS-012 adds the package build and isolated installed-wheel checks; do not bump a version
or create a release artifact merely to complete an earlier task.

## Active work

| ID | Status | Owner | Updated | Next review | Next action |
| --- | --- | --- | --- | --- | --- |
| CS-001 | Ready, in progress | Unassigned | 2026-09-08 | 2026-09-14 | Finish source reviews and publish explicit method decisions and fixture inputs. |
| CS-002 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Monitor source revisions; reopen only for a supported new material or fallback. |
| CS-003 | Complete | Unassigned | 2026-09-08 | 2026-09-20 | Reopen only if primary evidence supports a different digital transition or high-head extension. |
| CS-004 | Ready, high risk | Unassigned | 2026-09-08 | 2026-09-14 | Validate mixed profiles and resolve the long-case crown-transition method. |
| CS-005 | Ready, diagnostics implemented | Unassigned | 2026-09-08 | 2026-09-14 | Recheck result fields after CS-004, then unblock CS-011. |
| CS-006 | Ready in part, primitives added | Unassigned | 2026-09-08 | 2026-09-14 | Add profile, group/crossing, and rating fixtures after CS-004 settles. |
| CS-007 | Blocked by CS-004/006 | Unassigned | 2026-09-08 | 2026-09-14 | Replace the temporary 0.6 ms wall-clock ceiling with a reproducible benchmark after validation. |
| CS-008 | Ready, in progress | Unassigned | 2026-09-08 | 2026-09-14 | Reproduce and explain Type 6 and crown-transition differences without tuning to HY-8. |
| CS-011 | Waiting for CS-005 | Unassigned | 2026-09-08 | 2026-09-14 | Add mixed-regime and unsupported-result inventory tests after result fields settle. |
| CS-012 | Gated release task | Unassigned | 2026-09-08 | 2026-09-20 | Run the documented release gate and bump the version only for a deliberate wheel handoff. |

## Deferred work

| ID | Status | Owner | Updated | Next review | Next action |
| --- | --- | --- | --- | --- | --- |
| CS-009 | Deferred | Unassigned | 2026-09-06 | 2026-09-20 | Define a versioned JSON/configuration boundary only when a consumer requires it. |
| CS-010 | Deferred | Unassigned | 2026-09-06 | 2026-09-20 | Add design search, plotting, and roadway-overtopping features after validation. |

Agents must update the status, owner, date, next review, and next action when
taking over or handing off a task. Do not mark a task complete solely because
tests pass; satisfy its acceptance criteria and record the evidence first.
