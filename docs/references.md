# References and review register

Reviewed 2026-09-06. This register distinguishes transcription checks, methodology
review, discovery, and pending engineering acceptance. Implemented coefficient values
have been checked against HDS-5, but no combined solver is externally validated.

## Research gate status

Phase 0 Research Gate (CS-001) is **in progress**. The supplied research reports
and primary PDFs materially advance it, but the reports themselves do not support
a completion claim. The reviewed findings include:

- HDS-5 inlet transition must be smooth and tangent, not linearly interpolated.
- `tailwater_depth >= rise` does not unconditionally force full barrel flow.
- Hydraulic jumps are required for complete Type 1/5 treatment.
- Mixed free-surface/pressurised profile logic is needed for Type 6/7. The executable
  HY-8 matrix now contains both types, with Type 6 retained as an unresolved comparison.

Primary copies of Bodhaine, FHWA-HRT-06-138, NCHRP 734, HDS-5, the HY-8 8.0
user manual, and Austroads AGRD05B-23 are now available locally. Review is not
the same as adoption: worked-example fixtures, a version-pinned HY-8 8.0.1.2
technical-method check, and executable applicability mappings remain open.

Later phases may be implemented experimentally, but they must not be labelled complete or
engineering-verified until these dependencies are resolved.

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
The corrected electronic tables have been extracted into `fhwa_box_inlets.md` for our
inlet configuration catalogue. Do not infer that coefficients for one span-to-rise ratio,
bevel, fillet, skew, or multi-barrel configuration apply universally.

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

Worked examples section was retrieved; however, due to complex formatting, they must be manually transcribed into fixtures rather than automatically generated. Do not equate extended software flow labels with this original classification.

### NCHRP-734-2012

*Hydraulic Loss Coefficients for Culverts*, NCHRP Report 734 (2012).
DOI: [10.17226/22673][nchrp].

Publication metadata and abstract confirmed. The report addresses conventional and
environmentally sensitive culverts including entrance loss, exit loss, buried-invert/
embedded culverts, slip-lined culverts, multi-barrel effects, and composite roughness.

Key findings:

- Confirms the conventional outlet-control energy framework.
- Supports representative-barrel superposition for most total-flow cases, while
  documenting approach-flow and individual-barrel differences relevant to local design.
- Use for entrance/exit-loss refinement and multi-barrel interaction documentation.

An initial coefficient-table extraction is documented in `nchrp734_coefficients.md`.
Assess applicability before proposing refinements to HDS-5 assumptions.

### HEC-RAS technical reference

Inspected the current online [outlet][hec-outlet] and [inlet][hec-inlet] pages;
navigation identifies version 7.0. Links use `latest`, so pin the version before
formal method sign-off. Outlet calculations are energy based. The inlet page
uses English units and has an apparent submerged-equation transcription error.
Neither its HTML equation text nor a software result replaces a typeset source.

### Australian application guidance

[Austroads AGRD05B-23][austroads]: *Guide to Road Design Part 5B: Drainage – Open
Channels, Culverts and Floodway Crossings*, edition 1.2, 30 January 2023.
Inspected the publication page, edition details and contents; full text has been obtained and reviewed.

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

Inspected the [official release page][hy8], which lists 8.0.1.2, build date
2025-03-05. The supplied local user manual identifies itself as version 8.0;
it must not be represented as version 8.0.1.2 technical documentation without
further evidence. Comparison software and documentation must both be pinned.

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

Reviewed the README and selected engine sources on the `master` branch on
2026-09-06. These links are mutable; pin a commit before formal comparison or reuse.

The [README](https://github.com/alejandroechev/culvertflow#readme) describes a
TypeScript hydraulic engine separated from a browser UI, rating curves, and inlet
coefficient tables. It states MIT licensing; verify the applicable licence text
and attribution before copying any code. No code has been imported.

Useful as a secondary implementation reference for module separation, coefficient
organisation and eventual reporting ideas. It is not a primary hydraulic authority
or a validated benchmark for this project.

Specific observations from the source:

- [Outlet control](https://github.com/alejandroechev/culvertflow/blob/master/packages/engine/src/outlet-control.ts)
  uses feet/cfs and a fixed critical-depth approximation of `0.6 * D`; it does not
  solve a free-surface profile in that function. Review equations against primary
  references and derive SI forms before considering any adaptation.
- [Controlling headwater](https://github.com/alejandroechev/culvertflow/blob/master/packages/engine/src/controlling.ts)
  simply selects the maximum of inlet and outlet headwaters. This does not implement
  the physical-consistency checks required by Phase 6 of our plan.
- [Coefficient tables](https://github.com/alejandroechev/culvertflow/blob/master/packages/engine/src/reference.ts)
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
