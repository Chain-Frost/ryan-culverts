# HY-8 capability and verification matrix

This is a scope tracker, not a promise to reproduce HY-8 outputs. The official
[FHWA HY-8 page][hy8] lists 8.0.1.2, build date 2025-03-05, at this review.
The installed executable version and file hash, local `ShapeDB.dat`, and applicable
v8.0 manual method sections have been audited. The manual is not represented as
patch-specific 8.0.1.2 documentation; see [references](references.md) and
[validation](validation.md) for the separate pins and observed behaviour.

## `run-hy8/src` transfer review

The `run-hy8` source tree was reviewed on 2026-09-10 as an integration capability
inventory. It is evidence of useful workflows, not hydraulic authority.

| `run-hy8` capability | Decision here |
| --- | --- |
| Flow to headwater | Already provided by the barrel, group, and crossing solvers |
| Headwater to flow | Added publicly for barrels, groups, and complete culvert/roadway crossings in CS-034 |
| Flow for HW/D | Added for a single barrel; mixed-crossing HW/D is deliberately omitted because there is no unique invert or rise |
| Tailwater rating/channel definitions | Relevant missing boundary work, separated as CS-029 |
| Irregular roadway profile | Relevant extension already owned by CS-028 |
| Additional culvert shapes/materials | Relevant only with sourced equations and geometry tests; owned by CS-025 |
| Top/bottom or composite roughness | Relevant only with physical zones and applicability; split into CS-030 and CS-033 |
| Project dictionaries/JSON | Keep deferred under CS-009 until a real consumer fixes the schema contract |
| Flow sequences and performance tables | Existing rating-curve APIs cover the hydraulic need; HY-8's min/design/max presentation convention is not core physics |
| Project file reader/writer, executable discovery/execution, `.rst`/`.rsql` parsing | Remain in `run-hy8`; duplicating HY-8 orchestration would violate this repository's independent-core boundary |
| Pandas dataframe adapter and US-unit convenience | Presentation/integration concerns, not missing hydraulic capability in the SI-only core |

| Capability | HY-8 reference | New solver | Method / tests | External verification |
| --- | --- | --- | --- | --- |
| Numerical roots and SI conversion | Implementation detail | Foundation available | Analytical/contract tests | Not applicable |
| Circular/box culverts | HDS-5 and HY-8 scope | Implemented | Analytical geometry tests | Single-barrel matrix covers circular concrete/CSP and concrete box |
| Inlet control | HDS-5 methods | Implemented, provisional | Equations/Table A.1 and transition tests | HY-8 matrix and Type 6 sweep; high-head method difference retained |
| Full and partly full outlet control | HDS-5/HY-8 | Implemented, provisional | Energy and independent fixture tests | HY-8 candidate depth within `0.012 m` in matrix and sweeps |
| Critical/normal depth and velocity | HY-8 release notes | Implemented | Analytical and branch tests | Exercised through version-pinned regime comparisons |
| Multiple barrels and mixed groups | Confirm full versioned manual scope | Implemented | Conservation and inverse round-trip tests; broader cases pending | Deferred |
| Profiles and hydraulic jumps | HY-8 profile codes and plots | Supported prismatic families implemented | Independent M/H/S, jump, and mixed-flow fixtures | S2, S1, JS1, S1f, JS1f, and M2/full cases compared |
| Rating curves | Performance tables | Implemented | Scalar equivalence and repeatability tests | Deferred |
| Roadway overtopping | HDS-5 Equation 3.9 | Constant crest and free overflow implemented | Analytical, inactive, roadway-only, and combined-flow tests | Irregular/submerged cases deferred to CS-028 |
| Embedded/broken-back culverts | HY-8 release notes | Deferred | No implementation | Outside initial scope |

The executable evidence is diagnostic rather than an acceptance tolerance. See
[validation](validation.md) for version pins, discrepancy dispositions, and remaining
scope limits.

[hy8]: https://www.fhwa.dot.gov/engineering/hydraulics/software/hy8/
