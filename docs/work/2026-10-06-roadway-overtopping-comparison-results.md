# Roadway external comparison results

Date: 2026-10-06. Branch: `validation/roadway-overtopping-external`.

Status: Requested comparison matrix recorded; engineering acceptance remains limited.
Owner: Unassigned.

This execution follows the [desktop task scope](2026-10-05-roadway-overtopping-external-validation.md).
No production hydraulic code, coefficient, supported submergence boundary, or existing
external baseline was changed. HY-8 is comparison evidence, not hydraulic authority.

## Outcome

The new adapter supports the required authoring and execution workflows. We retained
**47 discharge comparisons** and **seven boundary investigations**. Saved roadway geometry,
surface, coefficient card, tailwater, barrel dimensions/inverts/roughness/inlet and requested
discharge were checked through the adapter reader after HY-8 execution.

Roadway-flow dispositions are:

| Cases | Count | Disposition |
| --- | --- | --- |
| Constant free crest, small partial-profile flows, and inactive roadway points | 15 | `externally corroborated` within a propagated report-precision band; six are inactive-roadway cases |
| Active sloping/sag free profiles beyond that band | 12 | `external-software behaviour unresolved` |
| Paved/gravel local submergence compared to HY-8 user-coefficient or automatic surface modes | 20 | `unsupported comparison` because fixed coefficient and physical surface correction cannot be selected independently |

These classifications concern roadway discharge at HY-8's reported upstream stage. They
do not imply complete culvert-method agreement. The CSV separately labels full crossing
comparisons; all 15 combined free-flow cases retain unresolved full-crossing disposition.
Their hydraulic differences are quantified below without a fitted acceptance tolerance.

## Executed environment and provenance

- Python `3.14.6`; Windows 10 Pro, build `19045`.
- Local source baseline: `66dff0f943effd05b5ce0a678697d81d69bf5ed2`.
- `run-hy8` source commit: `0baaa2ac83e38aaad1a0419dc6e39c40445cb98d`.
- Installed distribution reports `2026.10.5.1`; wheel SHA-256:
  `76ab3ea636f30be8c409136bd1717d42b00765c95c4cdeaee89bcc3a23016b39`.
  All 25 installed package Python/typing files match the wheel after newline normalization.
  This differs from the earlier wheel with the **same version**; identify it by hash.
- HY-8 file/product version `8.0.1.2`; executable SHA-256:
  `0b1c5e7fb6b48be9c675b5486ae9a84346f436c5c649aa5ed09a1552267ee806`.
- HEC-RAS is installed, but no new HEC-RAS execution was performed; see its disposition below.

The [machine-readable provenance](../validation_data/hy8_8_0_1_2_roadway_overtopping.json)
contains the actual package-file fingerprints, executable identity, shared inputs, evidence
hashes, and boundary workspace artifact hashes. No machine-specific absolute paths are
retained. Raw executable projects/reports remain ignored under `validation_artifacts/`.

## Matrix and retained quantities

All cases use SI authoring/display units, a `10 m` top width, explicit local coefficient
`1.6 m^0.5/s`, and one `1.2 m` circular concrete barrel, `30 m` long, outlet invert
`9.7 m`, Manning roughness `0.012`, square-edge headwall, default HY-8 profile, and
exit-loss option `0`. Constant and irregular flags are explicit. Automatic paved/gravel
HY-8 cases preserve the coefficient card but do not use it as the selected coefficient.

Profiles, in horizontal station/elevation metres:

- Constant: `(0,12), (20,12)`.
- Linear slope: `(0,12), (10,12.5), (20,13)`; the middle point is collinear.
- Sag: `(0,13), (5,12.4), (10,12), (15,12.3), (20,12.8)`.

The 27 free-flow cases use tailwater `9.7 m`:

- Each profile at `Q=(0.1,1,10,20) m3/s` with the culvert inlet raised to `15 m` so the
  barrel remains inactive. Its outlet remains `9.7 m`; this steep placeholder isolates
  roadway flow and is not an active-culvert validation geometry.
- Each profile at `Q=(1,3.45,4,8,20) m3/s`, inlet invert `10 m`, spanning culvert-only
  flow, near activation, and substantial combined flow.

The 20 submerged cases use constant crest and inlet invert `10 m`. For each local paved
and gravel surface, ratios `(0.5,0.8,0.9,0.98,0.99)` are prescribed at local stage `13 m`;
tailwater is `12 m + ratio`. Total discharge is independently assembled by the local
forward-capacity API at that fixed stage, then supplied unchanged to HY-8 in user-coefficient
and corresponding automatic-surface modes. These ratios label the **local** case; HY-8
finds its own upstream stage and therefore can have a different ratio.

The [47-case CSV](../validation_data/hy8_8_0_1_2_roadway_overtopping.csv) retains total flow,
tailwater, both headwaters, roadway/group/barrel flow, outlet velocity, local regime,
HY-8 flow type, flow-closure residuals and discrepancy classifications. One group with one
barrel makes the retained culvert flow both the group and barrel flow.

Local segment JSON retains interval index/limits, integration station, physical interval
length, Gaussian effective length, unit discharge/contribution, upstream/downstream heads,
crest, free/submerged state, ratio/factor and full source provenance. HY-8 does not expose
equivalent Gaussian segments or an unrounded roadway discharge in the inspected outputs;
none is invented.

## Precision, analytical evidence and differences

HY-8 `.rst` quantities are rounded to `0.01` in SI display units. The roadway comparison
propagates `HW +/- 0.005 m`, `Qroad +/- 0.005 m3/s`, and coefficient-card rounding of
`+/- 3e-7 m^0.5/s` through the local equation. This produces a case-specific flow band.
It is not a numerical-root, field-design or regulatory tolerance. Input parity checks use
`4e-7 m` for six-decimal US-length storage. No acceptance band is widened to cover a
discrepancy.

| Case family | Maximum absolute HW difference | Maximum roadway-flow difference | Maximum culvert-flow difference |
| --- | --- | --- | --- |
| Constant crest, inactive culvert | `0.001375 m` | `8.72e-8 m3/s` | `0 m3/s` |
| Sloping crest, inactive culvert | `0.019307 m` | `8.83e-8 m3/s` | `0 m3/s` |
| Sag crest, inactive culvert | `0.009834 m` | `1.24e-8 m3/s` | `0 m3/s` |
| Combined free flow, all profiles | `0.015977 m` | `0.031549 m3/s` | `0.031549 m3/s` |
| Submerged, unmatched methods | `0.030000 m` | `0.200000 m3/s` | `0.198705 m3/s` |

Inactive-culvert roadway flow equals the supplied total by conservation in both programs;
that near-zero flow difference alone does **not** corroborate the headwater relationship.
The stage-conditioned comparison is what identifies the irregular discrepancy.

Smallest retained irregular discrepancy: `road-only-slope-1`, input `1 m3/s`, local
headwater `12.360692872343 m`, HY-8 `12.38 m`, and zero culvert flow in both. At HY-8's
reported stage the local roadway calculation is `1.139239643063 m3/s`, with a report band
`[1.097133454772,1.182085480666] m3/s`, excluding HY-8's `1.00 m3/s` roadway flow.
Saved geometry, boundary and coefficient-card parity were checked. Its exact external
integration/coefficient/convergence explanation is unresolved.

For a linear interval, independent analytical integration uses
`C L (h_left^2.5 - h_right^2.5) / (2.5 (z_right-z_left))`, clipping negative endpoint heads
to zero; equal crest elevations use `C L h^1.5`. Four-point Gaussian integration has a
relative error of about `0.00012404` for the normalized wet-edge `x^1.5` integral.
The offline checks use a separate `0.0002` relative quadrature envelope against the exact
integral. All free-profile points satisfy it. This supports the implemented HDS-5 integral;
it does not establish which undocumented executable detail explains the difference.

The largest local crossing closure residual is `1.89e-7 m3/s`. HY-8 displayed closure is
zero in all free cases and at most `0.02 m3/s` in submerged cases. Two paved-local ratio
`0.98` cases exceed the `0.0151 m3/s` allowance for three rounded report quantities; their
closure is explicitly `external-software behaviour unresolved`, not accepted by increasing
the tolerance. For example, HY-8 reports total `19.71`, culvert `0.68`, roadway `19.05`.

Local roadway activation agrees with HY-8's inactive/active progression across the combined
sequences. Culvert regime names remain method-specific; the CSV preserves both labels
without asserting exact synonyms. A submerged local roadway retains its sourced correction
even in the unity-factor region; external roadway correction factors are not available.

## Boundary outcomes and external limitations

The [boundary CSV](../validation_data/hy8_8_0_1_2_roadway_overtopping_boundaries.csv) covers
crest stage, equal stage, supported paved ratios `0.98/0.99`, unsupported ratio `0.995`,
reverse head, and missing submerged surface.

The local solver returns zero at crest/equal stage, computes supported ratios and rejects
the unsupported gap, reverse head and missing surface. HY-8 inverse execution returned a
rounded crest stage with zero roadway flow; equal/gap requests selected the minimum
`0.05 m3/s` sample with reported HW `13.00 m`. Supported near-equal requests likewise can
select the minimum-flow sample because its stage is within the wrapper's `0.01 m` inverse
tolerance. The reverse request failed to bracket, nearest reported stage `13.00 m` versus
target `12.90 m`. Saved geometry, surface and boundary were verified in every inverse
workspace project.

These outcomes do not prove nonzero capacity at exactly equal stage or successful execution
at an exact ratio `0.995`: rounded reports and inverse-search tolerance cannot resolve that
question. Those cases remain unresolved. Missing-surface input has no equivalent HY-8 mode;
user-defined HY-8 submergence cannot be identified as the local paved law. Automatic surface
cases also have unmatched free coefficients. All such comparisons remain unsupported.

HEC-RAS is excluded from this matrix because a matched roadway/approach-section model
with equivalent energy-head treatment has not been established. Its weir head uses upstream
energy, whereas these local inputs supply stage. The existing normal-depth harness is not
an equivalent roadway fixture. No HEC-RAS comparison is claimed; a later matched model must
retain approach velocity head, geometry and submergence-method differences explicitly.

## Reproduction and checks

Run from this repository with normal user Python and the installed optional adapter:

```powershell
$env:PYTHONPATH='src'
python scripts/compare_hy8_roadway.py --workspace validation_artifacts/roadway-matrix-2026-10-06 --output docs/validation_data/hy8_8_0_1_2_roadway_overtopping.csv --wheel $runHy8Wheel --adapter-commit 0baaa2ac83e38aaad1a0419dc6e39c40445cb98d --local-commit 66dff0f943effd05b5ce0a678697d81d69bf5ed2
python -m pytest tests/test_external_roadway_validation.py -q
```

Set `$runHy8Wheel` to the verified wheel location before executing the command. Evidence
contains no absolute paths. HY-8 assigns project timestamps/GUIDs, so raw hashes can change
between runs even when hydraulic quantities repeat. The script verifies the imported
package against the supplied wheel before execution; commit arguments identify the tested
source and must be updated if source changes. Optional `run-hy8` remains outside runtime
dependencies, and the offline tests run without it or HY-8.

The `external-validation` extra in `pyproject.toml` declares the optional adapter at the
tested source commit. CI installs only `dev`, without `run-hy8`, and checks all offline
tests; ordinary Pyright excludes the two optional HY-8 harnesses. Local validation checks
those harnesses with `python -m pyright --project pyright-external.json` and the external
extra installed. Direct-reference metadata is
enabled for this optional Git dependency; no hydraulic runtime dependency was added.

The focused suite passed **81 tests**. One development check initially assumed every native
closure was explained by report rounding; it exposed the two `0.02 m3/s` residuals. The
final checks assert faithful unresolved classification instead of widening that allowance.

Executed repository checks:

- `python -m pytest -q`: **479 passed**, 19.53 seconds.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed, 131 files already formatted.
- `python -m pyright`: passed, 0 errors / 0 warnings.
- `python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md`: passed.
- `python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.

The separately installed adapter was verified against its existing wheel before running
the matrix. HY-8 execution was run; HEC-RAS execution was not.

### PR preparation and CI without HY-8

The user requested a draft PR for external-agent review and specified that GitHub CI cannot
use `run-hy8`. The `dev` extra therefore contains no adapter dependency; the optional
`external-validation` extra owns its exact source pin. CI no longer installs the adapter.
`pyright-external.json` checks the two optional harnesses locally, while ordinary Pyright
checks the library, offline tests and remaining scripts.

Checks repeated during PR preparation:

- Full suite using normal Python: **479 passed**, 20.10 seconds.
- Ordinary and external Pyright: passed; the external configuration checked two source files.
- Ruff check/format, Markdown scan, strict MkDocs and whitespace check: passed.
- Isolated review snapshot, with `run_hy8` confirmed absent: **479 passed**, 21.75 seconds;
  ordinary Pyright targeting that interpreter also passed.
- Wheel built from that review snapshot without a version bump: passed; verification through
  `scripts/verify_wheel.py` passed. Its optional adapter requirement is marked only for
  `external-validation`, and it retains the supported Python range `>=3.14,<3.15`.
- Installed-wheel smoke test in isolated Python with no adapter: passed.

The review snapshot excludes the user's separately staged `pyproject.toml` formatting and
Python-range edits. Those local edits are preserved; this PR changes only the optional
dependency and type-check configuration there. Build/install artifacts remain ignored;
no tracked distribution wheel is replaced. Remote CI evidence belongs to the draft PR.

## Remaining work

The matrix and offline regression evidence are delivered. The overall task is not marked
engineering-complete. Resolve the reduced irregular discrepancy using primary-method and
executable evidence, then establish whether user-defined submergence is comparable to a
documented local surface law. Exact equal/gap-stage behaviour requires an external output
or prescribed-stage workflow with sufficient precision. A heterogeneous roadway crossing
was not added because the simple discrepancies remain unresolved. HEC-RAS corroboration
requires the matched energy-head model described above.

No code was tuned to HY-8. Submission for review does not close the engineering-validation
limitations above.
