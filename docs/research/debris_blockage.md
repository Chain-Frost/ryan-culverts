# CS-026 debris and blockage research

Status: research recommendation only; no hydraulic implementation is authorised by this document.

Issue: [#18](https://github.com/Chain-Frost/ryan-culverts/issues/18).

Reviewed: 2026-10-06.

## Purpose

This record establishes the evidence and implementation boundary for explicit debris and
blockage scenarios. It does not introduce a generic culvert capacity factor, alter Manning
roughness, or modify culvert geometry. The purpose is to determine which blockage mechanisms
can be represented with defensible hydraulics, which inputs must be explicit, how provenance
must survive into results, and which combinations must fail closed.

The main conclusion is that "percent blockage" is not a hydraulic model by itself. Blockage
location, physical mechanism, obstruction geometry, hydraulic regime, and structure
configuration determine which quantity changes. A local inlet obstruction, a sediment deposit
that extends along the barrel, a debris screen, and an outlet obstruction must therefore remain
different scenario types.

## Research disposition

The following decisions are recommended before any solver implementation:

1. Separate **scenario selection** from **hydraulic transformation**. A source or project basis
   may establish why a 20% or 50% blockage scenario is analysed; a different primary source may
   establish how that blockage modifies inlet or outlet hydraulics. Results must retain both.
2. Use an unambiguous public quantity such as `blocked_area_fraction` and derive
   `open_area_fraction = 1 - blocked_area_fraction`. Do not expose a generic `BR` field:
   ARR Project 11 uses `BR` for the open/free-area ratio, while secondary software
   documentation has used the same term ambiguously.
3. Treat a local inlet blockage as an inlet hydraulic condition. Do not reduce the full barrel
   area, wetted perimeter, hydraulic radius, or friction length for a blockage confined to the
   inlet face.
4. Treat a physical obstruction extending into the barrel as geometry, not as an inlet loss or
   roughness multiplier. Its longitudinal extent is required.
5. Model debris screens/racks as explicit structures. ARR distinguishes a screen upstream of the
   inlet, a screen attached to the inlet, a screen at the outlet, and a screen well downstream;
   the loss accounting is not interchangeable.
6. Do not introduce an arbitrary "capacity efficiency" factor or hide blockage in Manning
   roughness.
7. Do not double-count a single obstruction by both reducing geometry and applying an empirical
   blockage loss unless the adopted source explicitly defines that decomposition.
8. The strongest reviewed physical validation is for idealised **bottom-up blockage at circular
   pipe inlets**. Rectangular culverts, floating top-down rafts, porous plugs, mixed debris,
   longitudinal barrel deposits, and generic outlet debris do not inherit that validation.
9. Current inlet coefficient names are not sufficient to prove exact equivalence to the inlet
   geometries tested by Sellevold et al. An implementation must add or resolve a source-specific
   inlet geometry identity rather than matching on a similar description.
10. Begin with static deterministic blockage snapshots. Time-varying debris accumulation is a
    separate modelling problem; timing may be retained as scenario metadata but must not be
    simulated implicitly.

## Evidence reviewed

| Source | Evidence role | Disposition |
| --- | --- | --- |
| ARR Revision Project 11 Stage 1, P11/S1/007 (2009) | Hydraulic blockage equations and distinct screen arrangements | Authoritative Australian historical method; retain as mechanism/equation source and comparison evidence, but not as a universal validated default |
| ARR Revision Project 11 Stage 2, P11/S2/021 (2013) | Blockage type, location, porosity, timing, design/severe scenario guidance | Adopt for scenario construction and application context, not as a blanket hydraulic capacity factor |
| Australian Rainfall and Runoff 2019, Book 6 Chapter 6 | Current Australian blockage guidance and limitations | Adopt for Australian application/risk context; chapter explicitly notes limited quantitative evidence |
| Sellevold et al. (2024), Journal of Irrigation and Drainage Engineering | Controlled physical experiments for bottom-up blockage of circular pipe inlets | Primary validation evidence for the bounded circular-inlet cases only |
| FHWA HEC-9, third edition (2005) | Debris accumulation, assessment, and countermeasure context for culverts and bridges | Authoritative context; it does not justify one generic culvert blockage factor |
| FHWA HDS-5, third edition (2012) | Existing clean-culvert hydraulic baseline | Remains the clean hydraulic baseline; blockage methods must compose with it without replacing unrelated equations |
| Ollett, Syme and Ryan (2017) | Numerical implementation and three ARR blockage case studies | Secondary case-study evidence; supports separating ELM from whole-barrel reduced-area treatment |
| French and Jones (2018) | Published technical critique of ARR blockage guidance | Contrary evidence reinforcing that scenario percentages are not calibrated hydraulic truth |
| TUFLOW Classic/HPC 2026.0 manual | Secondary implementation of ARR RAM/ELM concepts | Comparison evidence only; do not treat software behaviour or terminology as hydraulic authority |

No reviewed source supplied equally strong modern physical validation for rectangular culvert
inlet blockage. That absence is an implementation constraint, not permission to transfer the
circular regressions.

## Australian Rainfall and Runoff findings

### Stage 1 hydraulic methods

ARR Project 11 Stage 1, printed page 45, treats partial entrance blockage under outlet
control using an entrance-loss method. Its Equation 4.2 is

```text
Ke = ((1 + sqrt(Kc)) / BR - 1)^2
```

where `Kc` is the clean entrance-loss coefficient and `BR` is explicitly the free/open
cross-sectional area at the inlet divided by the downstream full-pipe area. The same page gives
the inlet-control relationship in Equation 4.3:

```text
BF = BR^(5/4)
```

where `BF` is blocked discharge divided by unblocked discharge.

These equations are useful as durable descriptions of the ARR energy-loss method (ELM) and
reduced-capacity concept. They should not be promoted to universal defaults merely because they
are simple. Later controlled experiments described below found substantial conservative bias in
both the traditional ELM and reduced-area method for the tested bottom-up pipe-inlet cases.

The source also distinguishes screen geometry and location:

- **Screen upstream and separated from the inlet:** screen loss is calculated as an additional
  component while the culvert retains its clean entrance loss.
- **Screen attached to the inlet:** printed page 47 states that the screen loss cannot be
  considered separately from pipe entry loss. Equation 4.7 gives a combined entry-loss
  coefficient. Adding a screen loss to a separately modified entrance loss would double-count.
- **Screen at the outlet:** a separate combined exit-loss formulation is supplied.
- **Screen well downstream of the outlet:** the report describes this as the most hydraulically
  complex of its five screen cases and does not support reducing it to the inlet equations.

This distinction is directly relevant to issue #18: a `DebrisScreen` cannot be a synonym for
`EntranceBlockage`.

### Stage 2 mechanism and scenario guidance

ARR Project 11 Stage 2 identifies blockage type, location, porosity, timing, and extent as key
factors affecting hydraulic impact. Printed pages 17-19 distinguish:

- floating/raft debris, typically a **top-down** restriction and commonly an inlet mechanism;
- non-floating/depositional debris, typically a **bottom-up** obstruction that can occur at the
  inlet, within the barrel, or at the outlet;
- porous plugs; and
- mixed-mode blockage.

The report also warns that the debris visible after a flood may not represent the obstruction at
peak discharge. A raft that appears to fully block an inlet after the event may have floated above
the culvert crown during the peak. This is a strong reason not to infer a hydraulic mechanism from
a single percentage alone.

Table 3.16, printed page 44, provides suggested design/severe blockage conditions. For pipe
inlets and waterway culverts it gives, among other cases, 20%/100% for smaller openings and
10%/25% for larger openings, with a note to adopt 25% bottom-up sediment blockage unless such
blockage is unlikely. Screened pipe and culvert inlets are listed separately at 50% design and
100% severe blockage. The report says design blockage should be determined separately by
structure type and location and says widespread severe blockage is generally inappropriate.

These percentages are **scenario-selection guidance**. They do not define which hydraulic
equation applies to every structure with that percentage blockage.

ARR 2019 Book 6 Chapter 6 carries the blockage guidance into the current national guideline but
states that actual evidence for blockage impacts and clear quantitative design advice is limited.
It describes the procedure as non-definitive and expected to evolve. This limitation must remain
visible in the public engineering documentation.

### Secondary Australian implementation and critique

Ollett, Syme, and Ryan (2017) implemented the ARR blockage methods in TUFLOW and compared
the energy-loss and reduced-area approaches in three flood-model case studies. Their published
abstract reports that the energy-loss approach produced more realistic headwater levels than
reducing culvert area in those models and that whole-area reduction can exaggerate energy
losses. This is useful implementation/case-study evidence, especially against treating a local
inlet blockage as a smaller barrel, but it is not a controlled physical validation dataset.

French and Jones (2018) published a technical critique of the ARR blockage guidance, focusing
on the limited observational data and unproven predictive basis for the recommended blockage
levels. The conclusion adopted here is narrower than either side of that debate: retain ARR as
authoritative Australian scenario/risk guidance, but do not present its generic blockage
percentages as calibrated hydraulic performance data. Source-specific physical evidence should
control the hydraulic transformation where it exists.

## Primary experimental evidence: Sellevold et al. 2024

Sellevold, Norem, Bruland, Rüther, and Pummer experimentally investigated idealised bottom-up
blockage at circular pipe culvert inlets. The tested inlet families included square-edge and
socket-edge headwalls, two bevel arrangements, socket and thin-wall projecting inlets, and a
mitered inlet. The paper compares the experiments with the traditional energy loss method (ELM)
and reduced area method (RAM), then develops regression relationships from the measurements.

### Outlet-control pressure flow

For the tested non-mitered inlets, the paper represents the blocked entrance coefficient with a
linear relationship of the form

```text
k_eb = k_e + beta * (A_b / A)
```

where `A_b / A` is blocked area divided by clean pipe area. The mitered inlet uses a separate
quadratic relationship. The authors recommend conservative use of the maximum fitted
coefficient where in-situ blockage variability cannot be known exactly.

The experiments show why the older ARR ELM should not be treated as exact physical truth for
these cases: ELM overpredicted blocked entrance coefficients by as much as about 124% in the
reported comparisons. The new source-specific regressions generally followed the physical
measurements much more closely.

The paper states that the pressure-flow entrance-coefficient results can be applied to the
corresponding outlet-control pressure-flow states (USGS flow Types 4, 6, and 7). It explicitly
does **not** extend the method to outlet-control Types 2 and 3. Any implementation in this
library must map those source flow types to the library's physical regime classification before
using a coefficient; matching by enum name is not sufficient.

### Inlet control

For submerged inlet-control Type 5 conditions, the measured discharge ratio is represented by

```text
Q_b / Q = 1 - A_b / A
```

within the experimental uncertainty for the tested bottom-up blockages. The paper evaluates this
relationship over the reported high-head range approximately

```text
1.3 < H'_w / D < 3.0
```

for the blockage-ratio analysis. The source must not be silently extrapolated below or above that
range.

The paper also includes inlet-control measurements beyond this single Type 5 ratio, including
Type 1 behaviour. The first implementation should nevertheless remain narrower: do not claim a
generic Type 1 method until the exact source relationship, inlet identity, dimensional
definitions, and fixtures have been transcribed and reviewed independently.

The paper reports that the traditional RAM can underpredict `Q_b / Q` by up to about 38% in
the Type 5 comparisons. That again makes RAM useful as conservative legacy/comparison evidence,
not as a reason to reduce the entire pipe geometry.

### Validation limits

The validation is not shape-agnostic. It is limited to the tested circular pipe inlet
configurations and idealised bottom-up obstruction. In particular:

- do not transfer its regression coefficients to rectangular or filleted-rectangular culverts;
- do not treat a top-down floating raft as bottom-up sediment merely because the blocked area is
  the same;
- do not apply the local-inlet regression to a deposit extending along the barrel;
- do not apply it to a porous plug without separate evidence; and
- do not assume a similarly named existing inlet coefficient is geometrically identical to the
  laboratory inlet.

The paper's reported experimental uncertainty provides a useful validation envelope. For the
outlet-control entrance-coefficient dataset, the largest reported measurement uncertainty across
the tested inlet families is about 10.4%, while reported regression errors are lower. For the
Type 5 blockage-ratio comparison, the source reports inlet-specific uncertainty values up to
about 9%. Those values are validation evidence for their measured quantities; they are **not** a
general accuracy claim for culvert headwater results.

## Proposed scenario model

The names below are conceptual API boundaries for a later implementation. They are not yet a
public API commitment.

```text
BlockageScenario
├── EntranceBlockage
├── BarrelObstruction
├── DebrisScreen
└── OutletObstruction
```

A non-zero blockage scenario should retain at least:

- a mandatory `scenario_source: SourceReference` describing why the scenario extent was
  selected, including a project design basis when no publication applies;
- an explicit physical mechanism such as `bottom_up_depositional`,
  `top_down_floating`, `porous_plug`, or `mixed`;
- `blocked_area_fraction`, validated on `0 <= f <= 1`;
- an obstruction geometry/extent descriptor sufficient to reproduce where the blocked area lies,
  rather than only its scalar area;
- location-specific data, including longitudinal start/end where the obstruction extends into the
  barrel;
- porosity where the adopted method uses it;
- timing/extent metadata when the scenario is derived from an event or ARR risk procedure; and
- an optional user/project label suitable for result provenance.

The hydraulic resolver should then produce or retain a distinct `method_source` for the adopted
hydraulic transformation. This separation matters. For example, ARR Stage 2 may be the source
for a 25% bottom-up design scenario while Sellevold et al. is the source for how that specific
circular inlet responds hydraulically.

The resolved result should retain the original scenario, the hydraulic method identity, both
sources, derived open area, any method-specific effective coefficients, and structured
applicability warnings. Reconstructing the scenario from a changed headwater after the solve is
not acceptable provenance.

### Why `blocked_area_fraction` should be the public scalar

ARR Stage 1 uses `BR` to mean the **open** free-area ratio. Some secondary implementation
documentation has described "blockage ratio" in a way that conflicts with that convention while
still using values such as 0.9 for 10% blockage. The public library should avoid this ambiguity:

```text
blocked_area_fraction = blocked_area / clean_area
open_area_fraction = 1 - blocked_area_fraction
```

Source-specific equations may internally translate to their own notation.

## Hydraulic interaction rules

### Localised entrance blockage

A blockage physically confined to the inlet face changes the inlet hydraulic relation. It does
not, by itself, make the downstream barrel smaller.

For **outlet control**, the supported method may resolve a blockage-specific entrance-loss
coefficient. The friction calculation must continue to use the clean barrel geometry and
roughness unless a separate barrel obstruction exists.

For **inlet control**, the blockage modifies the inlet head-discharge relationship. It must not
be represented by both a discharge factor and a reduced barrel geometry for the same local
obstruction.

### Barrel obstruction

A solid or effectively impermeable deposit extending along the barrel changes the actual
cross-section available to flow. A defensible model therefore needs the obstructed shape and its
longitudinal extent so that area, wetted perimeter, hydraulic radius, conveyance, critical depth,
normal depth, and profile calculations use the appropriate section.

The current solver assumes a prismatic barrel for its principal geometry. Until segmented
obstructed geometry can be routed consistently, a longitudinal barrel obstruction should fail
closed rather than being approximated by:

- increasing Manning roughness;
- applying an inlet `Ke`;
- multiplying final discharge by an efficiency factor; or
- reducing the geometry along the entire barrel when the source says the obstruction is local.

Full-length permanent embedment overlaps conceptually with CS-032 / issue #22, but a blockage
scenario must not silently reuse buried-invert assumptions unless geometry, material, and
applicability are genuinely the same.

### Screens and debris racks

Screens require their own structure type and geometry. At minimum an adopted screen model needs
screen location, gross area, net open area or bar area ratio, debris-blocked area, and the source
of those assumptions.

ARR Stage 1 supplies an important loss-accounting rule:

- a separated upstream screen can have a screen loss plus a clean culvert entrance loss;
- a screen attached to the inlet needs a combined screen/entry relationship and must not receive
  both losses independently;
- an outlet screen has a distinct exit relationship; and
- a screen well downstream is not reducible to the inlet equations.

These cases should therefore fail closed until a dedicated screen component is implemented and
tested. They must not be accepted by an `EntranceBlockage` constructor merely because a
blocked fraction is available.

### Downstream or outlet debris

A generic obstruction at the outlet can alter the outlet boundary, expansion/exit loss, local
geometry, or tailwater interaction. The reviewed evidence does not justify treating arbitrary
outlet debris as an inlet blockage coefficient.

An explicitly configured outlet screen may later use its source-specific screen formulation.
Other outlet debris should remain unsupported until an arrangement-specific method and
validation evidence are recorded.

### Roadway overtopping

Culvert blockage must not directly multiply or reduce roadway broad-crested-weir discharge.
Instead, blockage changes culvert capacity and therefore the common crossing headwater. The
existing crossing solution can then route additional flow over the roadway when overtopping is
active.

ARR Stage 2 recommends severe blockage consideration in important overtopping/flood-immunity
assessments. That guides which blockage scenario is run; it does not change the roadway weir
coefficient. Debris caught on handrails or traffic barriers is a separate roadway-obstruction
problem and is outside this initial culvert blockage scope.

## Multi-barrel structures

The current `CulvertGroup` represents hydraulically identical parallel barrels through a
representative equal-flow barrel. A blockage that differs between cells breaks that identity.

The first implementation must therefore use one of these behaviours:

- apply the exact same blockage scenario to every barrel in the group; or
- represent differently blocked cells as separate groups with explicit scenarios, where the
  crossing model can support that representation.

It must not average a 100% blocked cell and an unblocked cell into a single "50% blocked"
representative barrel. That would change both the physical mechanism and equal-flow assumption
without preserving provenance.

## Initial support matrix

| Scenario | Geometry/state | Research disposition |
| --- | --- | --- |
| Zero blockage | All currently supported clean geometries/regimes | Must be exact identity with current solver |
| Local bottom-up entrance blockage | Circular pipe, source-matched inlet, outlet-control pressure flow corresponding to source Types 4/6/7 | Candidate for first implementation using Sellevold et al. source-specific regression |
| Local bottom-up entrance blockage | Circular pipe, source-matched inlet, submerged inlet-control Type 5 and source head range | Candidate for first implementation using the source discharge-ratio relationship |
| Local bottom-up entrance blockage | Circular pipe, inlet-control Type 1 | Defer until exact source relationship and fixtures are transcribed |
| Local bottom-up entrance blockage | Circular pipe, outlet-control Types 2/3 | Fail closed; primary paper says the blocked entrance-loss method is not valid for these states |
| Local entrance blockage | Rectangular or filleted rectangular | Fail closed initially; no equally strong reviewed physical validation |
| Top-down floating/raft blockage | Any current geometry | Fail closed initially; area fraction alone does not represent the mechanism |
| Porous plug or mixed debris | Any current geometry | Fail closed initially |
| Longitudinal barrel obstruction | Any current geometry | Fail closed until segmented obstructed geometry is supported |
| Upstream/inlet/outlet screen | Explicit screen geometry | Separate future component using arrangement-specific equations; not generic entrance blockage |
| Screen well downstream | Any | Fail closed; source identifies materially more complex hydraulics |
| Generic outlet debris | Any | Fail closed until arrangement-specific method is adopted |
| Non-uniform blockage among barrels in one representative group | Multi-barrel | Split into explicit groups where valid or fail closed; never average the blockage |

"Candidate for first implementation" means the evidence is sufficient to design an implementation.
It does not mean the current solver supports the case.

## Exact inlet identity requirement

The current HDS-5 catalogue contains labels such as "Circular Concrete, Square edge with
headwall", "Groove end with headwall", generic mitered CMP, and projecting CMP. Sellevold et al.
tested physically defined inlet geometries, including bevel ratios, socket/projecting
configurations, projection details, and a specific mitered slope.

Those names are not enough to prove equivalence. An implementation must either:

1. introduce a typed source geometry/configuration identity that exactly matches a tested inlet;
   or
2. create an explicit reviewed mapping record showing that the existing configuration has the
   same geometry required by the blockage source.

Material or clean-culvert `Ke` alone is not an inlet identity. Regression coefficients must not
be selected merely because the clean loss coefficient is numerically similar.

## Validation and test plan

Validation must distinguish software fidelity from hydraulic validation.

### Equation and transcription fidelity

Tests that reproduce an adopted equation or a published table value should use ordinary strict
floating-point tolerances, for example relative tolerances on the order of `1e-12` for simple
closed-form algebra and a suitably tight tolerance for regression evaluation. Passing these tests
proves transcription/calculation fidelity only.

ARR Stage 1 candidate checks include:

- Equation 4.2 at several clean-`Kc` and open-area ratios;
- Equation 4.3 and Table 4.1 values;
- the limiting identity at zero blockage; and
- the explicit complete-blockage limit without evaluating a divide-by-zero form.

### Published experimental validation

For Sellevold et al. fixtures, compare the quantity actually validated by the source:

- blocked entrance-loss coefficient for the outlet-control regression; and
- blocked/unblocked discharge ratio for Type 5 inlet control.

Use source-specific published uncertainty/error by inlet where available. Do not invent a
headwater tolerance from a coefficient uncertainty. The paper reports outlet-control
measurement uncertainty up to about 10.4% across its inlet families and Type 5
blockage-ratio uncertainty up to about 9%; these are upper envelopes, not universal solver
tolerances. Fixture metadata should carry the actual applicable source value.

### Limiting and behavioural tests

A later implementation should include at least:

- `blocked_area_fraction == 0` produces the exact existing clean hydraulic path;
- an impermeable 100% entrance blockage produces explicit zero culvert capacity rather than a
  hidden epsilon/open-area clamp;
- supported blockage response is monotonic over its published range where the source method
  guarantees monotonicity;
- unsupported shape, inlet identity, mechanism, location, or hydraulic regime raises a clear
  engineering input/applicability error;
- a local entrance blockage leaves barrel area, wetted perimeter, Manning roughness, and
  friction geometry unchanged;
- a barrel obstruction cannot be accepted without longitudinal extent;
- an attached screen cannot receive both separate screen and entrance blockage losses;
- results retain scenario source, method source, resolved blockage extent, and applicability
  notices;
- a multi-barrel group rejects or separates non-identical blockage states rather than averaging
  them; and
- roadway discharge changes only through the common-headwater/capacity interaction, not through
  a blockage multiplier applied to roadway flow.

### Independent comparison

TUFLOW's RAM/ELM implementation is useful as a secondary comparison for legacy ARR equations.
It must not define acceptance when it conflicts with the source or physical validation. Its
2026.0 ELM documentation states that `BR = 1` is unblocked and tabulates `BR = 0.9` for 10%
blockage, consistent with ARR's open-area ratio, despite an adjacent prose definition that calls
`BR` blocked area divided by unblocked area. The ARR source definition governs. TUFLOW also
uses a minimum `BR` of 0.001 to avoid division by zero; this numerical clamp should not become a
physical library rule. A fully impermeable blockage should be represented explicitly as zero
culvert capacity for a method that supports that limiting state.

HY-8 is not currently identified as a primary blockage-method source for this task. Do not add a
HY-8 parity requirement unless a version-pinned blockage feature and its method documentation
are first identified.

## Public API and engineering limitations

The public API should make unsupported physics difficult to express accidentally.

A later implementation should therefore:

- avoid a generic `capacity_factor`, `efficiency`, or roughness-based blockage input;
- require a provenance-bearing scenario source for every non-zero blockage scenario;
- use discriminated scenario records rather than a bag of optional fields;
- resolve a hydraulic method only after exact shape/inlet/mechanism/regime applicability checks;
- retain the original scenario and resolved method in `BarrelHydraulicResult` and aggregate
  provenance without loss at group/crossing level;
- emit structured applicability notices for supported-but-bounded methods;
- raise an explicit error for unsupported combinations instead of silently reverting to an
  unblocked calculation or a generic reduced-area approximation; and
- document that static design scenarios do not simulate debris arrival, accumulation, washout,
  or changing porosity during a hydrograph.

Issue #18 requires the blockage source to be explicit. That is intentionally stricter than the
general optional provenance policy for some existing user overrides.

## Recommended implementation order

1. Add typed scenario/provenance records with no hydraulic effect and identity tests.
2. Add exact inlet-geometry identity/mapping required by the selected circular experimental
   fixtures.
3. Implement the narrow circular bottom-up entrance method for source-supported pressure-flow
   outlet control.
4. Add the bounded Type 5 inlet-control relationship.
5. Add result provenance and applicability warnings through barrel, group, crossing, rating, and
   inverse-capacity paths.
6. Add published validation fixtures and unsupported-case tests before broadening the method.
7. Treat screens, longitudinal barrel obstructions, rectangular inlet blockage, floating debris,
   porous plugs, and generic outlet obstruction as separate follow-on work, each with its own
   evidence gate.

No step should introduce a legacy ARR RAM/ELM fallback for unsupported cases merely to return a
number.

## References

- Weeks, W., Barthelmess, A., Rigby, E., Witheridge, G. and Adamson, R. (2009),
  *ARR Revision Project 11: Blockage of Hydraulic Structures, Stage 1 Report*,
  P11/S1/007. See Section 4, especially printed pages 45-51.
  https://www.arr-software.org/pdfs/ARR_Project11_Stage1_report_Final.pdf
- Weeks, W. and project contributors (2013), *ARR Revision Project 11: Blockage of
  Hydraulic Structures, Stage 2 Report*, P11/S2/021. See Section 2.5 and Table 3.16,
  especially printed pages 17-19 and 44-45.
  https://www.arr-software.org/pdfs/ARR_Project11_Stage2_Final.pdf
- Ball, J. et al. (eds.) (2019), *Australian Rainfall and Runoff*, Book 6,
  Chapter 6, "Blockage of Hydraulic Structures".
  https://www.arr-software.org/pdfs/ARR_190514_Book6_V4.1.pdf
- Sellevold, J., Norem, H., Bruland, O., Rüther, N. and Pummer, E. (2024),
  "Effects of Bottom-Up Blockage on Entrance Loss Coefficients and Head-Discharge
  Relationships for Pipe Culvert Inlets: Comparisons of Theoretical Methods and
  Experimental Results", *Journal of Irrigation and Drainage Engineering*, 150(2),
  04023038. https://doi.org/10.1061/JIDEDH.IRENG-10219
- Bradley, J.B., Richards, D.L. and Bahner, C.D. (2005), *Debris Control Structures -
  Evaluation and Countermeasures*, Hydraulic Engineering Circular 9, third edition,
  FHWA-IF-04-016.
  https://www.fhwa.dot.gov/engineering/hydraulics/library_arc.cfm?id=23&pub_number=9
- Schall, J.D., Thompson, P.L., Zerges, S.M., Kilgore, R.T. and Morris, J.L. (2012),
  *Hydraulic Design of Highway Culverts*, third edition, FHWA-HIF-12-026.
  https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf
- Ollett, P., Syme, B. and Ryan, P. (2017), "Australian Rainfall and Runoff guidance on
  blockage of hydraulic structures: numerical implementation and three case studies",
  *Journal of Hydrology (New Zealand)*, 56(2), 109-122.
  https://www.hydralinc.com/wp-content/uploads/JoHNZ-V56-2-2017-ARR-Blockage-Ollett-Ryan-Syme.pdf
- French, R. and Jones, M. (2018), "Design for culvert blockage: the ARR 2016 guidelines",
  *Australasian Journal of Water Resources*, 22(1), 84-87.
  https://doi.org/10.1080/13241583.2018.1477268
- TUFLOW (2026), *TUFLOW Classic/HPC User Manual 2026.0*, structures/blockage
  documentation. Secondary implementation evidence only.
  https://docs.tuflow.com/classic-hpc/manual/2026.0/Structures-2.html

## Remaining research gaps

Before broadening support beyond the narrow first implementation, further primary evidence is
needed for:

- rectangular and filleted-rectangular inlet blockage;
- top-down floating debris and time-dependent raft position;
- porous and mixed debris plugs;
- obstruction geometry and losses through non-prismatic/segmented barrels;
- outlet debris that is not a defined screen/rack;
- screen/rack validation beyond the analytical ARR Stage 1 relationships; and
- field validation tying design blockage scenarios to peak-event blockage rather than
  post-event observations.

These gaps should remain explicit issues or unsupported configurations. They must not be filled
with an undocumented engineering judgement inside the hydraulic core.
