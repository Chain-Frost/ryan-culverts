# PR #29 - independent hydraulic review and HY-8 comparison

**Review date:** 2026-10-18  
**Pull request:** [#29 - Add source-backed elliptical culvert support](https://github.com/Chain-Frost/ryan-culverts/pull/29)  
**Issue / work item:** [#3](https://github.com/Chain-Frost/ryan-culverts/issues/3) / CS-025  
**Scope of this review:** source-backed geometry, empirical applicability, and
the retained HY-8 8.0.1.2 comparisons.  
**Review disposition:** **Review round complete for the present scope.**
No further executable cases or changes to hydraulic coefficients are requested
by this review. This is **not** a declaration of numerical equivalence to HY-8,
construction-grade hydraulic certification, or a release/merge authorisation.

## Executive assessment

The PR provides a reasonable, source-backed implementation of horizontal and
vertical mathematical ellipses, together with a separate HY-8/ShapeDB four-arc
concrete-oval profile. It preserves the distinction between **geometry
reconciliation**, **equation/method fidelity**, and **independent engineering
validation**.

The two reconstructed catalogue sections used in executable testing agree with
their ShapeDB full areas within the existing 0.5% reconciliation gate. Critical
depths and S2 outlet profiles agree closely with HY-8 for most tested flows.
Headwater results also agree reasonably in practical absolute terms but **are
not identical**: the core and HY-8 do not implement precisely the same
inlet-control equations. This review does not recommend changing the native
HDS-5 method to reproduce an external fitted result.

The notable exception is the **128 x 82 inch, 34-36 m3/s** high-flow region.
HY-8's plotted critical-depth series changes discontinuously near the crown,
while the local solver's critical root rises smoothly. This review cannot
establish whether HY-8's behaviour reflects its internal section lookup,
near-crown treatment, profile algorithm, or a version-specific defect. The
finding is **unresolved as to cause**, but its evidence and applicability
limits are sufficiently recorded for this review round.

## 1. Methods and scope

| Aspect | Reviewed implementation and boundary |
| --- | --- |
| Mathematical ellipses | Exact analytical area/top width; elliptical arc perimeter integration |
| Concrete standard oval | Separate ShapeDB-pinned, tangent four-circular-arc profile, not an exact ellipse |
| Section catalogue | Explicit size lookup and fail-closed source-area/span checks |
| Inlet control | Direct HDS-5 Appendix A equations and project-specific smooth transition |
| HY-8 inlet comparison | HY-8 8.0.1.2 uses fitted/polynomial and low-headwater treatments; not guaranteed identical |
| Outlet-profile calculation | Local S2 direct-step integration; HY-8's internal profile method is not fully documented here |
| Empirical material applicability | Built-in concrete ellipse coefficients are restricted to concrete pipe materials |
| Not covered | Other oval families, arches/pipe-arches, general material parity, all inlet arrangements and all boundary conditions |

The **two executable sizes** are 83 x 53 inch and 128 x 82 inch
*horizontal concrete* standard ovals. The HY-8 comparison does not independently
validate arbitrary mathematical ellipses or vertical ellipses.

The 83 x 53 section's reconstructed full-area difference from ShapeDB is
approximately **-0.0037%**; the 128 x 82 section is **-0.1858%**.
Those are section **reconciliation** differences, not flow-result errors and
not permissible adjustment factors.

## 2. What the executable comparisons establish

All native tests used **HY-8 8.0.1.2**, Python 3.14.6 and
`run-hy8==2026.10.18.2`. The evidence folders contain native
`.hy8`, `.rst`, `.rsql` and `.plt` outputs and a manifest with
executable and input provenance.

- **Six baseline cases:** 0.5, 1 and 2 m3/s for both sizes. The retained
  native profile's critical depths agree with the local solver within
  approximately **0.04-0.15 mm**, and most outlet-depth differences
  are below 1 mm. The baseline is preserved unchanged.
- **18-case sweep:** the six originals plus 12 higher discharges. All have
  matching positive requested culvert flow and zero reported roadway flow;
  both methods report inlet-controlled, free-surface S2 cases.
- **Additional targeted sweep:** 28, 30, 32, 34 and 36 m3/s for
  the 128 x 82 section, with original 25 and 35 m3/s as anchors.
  This isolates the high-flow critical-depth anomaly without modifying
  the original matrices.

In the **18-case sweep**, 17 of 18 outlet-velocity differences are
below **1%** in absolute magnitude. For the **12 added-flow cases**, the
largest absolute headwater-depth percentage difference is approximately
**1.79%**, with headwater measured above the inlet invert.
The biggest percentage headwater discrepancy of the entire sweep is
**-6.66% at just 0.5 m3/s** through the larger culvert, where the
absolute difference is approximately **-22.6 mm** at shallow headwater.
Percentages should therefore be evaluated alongside absolute differences.

These comparisons are **diagnostic**, not an engineering accuracy tolerance.
Under the existing report-rounding-only limits (0.0051 m for headwater,
0.0051 m/s for outlet velocity), only **2 of the 18** cases pass both
checks. Thus the evidence **does not establish exact HY-8 equivalence**
despite the generally small engineering-scale residuals.

### 2.1 High-flow critical-depth and outlet-depth comparison

The following values are water depths in metres above the local barrel
invert. Asterisks indicate previously retained anchors; the other cases
are fresh runs. HY-8 depths are taken from the requested-flow **`.plt`**
series rather than two-decimal **`.rst`** summaries.

| Q (m3/s) | Local critical (m) | HY-8 critical (m) | Local outlet (m) | HY-8 outlet (m) |
| ---: | ---: | ---: | ---: | ---: |
| 25* | 1.863753 | 1.863500 | 1.463206 | 1.463300 |
| 28 | 1.924439 | 1.924300 | 1.559676 | 1.559700 |
| 30 | 1.955666 | 1.955500 | 1.618147 | 1.618200 |
| 32 | 1.980623 | 1.980500 | 1.672159 | 1.672200 |
| 34 | 2.000378 | 1.892800 | 1.722065 | 1.704800 |
| 35* | 2.008627 | 1.814000 | 1.745635 | 1.689800 |
| 36 | 2.015948 | 2.077600 | 1.768388 | 1.769300 |

**Interpretation:**

1. At **25-32 m3/s**, the critical and outlet depths show close agreement.
2. At **34-35 m3/s**, the HY-8 critical depth unexpectedly drops while
   the local root increases. HY-8 critical-depth candidates evaluated with
   the local four-arc geometry have **Fr squared ~1.668 and 2.284**,
   instead of the expected value near 1. At **36 m3/s**, its
   critical depth jumps to 2.0776 m and local **Fr squared ~0.272**.
   Decimal rounding is insufficient to explain these departures.
3. A 19,999-depth scan identified only one sign-changing local
   critical-depth bracket per tested flow. This does not prove
   HY-8 uses the same geometry or establish a HY-8 bug; it provides
   no supporting evidence for a second *local* critical root.
4. The **35 m3/s outlet depth** differs by approximately **55.8 mm**.
   The resulting velocities are **7.160 m/s local** versus
   **7.38 m/s HY-8** (about **-2.98%**). At the HY-8 outlet depth,
   applying the existing local four-arc area `A(y)` gives
   `Q/A(y) ~7.382 m/s`, matching HY-8. This points toward a
   **profile/outlet-depth divergence**, not a reason to change
   section-area calculations.
5. Increasing local S2 direct-step discretisation from 25 to
   3,200 steps changes the 35 m3/s outlet prediction by
   approximately **0.026 mm**. Simple step size is an unlikely
   explanation for the approximately 56 mm difference.
6. At **36 m3/s**, outlet-depth and velocity agreement largely
   return despite the anomalous HY-8 critical-depth ordinate.
   Therefore the disagreement is not monotonic and cannot be
   attributed conclusively to one undocumented HY-8 algorithm.

The cause of the abrupt HY-8 near-crown profile behaviour remains
**unverified**. It is not evidence that a hydraulic coefficient should be
tuned or that the local critical-flow equation is wrong.

### 2.2 Distinct inlet-control methods

The native inlet-control implementation evaluates HDS-5 Appendix A
regression forms, including critical specific energy for the relevant
unsubmerged form, and uses a defined transition between unsubmerged
and submerged branches. HY-8 applies fitted low-headwater relationships
and a fifth-degree polynomial over an intermediate range, as
described in HDS-5 Section 3.5.2 and the historical HY-8 guidance.

As a diagnostic, the published HY-8 concrete ellipse square-edge
polynomial predicts approximately **10.80569 m** at
**83 x 53 inch / Q = 2 m3/s**, versus HY-8's native
`.plt` value **10.8058 m**, a **0.11 mm** difference.
The local direct-HDS-5 prediction is **10.81727 m**. This
supports a **method difference**, not necessarily a computational
defect in the native solver. Historical polynomial constants have
not been verified as an implementation contract for every branch
of executable version 8.0.1.2.

## 3. Fixed code-review findings

The six GitHub review threads are **resolved** at the reviewed head.
The last material-applicability issue is addressed by explicit
`concrete_pipe_only` metadata on the built-in horizontal and
vertical concrete ellipse inlet and entrance-loss records, enforced
by both resolvers and the direct inlet API. This rejects their use
with corrugated steel or other incompatible material records,
including zero-flow calls, while retaining valid concrete uses.
Regression cases cover mathematical horizontal and vertical ellipses
and a ShapeDB four-arc oval.

The source catalogue's row index is read-only, preventing modification
of the recorded source identity without recomputing geometry.
The coefficient/material controls were added **without changing**
hydraulic equations or HY-8 baseline results.

## 4. Applicability boundaries and residual risks

- **High headwater:** HDS-5 inlet-control laboratory relationships
  are described over approximately **0.5 <= HW/D <= 3**.
  The existing `inlet_control_high_head_extension` warning applies
  above 3, including the 83 x 53 / 12 m3/s case and the
  128 x 82 / 34-36 m3/s cases. Agreement outside this range
  cannot, by itself, establish engineering validity.
- **Very low headwater:** differences in HY-8's fitted
  low-headwater treatment versus the direct HDS-5 implementation
  remain a plausible, uneliminated source of small residuals.
- **Restricted source catalogue:** only profiles passing the
  established size/area reconciliation rules can be selected;
  the remaining catalogue entries are intentionally rejected.
- **Solver scope:** demonstration of this implementation slice
  does not certify other materials, all boundary conditions,
  other culvert configurations, bridge hydraulics, road
  overtopping or full independent construction design suitability.
- **Hydraulic acceptance:** passing regression checks, fitting
  a HY-8 output or resolving code-review comments does not
  replace engineering judgement, source applicability review,
  independent worked-example verification or project-specific
  checking.

## 5. Review disposition and handoff

**This review round is complete.** The source-backed calculation
strategy and code-review corrections are acceptable for further
development within their **explicitly bounded scope**. The
retained evidence gives a transparent explanation for many
residuals and documents where the explanation is incomplete.

**No additional HY-8 cases, coefficient tuning, tolerance widening,
or algorithm changes are requested at this stage.** Treat the
34-36 m3/s near-crown anomaly as a **documented limitation** of
HY-8-to-local result comparison; retain it for a later source or
independent-method review if the relevant high-head regime is
required for an actual design. This is not a finding that HY-8
is definitively incorrect.

The maintainer can close this **review activity** based on the
recorded findings. A merge, release or decision to use the
method for a particular engineering design remains a **separate
explicit decision**, made with the above applicability and
validation limits visible. This file does not authorise release,
certify full hydraulic equivalence, or close the broader issue #3.

**Code verification available at review:** [GitHub CI #234](https://github.com/Chain-Frost/ryan-culverts/actions/runs/39137630446)
passed all four jobs, including **658 tests**, Ruff and
Pyright checks, and installed-wheel checks on Windows, Ubuntu
and macOS, at commit `12fbb891ea0b33e98bbf9d52032009492b1526ac`.
This is the **pre-documentation-commit** verification;
the Markdown addition itself has not been revalidated
until its own commit's CI completes.

## Evidence and primary reference links

- [Original six-case comparison](../validation_data/hy8_8_0_1_2_ellipse_comparison.csv)
  and [native six-case evidence manifest](../validation_data/hy8_8_0_1_2_ellipse/manifest.json).
- [18-case sweep CSV](../validation_data/hy8_8_0_1_2_ellipse_sweep/comparison.csv)
  and [manifest](../validation_data/hy8_8_0_1_2_ellipse_sweep/manifest.json).
- [Targeted seven-row critical/profile diagnostics](../validation_data/hy8_8_0_1_2_ellipse_critical/diagnostics.csv),
  [curve series](../validation_data/hy8_8_0_1_2_ellipse_critical/curves.json),
  [manifest](../validation_data/hy8_8_0_1_2_ellipse_critical/manifest.json).
- [Detailed development and diagnostic record](2026-10-07-cs-025-elliptical-culverts.md).
- [High-flow HY-8 agent's evidence and interpretation](https://github.com/Chain-Frost/ryan-culverts/pull/29#issuecomment-6251255222).
- [FHWA HDS-5, Third Edition](https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf),
  particularly Section 3.5.2 and Appendices A and C.
- [Historical HY-8 polynomial documentation](https://manualzz.com/doc/6566290/hy-8-v7.3-culvert-analysis-program-user-manual),
  used as **diagnostic context**, not confirmation of
  HY-8 8.0.1.2 internal source code.
