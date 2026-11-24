# Python 3.11 compatibility migration

| Field | Value |
| --- | --- |
| Status | Needs review: local source and wheel validation pass; hosted validation pending |
| Owner | Unassigned |
| Updated | 2026-11-24 |
| Next review | 2026-11-25 |
| Baseline | `01a37bebae09ad5f6605612d8e9f93114f64af2e` |
| Branch | `compat/python311` |
| Issue | [#41](https://github.com/Chain-Frost/ryan-culverts/issues/41) |

## Scope

Support Python 3.11, 3.12, 3.13 and 3.14; retain Python 3.14 as preferred development interpreter.
Exact standalone CPython 3.11.11 represents the owner's ArcGIS Pro version target;
it does not establish execution inside ArcGIS Pro. Preserve algorithms, numerical tolerances,
reference fixtures, licensing and publication protections. No merge or publication is authorized.

## Validation

Windows isolated environments: Python 3.11.11, 3.12.14, 3.13.15 and 3.14.6.
All four applicable source suites pass: **658 passed** per interpreter.
Ruff 0.16.6 lint/format and strict Pyright target Python 3.11; rule selection and complexity limits are unchanged.
Source compilation under Python 3.11.11 passed. Wheel and sdist builds pass.
Clean wheel installation, isolated import-origin verification and pip check pass on all four interpreters.
Installed CLI help passes where a CLI is exposed. FFA distribution verification and its independent
clean-wheel/console-entrypoint smoke also pass. Independent exact-head review and hosted results remain pending.
Native HY-8, ArcGIS Pro and Flike acceptance are not established by these checks.

## Changes and dependencies

Replace two PEP 695 aliases with TypeAlias. The hydraulic foundation retains zero runtime dependencies.

## Next action

Publish the checked compatibility PR, obtain independent review of its exact head and verify the final hosted matrix. No merge or release.

Local evidence directory: `E:/Github/compat311-evidence` (not required at runtime). Ruff safe fixes: 2 automatic; no remaining manual Ruff findings.
