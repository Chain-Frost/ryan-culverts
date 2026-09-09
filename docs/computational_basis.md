# Computational basis

Status: implementation basis under review, 2026-09-06. HDS-5 equation and table
transcriptions used by the current code have been checked. Phase 0 research and
combined-solver engineering validation are not complete.

## Source hierarchy and scope

Use FHWA HDS-5 (third edition, April 2012) as the starting culvert reference.
Evaluate refinements against the publications in [references](references.md).
External software is an implementation comparison, not the definition of truth.

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
and individual-barrel differences that matter where local barrel performance is
the design criterion.

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
Therefore it will not replace a free-surface profile in the production solver.
The standard-step versus direct-step decision remains open until profile
equations, critical-point treatment and mixed-flow transitions are reviewed.

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
inlet/outlet control, direct-step profiles, barrel/group/crossing solvers, and rating curves.
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
