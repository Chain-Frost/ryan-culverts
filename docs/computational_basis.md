# Computational basis

Status: Phase 0 research basis closed 2026-09-09. HDS-5 equation and table
transcriptions used by the current code have been checked. Research completion does not
make the combined solver engineering-validated; the remaining validation and external
comparison tasks are tracked separately.

## Source hierarchy and scope

Use FHWA HDS-5 (third edition, April 2012) as the starting culvert reference.
Evaluate refinements against the publications in [references](references.md).
External software is an implementation comparison, not the definition of truth.

The completed source review adopts the following method dispositions:

- Bodhaine's six types define physical classification evidence, not production equations
  or a one-to-one mapping to every extended HY-8 profile label.
- Corrected FHWA-HRT-06-138 coefficients apply only to their recorded box inlet geometry,
  barrel count, span-to-rise range, fillets, bevels, and skew. CS-013 implements that
  context and fails closed on unmatched Figure 93 configurations. Its Table 12 polynomial
  is limited to approximately
  `0.4 < HW/D < 2.3`; it is not HY-8's recomputed South Dakota-box curve.
- NCHRP 734 supports the current representative-barrel total-flow architecture within its
  tested limitations. Its Borda-Carnot outlet refinement is deferred because the initial
  reservoir/pool boundary has no downstream channel area. Slipline, buried-invert,
  depth-varying, and composite roughness are separated into CS-030 through CS-033. Original
  NCHRP embedded-
  culvert coefficients are rejected for implementation because the HY-8-bundled correction
  documents a dimensionless-discharge error and false 50% embedded beveled data. The
  correction's synthetic high-flow extension is also not adopted as primary evidence.
- Austroads AGRD05B-23 supplies Australian design context, including allowable
  headwater, blockage, outlet velocity, scour, multiple-event checking, and reporting.
  It does not displace the HDS-5 computational baseline. Its convention of assigning a
  near-crown Froude number to full flow is rejected for the computational core: Froude
  number remains undefined for a pressurised closed section.
- HY-8 v8.0 method documentation and executable 8.0.1.2 results are pinned comparison
  evidence. They do not define a local coefficient, transition, or acceptance tolerance.

Fixture-ready source records and the limits of their use are in
[`research/fixture_candidates.md`](research/fixture_candidates.md).

The first hydraulic scope is steady, forward flow through straight, prismatic
circular and rectangular barrels. Initial crossing boundaries will be specified
absolute headwater/tailwater elevations in a common datum. Negligible reservoir
approach and receiving-water velocity is an explicit initial simplification;
channel approach sections and their energy correction require a later contract.
Roadway overtopping, adverse-slope solutions, reverse flow and barrel junctions
are outside the first solver release. Models may represent a horizontal barrel;
normal depth at zero slope must not be invented for positive discharge.

These are project decisions, not claims that the excluded cases lack solutions.
An unsupported case must raise a structured error rather than silently selecting
a different hydraulic model. NCHRP 734 supports representative-barrel
superposition for most total-flow calculations, but reports nonuniform-approach
differences up to 10%, depressed-barrel average-flow differences up to about 4%,
and individual-barrel differences up to about 7%. These limitations matter where
local barrel performance is the design criterion.

## SI hydraulic primitives to implement after geometry

With flow area A, wetted perimeter P, free-surface top width T, discharge Q,
gravity g and Manning roughness n:

```text
R = A / P
V = Q / A
hydraulic_depth = A / T
velocity_head = V^2 / (2*g)
Fr^2 = Q^2*T / (g*A^3)                 [uniform velocity distribution]
E = y + Q^2 / (2*g*A^2)               [alpha = 1]
Q_normal = A*R^(2/3)*sqrt(S0) / n     [SI Manning, uniform flow]
Sf = (n*Q / (A*R^(2/3)))^2
hf = L*Sf                             [constant area/roughness]
h_local = K*V_reference^2 / (2*g)
M(y) = Q^2/(g*A(y)) + integral(A(z), z=0..y) [momentum function]
```

HDS-5 section 3.1.4, printed pages 3.9–3.12 (local PDF pages 91–94), provides
velocity, entrance/friction/exit losses and energy balance, equations 3.1–3.7.
Critical depth is the stationary-specific-energy solution, equivalently Fr = 1
under the assumptions above; it must be solved from geometry and discharge.
Normal-depth solvers must identify admissible branches rather than assuming
the circular Manning conveyance curve is monotone up to the crown.

For a circle of radius r at depth y, the segment angle is
`theta = 2*acos((r-y)/r)`, area is `r^2*(theta-sin(theta))/2`, wetted perimeter
is `r*theta`, and surface chord is `2*sqrt(y*(2*r-y))` for `0 < y < 2*r`.
These analytical geometry identities need cancellation/limiting-case tests.

Geometry conventions are a Phase 2 gate: distinguish a surface approaching the
crown from a pressurised closed section. Do not reuse the old circular top width
of one diameter at full depth. Hydraulic depth and Froude number are undefined
for a pressurised section and should not be manufactured from full-barrel radius.

## Outlet losses and profile requirements

HDS-5 equation 3.4b lists friction prefactors 29 in English units and 19.63 in SI.
The new solver will use the direct SI Manning friction slope above instead of
transplanting a prefactor from an English-unit implementation.

Exit loss requires an explicitly identified downstream velocity/reference area.
HDS-5 equations 3.4c–3.4e describe different assumptions. Do not derive barrel
outlet velocity merely by dividing flow by the tailwater-wetted barrel area.

HDS-5 describes the effective outlet depth `(dc + D)/2` as an approximation;
section 3.1.4 states that backwater calculations are required for low headwater.
Therefore it does not replace a free-surface profile in the production solver.

Direct step is the adopted production method for monotonic S1, S2, M1, M2, and H2
profiles in the currently supported prismatic circular and rectangular barrels. Depth is a
stable integration coordinate for those branches and directly locates normal-depth and
crown limits. Standard step is reserved as an independent spatial-coordinate validation
method and for future non-prismatic geometry; it is not currently a second production
solver. Hydraulic jumps use momentum matching between independently routed S1 and S2
branches rather than attempting to integrate through the discontinuity.

HEC-RAS's [outlet-control energy formulation][hec-outlet] is an independent
methodology reference for boundary energy accounting and candidate conditions.

## Empirical relationships and transition policy

The implemented inlet constants were checked against HDS-5 Appendix A, Table A.1
(local PDF page 197), and the implemented entrance-loss constants against Appendix C,
Table C.2 (local PDF page 216). Equation form, unit conversion, chart/scale, entrance
geometry, locator and shape applicability are represented in typed records. The box-report
(FHWA-HRT-06-138) and NCHRP 734 coefficients have been extracted into `docs/research/`, providing
expanded parameters for slip-lined culverts and modern box geometries. Transcription is not
the same as engineering acceptance; assess applicability before adding these to the catalogue.

HDS-5 Appendix A, printed page A.1 (local PDF page 190), describes the transition as a
smooth curve drawn between and tangent to the unsubmerged and submerged curves. Printed
page A.6 states that the nomograph transition was drawn by hand, so no reproducible digital
algorithm is prescribed. The adopted project method is a cubic Hermite bridge over
`3.5 <= q* <= 4.0`, using the value and first derivative of each bounding curve. For Form
1, the lower tangent includes the exact critical-specific-energy derivative. It is C1
continuous and monotonic for every catalogued circular and rectangular coefficient set.
This is a deterministic implementation of the HDS-5 tangency requirement, not a claim of
exact HY-8 polynomial or hand-drawn-nomograph equivalence.

HDS-5 Section 3.5.2, printed page 3.39 (local PDF page 121), states that its laboratory
inlet-control curves cover `0.5 <= HW/D <= 3.0`. Below `0.5`, a general weir equation is
fitted at the boundary; above `3.0`, a general orifice equation is fitted at the boundary.
The project evaluates the direct Appendix A Equation A.3 relationship above that range but
marks every such result with `inlet_control_high_head_extension`. Results above `HW/D =
10` receive the additional `inlet_control_extreme_headwater` review warning. These numeric
extensions are available for sensitivity and comparison work; the warnings prevent them
from appearing ordinarily validated. HY-8's version-specific `**` report marker motivated
the conservative extreme-review threshold but is not the source of the `HW/D = 3`
applicability boundary.

The [HEC-RAS inlet page][hec-inlet] renders the submerged slope term with an
apparent equality-sign error. Verify the typeset primary equation before use.
SWMM's inlet transition is an implementation choice to investigate, not an
automatically adopted continuous-regime model.

## Current implementation boundary

Default selection follows the typed-context policy in CS-002. Current MRWA Design
Procedure version 2E, Table 2.1 supplies distinct smooth reinforced-concrete pipe and box
ranges; Table 2.2 supplies diameter/corrugation-specific CSP values. The MRWA Part 5B
supplement requires plastic-pipe Manning roughness from the applicable manufacturer.
Accordingly, generic concrete roughness and missing material context fail explicitly,
while a plastic HDS-5 laboratory value is available only through a deliberate fallback
flag with structured applicability notices. Hydraulic defaults and construction
compliance remain separate decisions. No HY-8 fallback value has been adopted.

The repository implements circular and rectangular geometry, hydraulic primitives,
critical and normal depth, selected HDS-5 inlet and loss coefficients, provisional
inlet/outlet control, direct-step profiles, barrel/group/crossing solvers, rating curves,
and constant-crest unsubmerged roadway overtopping. Roadway flow follows HDS-5 Section
3.1.5 Equation 3.9 in SI units:

```text
Q_roadway = C_d L H_wr^1.5
```

The caller must supply the SI coefficient selected for the actual roadway geometry and
overtopping depth. The crossing solver adds this flow to the independently calculated
culvert-group flows at a common headwater. Tailwater above the crest fails explicitly
because the Figure 3.11C submergence correction has not been digitised or validated;
irregular sag curves and segment summation are also deferred.

The initial discharge-dependent tailwater option is a prismatic-channel normal-depth
boundary. For bottom width `b`, left and right horizontal-to-vertical side slopes `zL`
and `zR`, and depth `y`, it uses:

```text
A = b y + 0.5 (zL + zR) y^2
P = b + y sqrt(1 + zL^2) + y sqrt(1 + zR^2)
T = b + (zL + zR) y
Q = (1/n) A (A/P)^(2/3) sqrt(Sf)
```

The solver brackets and solves `Q(y) - Qtarget = 0` with Brent's method, then returns
`tailwater elevation = channel invert elevation + y`. `Sf` remains explicitly the
friction/energy slope; using bed slope estimates it only under uniform flow. Consistent
with HDS-5 Section 1.4.4, this is an approximation for a downstream channel without a
controlling backwater influence. It is not valid as a general reach model for downstream
impoundment, constriction, junction, tidal, or other backwater controls.

The boundary's `method_source` records HDS-5 as the basis for using a normal-depth
approximation. It does not attribute the caller's Manning roughness, friction slope,
surveyed geometry, or channel invert to HDS-5; those inputs have separate optional source
fields. Likewise, `TailwaterResolution.depth` is normal depth above the downstream channel
invert. `RatingCurvePoint.tailwater_depth` retains the older culvert-relative reporting
meaning: depth above the barrel outlet for a barrel curve or above the lowest outlet invert
for a crossing curve. These values differ whenever the channel and culvert inverts differ.

A user-supplied tailwater rating curve is a separate empirical boundary, not a Manning
calculation. It contains at least two finite `(Q, WSE)` points, with nonnegative strictly
increasing discharge and nondecreasing absolute water-surface elevation. At a supplied
discharge the exact elevation is returned. Between adjacent points the implementation uses
only linear interpolation:

```text
WSE(Q) = WSE1 + (Q - Q1) (WSE2 - WSE1) / (Q2 - Q1)
```

Discharge outside the supplied closed range fails explicitly; there is no implicit clamp
or extrapolation. The caller's `rating_curve_source`, complete curve, requested discharge,
resolved elevation, and exact-versus-linear interpolation decision are retained in the
tailwater resolution. The curve is resolved from barrel flow for a standalone barrel,
total group flow for a standalone group, and total crossing flow before allocation for a
crossing. Every generated rating point performs an independent boundary resolution.

For HDS-5 Section 3.5 steep-slope inlet-control cases, the solver routes an S2 profile
downstream from immediately below critical depth toward normal depth. Tailwater no higher
than normal depth directly implies a swept-out jump. For higher sub-crown tailwater, the
solver compares the boundary depth with the conjugate depth of the S2 outlet section,
found by equating momentum functions. If tailwater cannot sustain that conjugate depth,
the S2 outlet depth and velocity remain valid. HDS-5 printed pages 3.36-3.37 (local PDF
pages 118-119) describe this momentum comparison and swept-out-jump result.

When the S1 and S2 conjugate-depth profiles intersect, the solver records a `JS1` profile,
the jump station, and both depths at that duplicated station. If S1 instead reaches the
inlet, its free-surface outlet-control headwater remains a physical candidate. The solver
still does not resolve all mixed free-surface/pressurised Type 6/7 cases, so the combined
solver remains provisional rather than engineering accepted. See [progress](progress.md)
and [validation](validation.md) for the remaining gates.

For outlet-controlled M2 flow that reaches the crown before the inlet, the upstream
remainder is continued as a full-section reach. Its headwater is the transition-section
energy plus full-flow Manning friction over the reported `full_flow_length` and the inlet
loss. This represents a mixed free-surface/pressurised Type 7 path without treating the
whole barrel as full. An explicit Type 6 comparison now exercises nearly full-length
pressurisation, but its high-head inlet result does not yet agree sufficiently with HY-8
and remains unsupported.

For a submerged outlet whose full-flow HGL intersects the crown inside the barrel, the
intersection defines a downstream pressurised length and an upstream free-surface reach.
The upstream reach is routed from immediately below the crown using the same backward S1
and S1/S2 momentum-intersection methods as sub-crown tailwater cases. This distinguishes
S1f from JS1f while retaining the full length and jump station in the result.

Supported calculations that retain a known approximation expose stable
`HydraulicWarningCode` values rather than relying on prose or inferred regimes. Current
codes identify the inlet-control outlet-depth approximation and unresolved mixed flow.
Candidate headwaters and these warnings are calculation evidence; they do not make an
unsupported flow state valid.

[hec-outlet]: https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/modeling-culverts/culvert-hydraulics/computing-outlet-control-headwater
[hec-inlet]: https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/modeling-culverts/culvert-hydraulics/computing-inlet-control-headwater
