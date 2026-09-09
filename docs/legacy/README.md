# Legacy cleanup and work-plan review

Reviewed 2026-09-06 against the long-term development plan, now stored at
`docs/work/long-term-development-plan.md`. The plan content is unchanged by its move.

## Plan assessment

The plan replaces HY-8 replication with an independent, literature-led solver.
Separating geometry, numerical methods, hydraulic relationships, regime selection,
and crossing aggregation supports that change. Analytical tests should accompany
implementation, with external comparisons later as the plan specifies.

Resolve these points during Phase 0 before implementation:

- Define tailwater as absolute elevation, group-specific depth, or a rating
  relationship, including treatment of differing outlet inverts.
- Define support or rejection rules for adverse slopes, reverse flow, dry conditions,
  and inconsistent length/slope/invert inputs. Choose authoritative geometric inputs.
- Define free-surface versus pressurised geometry at the crown: top width,
  hydraulic depth, and cases where Froude number is undefined.
- Document applicability of identical-barrel scaling and shared-headwater crossings,
  including excluded approach-flow interactions.
- Specify quantity-specific tolerances, convergence failures and result contracts.
  Require monotonicity only over physically supported solution branches.

This is a scope/architecture review, not completion of the literature review or
engineering acceptance process. The next work is the plan's Phase 0 deliverables.

## Removed

- `culvertflow/`: legacy models, approximate hydraulics, defaults, CLI and HY-8 adapter.
- Old tests and golden outputs: these encode the retired API and implementation,
  rather than independently validated targets for the new solver.
- Batch comparison scripts and wheel updater: tied to the retired package and
  bundled runner. Later verification should use external tooling per the plan.
- Installers, packaging wrappers, `pyproject.toml`, pytest configuration and test
  wrapper: these built or tested a package that no longer exists.
- Conflicting `instructions.txt`, outdated README content and `temp_view.txt`.

Ignored bytecode caches, their directories and `.coverage` remain: automatic approval
review rejected their cleanup commands as blocked by policy. They contain no active
source and are not part of the new implementation.

The user's existing `dist/` and `third_party/` deletions were preserved. No new
implementation or placeholder package was introduced ahead of Phase 0.

## Reuse candidates in Git history

The full previous implementation remains at commit
`b8574bc5432424a28d2e8fa868cbce208a577686`.

| Original path | Potential reuse and conditions |
| --- | --- |
| `culvertflow/shapes.py` | Circular segment area/perimeter and box formulas. Decouple from old models and validate limits; the circular top-width function returns diameter at full depth and needs review under an explicit crown convention. |
| `culvertflow/numerics.py` | Bracketed bisection with finite-value checks and explicit failure. Separate residual and interval tolerances; test nonfinite tolerances and difficult brackets before reuse. |
| `tests/test_outlet.py` | Test ideas for loss sensitivity, barrel scaling, elevation translation and inverse solutions. Rebuild against new contracts and independent expectations. |
| `culvertflow/cases.py` | Historical CSV interpretation. Consult when translating retained inputs; avoid carrying ambiguous units and implicit defaults into the new API. |
| `culvertflow/integrations/aquaveo.py`, `scripts/run_case_batch.py` | Historical report parsing and diagnostics, for reference when building later external verification tooling. |

For example:

```powershell
git show b8574bc:culvertflow/numerics.py
```

These are review candidates, not validated production components. Git pointers
preserve access without maintaining another executable copy of the old architecture.

## Retained evidence

| File here | Original location / purpose |
| --- | --- |
| `some-culverts.csv` | Root input table; old parser conventions include millimetres for diameter. |
| `sample_cases.csv` | `tests/data/sample_cases.csv`; metre-based legacy API examples with obsolete engine names. |
| `test.hy8` | Root historical HY-8 project. |
| `comparison_terms.csv` | `scripts/diagnostics_terms.csv`; saved Python/HY-8 differences. |
| `batch_attempts.csv` | `scripts/hy8_attempts.csv`; batch trace. |
| `root_attempts.csv` | Root `hy8_attempts.csv`; separate trace, retained without merging runs. |

These are candidate scenarios and historical evidence, not accepted golden results.
Saved comparisons contain substantial flow, velocity and headwater differences;
input/default mismatches may also contribute. Independently check inputs before reuse.

The 776 generated files from `scripts/hy8_runs/` are retained locally under
`archive/legacy-hy8-runs/`, with contents hash-verified after relocation. This folder
remains Git-ignored and needs a separate backup before discarding the checkout.
CSV report/workspace paths are unchanged historical provenance; map their
`hy8_runs/<run>/...` suffix to the archive when locating reports.

The local `hif12026.pdf` remains at the root, Git-ignored. The small CSV traces here
are outside the old ignore patterns so they can be reviewed and versioned.

## Verification

The earlier pre-cleanup check passed 21 tests and skipped the HY-8 parity module.
That established regression behaviour, not engineering validation. No external
hydraulic application was rerun for this cleanup.

There is now no executable package or active suite. Introduce new analytical and
internal tests alongside the components specified in the plan.
