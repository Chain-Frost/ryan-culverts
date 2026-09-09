# Validation strategy and evidence

## Current evidence boundary

As of the Phase 0–10 review on 2026-09-06, the suite contains 170 passing internal tests.
These establish many analytical identities, input contracts, conservation properties, and
deterministic wrapper relationships. They do not establish engineering validity for the
combined solver. Several higher-level tests compare one package entry point with another
path through the same implementation, so they are regression tests rather than independent
hydraulic oracles.

Missing evidence includes independent published water-surface-profile and hydraulic-jump
benchmarks, mixed free-surface/pressurised transitions, corrected box-inlet applicability,
and version-pinned HY-8/HEC-RAS comparisons. Performance thresholds are development
regressions and do not imply hydraulic correctness.

## Foundation milestone

The active tests are analytical and contractual, independent of legacy outputs.
`tests/test_foundations.py` covers:

- An irrational analytical root, decreasing functions and endpoint solutions.
- Tiny residuals whose scale must not cause premature convergence.
- Very large positive and opposite-sign brackets without overflow.
- Separate residual and coordinate tolerances.
- Explicit iteration exhaustion and floating-point resolution failures.
- Invalid bounds/counts/tolerances and nonfinite function evaluations.
- Millimetre conversion, invalid dimensions and floating-point underflow.
- Specific source locators and frozen result/configuration records.

Test counts and executed checks are recorded in [progress](progress.md).
Package build/import checks also verify the new source layout and typed marker.

## Numerical tolerances versus engineering acceptance

Root defaults (`x_abs=1e-10`, `x_rel=1e-12`) are algorithm settings. Hydraulic
callers must choose tolerances in appropriate units and scales. There is no
global percentage acceptance limit and these defaults are not design accuracy.

| Quantity | Planned internal oracle | Acceptance basis |
| --- | --- | --- |
| Area/perimeter/top width | Analytical empty/partial/full geometry | Absolute + relative numerical error |
| Critical depth | Rectangular closed form and independent circle cases | Depth error and Fr residual |
| Normal depth | Independently computed Manning cases | Depth and discharge residual on selected branch |
| Full-flow losses | Energy balance and direct SI equations | Head loss residual and physical sensitivity |
| Profiles | Uniform flow and published reference profiles | Elevation, energy and step refinement |
| Group/crossing flow | Conservation and independent barrel sums | Absolute flow closure and partitioning |

Set numerical values per fixture when independently deriving its expected result.
Record source precision separately from solver tolerance. Tests must cover failure
and applicability boundaries, not just successful cases or inverse self-consistency.

## Independent primitive fixtures

The following CS-006 fixtures use fixed expected values calculated independently of the
public solver entry points. HDS-5 printed page 1.15, Equation 1.1 supplies the critical-flow
condition; Appendix B, Equation B.3 supplies SI Manning flow; and printed pages 3.9-3.10,
Equations 3.1-3.5 supply the full-flow energy and loss relationships. Calculations use the
project gravity constant `g = 9.80665 m/s²`; source equations are not precision-limiting, so
the listed tolerances are numerical comparison tolerances rather than design accuracy.

| Fixture | Inputs | Independent expected result | Solver difference | Test tolerance |
| --- | --- | --- | ---: | --- |
| Circular full geometry | `D=1.0 m` | `A=0.7853981633974483 m²`, `R=0.25 m` | `0.0` at shown precision | relative `1e-14` |
| Rectangular critical flow | `b=2.0 m`, `Q=6.0 m³/s` | `yc=0.9717933987105833 m`, `Ec=1.457690098065875 m` | `0.0` at shown precision | relative `1e-12` |
| Rectangular Manning flow | `b=2.4 m`, `S=0.002`, `n=0.013`, `Q=2.6893095773667723 m³/s` | `yn=0.6 m`, `K=0.7817522735793332 m^(8/3)` | `0.0` at shown precision | depth absolute `1e-6`; conveyance relative `1e-12` |
| Circular full-flow losses | `D=1.0 m`, `L=100 m`, `Q=2.0 m³/s`, `n=0.013`, `Ke=0.5`, `Ko=1.0` | `He=0.16531016588512945 m`, `Hf=0.6958467261846067 m`, `Ho=0.3306203317702589 m`, `HL=1.191777223839995 m` | `0.0` at shown precision | relative `1e-12` |

These fixtures separate geometry, critical flow, uniform flow, and loss transcription from
the numerical solvers that consume them. They do not validate profile selection, mixed
free-surface/pressurised transitions, groups, crossings, or rating curves.

## Later hydraulic and external gates

Validate primitives before inlet/outlet control. Cover each regime and reject
inconsistent candidate solutions before integrating a barrel or crossing solver.
Check continuity only where physically expected; investigate branch transitions.

### Initial HY-8 executable comparison (2026-09-07)

The first executable comparison is now reproducible with `scripts/compare_hy8.py`.
The complete captured result matrix is retained in
[`validation_data/hy8_8_0_1_2_matrix.csv`](validation_data/hy8_8_0_1_2_matrix.csv).
It used:

- FHWA HY-8 `HY864.exe` file/product version `8.0.1.2`;
- installed `run-hy8` distribution `2026.9.8.1`, source commit
  `d3f0dbd4f85fb4aa195ade478c9a407a0bb3c0c5`; the validation wheel SHA-256 is
  `efacb82b13f0fc07fa239a9db91a3e329e87f6622e53e3c5d92525848ca70a1e`;
- `ryan-culverts` commit `1f78b3280f82169b19d059ff6509636091d87d83`;
- SI units, one barrel, no roadway overtopping, HY-8's default profile option, and
matched shape, material, entrance, dimensions, invert levels, Manning roughness,
discharge, and constant tailwater.

The comparison harness now rejects a nearest result row more than `0.0051 m³/s` from
the requested flow, any non-finite result, and any displayed roadway discharge above
`0.0051 m³/s`. It also requires exactly one indexed per-culvert diagnostic, checks its
discharge, outlet velocity, and flow type against the crossing summary, and verifies
that its full/free lengths sum to the configured barrel length. These tolerances only
accommodate HY-8's two-decimal report precision; they are not hydraulic acceptance
tolerances.

### HY-8 control-depth qualifiers

The qualifier is retained separately from the numeric depth and must be included when
interpreting or exporting a comparison result:

- `*` on an outlet-control depth means HY-8 calculated a negative depth and replaced it
  with `0.0` because the implied headwater was below the inlet invert. HY-8 developer
  Eric Jones documents this behaviour in [HY-8 Insider Article 15][hy8-insider-15].
- `**` on an inlet-control depth is treated as an extreme-headwater warning. Executable
  tests with HY-8 8.0.1.2 observed it beginning at approximately inlet-control
  `HW/D > 10`. The installed manual does not define the marker, so neither the threshold
  nor meaning is a cross-version contract. Preserve it as version-specific evidence.

HDS-5 Section 3.5.2, printed page 3.39 (local PDF page 121), provides the independent
engineering caution: the laboratory inlet curves cover `0.5 <= HW/D <= 3.0`, with a
general orifice relationship fitted at `HW/D = 3.0` for larger values. Consequently, an
unqualified numeric parse does not make an extreme result ordinarily validated. The
adopted CS-003 policy retains the direct numeric result but attaches a stable high-head
warning above `HW/D = 3` and an additional extreme-headwater warning above `HW/D = 10`.
CS-008 owns preservation of the external qualifier in comparison evidence.

### Type 6 harness audit

The large Type 6 inlet-headwater difference triggered a direct audit rather than an
assumption that HY-8 or `run-hy8` was authoritative. The installed executable reports
file and product version `8.0.1.2`. The repository's `hy8/ShapeDB.dat` and HY-8 User
Manual are byte-for-byte identical to the installed files under
`C:\Program Files\HY-8 8.00`, with SHA-256 values
`2479e9444feaff529313e18a1b26fc2de4f6b6c541db58477da6bebc602164a7` and
`267fef1f838945dcf7c0524ddd30c0b972e24abd3ace0eaec39d9aad8402a4f5`.

The HY-8-saved project contains one 0.9 m circular corrugated-steel barrel, 10 m
length, inverts 100.2/100.0 m, Manning n `0.020` on top and bottom, constant tailwater
100.1 m, and contextual inlet index 2. The installed ShapeDB identifies that index as
"Square Edge with Headwall." The raw `.rst` reports Q = `4.63 m³/s`, zero roadway
flow, Type `6-FFc`, inlet-control depth `7.61 m`, outlet-control depth `6.29 m`, velocity
`7.28 m/s`, full length `10.00 m`, and free length `0.00 m`; `run-hy8` returns those
same values through the per-culvert result API.

The local HDS-5 outlet-control depth is `6.297 m`, so the large governing difference is
not evidence of a barrel-loss or result-parser error. The local inlet depth of `7.196 m`
is the direct Appendix A Equation A.3 result using Table A.1 Chart 2 Scale 1 constants
`c = 0.0379`, `Y = 0.69`, `Ks = -0.5`, slope `0.02`, and `q* = 13.893`. HY-8 instead
reports the result of its documented polynomial-based inlet method. The audit did not
independently reconstruct the executable's treatment at this high `HW/D`. It found no
issue to raise against `run-hy8`, but it does not prove HY-8's closed executable method
correct outside the scenarios and report fields exercised by the harness.

The 20-case matrix covers circular concrete, circular corrugated steel, and concrete
box barrels under low and high discharges and low, intermediate, and submerged
tailwaters, two cases at `q* = 3.75` inside the HDS-5 transition interval, and explicit
in-barrel `JS1`, inlet-reaching `S1`, long-barrel mixed M2/full-flow, and Type `6-FFc`
cases. HY-8
reports headwater to `0.01 m` and velocity to `0.01 m/s`, which limits the precision
of comparisons made through its reports.

| Case family | Cases | Maximum absolute HW difference | Maximum absolute velocity difference |
| --- | ---: | ---: | ---: |
| Circular concrete | 11 | `0.012 m` | `0.015 m/s` |
| Circular CSP, implemented paths | 3 | `0.007 m` | `0.003 m/s` |
| Circular CSP, unresolved Type 6 | 1 | `0.414 m` | `0.002 m/s` |
| Concrete box | 5 | `0.057 m` | `0.019 m/s` |

The per-culvert candidate fields make the source of those governing differences more
specific. Local outlet-control depth is within `0.008 m` of HY-8 in every case. The
largest inlet-control depth differences are the retained Type 6 CSP case (`0.414 m`)
and the box transition case (`0.057 m`), consistent with the documented differences
between direct HDS-5 equations and HY-8's fitted inlet curves.

All three fully submerged Type `4-FFf` cases agreed within `0.007 m` headwater and
`0.004 m/s` velocity. The local solver now routes the steep-slope `S2n` profile from
critical depth toward normal depth. Where tailwater exceeds normal depth, a
momentum-function solve determines whether it can sustain the conjugate depth of the S2
outlet section. The moderate-tailwater circular case cannot, so its jump is swept out and
S2 remains valid, matching HY-8's `1-S2n` classification. This reduced the maximum
circular-concrete velocity difference from `0.178 m/s` to `0.015 m/s`; the maximum box
difference remains `0.019 m/s`.

The new jump case locates the S2-to-S1 transition at station `25.584 m`; its headwater
and velocity differ from HY-8's `1-JS1t` outputs by `0.012 m` and `0.005 m/s`. The higher
tailwater case correctly routes S1 to the inlet and selects the free-surface outlet-control
candidate, agreeing with HY-8 `1-S1t` within `0.005 m` and `0.003 m/s`. Removing the old
full-flow-candidate shortcut also exposes the valid Type `7-M2c` profile: its headwater
difference fell from `0.089 m` to `0.004 m`.

For the long circular barrel, the M2 profile reaches the crown at station `68.483 m`
from the inlet. Treating the upstream reach as full and continuing with full-section friction gives
`12.015 m` headwater versus HY-8's `12.02 m`, while outlet velocity differs by
`0.003 m/s`. The result is explicitly classified `outlet_control_mixed` and retains
the full-flow length rather than presenting the entire barrel as free-surface flow.
HY-8's new diagnostic reports `69.48 m` full and `30.52 m` free, revealing a
`0.997 m` transition-location difference despite its outlet-control depth agreeing
within `0.005 m`. The HY-8 plot places the crown transition at station `69.4755 m`.
This is retained as a profile-detail discrepancy for independent validation, not used
to tune the local direct-step integration.

The shallow submerged-outlet path now routes the upstream free-surface reach to the
HGL-crown transition instead of stopping after reporting the downstream full segment.
For Q = `1.0 m³/s`, the solver reports `0.106 m` of downstream full flow and an upstream
S1 curve; headwater and velocity differ from HY-8 `1-S1f` by `0.002 m` and `0.005 m/s`.
For Q = `3.0 m³/s`, momentum matching locates a JS1 jump at station `17.528 m` before
`0.202 m` of downstream full flow. HY-8 independently reports `5-JS1f`; headwater and
velocity differ by `0.007 m` and `0.003 m/s`. Deeper submerged cases pass the HGL-at-inlet
check, retain `4-FFf`, and do not carry a mixed-profile warning.

The explicit Type `6-FFc` case is intentionally retained as a limitation rather than an
accepted match. The local result identifies `9.991 m` of the 10 m barrel as full and its
outlet velocity differs from HY-8 by `0.002 m/s`, but its HDS-5 inlet-control headwater is
`0.414 m` below HY-8. The local full-flow outlet-control candidate is lower again, so the
discrepancy is associated with the governing high-head inlet calculation, not the
full-section velocity. The result retains its short M2 outlet reach and no longer emits an
unresolved-profile warning merely because inlet control governs. Both harnesses select the
semantically equivalent circular-CSP
square-edge-with-headwall inlet. At `q* = 13.893`, the local solver uses direct HDS-5
Equation A.3 and now attaches `inlet_control_high_head_extension` because the resulting
`HW/D` exceeds 3. HY-8 reports its polynomial/general-orifice extension instead. The
precise closed-executable behavior has not been independently reconstructed, so the
`0.414 m` difference is an explained method difference rather than a calibration target.
It remains inappropriate to tune the published HDS-5 coefficients to this one HY-8 result.

HY-8 uses a fitted fifth-degree inlet curve for the compared shapes (User Manual
sections 5.2.1.1-5.2.1.2 and Appendix 11.3), whereas this project currently evaluates
the HDS-5/NBS equations directly. Their differences are recorded as method differences,
not automatically treated as defects. The initial harness also revealed and fixed a
test-configuration error: its fixed road crest intersected the arbitrary box-culvert
datum and allowed roadway flow. The harness now places the crest above each case.

At `q* = 3.75`, the tangent bridge differs from HY-8 by `0.0003 m` for the circular
concrete case and `0.057 m` for the concrete box. This supports the expected distinction
between the HDS-5 branch/tangent implementation and HY-8's fitted shape-specific curves;
it is not evidence that one universal correction should be applied.

Run the comparison from the repository root with `run-hy8 2026.9.8.1` installed:

```powershell
$env:PYTHONPATH = 'E:\Github\ryan-culverts\src'
python scripts/compare_hy8.py `
  --workspace validation_artifacts/hy8-matrix `
  --output docs/validation_data/hy8_8_0_1_2_matrix.csv
```

HY-8 project/report artifacts are intentionally ignored because they are regenerable
and include machine-specific execution output. The explicit output option writes UTF-8
independently of the invoking shell's redirection rules. This matrix is diagnostic
evidence, not an acceptance tolerance or engineering
validation. The retained CSV includes profile codes, jump stations, stable local warning
codes, HY-8 inlet/outlet candidate depths and qualifiers, and HY-8 full/free barrel
lengths. CS-003 has classified the Type 6 headwater discrepancy as a warned high-head
method difference. CS-004 must still add independent primary-source fixtures and settle
the remaining mixed-profile details.

Further HEC-RAS, SWMM and STREAM-1D comparisons remain deferred. Pin versions, inputs,
units, coefficient mappings, method options and output precision. Agreement does not
override primary equations. No external acceptance is claimed.

Historical cases under `docs/legacy/` are scenario ideas, not new golden values.

[hy8-insider-15]: https://www.linkedin.com/pulse/hy-8-insider-article-15-culvert-barrel-results-eric-jones-p-e-/
