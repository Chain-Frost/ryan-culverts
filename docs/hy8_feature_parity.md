# HY-8 capability and verification matrix

This is a scope tracker, not a promise to reproduce HY-8 outputs. The official
[FHWA HY-8 page][hy8] lists 8.0.1.2, build date 2025-03-05, at this review.
The installed executable version and file hash, local `ShapeDB.dat`, and applicable
v8.0 manual method sections have been audited. The manual is not represented as
patch-specific 8.0.1.2 documentation; see [references](references.md) and
[validation](validation.md) for the separate pins and observed behaviour.

| Capability | HY-8 reference | New solver | Method / tests | External verification |
| --- | --- | --- | --- | --- |
| Numerical roots and SI conversion | Implementation detail | Foundation available | Analytical/contract tests | Not applicable |
| Circular/box culverts | HDS-5 and HY-8 scope | Implemented | Analytical geometry tests | Single-barrel matrix covers circular concrete/CSP and concrete box |
| Inlet control | HDS-5 methods | Implemented, provisional | Equations/Table A.1 and transition tests | HY-8 matrix and Type 6 sweep; high-head method difference retained |
| Full and partly full outlet control | HDS-5/HY-8 | Implemented, provisional | Energy and independent fixture tests | HY-8 candidate depth within `0.012 m` in matrix and sweeps |
| Critical/normal depth and velocity | HY-8 release notes | Implemented | Analytical and branch tests | Exercised through version-pinned regime comparisons |
| Multiple barrels and mixed groups | Confirm full versioned manual scope | Implemented | Conservation tests; broader cases pending | Deferred |
| Profiles and hydraulic jumps | HY-8 profile codes and plots | Supported prismatic families implemented | Independent M/H/S, jump, and mixed-flow fixtures | S2, S1, JS1, S1f, JS1f, and M2/full cases compared |
| Rating curves | Performance tables | Implemented | Scalar equivalence and repeatability tests | Deferred |
| Roadway overtopping | HY-8 release notes | Excluded initially | No implementation | Outside initial scope |
| Embedded/broken-back culverts | HY-8 release notes | Deferred | No implementation | Outside initial scope |

The executable evidence is diagnostic rather than an acceptance tolerance. See
[validation](validation.md) for version pins, discrepancy dispositions, and remaining
scope limits.

[hy8]: https://www.fhwa.dot.gov/engineering/hydraulics/software/hy8/
