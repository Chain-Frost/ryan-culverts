# Uncertainty PR CI repair

Task: repair CI for PR #25, within issue #19's uncertainty-primitives boundary.
Owner: Unassigned. Status: CI repair verified locally; awaiting commit and push.

The GitHub issue remains the authoritative feature tracker. This bounded repair
preserves runtime integer validation for sampling counts and seeds while addressing
Pyright diagnostics. Hydraulic equations and comparison baselines are unchanged.

GitHub Actions run 37349638175 failed only at type checking, reporting
`reportUnnecessaryIsInstance` for seed and count validation. Targeted annotations
match existing runtime-validation conventions in the module. Local full testing
also revealed missing public API reference entries for all 13 uncertainty exports;
the new API reference page documents each once and is included in navigation.

Verification on Python 3.14.6:

- `python -m pytest -q tests/test_uncertainty.py tests/test_public_api.py`: 21 passed.
- `python -m pytest -q`: 494 passed.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 136 files formatted.
- `python -m pyright`: zero errors, warnings or information messages.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`: passed.
- `python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- `python scripts/verify_wheel.py`: existing retained wheel verified; this is
  artifact integrity evidence, not verification that the wheel contains this patch.

HY-8 executable comparison was not run; this repair changes no hydraulic behaviour.
No version bump, new package build, staging, commit, push or publication was performed.
Installed-wheel jobs for Windows, Ubuntu and macOS passed in the existing CI run;
they were not repeated locally. Issue #19's broader feature acceptance remains open.
Next action: commit and push the repair, then confirm the new PR CI run passes.
