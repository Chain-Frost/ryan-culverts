# HY-8 capability and verification matrix

This is a scope tracker, not a promise to reproduce HY-8 outputs. The official
[FHWA HY-8 page][hy8] lists 8.0.1.2, build date 2025-03-05, at this review.
The installed executable and its full technical manual have not been audited.

| Capability | HY-8 reference | New solver | Method / tests | External verification |
| --- | --- | --- | --- | --- |
| Numerical roots and SI conversion | Implementation detail | Foundation available | Analytical/contract tests | Not applicable |
| Circular/box culverts | HDS-5 and HY-8 scope | Implemented | Analytical geometry tests | Deferred |
| Inlet control | HDS-5 methods | Provisional | Equations/Table A.1 checked; transition policy open | Deferred |
| Full and partly full outlet control | HDS-5/HY-8 | Provisional | Energy tests; profile validation incomplete | Deferred |
| Critical/normal depth and velocity | HY-8 release notes | Implemented | Analytical and branch tests | Deferred |
| Multiple barrels and mixed groups | Confirm full versioned manual scope | Implemented | Conservation tests; broader cases pending | Deferred |
| Profiles and hydraulic jumps | Confirm detailed versioned options | Partial | M/H/S framework; jumps and mixed-flow transitions absent | Deferred |
| Rating curves | Performance tables | Implemented | Scalar equivalence and repeatability tests | Deferred |
| Roadway overtopping | HY-8 release notes | Excluded initially | No implementation | Outside initial scope |
| Embedded/broken-back culverts | HY-8 release notes | Deferred | No implementation | Outside initial scope |

The initial matrix deliberately marks unreviewed details. Expand it from the
versioned technical manual before defining the external test matrix.

[hy8]: https://www.fhwa.dot.gov/engineering/hydraulics/software/hy8/
