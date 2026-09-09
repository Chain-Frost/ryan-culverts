# References and review register

Reviewed through 2026-09-09. This register distinguishes transcription checks, methodology
review, discovery, and pending engineering acceptance. Implemented coefficient values
have been checked against HDS-5, but no combined solver is externally validated.

## Research gate status

Phase 0 Research Gate (CS-001) is **complete**. Completion means that the applicable
source sections, method decisions, fixture inputs, and unresolved conflicts have been
recorded. It does not mean that every deferred geometry is implemented or that the
combined solver is engineering-validated. The reviewed findings include:

- HDS-5 inlet transition must be smooth and tangent, not linearly interpolated.
- `tailwater_depth >= rise` does not unconditionally force full barrel flow.
- Hydraulic jumps are required for complete Type 1/5 treatment.
- Mixed free-surface/pressurised profile logic is needed for Type 6/7. The executable
  HY-8 matrix now contains both types, with Type 6 retained as an unresolved comparison.

Primary copies of Bodhaine, corrected FHWA-HRT-06-138, NCHRP 734, HDS-5, the HY-8
8.0 user manual, and Austroads AGRD05B-23 are available under `reference_docs/`.
The selected worked examples and their applicability are recorded in
[`research/fixture_candidates.md`](research/fixture_candidates.md). Review is not the
same as adoption: unsupported geometry and context remain explicit future tasks.

| Source | Review status | Computational disposition |
| --- | --- | --- |
| FHWA HDS-5, third edition | Reviewed | Adopted primary hydraulic baseline within documented scope |
| Bodhaine, TWRI 3-A3 | Reviewed | Adopt flow-type physics and terminology; retain worked examples as historical-method comparisons |
| Corrected FHWA-HRT-06-138 | Reviewed | Configuration-specific box evidence; defer executable catalogue to CS-013 |
| NCHRP Report 734 | Reviewed | Adopt representative-barrel limitation; defer context-dependent refinements to CS-014 |
| HY-8 embedded-coefficient correction note | Reviewed | Reject original NCHRP embedded coefficients as executable; treat adjusted curves as secondary HY-8 implementation evidence |
| HY-8 User Manual v8.0 and executable 8.0.1.2 | Reviewed | Version-pinned implementation comparison, never hydraulic authority |
| Austroads AGRD05B-23 edition 1.2 | Reviewed | Adopt Australian workflow/reporting context; do not replace HDS-5 equations |
| Current MRWA guidance listed below | Reviewed | Adopt jurisdiction-specific defaults and application notices where implemented |
| HEC-RAS 7.0 technical reference | Reviewed | Independent methodology comparison; apparent inlet-page transcription rejected |
| EPA SWMM source at `07c371f8` | Reviewed | Secondary implementation comparison; code reuse not licensed |
| STREAM-1D at `32ede6fb` | Reviewed | Secondary architecture/method comparison |
| `alejandroechev/culvertflow` at `5a5ac50c` | Reviewed | Secondary implementation only; no code imported |
| Supplied agent research reports | Reviewed; rejected as authority | Discovery leads only; embedded tool citations are not durable evidence |

Every PDF found under `reference_docs/` and `hy8/`, including duplicates and adjacent
future-scope material, is classified and hash-pinned in the
[`local evidence inventory`](research/local_evidence_inventory.md). Later phases must
not be labelled engineering-verified merely because the research gate is complete.

## Primary publications

### FHWA-HDS5-2012

Schall, Thompson, Zerges, Kilgore and Morris (2012), *Hydraulic Design of Highway
Culverts*, third edition, FHWA-HIF-12-026, April 2012. [Official PDF][hds5].

Inspected the local PDF title/report pages; Section 3.1.4, printed pages 3.9–3.12
(PDF pages 91–94); flow types and profiles in Section 3.5, printed pages 3.36–3.43
(PDF pages 118–125); inlet equations and transition discussion in Appendix A
(PDF pages 190–196); inlet constants in Table A.1 (PDF page 197); resistance guidance
and Manning values in Appendix B/Table B.1 (PDF pages 203–208); and entrance losses in
Table C.2 (PDF page 216). These sections support transcription checks and also expose
remaining gaps in mixed-flow profiles and hydraulic-jump handling.

HDS-5 printed pages 3.36-3.37 (local PDF pages 118-119) state that HY-8 Version 7.3
introduced momentum calculations to determine whether the conjugate depth of an S2
profile intersects an S1 profile inside the barrel. If it does not, the jump is treated as
swept out and S2 determines outlet velocity. The implementation first tests the S2 outlet,
then intersects the backward S1 profile with the S2 conjugate-depth envelope to locate an
in-barrel `JS1` jump. Both swept-out and in-barrel cases are compared with HY-8 8.0.1.2;
an independent published numerical jump-location fixture is still required.

HDS-5 Appendix A, printed page A.1, says the inlet transition is drawn between and tangent
to the unsubmerged and submerged equation curves; printed page A.6 says the nomograph
transition was drawn by hand. It does not specify a digital interpolation algorithm. The
implemented cubic Hermite bridge is the project's adopted deterministic interpretation: it
matches both endpoint values and tangents, including the Form 1 critical-head derivative,
but is not represented as HY-8's polynomial method or an exact reconstruction of the
hand-drawn curve. Printed pages A.2-A.4 provide the equation definitions and independently
reproduced dimensionless example values used by the tests. The local `hif12026.pdf` is the
inspected copy; the official URL is retained below.

### FHWA-BOX-2006

*Effects of Inlet Geometry on Hydraulic Performance of Box Culverts*,
FHWA-HRT-06-138, October 2006. [Official corrected PDF][box-report].

Inspected the report landing page, errata notice, and electronic report. The errata
confirms that Tables 1, 2, 3, 4, 7–12, and 17–18 were replaced after initial publication.
The corrected electronic Tables 11 and 12 (printed pages 85–86; local PDF pages 98–99)
have been checked against `research/fhwa_box_inlets.md`. Printed pages 72–73 (local PDF
pages 85–86) limit the fifth-order polynomials to approximately `0.4 < HW/D < 2.3`
and warn of numerical errors outside that range. HY-8 v8.0 manual page 45 says HY-8
therefore recomputed South Dakota box coefficients for its required `0.5 <= HW/D <=
3.0` range; the two polynomial sets are not interchangeable.

Appendix D, printed pages 127–140 (local PDF pages 140–153), was reviewed and the
FC-D-30 `Q25`/`Q100` cases were selected in `research/fixture_candidates.md`. The
current geometry cannot reproduce their corner fillets and bevel, so CS-013 owns typed
configuration support. Do not infer that coefficients for one span-to-rise ratio, bevel,
fillet, skew, or multi-barrel configuration apply universally.

### USGS-BODHAINE-1968

G. L. Bodhaine (1968), *Measurement of Peak Discharge at Culverts by Indirect
Methods*, Techniques of Water-Resources Investigations, book 3, chapter A3.
DOI: [10.3133/twri03A3][bodhaine].

General classification and computational discussion were accessed and reviewed.
Bodhaine classifies six flow types using control location and relative headwater/tailwater.
Key findings from the review:

- Types 1, 2, 3: low-head regime, outlet submergence not complete.
- Type 1: critical control near inlet, steep barrel, partly full.
- Type 2: critical depth at outlet, mild barrel, partly full.
- Type 3: backwater-controlled, tranquil/subcritical; can occur on **any** slope.
- Type 4: both ends submerged, barrel full.
- Type 5: high head, inlet submerged, rapid contracted flow, partly full.
- Type 6: high head, free outfall, barrel full under pressure.
- "Unusual conditions" section warns that Type 3 can occur on steep slopes.

All ten worked examples on printed pages 52–60 (local PDF pages 61–69) were reviewed.
Their final discharges and four selected input records are transcribed in
`research/fixture_candidates.md`. The examples use Bodhaine's historical coefficient
charts and indirect-measurement method, so they are classification and method-
reproduction evidence rather than HDS-5 acceptance values. Do not equate extended
software flow labels with this original classification.

### NCHRP-734-2012

*Hydraulic Loss Coefficients for Culverts*, NCHRP Report 734 (2012).
DOI: [10.17226/22673][nchrp].

The full local report and applicable Chapters 2–5, 7, and 8 were reviewed. It addresses
entrance loss, exit loss, buried-invert/embedded culverts, slip-lined culverts,
multi-barrel effects, depth-dependent roughness, and composite roughness.

Key findings:

- Confirms the conventional outlet-control energy framework.
- Supports representative-barrel superposition for most total-flow cases, while
  documenting approach-flow and individual-barrel differences relevant to local design.
- Chapter 4, printed page 30 (local PDF page 38), supports a context-dependent
  Borda-Carnot sudden-expansion exit loss and reports `6.43 ft` upstream depth versus
  `6.93 ft` using `Ko = 1.0` for its example. That refinement requires downstream
  channel area and is not adopted for the current reservoir/pool boundary.
- Chapter 7, printed page 67 (local PDF page 75), shows that constant Manning `n`
  becomes less defensible as boundary roughness increases and hydraulic radius decreases.
- Chapter 8, printed pages 68 and 78 (local PDF pages 76 and 86), recommends the Horton
  composite-roughness relationship only as an approximate first-order option and finds no
  single robust relationship for all tested configurations.

The coefficient extraction is documented in `research/nchrp734_coefficients.md`.
Tables 3-1 and 3-2 repeat the `2-in. projecting, tapered` label for their final row, but
the preceding narrative identifies the `Ke = 0.70` condition as the 4-in projection.
The HY-8-bundled 2019 note *Reviewing Coefficients in Embedded Circular Culverts from
NCHRP Report 734* additionally identifies a mathematical error in the original embedded-
culvert dimensionless discharge and false data for the 50% embedded beveled case. Its
replacement polynomial extends experimental data using an HY-8 unembedded trend to
stabilise the curve, so it is secondary implementation evidence rather than a correction
to adopt silently. CS-014 must represent source status as well as slipline, downstream-
channel, or composite-roughness context before any corresponding coefficient or equation
is executable.

### HEC-RAS technical reference

Inspected the current online [outlet][hec-outlet] and [inlet][hec-inlet] pages;
navigation identifies version 7.0. Links use `latest`, so pin the version before
formal method sign-off. Outlet calculations are energy based. The inlet page
uses English units and has an apparent submerged-equation transcription error.
Neither its HTML equation text nor a software result replaces a typeset source.

### Australian application guidance

[Austroads AGRD05B-23][austroads]: *Guide to Road Design Part 5B: Drainage – Open
Channels, Culverts and Floodway Crossings*, edition 1.2, 30 January 2023.
The full local text was reviewed for the open-channel assumptions and equations in
Section 2.3, culvert scope and hydraulic design in Sections 3.4–3.14, and the design
example in Section 3.15.1 (printed pages 101–106; local PDF pages 111–116).
Austroads supplies Australian design workflow, allowable-headwater, blockage, velocity,
scour and reporting context; HDS-5 remains the project's hydraulic method baseline.
The Section 3.15.1 example is not a strict numerical fixture because it first states
full-flow velocity `2.5 m/s`, then tabulates `2.75 m/s` and uses the latter to obtain
`3.08 m/s`. CS-015 records the required source clarification.

[MRWA supplement to Part 5B][mrwa]: inspected the live page, version 1F,
3 July 2020. Relevant to local culvert types and site/design information.
Full Australian design-compliance review is not complete; hydraulic solver
validation alone will not certify an entire road-drainage design.

[MRWA culvert design procedure][mrwa-culvert-design]: inspected the live Section 2.8
and Tables 2.1-2.2 on 8 September 2026, version 2E, 5 May 2026. Table 2.1 gives
distinct smooth concrete-pipe and concrete-box ranges. Table 2.2 gives
diameter- and corrugation-specific Manning values for helically wound CSP and attributes
them to AISI (1999). The Part 5B supplement directs designers to manufacturer information
first and Table 3.1 (the same values) when it is absent. The typed CSP lookup uses
these values and rejects combinations marked unavailable. Plastic-pipe values must
come from the applicable manufacturer; any future HY-8 plastic value is a documented
fallback, not an MRWA value. The implemented resolver separates concrete pipe and box,
requires manufacturer plastic data by default, and attaches source-bearing notices to an
explicitly requested HDS-5 plastic fallback.

[MRWA Specification 404][mrwa-spec404]: issued 17 July 2026, reviewed 6 September 2026.
For spirally wound corrugated steel pipe: 68 × 13 mm corrugations up to and including
1500 mm diameter; 125 × 25 mm for 1650–2100 mm. Steel thickness varies 2.0–3.0 mm by
diameter. Plastic flexible culverts are a contract-specific provision, limited to PE
only, with roughness from manufacturer data. A hydraulic Table 2.2 lookup does not
establish current Spec 404 construction compliance.

## Reference implementations

### EPA SWMM

Inspected [`culvert.c` at pinned commit `07c371f8`][swmm], header build 5.2.0 (2021-11-01).
This routine limits conduit flow for inlet control. It carries explicit equation
forms and configuration-specific coefficients. Important findings:

- SWMM uses the submerged criterion `Q/(A sqrt(D)) > 4`.
- For the lower transition bound, SWMM uses an arbitrary 0.95 full-depth head criterion
  because converting the FHWA 3.5 discharge criterion to a prior head limit is difficult
  for Form 1.
- It linearly interpolates **flow versus head** between its two head bounds.
- Therefore SWMM does **not** justify linear interpolation of `HWi/D` versus `q*`.

It is not a complete independent culvert/profile solver. Pin repository revision and
check tables against FHWA before reuse.

**Licence status:** repository metadata at the reviewed revision did not identify a
machine-readable licence and no root `LICENSE` file was found. Code reuse is **not
cleared** until applicable EPA/public-domain terms are confirmed. Algorithmic comparison
is permitted.

### STREAM-1D

Inspected the [repository at pinned commit `32ede6fb`][stream]. MIT licence confirmed.
Useful architectural ideas:

- Steady GVF engine separated from Python interface.
- Standard-step reach solver.
- Structured culvert diagnostics.
- Verification cases against HEC-RAS.

Cautions: README inlet-control documentation uses a linear transition over `F` range
of 3.0 to 4.0, which differs from HDS-5's 3.5/4.0 and is not authoritative. It is a
secondary implementation, not a hydraulic source. Reuse only after auditing the exact
source file and tests for the feature being considered.

### HY-8

The local User Manual v8.0 was reviewed at pages 44–45 and 68–73 for coefficient
selection, inlet polynomials, control selection, flow types, and direct-step profile use.
The installed executable is separately pinned at file/product version `8.0.1.2` and
SHA-256 `0b1c5e7fb6b48be9c675b5486ae9a84346f436c5c649aa5ed09a1552267ee806`.
The installed and repository `ShapeDB.dat` hash is
`2479e9444feaff529313e18a1b26fc2de4f6b6c541db58477da6bebc602164a7`;
the installed and repository manual hash is recorded in the local evidence inventory.
The v8.0 manual documents method families but is not relabelled as patch-specific
8.0.1.2 documentation. Executable observations remain version-specific evidence.

[HY-8 Insider Article 15][hy8-insider-15], published by HY-8 developer Eric Jones on
21 April 2021, documents the Culvert Summary Table and specifically explains that `*`
marks a negative computed outlet-control depth that HY-8 replaces with `0.0`. Treat this
as developer documentation for report interpretation, not as a primary hydraulic-method
source. The installed manual does not define the `**` inlet-depth marker. Testing against
HY-8 8.0.1.2 places its onset at approximately inlet-control `HW/D > 10`; that is retained
as version-specific observed behaviour rather than a cross-version contract.

HDS-5 Section 3.5.2, printed page 3.39 (local PDF page 121), independently states that
the laboratory inlet curves apply over `0.5 <= HW/D <= 3.0` and that a general orifice
equation fitted at `HW/D = 3.0` is used above that range. This primary-method limitation,
not HY-8's undocumented marker threshold, drives the local high-head applicability
warning. The direct Equation A.3 result remains available, but it is explicitly identified
as an extrapolated project method above `HW/D = 3`; a second review warning is added above
the conservative `HW/D = 10` extreme-head threshold.

## alejandroechev/culvertflow

User-supplied repository: [alejandroechev/culvertflow][external-culvertflow].

Reviewed the README and selected engine sources on the `master` branch. The reviewed
revision is pinned to `5a5ac50ca4c926b20e4f078dc0bcda2d43c3490e` as resolved on
2026-09-09; links below use that revision.

The [README](https://github.com/alejandroechev/culvertflow#readme) describes a
TypeScript hydraulic engine separated from a browser UI, rating curves, and inlet
coefficient tables. It states MIT licensing; verify the applicable licence text
and attribution before copying any code. No code has been imported.

Useful as a secondary implementation reference for module separation, coefficient
organisation and eventual reporting ideas. It is not a primary hydraulic authority
or a validated benchmark for this project.

Specific observations from the source:

- [Outlet control](https://github.com/alejandroechev/culvertflow/blob/5a5ac50ca4c926b20e4f078dc0bcda2d43c3490e/packages/engine/src/outlet-control.ts)
  uses feet/cfs and a fixed critical-depth approximation of `0.6 * D`; it does not
  solve a free-surface profile in that function. Review equations against primary
  references and derive SI forms before considering any adaptation.
- [Controlling headwater](https://github.com/alejandroechev/culvertflow/blob/5a5ac50ca4c926b20e4f078dc0bcda2d43c3490e/packages/engine/src/controlling.ts)
  simply selects the maximum of inlet and outlet headwaters. This does not implement
  the physical-consistency checks required by Phase 6 of our plan.
- [Coefficient tables](https://github.com/alejandroechev/culvertflow/blob/5a5ac50ca4c926b20e4f078dc0bcda2d43c3490e/packages/engine/src/reference.ts)
  provide a compact shape/inlet mapping, but lack the edition, equation/table and
  applicability metadata required by our plan. Elliptical entries repeat circular
  values; validate each relationship independently before use.

This limited source review did not execute the project, validate its coefficients,
or audit its complete test suite. It does not change the decision to retire our
old `culvertflow` package; the similarly named external project is a separate codebase.

The HDS-5 friction-unit audit adds another caution: the inspected English-unit
outlet implementation uses 19.63, whereas HDS-5 equation 3.4b assigns 29 to English
units and 19.63 to SI. Do not adopt its loss results as reference values.

[hds5]: https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf
[box-report]: https://highways.dot.gov/sites/fhwa.dot.gov/files/FHWA-HRT-06-138.pdf
[bodhaine]: https://pubs.usgs.gov/publication/twri03A3
[nchrp]: https://www.nationalacademies.org/publications/22673
[hec-outlet]: https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/modeling-culverts/culvert-hydraulics/computing-outlet-control-headwater
[hec-inlet]: https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/latest/modeling-culverts/culvert-hydraulics/computing-inlet-control-headwater
[austroads]: https://austroads.gov.au/publications/road-design/agrd05b
[mrwa]: https://www.mainroads.wa.gov.au/technical-commercial/technical-library/road-traffic-engineering/guide-to-road-design/mrwa-supplement-to-austroads-guide-to-road-design-part-5b/
[mrwa-culvert-design]: https://www.mainroads.wa.gov.au/technical-commercial/technical-library/road-traffic-engineering/drainage-waterways/culverts/design-procedure/
[mrwa-spec404]: https://www.mainroads.wa.gov.au/globalassets/technical-commercial/technical-library/specifications/400-series-drainage/specification-404-culverts.pdf
[swmm]: https://github.com/USEPA/Stormwater-Management-Model/blob/07c371f8a0d477da1d9d4e7c0d75719664f62fec/src/solver/culvert.c
[stream]: https://github.com/jlillywh/STREAM-1D/tree/32ede6fb1e211db97c76cc82d1cf0a80eb8a55a0
[hy8]: https://www.fhwa.dot.gov/engineering/hydraulics/software/hy8/
[hy8-insider-15]: https://www.linkedin.com/pulse/hy-8-insider-article-15-culvert-barrel-results-eric-jones-p-e-/
[external-culvertflow]: https://github.com/alejandroechev/culvertflow
