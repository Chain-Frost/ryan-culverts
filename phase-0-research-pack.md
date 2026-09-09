# Deep Research Report: Culvert Hydraulic Methods, Regime Logic, Defaults, and Validation

**Repository reviewed:** `Chain-Frost/ryan-culverts`\
**Repository baseline:** commit
`2c431e6a205fd7127ec940226aa4ee17599a9999` (`main`, 6 September 2026)\
**Research date:** 6 September 2026\
**Scope:** research and planning only; no source-code modifications,
commits, staging, or publication.

## 1. Executive summary

The repository is in a materially better state than its earlier
phase-completion labels implied: the geometry, critical/normal-depth,
source metadata, typed domain models, and multi-group crossing
architecture are generally sound foundations. The main remaining risk is
concentrated in **regime classification and mixed-flow hydraulics**, not
in basic geometry or numerical root finding.

The highest-priority findings are:

1.  **The current inlet-control transition is not HDS-5 compliant.**
    HDS-5 states that the transition between unsubmerged and submerged
    inlet-control curves is an empirically drawn **smooth curve tangent
    to both branches**. The current implementation linearly interpolates
    `HWi/D` between `q* = 3.5` and `q* = 4.0`. Those values are HDS-5
    applicability limits for the two equations, not a prescription for
    linear interpolation. A deterministic cubic-Hermite tangent bridge
    is the best research-grounded replacement if the project wants to
    retain the explicit HDS-5 equations. Exact HY-8 parity is a separate
    problem because HY-8 uses fitted inlet-control curves/polynomials
    for standard shapes rather than simply evaluating the Appendix A
    branches with a linear bridge.

2.  **`tailwater_depth >= rise` must not unconditionally force the
    entire barrel to full flow.** HDS-5/HY-8 profile logic explicitly
    allows inlet-controlled Type 1/5 cases in which tailwater above the
    crown causes full flow only at the downstream end, with an S1
    profile and possibly a hydraulic jump to full flow. Whether the
    whole barrel is pressurised depends on the controlling regime and
    profile development, not tailwater depth alone.

3.  **The current full-flow candidate shortcut is not defensible as a
    general regime selector.** `determine_governing_regime()` compares
    inlet headwater to a full-flow outlet-control headwater before
    establishing whether the full-flow state is physically admissible.
    The correct sequence is: classify feasible profile families from
    slope, critical/normal depth and downstream boundary; solve the
    applicable free-surface/full/mixed outlet-control state; then
    compare the valid inlet- and outlet-control headwater requirements.

4.  **Hydraulic jumps are a required core capability, not an optional
    refinement.** HDS-5 documents S1/S2 matching and hydraulic-jump
    outcomes for inlet-controlled Type 1/5 flows. HY-8 changed its jump
    logic in version 7.3 to use momentum calculations. The repository
    already acknowledges that jumps are not solved. A
    momentum-function/conjugate-depth solver should be added before the
    regime layer is considered complete.

5.  **Direct step is appropriate for the current prismatic-barrel scope,
    but it should not own regime classification.** Keep direct step as
    the initial free-surface GVF engine for straight, prismatic
    culverts. Move pressurisation, hydraulic jumps and flow-type
    decisions into separate state/profile logic. Preserve an interface
    that allows a standard-step implementation later for non-prismatic,
    embedded, spatially varying roughness, or more general conduit
    geometry.

6.  **MRWA hydraulic roughness data and MRWA construction compliance
    must be represented separately.** The current typed MRWA CSP Manning
    table correctly reproduces hydraulic values from the design
    procedure, but current Specification 404 (issued 17 July 2026)
    limits spirally wound CSP to different diameter/corrugation
    combinations. For example, current Spec 404 specifies 68 x 13 mm
    corrugations through 1500 mm diameter and 125 x 25 mm from 1650 to
    2100 mm; the hydraulic table contains additional combinations such
    as 75 x 25 mm. Those values may remain useful as hydraulic reference
    data, but must not be presented as current MRWA
    construction-compliant defaults.

7.  **Australian defaults should fail closed where the source requires
    project/manufacturer data.** MRWA directs designers to manufacturer
    information for plastic pipe roughness; current Spec 404 permits
    plastic flexible culverts only as a contract-specific provision and
    limits them to PE. A generic HDS-5 thermoplastic `n` range can
    remain as reference metadata, but it should not silently become an
    MRWA design default.

8.  **The current crossing architecture is fundamentally correct.**
    Solving a common upstream headwater such that the sum of group
    discharges equals the crossing discharge is the right architecture
    for groups with different sizes, inverts and roughnesses. Keep it.
    The important caveat is that identical-barrel multiplication is a
    superposition assumption; NCHRP 734 specifically investigated
    multi-barrel interaction because inlet contraction can change when
    barrels are adjacent.

9.  **External verification should remain late in the implementation
    sequence.** First correct the source-derived equations, regime state
    machine, jumps and mixed full/free-surface profiles; then validate
    internally against analytical and published cases; only then compare
    against pinned HY-8, HEC-RAS, SWMM and STREAM-1D cases.

The research is sufficient to define the remediation architecture and
validation plan. It is **not yet sufficient to declare the solver
engineering-validated** because the full HY-8 8.0.1.2 technical manual,
full Austroads AGRD05B-23 text, detailed corrected FHWA-HRT-06-138
coefficient-table applicability, and all NCHRP 734 coefficient tables
were not completely extracted in this session.

------------------------------------------------------------------------

## 2. Repository state reviewed

The repository was reviewed at commit:

`2c431e6a205fd7127ec940226aa4ee17599a9999`

Key current files inspected:

-   `culvert_solver_updated_work_plan.md`
-   `docs/work/README.md`
-   `docs/work/2026-09-06-phase-0-to-10-remediation.md`
-   `docs/references.md`
-   `docs/computational_basis.md`
-   `docs/validation.md`
-   `docs/hy8_feature_parity.md`
-   `docs/architecture.md`
-   `docs/progress.md`
-   `src/culvert_solver/inlet_control/fhwa.py`
-   `src/culvert_solver/inlet_control/coefficients.py`
-   `src/culvert_solver/outlet_control/full_flow.py`
-   `src/culvert_solver/outlet_control/partial_flow.py`
-   `src/culvert_solver/profiles/direct_step.py`
-   `src/culvert_solver/solver/regime.py`
-   `src/culvert_solver/solver/crossing.py`
-   `src/culvert_solver/models/materials.py`

Current repository strengths:

-   explicit SI computational core;
-   geometry separated from hydraulics;
-   critical and normal depth solved numerically/analytically rather
    than approximated;
-   typed inlet coefficient metadata and shape applicability;
-   explicit absolute tailwater elevation;
-   multi-group crossing solution based on a common upstream headwater;
-   source metadata is embedded in the domain objects;
-   provisional methods are now documented as provisional rather than
    "verified."

Current hydraulic weaknesses:

-   linear inlet transition;
-   no hydraulic-jump solver;
-   no physically complete mixed free-surface/pressurised profile
    solver;
-   tailwater-at-crown shortcut to full flow;
-   full-flow candidate used before physical applicability is
    established;
-   direct-step profile routine contains state-classification decisions
    that belong above the profile integrator;
-   high-level solver still has geometry-based entrance-loss defaults
    that are convenient but not site-specific;
-   external validation remains incomplete.

------------------------------------------------------------------------

## 3. Primary-source findings

### 3.1 FHWA HDS-5, third edition, FHWA-HIF-12-026 (2012)

**Primary authority for the current conventional culvert solver.**

Official source:\
https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf

Relevant locations:

-   Chapter 3, conventional culvert hydraulics and outlet control:
    printed pp. 3.1-3.18.
-   Section 3.5.1, USGS flow types and water-surface profiles: printed
    pp. 3.36-3.39.
-   Appendix A, inlet-control equations: printed pp. A.1-A.6.
-   Table A.1, inlet-control constants.
-   Appendix B/Table B.1, Manning roughness.
-   Table C.2, entrance-loss coefficients.

#### 3.1.1 Inlet-control equations

HDS-5 retains:

-   unsubmerged Form 1, based on critical specific head;
-   unsubmerged Form 2, weir-like;
-   submerged/orifice form.

In SI, the dimensionless discharge parameter includes `Ku = 1.811`.

HDS-5 states:

-   unsubmerged equations apply up to about `Q/(A*sqrt(D)) = 1.93` in
    SI, equivalent to `q* = Ku Q/(A sqrt(D)) ≈ 3.5`;
-   submerged equation applies above about `2.21` in SI, equivalent to
    `q* ≈ 4.0`.

Those are **branch applicability limits**, not a specified interpolation
rule.

#### 3.1.2 Transition treatment

HDS-5 is explicit that the transition zone is defined empirically by
drawing a curve **between and tangent to** the unsubmerged and submerged
curves. It also notes that the historical nomograph transition was drawn
smoothly by hand.

Therefore:

-   current linear interpolation in `inlet_control/fhwa.py` is not
    source-faithful;
-   simply retaining the endpoints 3.5 and 4.0 and changing
    interpolation to a smooth tangent construction is a defensible
    deterministic implementation;
-   exact historical nomograph/HY-8 equivalence is not guaranteed by any
    newly invented analytic bridge.

**Recommended implementation:** cubic Hermite interpolation over
`[3.5, 4.0]`, using the value and first derivative of the unsubmerged
branch at 3.5 and the value and first derivative of the submerged branch
at 4.0. This gives a unique C1 curve tangent to both branches at the
adopted HDS-5 applicability limits.

For Form 1, the derivative must include the derivative of `Hc/D` with
respect to `q*`; this should be evaluated from the same critical-depth
solver rather than approximated by ignoring the critical-head term.

Acceptance checks for the new transition:

-   exact value continuity at both endpoints;
-   exact derivative continuity at both endpoints;
-   monotonic `HWi/D` through the transition for all supported
    coefficient sets;
-   no local overshoot below either physically relevant branch envelope;
-   numerical stability for very small and very large culverts;
-   comparison against HDS-5 nomograph/HY-8 results for representative
    inlet configurations.

#### 3.1.3 HDS-5/HY-8 profile logic

HDS-5 Section 3.5.1 documents the profile families used by HY-8:

-   Type 1/5 inlet control: S1/S2 profiles, with hydraulic-jump checks;
-   Type 2 outlet control: M2 from critical depth at the outlet;
-   Type 3 outlet control: M1 from tailwater;
-   Type 4/6: full flow for most/all of the barrel depending on the
    case, with an M2 profile used to determine the full-flow length in
    the mixed case;
-   Type 7: partially pressurised/full for part of the barrel, with
    M1/M2 logic;
-   horizontal cases include H2/H3 profiles.

Most importantly, HDS-5 states that for Type 1/5, when tailwater is
above the crown, the barrel may be full **at the downstream end**, and
an S1 profile or hydraulic jump to full flow is evaluated. This directly
disproves the general rule:

`tailwater_depth >= rise -> entire barrel full`.

The current shortcut is only valid after the flow type/profile state has
been established as a fully pressurised outlet-control case.

------------------------------------------------------------------------

### 3.2 Bodhaine, USGS TWRI Book 3, Chapter A3 (1968)

Official landing page:\
https://pubs.usgs.gov/twri/twri3-a3/html/pdf.html

The official report sections were accessed for the general
classification and computational discussion. The worked-example section
could not be fully retrieved in this session.

Bodhaine classifies six flow types using control location and relative
headwater/tailwater elevations.

Key findings:

-   Types 1, 2 and 3 occur in the low-head regime when outlet
    submergence is not complete.
-   Type 1: critical control near the inlet, steep barrel, partly full.
-   Type 2: critical depth at the outlet, mild barrel, partly full.
-   Type 3: backwater-controlled, tranquil/subcritical flow; it can
    occur on **any** bottom slope.
-   Type 4: both ends submerged; barrel full.
-   Type 5: high head, inlet submerged, rapid contracted flow, barrel
    partly full.
-   Type 6: high head, free outfall, barrel full under pressure.

Bodhaine also warns that the simple classification has exceptions. In
the "unusual conditions" discussion, Type 3 can occur on a steep slope,
and the fact that both headwater and tailwater exceed nominal thresholds
does not automatically prove Type 4. This supports a profile/state
approach rather than threshold-only logic.

**Implication for the repository:** use Bodhaine's six types as the
physical foundation, but use HDS-5/HY-8's extended profile codes (S1,
S2, M1, M2, H2/H3, jump/full suffixes) for implementation diagnostics.

------------------------------------------------------------------------

### 3.3 FHWA-HRT-06-138: Effects of Inlet Geometry on Hydraulic Performance of Box Culverts

Official corrected PDF:\
https://highways.dot.gov/sites/fhwa.dot.gov/files/FHWA-HRT-06-138.pdf

The electronic report contains an errata notice. It states that the
following tables were replaced after initial publication:

-   Table 1;
-   Table 2;
-   Table 3;
-   Table 4;
-   Tables 7-12;
-   Tables 17-18.

The report's purpose is to provide experimental results and recommended
coefficients for box-inlet configurations, including configurations not
specifically covered by HDS-5.

**Current repository implication:**

-   the current code primarily uses HDS-5 2012 Table A.1 constants, not
    a direct transcription of the 2006 report tables;
-   therefore there is no basis to replace the current HDS-5 constants
    wholesale with 2006 values;
-   when adding or auditing box configurations that originate from
    FHWA-HRT-06-138, use only the corrected electronic tables and
    explicitly map each coefficient set to its tested geometry;
-   do not infer that a coefficient for one span-to-rise ratio, bevel,
    fillet, skew, or multi-barrel configuration applies universally.

**Open item:** a row-by-row applicability map from corrected Tables 1-18
into the project's inlet configuration catalogue is still required
before adding those configurations.

------------------------------------------------------------------------

### 3.4 NCHRP Report 734: Hydraulic Loss Coefficients for Culverts (2012)

Official publication page:\
https://www.nationalacademies.org/publications/22673

DOI:\
https://doi.org/10.17226/22673

The report addresses conventional and environmentally sensitive culverts
and specifically examines:

-   entrance loss;
-   exit loss;
-   buried-invert/embedded culverts;
-   slip-lined culverts;
-   multi-barrel effects;
-   composite roughness.

The report confirms the conventional outlet-control energy framework:

`available energy = entrance loss + barrel friction + exit loss + other minor losses`.

It also explicitly identifies the limitation of assuming that a
multi-barrel installation is simply the single-barrel result multiplied
by the number of barrels: inlet contraction changes when adjacent
barrels are present, so capacity/loss behaviour can change.

**Recommended use in this project:**

-   use NCHRP 734 to refine entrance/exit-loss handling where the tested
    geometry matches;
-   use its multi-barrel findings to document the limits of simple
    superposition;
-   use its composite-roughness work if embedded/natural-bottom culverts
    are later added;
-   do not adopt coefficients until the exact chapter/table, test
    geometry and applicability have been extracted into source metadata.

**Open item:** detailed coefficient-table extraction was not completed
in this session.

------------------------------------------------------------------------

## 4. Corrected hydraulic regime logic

### 4.1 Core principle

The solver should not determine regime from a single threshold. It
should determine a **physically admissible state** from:

-   inlet submergence/headwater;
-   outlet tailwater;
-   critical depth `yc`;
-   normal depth `yn`;
-   barrel slope relative to critical slope;
-   whether the profile reaches the crown;
-   whether a hydraulic jump occurs;
-   whether a pressurised reach exists;
-   inlet-control versus outlet-control required headwater.

The governing headwater is still the larger of valid inlet- and
outlet-control requirements, but only after each candidate has been
solved using a physically admissible profile.

### 4.2 Proposed state hierarchy

For each trial discharge:

1.  Compute geometry properties, `yc`, `yn` where defined, and
    inlet-control headwater.
2.  Classify the free-surface profile family implied by slope and
    downstream boundary.
3.  Solve the outlet-control profile:
    -   M2 from critical outlet;
    -   M1 from tailwater;
    -   H2/H3 for horizontal;
    -   mixed full/free-surface profile where the free-surface branch
        intersects the crown.
4.  For inlet-controlled steep/high-head cases, solve downstream S2 and
    upstream-from-tailwater S1 where applicable.
5.  Test hydraulic-jump compatibility using momentum/conjugate depth.
6.  Determine whether full flow is:
    -   absent;
    -   downstream only;
    -   upstream/most of barrel;
    -   entire barrel.
7.  Compute the valid outlet-control upstream energy/headwater.
8.  Compare valid inlet and outlet requirements.
9.  Return both physical flow type and computational profile
    diagnostics.

### 4.3 Why the current tailwater shortcut fails

Current code in `solver/regime.py`:

``` text
if tw_depth >= rise:
    # Fully submerged outlet forces full flow
```

Current `profiles/direct_step.py` similarly returns a uniform full-flow
profile immediately when `tw_depth >= rise`.

This is too broad.

Counterexample from HDS-5 profile logic:

-   steep barrel;
-   inlet-controlled Type 1 or Type 5;
-   tailwater above the crown;
-   S1 profile develops upstream from the outlet;
-   if S1 does not reach the inlet, the upstream barrel remains
    supercritical/free-surface;
-   a jump may occur to tailwater/full flow downstream.

Thus tailwater above the crown can mean "full at outlet" without meaning
"full along the entire barrel."

### 4.4 Full-flow candidate shortcut

Current logic also contains:

``` text
elif hw_inlet_elev >= hw_full_elev:
    # provisional performance heuristic
```

This is unsafe because the "full-flow outlet" result may be a
mathematically computed energy balance for a state that is not
physically realised.

**Recommendation:** remove this shortcut from governing-regime
selection. A full-flow formula may remain as a candidate calculator, but
its result must only enter the governing comparison after the profile
classifier says that a full or mixed pressurised state is admissible.

------------------------------------------------------------------------

## 5. Direct-step versus standard-step profile methods

### 5.1 Direct step

For the current scope---straight, prismatic culvert barrels with
constant roughness---direct step is appropriate.

Advantages:

-   efficient for prismatic sections;
-   depth is the integration variable, which maps naturally to
    M1/M2/S1/S2 profile families;
-   no iterative depth solution is needed at every fixed station;
-   the current geometry API already provides area, hydraulic radius,
    top width, velocity and friction slope as functions of depth.

Limitations:

-   singular behaviour near critical depth and normal depth requires
    explicit stopping/branch rules;
-   it cannot cross a hydraulic jump; the jump must be solved separately
    by momentum;
-   mixed free-surface/pressurised transitions need separate logic;
-   variable geometry/roughness along the barrel makes it less
    attractive.

### 5.2 Standard step

Standard step is more general because it advances by station and solves
for depth at the next location.

It becomes preferable when:

-   geometry varies longitudinally;
-   roughness varies along the barrel;
-   embedded/natural-bottom geometry changes;
-   bends, transitions, or local structures are introduced;
-   the solver evolves toward a general 1D conduit/reach engine.

### 5.3 Recommendation

Keep direct step now, but refactor it into a **pure GVF profile
engine**.

It should accept:

-   profile family;
-   starting depth/state;
-   target/asymptotic condition;
-   direction;
-   numerical tolerances.

It should not decide:

-   whether the barrel is fully pressurised;
-   whether tailwater submergence forces full flow;
-   whether a jump occurs;
-   whether inlet or outlet control governs.

Add a profile-solver protocol/interface so standard step can be
introduced later without changing the regime layer.

------------------------------------------------------------------------

## 6. Hydraulic-jump implementation

Hydraulic jumps are required for HDS-5/HY-8-consistent Type 1/5
treatment.

### 6.1 Required hydraulic primitive

For arbitrary supported cross-sections, add a momentum/specific-force
function:

`M(y) = Q^2/(g A(y)) + hydrostatic_force_term(y)`

The hydrostatic term requires the first moment of the wetted area
relative to the free surface.

Recommended geometry API addition:

-   `hydrostatic_first_moment(depth: float) -> float`

or a directly usable:

-   `specific_force(depth: float, discharge: float, g: float) -> float`.

For a rectangular section, retain the closed-form conjugate-depth
equation as an analytical test oracle.

For circular/other shapes, solve:

`M(y1) = M(y2)`

for the subcritical conjugate depth `y2 > yc` given supercritical
`y1 < yc`.

### 6.2 Jump location

For Type 1/5:

1.  compute the supercritical S2 profile downstream from the
    inlet/control region;
2.  compute the subcritical S1 profile upstream from tailwater;
3.  at candidate station `x`, compute conjugate depth of the S2 depth;
4.  solve for station where:

`y_conjugate(S2(x)) - y_S1(x) = 0`.

If a root lies within the barrel, the jump is inside the barrel.

If not:

-   the jump is swept out downstream; or
-   the downstream state becomes a jump-to-full condition when the
    tailwater/full-flow boundary requires it.

The jump should be treated as a discontinuity: energy is lost, momentum
is the matching principle.

### 6.3 Result diagnostics

Add:

-   jump present: bool;
-   jump station;
-   pre-jump depth/velocity/Froude;
-   post-jump depth/velocity/Froude;
-   jump head loss;
-   downstream boundary state;
-   HDS-5/HY-8-style profile code where useful.

------------------------------------------------------------------------

## 7. Mixed free-surface and pressurised flow

A separate mixed-profile solver is needed for HDS-5 Type 6/7-style
states.

### 7.1 Downstream free-surface to upstream full-flow transition

For cases where the barrel is full for part of its length but the outlet
is not fully submerged:

-   start an M2/M1 profile at the downstream boundary as HDS-5
    prescribes;
-   integrate upstream until the free-surface depth reaches the crown;
-   the crown-intersection station defines the downstream end of the
    pressurised reach;
-   solve the upstream full-flow energy/HGL from that station to the
    inlet.

This is different from assuming the whole barrel is full.

### 7.2 Fully submerged Type 4

When both ends and the governing energy state support full flow, the
full-flow energy equation is appropriate over the full barrel.

### 7.3 HGL/EGL handling

Keep separate concepts:

-   WSE for free-surface states;
-   HGL for pressurised states;
-   EGL = HGL/WSE + velocity head as appropriate.

The current full-flow method's HDS-5 effective downstream depth:

`max(TW, (dc + D)/2)`

is a standard simplified outlet-control approximation. It should remain
available for the conventional HDS-5 full-flow method, but should not be
used to override a more explicit mixed-profile solution.

### 7.4 Entrance loss

For a ponded upstream approach with negligible approach velocity:

`HW_energy = barrel_inlet_EGL + Ke * V_in^2/(2g)`.

If future inputs include an upstream approach section/velocity, the
solver should use the full energy balance rather than silently assuming
zero approach velocity.

------------------------------------------------------------------------

## 8. Inlet-control transition: recommended implementation

### 8.1 Current code

`src/culvert_solver/inlet_control/fhwa.py` defines:

-   `Q_STAR_UNSUBMERGED_LIMIT = 3.5`
-   `Q_STAR_SUBMERGED_THRESHOLD = 4.0`
-   `transition_headwater()` as linear interpolation.

The thresholds are source-based; the interpolation is not.

### 8.2 Recommended default

Replace the linear interpolation with a cubic Hermite tangent bridge:

Given:

-   `x0 = 3.5`;
-   `x1 = 4.0`;
-   `y0 = H_unsub(x0)`;
-   `y1 = H_sub(x1)`;
-   `m0 = dH_unsub/dq*(x0)`;
-   `m1 = dH_sub/dq*(x1)`,

use the standard cubic Hermite basis to construct `H(q*)` over
`[x0, x1]`.

This directly implements the HDS-5 requirement that the transition curve
be tangent to both branches.

### 8.3 Form 1 derivative

For Form 1:

`H/D = Hc/D + K q*^M + Ks S`.

The derivative is not just `K M q*^(M-1)` because `Hc` changes with
discharge.

Recommended implementation:

-   compute `Hc(q*)` from the critical-depth solver;
-   obtain derivative using either:
    -   an analytical geometry derivative if introduced later; or
    -   a tightly controlled symmetric numerical derivative of the
        complete unsubmerged function at `q* = 3.5`.

The derivative calculation itself should be unit-tested for stability.

### 8.4 HY-8 compatibility

Do not call the Hermite bridge "HY-8 exact."

HDS-5 states that HY-8 uses fitted inlet-control curves/polynomials for
standard shapes over the normal design range, with weir/orifice
extensions outside that range.

Therefore define two concepts:

-   **HDS-5 equation implementation**: Appendix A equations + tangent
    transition.
-   **HY-8 verification target**: compare final headwater results
    against pinned HY-8 8.0.1.2 cases.

Only add a dedicated "HY-8 compatibility mode" if exact HY-8 curve
reproduction becomes a formal product requirement and the pinned
technical coefficients/algorithm are fully extracted.

------------------------------------------------------------------------

## 9. HEC-RAS, HY-8, SWMM and STREAM-1D comparison

### 9.1 HY-8

Official release page:\
https://www.fhwa.dot.gov/engineering/hydraulics/software/hy8/

Pinned target:

-   HY-8 8.0.1.2;
-   build date 5 March 2025.

The official page records recent fixes affecting:

-   water-surface profiles;
-   hydraulic jumps;
-   Manning's n in full flow;
-   small-flow iteration;
-   roadway/overtopping logic.

This reinforces the requirement to pin the exact HY-8 version for
verification.

**Status:** release/version confirmed. The complete technical manual is
distributed with the software installation and was not fully extracted
in this session. Treat detailed HY-8 algorithm parity as pending until
that manual is archived/reviewed.

### 9.2 HEC-RAS

Current HEC-RAS release 7.0 was confirmed. The culvert
technical-reference material reviewed includes:

-   HEC-RAS 6.4.1 Hydraulic Reference Manual inlet-control equations;
-   HEC-RAS 6.6 online outlet-control energy method.

HEC-RAS uses FHWA inlet-control equations and an energy-based
outlet-control computation.

**Use:** independent implementation comparison after the internal solver
is corrected.

**Do not use:** HEC-RAS as the primary source for HDS-5 coefficient
provenance.

**Open item:** pin and archive the exact HEC-RAS 7.0 culvert
technical-reference pages before formal sign-off.

### 9.3 EPA SWMM

Repository:

https://github.com/USEPA/Stormwater-Management-Model

Pinned commit reviewed:

`07c371f8a0d477da1d9d4e7c0d75719664f62fec`

File:

`src/solver/culvert.c`

Important findings:

-   SWMM's culvert routine is an **inlet-control flow limiter**, not a
    complete culvert profile/regime solver.
-   It carries FHWA-style coefficient tables and Form 1/Form 2 logic.
-   It uses the submerged criterion corresponding to
    `Q/(A sqrt(D)) > 4`.
-   For the lower transition bound, SWMM uses an **arbitrary 0.95
    full-depth head criterion**, explicitly because converting the FHWA
    3.5 discharge criterion to a prior head limit is difficult for Form
    1.
-   It then linearly interpolates **flow versus head** between its two
    head bounds.

Therefore SWMM does **not** justify the current project's linear
interpolation of `HWi/D` versus `q*` between 3.5 and 4.0.

Licensing note: the GitHub repository metadata reports no
machine-readable licence and no root `LICENSE` file was found at the
reviewed revision. Treat code reuse as **not cleared** until the
applicable EPA/public-domain/licence terms are confirmed. Algorithmic
comparison is still useful.

### 9.4 STREAM-1D

Repository:

https://github.com/jlillywh/STREAM-1D

Pinned commit reviewed:

`32ede6fb1e211db97c76cc82d1cf0a80eb8a55a0`

Licence:

-   MIT.

Useful architectural ideas:

-   steady GVF engine separated from Python interface;
-   standard-step reach solver;
-   structured culvert diagnostics;
-   verification cases against HEC-RAS.

Cautions:

-   README inlet-control documentation uses a linear transition over a
    stated `F` range of 3.0 to 4.0, which is not the HDS-5 3.5/4.0
    applicability statement and is not authoritative;
-   it is a secondary implementation, not a hydraulic source;
-   reuse only after auditing the exact source file and tests for the
    feature being considered.

**Recommendation:** use STREAM-1D primarily as an architecture and later
comparison reference. Its MIT licence makes code reuse legally simpler
than SWMM, but source provenance and hydraulic correctness still need
independent review.

------------------------------------------------------------------------

## 10. Australian and MRWA guidance

### 10.1 Austroads AGRD05B-23

Publication:

*Guide to Road Design Part 5B: Drainage -- Open Channels, Culverts and
Floodway Crossings*, edition 1.2, 30 January 2023.

Publication page:

https://austroads.gov.au/publications/road-design/agrd05b

The publication page and edition were confirmed, but the full PDF was
not accessible in this session.

**Status:** pending full-text review. Do not claim Austroads compliance
from the current research alone.

### 10.2 MRWA Supplement to Austroads Part 5B

Current repository research identifies:

-   version 1F;
-   3 July 2020.

Important policy point:

-   minimum culvert size is generally 450 mm;
-   375 mm may be used only in special circumstances.

This should be treated as a design-policy/compliance constraint, not a
hydraulic equation.

### 10.3 MRWA Culvert Design Procedure

Current page reviewed:

-   version 2E;
-   5 May 2026.

Section 2.8/Table 2.2 provides Manning `n` for helically wound CSP by
diameter and corrugation. The current repository has correctly typed
those values and fails closed for combinations absent from the table.

However, the table is a **hydraulic roughness source**, not proof that
every listed product is currently permitted by Specification 404.

Structural-plate roughness ranges in the design procedure include
approximately:

-   150 x 50 mm corrugation: `n = 0.033-0.035`;
-   230 x 64 mm corrugation: `n = 0.033-0.037`.

These should be modelled as ranges/contextual values, not a single
universal structural-plate default.

### 10.4 MRWA Specification 404, issued 17 July 2026

Current Specification 404 was reviewed.

For spirally wound corrugated steel pipe:

-   pipe conforms to AS 1761;
-   450 mm diameter: 2.0 mm steel;
-   600-1500 mm: 2.5 mm steel;
-   1650-2100 mm: 3.0 mm steel;
-   corrugation 68 x 13 mm up to and including 1500 mm;
-   corrugation 125 x 25 mm for 1650-2100 mm.

This creates a deliberate distinction from the hydraulic Table 2.2
catalogue.

Recommended data model:

``` text
HydraulicRoughnessReference
    source
    geometry/corrugation
    diameter applicability
    n/range
    hydraulic_reference_status

ConstructionCompliance
    authority
    specification/version
    material/product type
    permitted diameter range
    permitted corrugation
    conditions/contract-specific flags
```

Do not merge these into one "MRWA default" table.

### 10.5 Plastic flexible culverts

Current Specification 404:

-   plastic flexible culverts are a contract-specific provision;
-   limited to polyethylene (PE);
-   installation/design references AS/NZS 2566.2 and manufacturer
    requirements.

MRWA guidance directs roughness selection to manufacturer data.

Recommendation:

-   generic library may retain an HDS-5 thermoplastic roughness range
    for non-MRWA/general reference;
-   MRWA design profile should require explicit manufacturer/project
    `n`;
-   no automatic `SMOOTH_HDPE.typical_n` should be applied when the user
    requests MRWA-compliant defaults.

------------------------------------------------------------------------

## 11. Material/default audit

### 11.1 Concrete

Current generic default:

-   `n = 0.012`;
-   range `0.010-0.015`;
-   HDS-5 Table B.1 provenance.

This is reasonable as a **generic hydraulic reference default**.

For project/authority compliance, allow explicit override and record the
selected source.

### 11.2 Smooth thermoplastic

Current generic default:

-   `n = 0.012`;
-   range `0.009-0.015`.

Keep only as generic reference metadata.

For MRWA:

-   require manufacturer/project value;
-   identify PE-only construction applicability where Spec 404 is being
    applied.

### 11.3 Corrugated steel pipe

Current implementation correctly avoids using a single `0.024` value
automatically and requires diameter/corrugation context for the MRWA
lookup.

Keep that fail-closed behaviour.

Add:

-   current Spec 404 compliance flag/check;
-   separate handling for structural plate/non-helical CSP;
-   explicit warning that hydraulic Table 2.2 availability does not
    imply current construction approval.

### 11.4 Documentation correction

`models/materials.py` contains the comment:

`# Standard materials from HDS-5 Table A.1`

This should be corrected to Appendix B/Table B.1. Table A.1 is
inlet-control coefficients, not Manning roughness.

------------------------------------------------------------------------

## 12. Multi-barrel and mixed-group crossings

The current crossing algorithm is the correct high-level architecture:

For common upstream headwater `H` and tailwater `TW`:

`Q_total(H,TW) = sum_i N_i * Q_i(H,TW)`.

For a specified total discharge, solve:

`Q_total(H,TW) - Q_target = 0`.

This naturally handles:

-   different culvert sizes;
-   different inlet/outlet inverts;
-   different barrel lengths/slopes;
-   different roughness;
-   different inlet configurations;
-   groups becoming active at different upstream stages.

Recommended improvements:

1.  retain exact inactive groups at zero discharge;
2.  expose group activation/headwater thresholds in diagnostics;
3.  require each group to carry its own inlet and entrance configuration
    for engineering-mode solves;
4.  preserve the common absolute tailwater elevation;
5.  make identical-barrel multiplication an explicit **superposition
    assumption**;
6.  later add optional multi-barrel interaction corrections only where a
    source such as NCHRP 734 provides a tested relationship.

Do not replace the current common-headwater root solve with a
pre-allocation of discharge by area or nominal capacity.

------------------------------------------------------------------------

## 13. Proposed validation matrix

Validation should be layered. Internal analytical/source tests come
first; external software comparisons come near the end.

### 13.1 Layer A: geometry and analytical hydraulics

  ------------------------------------------------------------------------------------
  Case              Geometry/state       Reference                Acceptance
  ----------------- -------------------- ------------------------ --------------------
  A1                Rectangular          closed form              machine-level
                    area/perimeter/top                            agreement
                    width                                         

  A2                Circular segment     analytical segment       `<= 1e-10` relative
                    geometry             equations                where
                                                                  well-conditioned

  A3                Rectangular critical `yc=(Q²/(g b²))^(1/3)`   `<= 1e-8 m`
                    depth                                         

  A4                Circular critical    `Fr=1` residual          residual/tolerance
                    depth                                         contract

  A5                Rectangular normal   Manning equation         `<= 1e-8 m` for
                    depth                                         benchmark

  A6                Full-flow Manning    analytical               `<= 1e-10` relative
                    friction                                      
  ------------------------------------------------------------------------------------

### 13.2 Layer B: HDS-5 inlet equations

Use at least:

-   circular concrete square edge, Chart 1 Scale 1;
-   circular CMP projecting, Chart 2 Scale 3;
-   box flared wingwall, Chart 8 Scale 1;
-   box 90-degree headwall/chamfer, Chart 10 Scale 1.

For each:

-   unsubmerged branch at low `q*`;
-   endpoint `q*=3.5`;
-   transition interior;
-   endpoint `q*=4.0`;
-   submerged branch at high `q*`.

Acceptance:

-   coefficient transcription: exact;
-   branch equations: numerical roundoff only;
-   tangent bridge: exact endpoint value/slope continuity within
    numerical derivative tolerance;
-   HDS-5 published/nomograph examples: investigate differences above
    1%; HDS-5 notes nomograph graphical precision can be materially
    looser than the underlying equations.

### 13.3 Layer C: Bodhaine/HDS-5 flow types

  -----------------------------------------------------------------------
  Case                                Expected state
  ----------------------------------- -----------------------------------
  C1                                  steep, low TW: Type 1 inlet
                                      control, S2/free outlet

  C2                                  steep, TW \> yc but \< crown: Type
                                      1 with S1/S2 interaction

  C3                                  steep, TW \> crown: downstream
                                      full/jump possible; **not
                                      automatically full barrel**

  C4                                  mild, TW \< yc: Type 2, M2 from
                                      critical outlet

  C5                                  mild, yc \< TW \< crown: Type 3, M1
                                      from TW

  C6                                  both ends submerged and full state
                                      admissible: Type 4 full flow

  C7                                  high-head inlet, free outlet: Type
                                      5

  C8                                  high-head/mixed pressurised: Type
                                      6/7-style full/free transition

  C9                                  horizontal barrel: H2/H3 family

  C10                                 steep Type 3 exception/backwater
                                      case
  -----------------------------------------------------------------------

Acceptance:

-   correct control type;
-   correct profile family;
-   no physically impossible whole-barrel pressurisation;
-   WSE/HGL continuity outside jumps;
-   energy decreases in the flow direction by calculated losses.

### 13.4 Layer D: hydraulic jumps

1.  Rectangular classical jump with known `Fr1` and closed-form `y2/y1`.
2.  Jump location in a prismatic rectangular culvert where S2 and S1
    profiles intersect by conjugate depth.
3.  No-root case: jump swept out.
4.  Jump to full-flow downstream condition.
5.  Circular conjugate-depth numerical benchmark.

Acceptance:

-   rectangular conjugate depth: `<= 1e-8 m`;
-   momentum residual: solver tolerance;
-   jump station: initially `max(0.05 m, 0.2% of barrel length)` for
    internal deterministic benchmarks;
-   energy loss across jump positive.

### 13.5 Layer E: mixed pressurised/free-surface

1.  M2 profile reaches crown upstream -\> pressurised upstream reach.
2.  M1 profile reaches crown.
3.  tailwater above crown but inlet-controlled upstream free-surface
    reach.
4.  fully submerged Type 4.
5.  transition point close to inlet/outlet boundaries.

Acceptance:

-   crown transition located consistently;
-   HGL/EGL continuous through the free/full transition;
-   no discontinuous headwater jump as tailwater is varied incrementally
    through the transition.

### 13.6 Layer F: multi-group crossings

1.  two identical groups -\> exact superposition in the model;
2.  same size, different inverts -\> staged activation;
3.  different size/roughness -\> common-HW flow split;
4.  one inlet-controlled group + one outlet-controlled group;
5.  one inactive group;
6.  three groups with non-monotonic individual regime changes but
    monotonic total rating.

Acceptance:

-   discharge conservation to root tolerance;
-   common upstream headwater;
-   each group independently satisfies its own hydraulic equation;
-   total rating curve monotonic unless a documented physical transition
    explains otherwise.

### 13.7 Layer G: external software verification

Run only after Layers A-F pass.

#### HY-8 8.0.1.2

Minimum matrix:

-   RCP square edge;
-   CMP projecting;
-   concrete box;
-   steep inlet-control;
-   mild outlet-control M1/M2;
-   hydraulic jump;
-   tailwater above crown but not full barrel;
-   mixed full/free;
-   multi-barrel identical case.

Suggested initial tolerances:

-   headwater: `<= 0.01 m` or `0.5%`, whichever is larger;
-   discharge in inverse/rating comparisons: `<= 0.5%`;
-   profile WSE: `<= 0.01-0.02 m`;
-   jump station: `<= 0.5 m` initially, then tighten once algorithmic
    differences are understood.

Any systematic difference in inlet transition should be classified as: -
expected HDS-5-equation versus HY-8-polynomial difference; or -
implementation defect.

#### HEC-RAS

Use simple one-culvert steady cases with explicit upstream/downstream
sections and matched loss coefficients.

Compare:

-   control type;
-   upstream energy/headwater;
-   barrel profile;
-   outlet depth/velocity.

#### SWMM pinned commit

Compare only inlet-control limiting curves. Do not use SWMM as a
reference for full culvert regime/profile logic.

#### STREAM-1D pinned commit

Compare selected standard-step profile and culvert cases. Treat
differences as diagnostic, not proof of correctness.

------------------------------------------------------------------------

## 14. Prioritised implementation plan

### Priority 0 - source and terminology corrections

1.  Correct the `models/materials.py` Table A.1 comment to Table B.1.
2.  Update `docs/references.md` with:
    -   Bodhaine sections actually reviewed;
    -   HDS-5 transition conclusion;
    -   current Spec 404 issue date and CSP applicability;
    -   pinned SWMM/STREAM commits and licensing status;
    -   explicit pending status for HY-8 manual, Austroads full text,
        NCHRP detailed tables, HRT corrected-table mapping.
3.  Add a source-correction register for HRT-06-138 replaced tables.

**Acceptance:** no source claim is broader than the material actually
reviewed.

### Priority 1 - inlet-control transition

Modules:

-   `src/culvert_solver/inlet_control/fhwa.py`
-   `src/culvert_solver/inlet_control/solver.py`
-   `tests/test_inlet_control.py`

Changes:

1.  replace linear transition with tangent/Hermite bridge;
2.  implement complete Form 1 endpoint derivative;
3.  add monotonicity/continuity tests for every supported coefficient
    set;
4.  retain explicit metadata that this is the project's deterministic
    implementation of the HDS-5 tangent requirement, not an exact HY-8
    polynomial reproduction.

**Acceptance:** C1 continuity and source-faithful transition semantics.

### Priority 2 - separate profile integration from regime classification

Modules:

-   `profiles/direct_step.py`
-   new `profiles/base.py` or protocol module;
-   `outlet_control/partial_flow.py`.

Changes:

1.  remove unconditional full-flow return from direct-step;
2.  make direct-step solve only requested free-surface profile families;
3.  make invalid crown crossing a returned event/state rather than
    silently switching regime;
4.  expose crown/critical/normal termination events.

**Acceptance:** direct-step has no policy decision about full-barrel
pressurisation.

### Priority 3 - momentum and hydraulic jumps

Modules:

-   `geometry/base.py`;
-   `geometry/circular.py`;
-   `geometry/rectangular.py`;
-   new `hydraulics/momentum.py`;
-   new `profiles/hydraulic_jump.py`.

Changes:

1.  add hydrostatic first-moment/specific-force primitive;
2.  rectangular analytical conjugate depth;
3.  general numerical conjugate depth;
4.  S1/S2 jump-location root;
5.  jump diagnostics.

**Acceptance:** analytical rectangular jump benchmarks and HDS-5 Type
1/5 jump cases pass.

### Priority 4 - mixed full/free-surface profile solver

Modules:

-   new `profiles/mixed.py` or `profiles/pressurized.py`;
-   `outlet_control/full_flow.py`;
-   `outlet_control/partial_flow.py`.

Changes:

1.  detect free-surface profile intersection with crown;
2.  solve pressurised reach HGL/EGL upstream of transition;
3.  support downstream-full but upstream-free inlet-controlled cases;
4.  preserve HDS-5 simplified full-flow method as a clearly named
    conventional method.

**Acceptance:** Type 4/6/7-style cases and crown-transition continuity
tests pass.

### Priority 5 - replace regime selector with explicit state machine

Module:

-   `solver/regime.py`.

Remove:

-   unconditional `tw_depth >= rise -> full barrel`;
-   `hw_inlet >= hw_full` performance shortcut.

Add:

-   explicit feasible-state construction;
-   profile-family selection;
-   jump/mixed-state evaluation;
-   comparison of physically valid inlet/outlet candidates.

Recommended result fields:

-   Bodhaine flow type where applicable;
-   HDS-5/HY-8 profile code;
-   control type;
-   free/full/mixed state;
-   jump state;
-   full-flow length;
-   transition station;
-   warnings/assumptions.

**Acceptance:** all Layer C-E cases pass without special-case test-only
logic.

### Priority 6 - explicit engineering configuration

Modules:

-   `models/barrel.py`;
-   high-level solver entry points.

Changes:

1.  keep low-level convenience defaults if useful for exploratory
    calculations;
2.  add an engineering/strict mode requiring explicit:
    -   inlet configuration;
    -   entrance-loss coefficient/configuration;
    -   roughness source/override where authority-specific data require
        it;
3.  record source metadata in results.

**Acceptance:** no silent geometry-only assumption in strict mode.

### Priority 7 - MRWA applicability/compliance layer

Modules:

-   `models/materials.py`;
-   new `standards/mrwa.py` or similar.

Changes:

1.  preserve hydraulic roughness lookup;
2.  add current Spec 404 construction applicability;
3.  model 450 mm general minimum and 375 mm special-use policy;
4.  PE plastic as contract-specific;
5.  structural-plate roughness ranges;
6.  manufacturer-required roughness for MRWA plastic.

**Acceptance:** hydraulic lookup and compliance checks cannot be
confused in API or docs.

### Priority 8 - internal validation suite

Add published/analytical fixtures described in Section 13.

Do not move to external package matching until these pass.

### Priority 9 - external verification

Pin:

-   HY-8 8.0.1.2;
-   HEC-RAS exact release/docs used;
-   SWMM `07c371f8a0d477da1d9d4e7c0d75719664f62fec`;
-   STREAM-1D `32ede6fb1e211db97c76cc82d1cf0a80eb8a55a0`.

Create machine-readable benchmark fixtures and comparison reports.

### Priority 10 - only then broaden feature scope

After the conventional solver is validated:

-   embedded/natural-bottom culverts;
-   composite roughness;
-   non-prismatic barrels;
-   more Australian product catalogues;
-   roadway overtopping;
-   debris/blockage;
-   scour/energy dissipators;
-   reverse flow.

------------------------------------------------------------------------

## 15. Open-source reuse recommendations

### 15.1 SWMM

**Reuse status:** do not copy code yet.

Reason:

-   useful, mature FHWA inlet-control implementation;
-   but repository metadata at the reviewed revision did not identify a
    licence and a root `LICENSE` file was not found.

Permitted current use:

-   algorithm comparison;
-   coefficient cross-check;
-   test-case inspiration.

Before copying any source:

-   establish EPA/public-domain/licence terms for the exact
    files/revision;
-   preserve attribution if required;
-   document copied/adapted sections.

### 15.2 STREAM-1D

**Reuse status:** legally reusable under MIT, subject to
attribution/notice.

Good candidates for study/reuse after source audit:

-   profile-solver interfaces;
-   result diagnostics;
-   verification harness structure.

Do not copy its hydraulic equations merely because the licence permits
it. Check each method against primary sources first.

### 15.3 HEC-RAS and HY-8

Use as external verification targets, not code sources.

### 15.4 General rule

For every imported/adapted algorithm:

1.  identify primary hydraulic source;
2.  identify software source and exact revision;
3.  verify licence;
4.  record what was copied versus independently reimplemented;
5.  add independent tests not derived from the same implementation.

------------------------------------------------------------------------

## 16. Source correction and blocker register

  -----------------------------------------------------------------------------
  Topic                      Status                  Decision / blocker
  -------------------------- ----------------------- --------------------------
  HDS-5 inlet equations      Reviewed                keep equations and
                                                     coefficient provenance

  HDS-5 transition           Resolved                replace linear bridge with
                                                     tangent/C1 implementation

  HDS-5 profile logic        Reviewed sufficiently   implement
                             for remediation         S1/S2/M1/M2/H2/H3, jumps,
                                                     mixed full/free

  Bodhaine six types         Core classification     worked examples still to
                             reviewed                extract

  `TW >= D -> full barrel`   Rejected                replace with profile/state
                                                     logic

  Full-flow candidate        Rejected as general     solve physically
  shortcut                   rule                    admissible outlet state
                                                     first

  Direct step                Retain for prismatic    separate from regime
                             free-surface profiles   policy

  Standard step              Future/generalisation   define interface now

  Hydraulic jumps            Required                momentum/conjugate-depth
                                                     solver

  HRT-06-138 errata          Errata scope confirmed  detailed corrected-table
                                                     applicability map pending

  NCHRP 734                  Relevant methods        detailed coefficient
                             confirmed               tables pending

  HY-8                       Pin 8.0.1.2             full installed technical
                                                     manual pending

  HEC-RAS                    use as external check   pin exact 7.0 technical
                                                     pages before sign-off

  SWMM                       pin commit              no code copying until
                                                     licence resolved

  STREAM-1D                  pin commit, MIT         source audit before any
                                                     reuse

  Austroads AGRD05B-23       publication confirmed   full text inaccessible in
                                                     session; pending

  MRWA CSP roughness         reviewed                keep typed hydraulic
                                                     lookup

  MRWA Spec 404 CSP          reviewed, 17 Jul 2026   add separate construction
                                                     compliance

  MRWA plastic               reviewed                PE only,
                                                     contract-specific;
                                                     manufacturer roughness

  Roadway overtopping        out of current scope    no implementation now
  -----------------------------------------------------------------------------

------------------------------------------------------------------------

## 17. Recommended immediate next development sequence

The next coding work should be narrowly sequenced:

1.  implement and test the HDS-5 tangent inlet transition;
2.  refactor direct-step so it cannot declare full flow;
3.  add momentum/conjugate-depth geometry support;
4.  implement hydraulic-jump location;
5.  implement mixed free/full crown-transition logic;
6.  replace `determine_governing_regime()` with the explicit state
    machine;
7.  add MRWA compliance metadata/checks;
8.  build the analytical/published validation matrix;
9.  only then run pinned HY-8/HEC-RAS/SWMM/STREAM comparisons.

This sequence minimises rework because the external comparisons will
then test the intended final hydraulic architecture rather than
provisional regime shortcuts.

------------------------------------------------------------------------

## 18. Sources

### Primary hydraulic sources

1.  Federal Highway Administration. *Hydraulic Design of Highway
    Culverts*, HDS-5, Third Edition, FHWA-HIF-12-026, April 2012.\
    https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf

2.  Bodhaine, G. L. *Measurement of Peak Discharge at Culverts by
    Indirect Methods*, USGS TWRI Book 3, Chapter A3.\
    https://pubs.usgs.gov/twri/twri3-a3/html/pdf.html

3.  Federal Highway Administration. *Effects of Inlet Geometry on
    Hydraulic Performance of Box Culverts*, FHWA-HRT-06-138, corrected
    electronic report.\
    https://highways.dot.gov/sites/fhwa.dot.gov/files/FHWA-HRT-06-138.pdf

4.  National Academies / NCHRP Report 734. *Hydraulic Loss Coefficients
    for Culverts*.\
    https://www.nationalacademies.org/publications/22673\
    DOI: https://doi.org/10.17226/22673

### Australian / MRWA sources

5.  Austroads. *Guide to Road Design Part 5B: Drainage - Open Channels,
    Culverts and Floodway Crossings*, AGRD05B-23, Edition 1.2, 30
    January 2023.\
    https://austroads.gov.au/publications/road-design/agrd05b

6.  Main Roads Western Australia. *MRWA Supplement to Austroads Guide to
    Road Design Part 5B*.\
    https://www.mainroads.wa.gov.au/technical-commercial/technical-library/road-traffic-engineering/guide-to-road-design/mrwa-supplement-to-austroads-guide-to-road-design-part-5b/

7.  Main Roads Western Australia. *Design Procedure - Culverts*, version
    2E, 5 May 2026.\
    https://www.mainroads.wa.gov.au/technical-commercial/technical-library/road-traffic-engineering/drainage-waterways/culverts/design-procedure/

8.  Main Roads Western Australia. *Specification 404 Culverts*, issued
    17 July 2026.\
    https://www.mainroads.wa.gov.au/globalassets/technical-commercial/technical-library/specifications/400-series-drainage/specification-404-culverts.pdf

### Software / implementation references

9.  FHWA HY-8 official release page; target version 8.0.1.2, build 5
    March 2025.\
    https://www.fhwa.dot.gov/engineering/hydraulics/software/hy8/

10. USACE HEC-RAS culvert technical reference, outlet control (6.6 page
    reviewed).\
    https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.6/modeling-culverts/culvert-hydraulics/computing-outlet-control-headwater

11. USACE HEC-RAS Hydraulic Reference Manual 6.4.1, inlet-control
    section reviewed.\
    https://www.hec.usace.army.mil/software/hec-ras/documentation/HEC-RAS%20Hydraulic%20Reference%20Manual-v6.4.1.pdf

12. EPA SWMM, pinned revision
    `07c371f8a0d477da1d9d4e7c0d75719664f62fec`, `src/solver/culvert.c`.\
    https://github.com/USEPA/Stormwater-Management-Model/blob/07c371f8a0d477da1d9d4e7c0d75719664f62fec/src/solver/culvert.c

13. STREAM-1D, pinned revision
    `32ede6fb1e211db97c76cc82d1cf0a80eb8a55a0`, MIT licence.\
    https://github.com/jlillywh/STREAM-1D/tree/32ede6fb1e211db97c76cc82d1cf0a80eb8a55a0

### Repository reviewed

14. `Chain-Frost/ryan-culverts`, baseline
    `2c431e6a205fd7127ec940226aa4ee17599a9999`.\
    https://github.com/Chain-Frost/ryan-culverts/tree/2c431e6a205fd7127ec940226aa4ee17599a9999

------------------------------------------------------------------------

## 19. Research limitations

The following items remain genuine research blockers before engineering
validation is claimed:

-   full HY-8 8.0.1.2 technical manual extraction and archival;
-   exact HEC-RAS 7.0 culvert-method pinning;
-   full Austroads AGRD05B-23 text review;
-   detailed corrected FHWA-HRT-06-138 table-to-configuration mapping;
-   detailed NCHRP 734 coefficient-table extraction and applicability
    mapping;
-   Bodhaine worked-example extraction for direct benchmark fixtures.

These blockers do **not** prevent the remediation work in Priorities
0-7. They do prevent final claims of HY-8 parity, Australian design
compliance, or comprehensive external validation.
