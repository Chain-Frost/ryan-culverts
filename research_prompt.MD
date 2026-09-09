You are conducting the Phase 0 hydraulic research gate for this repository:

E:\Github\ryan-culverts

This is a research and evidence task only. Do not modify hydraulic Python code, tests, package versions, or existing documentation. Create one new report:

docs/research/2026-09-06-phase-0-research-pack.md

If you cannot write to the repository, return the complete report as Markdown using exactly the structure requested below.

Before researching, read:

- culvert_solver_updated_work_plan.md
- docs/work/README.md
- docs/work/2026-09-06-phase-0-to-10-remediation.md
- docs/references.md
- docs/computational_basis.md
- docs/validation.md
- docs/hy8_feature_parity.md
- docs/architecture.md

Objective
=========

Close as much of CS-001 as authoritative source access permits and produce implementation-ready findings for CS-002 through CS-007.

Do not describe Phase 0 as complete unless every required primary source was actually accessed and reviewed. A search result, abstract, metadata page, secondary implementation, or another application’s output does not count as reviewing the underlying methodology.

Source hierarchy
================

Prefer sources in this order:

1. Current MRWA requirements and guidance for Western Australian application.
2. Applicable Australian/Austroads guidance.
3. Original or authoritative FHWA, USGS, NCHRP, AISI or other primary publications.
4. Official technical manuals for HY-8, HEC-RAS and SWMM.
5. Version-pinned source code from official repositories.
6. Secondary implementations only for comparison or discovery.

For every online source, give a direct URL. For source code, pin the repository commit SHA and link to exact lines where possible. Record the access date.

Required investigations
=======================

1. Bodhaine culvert flow classification

Review the full USGS publication:

G. L. Bodhaine, Measurement of Peak Discharge at Culverts by Indirect Methods,
Techniques of Water-Resources Investigations, Book 3, Chapter A3, 1968.

Determine:

- the original flow types and their physical definitions;
- control location and governing equations for each type;
- inlet/outlet submergence criteria;
- treatment of partially full, full and mixed flow;
- hydraulic-jump treatment;
- applicability limitations;
- which worked examples can become independent automated tests;
- whether the repository’s current regime names and logic map correctly to Bodhaine.

1. FHWA inlet-control methodology

Review HDS-5, Third Edition, FHWA-HIF-12-026, including Appendix A and relevant main-text sections.

Determine:

- exact unsubmerged and submerged inlet-control equations;
- correct interpretation of Form 1 and Form 2;
- transition-region construction;
- whether FHWA prescribes an equation, tangent construction, interpolation method, graphical procedure, or engineering judgement;
- applicability bounds and warnings;
- whether the current linear transition interpolation is defensible;
- suitable published values/examples for automated tests.

Give exact printed page, PDF page, equation, table and figure locators.

1. Corrected box-culvert inlet research

Review FHWA-HRT-06-138 and all official errata or replacement tables.

Determine:

- which original tables were corrected;
- the authoritative replacement values;
- applicable box geometry and inlet configurations;
- whether any current repository coefficients need correction or expansion;
- whether the research modifies HDS-5 coefficients or only particular configurations;
- suitable validation cases.

Do not use superseded table values.

1. Outlet control, profiles and regime selection

Using HDS-5 and other primary references, determine the accepted method for:

- full-flow outlet control;
- partly full outlet control;
- effective tailwater depth;
- submerged outlets that do not necessarily cause full-barrel pressurisation;
- S1, S2, M1, M2, H2 and other relevant profiles;
- mixed free-surface/pressurised flow;
- hydraulic-jump occurrence and placement;
- steep, mild, critical, horizontal and adverse slopes;
- candidate-solution physical consistency;
- transitions into and out of pressurised flow.

Specifically answer whether this rule is valid:

    tailwater_depth >= culvert_rise => whole barrel is full flow

If it is not universally valid, provide the correct decision process or the best source-supported implementation approach.

Compare direct-step and standard-step methods and recommend which method should be used for each supported case.

1. NCHRP Report 734

Review the full report if accessible:

Hydraulic Loss Coefficients for Culverts, NCHRP Report 734, 2012.

Determine:

- which entrance, exit, junction or barrel-loss methods are relevant;
- whether it supersedes, refines or supplements HDS-5;
- applicability to conventional and environmentally sensitive culverts;
- whether any values should replace current repository constants;
- implementation and test implications.

If the full text cannot be accessed, mark it “pending full-text review.” Do not infer detailed recommendations from the abstract.

1. Australian and MRWA requirements

Review current applicable MRWA and accessible Austroads guidance.

At minimum verify:

- Manning n for concrete pipes and boxes;
- helically wound CSP values by diameter and corrugation;
- structural-plate CSP ranges;
- manufacturer-data requirements;
- plastic-pipe requirements;
- current MRWA Specification 404 permitted CSP diameters and corrugations;
- whether hydraulic lookup availability differs from current MRWA supply/construction compliance;
- minimum culvert sizes;
- required design outputs, assumptions and documentation;
- any requirements affecting inlet type, blockage, debris, scour, outlet velocity, headwater or freeboard.

Clearly distinguish:

- hydraulic calculation defaults;
- product availability;
- construction compliance;
- project-specific design requirements.

Use this default precedence unless a primary source requires a change:

1. explicit user override;
2. project/manufacturer value;
3. applicable MRWA value;
4. version-pinned HY-8 fallback;
5. explicit error.

All defaults must remain user-overridable.

1. HY-8 technical methodology and defaults

Pin the exact HY-8 version reviewed. The currently relevant comparison version is expected to be HY-8 8.0.1.2, but verify this rather than assuming it.

Review the official technical manual and, where necessary, version-specific installed data.

Determine:

- documented inlet-control methodology;
- transition treatment;
- outlet-control/profile methodology;
- regime classification;
- default Manning values by shape/material;
- inlet and entrance configuration defaults;
- which values are documented versus merely observed in installed data;
- output quantities suitable for comparison;
- known limitations or version-specific bugs.

HY-8 is a comparison implementation, not the primary hydraulic authority.

When useful, inspect E:\Github\run-hy8 read-only. Do not modify that repository.

1. Independent implementation references

Inspect relevant official or authoritative implementation material for:

- EPA SWMM;
- HEC-RAS;
- STREAM-1D, if its methodology and licence can be established.

Pin versions or commit SHAs.

For each, state:

- what it is useful for validating;
- what it cannot validate independently;
- important methodological differences;
- candidate comparison cases;
- whether its source or documentation exposes edge cases missing from the current solver.

1. Validation cases and acceptance criteria

Identify practical independent test cases for:

- inlet-control equations and transition;
- concrete circular culverts;
- CSP circular culverts;
- concrete boxes;
- full outlet control;
- partial-flow profiles;
- submerged outlets;
- hydraulic jumps;
- single barrels;
- identical barrel groups;
- mixed-group crossings;
- rating curves spanning regime changes.

For every proposed case record:

- source and exact locator;
- complete SI inputs;
- expected outputs;
- original units and conversions;
- expected flow/control regime;
- displayed precision;
- recommended absolute and relative tolerances;
- whether the expected value is published, independently calculated, or software-generated.

Do not invent one global percentage tolerance.

Required report structure
=========================

# Phase 0 research evidence pack

## 1. Executive conclusion

State:

- whether Phase 0 can now be closed;
- which questions were resolved;
- which remain blocked;
- the highest-risk findings for the current implementation;
- the recommended implementation order.

## 2. Source review matrix

Use this table:

| Source ID | Publication/version | Authority | Accessed in full? | Exact sections reviewed | Relevant tasks | Status |
| --- | --- | --- | --- | --- | --- | --- |

Allowed status values:

- Reviewed
- Partially reviewed
- Metadata only
- Inaccessible
- Superseded
- Not applicable

## 3. Finding register

Give every material finding a stable ID such as RES-001.

Use this table:

| Finding ID | Topic | Finding | Source ID and locator | Confidence | Implementation impact |
| --- | --- | --- | --- | --- | --- |

Confidence must be one of:

- High: explicit primary-source statement or equation
- Medium: inference combining primary-source material
- Low: secondary implementation or incomplete access

Clearly label all inferences.

## 4. Detailed methodological findings

Use subsections for:

- Bodhaine flow types
- FHWA inlet control
- Inlet transition
- Corrected box-inlet research
- Outlet control
- Water-surface profiles
- Hydraulic jumps
- Regime selection
- Manning roughness/defaults
- Australian/MRWA requirements
- HY-8
- HEC-RAS
- SWMM
- STREAM-1D

For equations, define every variable and unit. Do not silently convert US customary equations to SI. Show the conversion or cite the authoritative SI form.

## 5. Current-repository impact assessment

Review the present repository implementation read-only.

Use this table:

| Finding ID | Current module/function | Current behaviour | Required change | Severity | Proposed tests |
| --- | --- | --- | --- | --- | --- |

Severity:

- Critical: materially wrong hydraulic result or unsafe default
- High: unsupported method represented as valid
- Medium: incomplete diagnostics, applicability or provenance
- Low: documentation, naming or maintainability

Give file and line references based on the current checkout.

## 6. Defaults recommendation

Provide a concrete typed defaults design covering:

- user overrides;
- manufacturer/project values;
- MRWA defaults;
- HY-8 fallback values;
- provenance attached to selected values;
- partial overrides;
- unavailable combinations;
- warnings versus errors;
- JSON/configuration implications.

Do not write the implementation.

## 7. Validation-case catalogue

Use this table:

| Case ID | Phenomenon | Source/locator | Inputs | Expected outputs | Regime | Tolerances | Automation readiness |
| --- | --- | --- | --- | --- | --- | --- | --- |

Automation readiness:

- Ready
- Needs independent calculation
- Needs source clarification
- External-software comparison only

## 8. Proposed decisions

For each decision, state:

- recommended choice;
- evidence;
- rejected alternatives;
- effect on existing API/results;
- remaining uncertainty.

At minimum address:

- inlet transition method;
- tailwater/full-flow decision process;
- hydraulic-jump scope;
- profile method;
- default-resolution precedence;
- MRWA versus HY-8 defaults;
- which currently supported regimes should be temporarily rejected until implemented correctly.

## 9. Remaining blockers and questions

Separate:

- missing source access;
- genuine engineering decisions;
- information required from the user;
- work that can proceed without user input.

Do not ask the user questions that can be answered from primary sources.

## 10. Agent-ready implementation tasks

Translate findings into bounded tasks with:

- task ID;
- files/modules likely affected;
- prerequisites;
- acceptance criteria;
- required focused tests;
- required documentation updates;
- whether the change is breaking.

## 11. Bibliography and source links

Give full publication details, direct URLs, editions/versions, access dates and pinned commit SHAs.

Evidence rules
==============

- Cite every substantive hydraulic claim.
- Prefer paraphrase; use only short quotations when wording is decisive.
- Give exact page/equation/table/figure locators.
- Distinguish printed page numbers from PDF page numbers.
- Record failed access attempts.
- Never fill a source gap with an uncited assumption.
- Never treat agreement between two software packages as proof of correctness.
- Do not copy code from third-party repositories.
- Record licences before recommending any implementation-derived reuse.
- Do not describe current code as validated merely because its internal tests pass.
- Do not commit, stage, package, or publish anything.

Final response
==============

Return:

1. the path to the completed research report;
2. a five-to-ten bullet executive summary;
3. the list of unresolved blockers;
4. confirmation that no implementation files were changed;
5. confirmation that no commit or publication was made.
