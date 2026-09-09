# Repository instructions for coding agents

These instructions apply to the entire repository. They are written so cloud and web-only
agents can make useful progress without access to the locally installed HY-8 executable.

## Start here

1. Read `docs/work/README.md` and the task's detailed section in
   `docs/work/2026-09-06-phase-0-to-10-remediation.md`.
2. Claim exactly one task in the work register before editing. Stay within its stated
   boundary and return its owner to `Unassigned` at handoff.
3. Inspect Git status before writing. Preserve unrelated staged and unstaged changes. Do
   not stage, commit, push, reset, release, or broadly delete files unless explicitly asked.
4. Read the relevant parts of `docs/computational_basis.md`, `docs/architecture.md`, and
   `docs/validation.md` before changing hydraulic behaviour.

## Engineering authority

- This is a literature-led, independent culvert hydraulics library. Primary publications
  define methods and applicability; HY-8 is comparison evidence, not the definition of
  correctness.
- Do not tune equations or expected values merely to match HY-8, a legacy output, or another
  path through this implementation.
- Preserve units, source provenance, applicability limits, warnings, and convergence
  evidence in public results.
- Fail closed when physical configuration or empirical-coefficient applicability is
  ambiguous. Do not select a visually similar inlet, material, shape, or boundary silently.
- Passing tests establishes regression evidence, not construction-grade engineering
  acceptance. Describe validation limits honestly.

## Web and cloud agents without HY-8

HY-8 is a Windows application and is not expected to be available in a web agent. Its
absence is not a blocker for ordinary independent-core development.

The repository contains the offline context that web agents should use:

- `reference_docs/` contains tracked primary references, the HY-8 manual, and the audited
  `ShapeDB.dat` snapshot.
- `docs/research/` contains source interpretations and exact locators.
- `docs/validation_data/` contains version-pinned HY-8 comparison snapshots.
- `scripts/compare_hy8.py` records the local executable comparison procedure.
- `docs/hy8_feature_parity.md` distinguishes relevant solver gaps from HY-8-specific
  orchestration that belongs in `run-hy8`.

When HY-8 is unavailable:

- Treat tracked HY-8 CSVs and raw-source interpretations as read-only evidence unless the
  task explicitly authorises a baseline change backed by a fresh local HY-8 run.
- Do not regenerate, rewrite, or weaken HY-8 expectations to make a test pass.
- Do not claim new HY-8 verification. State that executable comparison was not run.
- Prefer analytical identities, primary published examples, conservation checks,
  metamorphic tests, and forward/inverse round trips.
- A task requiring a new executable result, executable-version investigation, or raw HY-8
  project/report evidence must be handed back for local Windows verification.

Good web-only tasks include typed domain models, independently sourced equations,
discharge-dependent tailwater boundaries, design-option orchestration, documentation,
API examples, and analytical tests. HY-8 file IO, executable control, and `.rst`/`.rsql`
parsing belong in the separate `run-hy8` repository unless this repository's documented
boundary is deliberately changed.

## Implementation conventions

- The supported and tested interpreter baseline is Python 3.14. If the cloud environment
  lacks it, do not relax `requires-python`; run the available checks and report the gap so
  CI or a local Python 3.14 checkout can finish verification.
- Use SI units in the hydraulic core. Keep unit conversion at explicit boundaries.
- `pyproject.toml` is the dependency authority. Do not add silent fallback dependencies.
- Import public names from `culvert_solver`. Add intentional new public names to
  `culvert_solver.__all__`, document them, and test the public import surface.
- Keep file/configuration adapters outside hydraulic equations. Add JSON or project-schema
  support only for a concrete consumer and a documented versioning contract.
- Preserve the distinction between the core solver and optional plotting, reporting,
  optimisation, or external-program orchestration.

## Verification and handoff

Run focused tests while developing, then run the ordinary repository checks when the
environment supports them:

```powershell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m pyright
python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md
python -m mkdocs build --strict
git diff --check
```

At handoff, record the exact checks and results in the relevant development documentation.
List anything not run, especially HY-8, and distinguish an environment limitation from a
test failure. Do not mark a task complete solely because automated checks pass; satisfy its
documented acceptance criteria and record remaining engineering limitations.
