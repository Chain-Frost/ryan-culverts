# Culvert Solver — Updated Development Work Plan

> This file defines intended scope and gates; it is not evidence that a phase is complete.
> Current implementation and review status is maintained in [docs/progress.md](docs/progress.md).

## 1. Project Objective

Develop a new, standalone Python library for engineering-grade culvert hydraulic analysis and rapid design iteration.

The library must:

- operate independently of HY-8 or any other external hydraulic application;
- eventually provide at least the hydraulic capability required for culvert calculations comparable to HY-8;
- use the best defensible methodology from primary hydraulic references rather than reproducing HY-8 blindly;
- be sufficiently transparent, testable and traceable for engineering design workflows;
- support rapid repeated evaluation of culvert alternatives without launching external applications;
- use SI units internally;
- use metres, m³/s and m/s as the normal engineering units;
- accept culvert dimensions in millimetres by default at the user-facing API;
- support crossings consisting of multiple culvert groups with different sizes, shapes, materials, invert levels and hydraulic properties;
- preserve sufficient structured output for later plotting and reporting without requiring redesign of the numerical core.

Roadway overtopping is **not part of the initial implementation**.

External packages such as HY-8, HEC-RAS, SWMM and STREAM-1D are primarily for later verification and comparison, not runtime dependencies.

---

## 2. Core Development Principles

### 2.1 Independent computational core

The production library must not depend on:

- HY-8;
- `run-hy8`;
- HEC-RAS;
- SWMM;
- STREAM-1D.

These may be used later as external reference implementations or verification tools.

`run-hy8` may be especially useful for automating HY-8 comparison cases, but it must remain outside the new library.

---

### 2.2 Develop and test together

Testing is not a final-stage activity.

Each hydraulic component should be accompanied by relevant tests while that component is being designed and implemented.

The preferred sequence is:

1. define the engineering behaviour;
2. implement the smallest coherent component;
3. immediately add analytical and internal unit tests;
4. verify edge cases and applicability limits;
5. only then build higher-level functionality on top of it.

This is intended to preserve engineering context while the implementation decisions are still fresh.

Additional tests may and should be added later as integration behaviour and edge cases become clearer.

---

### 2.3 External verification comes later

Comparison against external hydraulic packages should occur only after the internal computational system is substantially complete and internally tested.

The sequence should therefore be:

```text
Methodology
    ↓
Architecture
    ↓
Geometry + hydraulic primitives
    ↓
Internal unit tests
    ↓
Inlet control
    ↓
Internal tests
    ↓
Outlet control / profiles
    ↓
Internal tests
    ↓
Flow-regime selection
    ↓
Internal tests
    ↓
Culvert groups and crossings
    ↓
Internal integration tests
    ↓
Rating curves / repeated evaluation
    ↓
Internal tests
    ↓
External verification
    ↓
Engineering acceptance review
```

Do not design the solver around reproducing the output of any one external package.

---

## 3. Technical Reference Hierarchy

The solver should be based primarily on authoritative literature.

At minimum review:

### FHWA

- Hydraulic Design of Highway Culverts, HDS-5, Third Edition;
- current HY-8 technical documentation;
- applicable FHWA culvert research;
- FHWA-HRT-06-138 for box culvert inlet performance and transition relationships.

### USGS

- Bodhaine, *Measurement of Peak Discharge at Culverts by Indirect Methods*;
- six classical culvert flow types and their physical interpretation.

### USACE / HEC-RAS

Review current documentation for:

- culvert inlet control;
- outlet control;
- critical depth;
- normal depth;
- direct-step / standard-step profile calculations;
- pressurised flow;
- hydraulic jumps;
- regime selection.

HEC-RAS should be treated as a valuable implementation and methodology reference, not automatically as the governing authority over FHWA.

### NCHRP

- NCHRP Report 734 — *Hydraulic Loss Coefficients for Culverts*.

Assess whether later loss relationships improve or refine traditional assumptions.

### Australian guidance

Review current:

- Austroads Guide to Road Design Part 5B;
- applicable Main Roads Western Australia guidance.

These are important for Australian design application, terminology, reporting and jurisdictional requirements.

### Reference implementations

Review, where useful:

- EPA SWMM source code;
- HY-8;
- HEC-RAS;
- STREAM-1D.

These should help identify implementation approaches, numerical edge cases and independent interpretations of the published equations.

They are not substitutes for the primary literature.

---

## 4. Geometry Strategy

Implement standard culvert geometry internally.

Do not make a general geometry package a required dependency for normal culvert calculations.

Initial priority:

- circular culverts;
- rectangular / box culverts.

The common hydraulic geometry interface should support:

```python
area(depth_m)
wetted_perimeter(depth_m)
top_width(depth_m)
hydraulic_radius(depth_m)
hydraulic_depth(depth_m)
full_area
full_wetted_perimeter
full_depth
```

Later geometry should accommodate, as required:

- elliptical sections;
- arch sections;
- pipe arches;
- embedded culverts;
- user-defined sections.

Critical depth, normal depth and profile algorithms should operate on the common geometry interface rather than having separate versions for each shape where physically possible.

Standard shapes should use analytical relationships wherever practical.

---

## 5. Units Strategy

### 5.1 Internal computational units

Use SI units internally:

| Quantity | Internal unit |
| --- | --- |
| Length | m |
| Elevation | m |
| Area | m² |
| Discharge | m³/s |
| Velocity | m/s |
| Acceleration | m/s² |
| Slope | dimensionless |
| Manning roughness | SI convention |

All numerical solvers should operate on plain canonical SI values.

---

### 5.2 User-facing culvert dimensions

Use millimetres by default for culvert dimensions.

Examples:

```python
CircularCulvert(
    diameter_mm=1200,
    length_m=18.5,
    inlet_invert_m=102.35,
    outlet_invert_m=102.20,
)
```

```python
BoxCulvert(
    span_mm=2400,
    rise_mm=1200,
    length_m=16.0,
)
```

Convert dimensions to metres when constructing the internal hydraulic model.

Avoid ambiguous API fields where the unit cannot be determined from the name or type.

---

### 5.3 Units library

A units library such as Pint may be supported as an optional API convenience.

However:

- Pint quantities should not propagate through the computational core;
- numerical root solving and profile calculations should operate on plain SI floats;
- unit conversion should occur at a defined API boundary;
- the core library should remain usable without a units package unless later requirements justify making one mandatory.

---

## 6. Initial Domain Model

The crossing model must support combinations of different culvert groups.

Suggested conceptual structure:

```text
CulvertCrossing
│
├── CulvertGroup
│   ├── quantity = 3
│   └── Circular culvert, DN1200 concrete
│
├── CulvertGroup
│   ├── quantity = 2
│   └── 2400 × 1200 RCBC
│
└── CulvertGroup
    ├── quantity = 1
    └── DN900 corrugated steel
```

A `CulvertGroup` represents hydraulically identical parallel barrels.

Different groups may have different:

- shape;
- dimensions;
- quantity;
- material;
- Manning roughness;
- inlet configuration;
- inlet invert;
- outlet invert;
- length;
- slope.

The crossing solver should solve a common upstream headwater for all groups at the specified tailwater.

Conceptually:

```math
Q_{crossing}(HW,TW)
=

\sum_i N_i Q_i(HW,TW)
```

where:

- \(N_i\) is the number of identical barrels in group \(i\);
- \(Q_i\) is the discharge through one barrel of that group.

---

## 7. Initial Scope Exclusions

The following should **not** be implemented during the initial hydraulic build unless required for the architecture:

- roadway overtopping;
- roadway weir flow;
- bridge hydraulics;
- full river-network simulation;
- 2D hydraulics;
- sediment transport;
- debris blockage modelling;
- scour modelling;
- graphical user interface;
- plotting implementation.

The architecture should not prevent future implementation of these items.

---

## 8. Plotting Architecture

Plotting is a later feature.

Do not introduce a plotting dependency into the hydraulic core during initial development.

Instead, result objects should preserve the information required for later plotting.

For example, profile results should support data such as:

```python
@dataclass(frozen=True, slots=True)
class ProfilePoint:
    station_m: float
    invert_elevation_m: float
    crown_elevation_m: float
    water_surface_elevation_m: float | None
    hydraulic_grade_elevation_m: float
    energy_grade_elevation_m: float
    depth_m: float
    velocity_m_s: float
    froude_number: float | None
```

Rating-curve results should naturally expose:

```text
flow_m3_s
headwater_elevation_m
tailwater_elevation_m
outlet_velocity_m_s
control
flow_regime
```

A future optional plotting module should therefore be able to produce:

- culvert longitudinal profiles;
- HGL / EGL plots;
- headwater versus discharge curves;
- velocity versus discharge curves;
- comparison plots between design alternatives;

without changing the hydraulic solver.

---

## 9. Proposed Package Architecture

A starting structure may be:

```text
src/
    culvert_solver/
        __init__.py

        models/
            barrel.py
            group.py
            crossing.py
            materials.py
            tailwater.py
            results.py

        geometry/
            base.py
            circular.py
            rectangular.py

        hydraulics/
            energy.py
            resistance.py
            critical.py
            normal.py
            losses.py
            froude.py

        inlet_control/
            solver.py
            fhwa.py
            coefficients.py

        outlet_control/
            solver.py
            full_flow.py
            free_surface.py

        profiles/
            direct_step.py
            hydraulic_jump.py

        solver/
            barrel.py
            group.py
            crossing.py
            regime.py
            rating_curve.py

        numerical/
            roots.py
            tolerances.py

        references/
            models.py
            source_registry.py
            fhwa_coefficients.py

        units/
            conversion.py
            pint_adapter.py

        constants.py
        exceptions.py
```

Future optional module:

```text
culvert_solver/
    plotting/
```

Do not follow this layout mechanically if research identifies a better decomposition.

The important separation is between:

- geometry;
- hydraulic fundamentals;
- empirical inlet relationships;
- outlet-control calculations;
- numerical algorithms;
- culvert/barrel/group/crossing logic;
- units/API conversion;
- results;
- plotting/presentation.

---

## 10. Development Phases

### Phase 0 — Research and computational basis

Before substantial coding:

1. review the primary references;
2. identify the hydraulic equations required;
3. define the supported flow regimes;
4. identify empirical coefficient sources and limits;
5. identify known HY-8 capabilities;
6. identify areas where later literature may refine HY-8/HDS-5;
7. review SWMM and STREAM-1D source/architecture where useful;
8. document methodological uncertainties before coding around them.

Deliverables:

```text
docs/
    computational_basis.md
    references.md
    architecture.md
    hy8_feature_parity.md
    validation.md
```

No attempt should be made at this stage to force agreement with HY-8.

---

### Phase 1 — Core models, constants and numerical infrastructure

Implement:

- core dataclasses;
- material and inlet enums/models;
- result models;
- central physical constants;
- numerical tolerances;
- bracketed root-solving utilities;
- structured errors and warnings;
- reference/source metadata model;
- SI conversion boundaries.

#### Phase 1 — Core models, constants and numerical infrastructure tests

Test immediately:

- validation of model inputs;
- unit conversion;
- tolerance handling;
- bracket/root behaviour;
- expected failure behaviour;
- immutable/result object behaviour where applicable.

Do not defer these tests.

---

### Phase 2 — Hydraulic geometry

Implement:

- geometry protocol / abstract interface;
- circular geometry;
- rectangular/box geometry.

Add other standard geometries later once the first two are proven.

#### Phase 2 — Hydraulic geometry tests

For each geometry, test:

- zero depth;
- partial depth;
- full depth;
- area;
- wetted perimeter;
- top width;
- hydraulic radius;
- hydraulic depth;
- symmetry and limiting behaviour where relevant.

Use analytical reference values where possible.

For circles, include checks at meaningful depths such as:

- empty;
- quarter depth;
- half depth;
- three-quarter depth;
- full.

Geometry should be highly trusted before hydraulic solvers depend on it.

---

### Phase 3 — Fundamental hydraulics

Implement reusable functions for:

- velocity;
- velocity head;
- Froude number;
- specific energy;
- Manning discharge;
- Manning friction slope;
- local loss terms;
- critical depth;
- normal depth.

#### Phase 3 — Fundamental hydraulics tests

Add tests immediately for:

- rectangular critical-depth analytical solutions;
- circular critical-depth numerical solutions;
- rectangular normal depth against independently calculated values;
- Manning flow at known depth;
- conservation and expected monotonic behaviour;
- local loss calculations;
- limiting cases.

Do not proceed to inlet/outlet control until these functions are reliable.

---

### Phase 4 — Inlet-control hydraulics

Implement FHWA inlet-control calculations.

Support, as appropriate:

- unsubmerged inlet control;
- submerged inlet control;
- transition region;
- circular culverts;
- box culverts;
- relevant inlet configurations;
- traceable coefficient sets.

All empirical coefficients must contain source metadata and applicability information.

#### Phase 4 — Inlet-control hydraulics tests

Add:

- equation-level tests;
- published reference cases where available;
- transition continuity checks;
- submerged/unsubmerged limiting cases;
- coefficient selection tests;
- invalid configuration tests;
- applicability-limit tests.

At this stage, tests should primarily verify the implementation against the equations and published source material, not against HY-8.

---

### Phase 5 — Outlet-control hydraulics

Implement:

- tailwater handling;
- entrance losses;
- barrel friction;
- exit losses;
- full-flow energy solution;
- partially full outlet-control flow;
- critical/normal depth interactions;
- free-surface profile solution.

Determine from the literature whether direct-step, standard-step or another accepted approach is most appropriate for each case.

#### Phase 5 — Outlet-control hydraulics tests

Add tests for:

- full-barrel energy balance;
- known uniform-flow cases;
- simple subcritical profiles;
- simple supercritical profiles;
- tailwater sensitivity;
- friction-loss sensitivity;
- entrance/exit loss sensitivity;
- horizontal and low-slope cases where supported;
- convergence and failure modes.

---

### Phase 6 — Flow regime and governing solution

Implement explicit regime-selection logic.

The solver should reason about:

- inlet control;
- outlet control;
- critical control;
- subcritical barrel flow;
- supercritical barrel flow;
- partially full barrel flow;
- full / pressurised barrel flow;
- submerged inlet;
- submerged outlet;
- hydraulic jumps where relevant.

Do not simply choose the larger of two independently calculated headwater values without checking physical consistency.

#### Phase 6 — Flow regime and governing solution tests

Create targeted tests that force each supported regime.

Verify:

- regime classification;
- continuity at regime transitions;
- physically admissible candidate selection;
- rejection of inconsistent solutions;
- expected pressurisation behaviour;
- hydraulic jump placement/behaviour where implemented.

---

### Phase 7 — Single-barrel solver

Combine the lower-level components into a complete single-barrel hydraulic solution.

Inputs should include:

- geometry;
- dimensions;
- material / roughness;
- inlet configuration;
- inlet invert;
- outlet invert;
- length;
- discharge or headwater depending on solution mode;
- tailwater.

Results should include sufficient intermediate quantities for engineering checking.

#### Phase 7 — Single-barrel solver tests

Add end-to-end single-barrel tests covering:

- low flow;
- moderate flow;
- near-full flow;
- inlet control;
- outlet control;
- submerged conditions;
- steep slope;
- mild slope;
- box culvert;
- circular culvert.

These are internal integration tests, still not primarily external-package comparisons.

---

### Phase 8 — Culvert groups

Implement `CulvertGroup` for multiple identical barrels.

A group should avoid unnecessary duplication of identical geometry and coefficient data.

Conceptually:

```math
Q_{group} = N Q_{barrel}
```

where hydraulic conditions are shared.

#### Phase 8 — Culvert groups tests

Test:

- one barrel versus one-barrel group equivalence;
- exact scaling for identical parallel barrels where appropriate;
- group-level result aggregation;
- velocity and per-barrel values;
- differing quantities.

---

### Phase 9 — Multi-group culvert crossings

Implement crossings comprising multiple culvert groups with different hydraulic properties.

The solver should determine the common upstream headwater required to convey the crossing discharge under the specified tailwater.

For a prescribed crossing flow:

```math
Q_{target}
=

\sum_i N_i Q_i(HW,TW)
```

Solve for \(HW\).

Groups may differ in:

- size;
- shape;
- material;
- roughness;
- inlet type;
- invert;
- length;
- slope;
- quantity.

#### Phase 9 — Multi-group culvert crossings tests

Create crossing tests for:

- two different pipe sizes;
- pipe plus box culvert;
- differing invert levels;
- differing Manning roughness;
- groups entering flow at different headwater levels;
- discharge partitioning;
- total-flow conservation;
- monotonic headwater response.

---

### Phase 10 — Rating curves and rapid design evaluation

Implement efficient repeated evaluation.

Examples:

```python
rating_curve(...)
```

and later:

```python
evaluate_designs(...)
find_minimum_culvert_size(...)
```

Correctness should be established before optimisation or vectorisation.

#### Phase 10 — Rating curves and rapid design evaluation tests

Test:

- scalar result equivalence;
- monotonicity where physically expected;
- deterministic repeated runs;
- correct handling of regime changes over the rating curve;
- reproducibility;
- performance benchmarks without weakening numerical correctness.

---

## 11. External Verification Phase

Only after the internal solver and internal tests are substantially mature should systematic external verification begin.

This phase is distinct from the development tests above.

### 11.1 HY-8

Use `run-hy8` externally to automate a broad HY-8 comparison suite.

Compare:

- headwater;
- control;
- critical depth;
- normal depth;
- outlet depth;
- outlet velocity;
- flow regime where comparable;
- profile values where available.

Cover combinations of:

- culvert shape;
- dimensions;
- slope;
- length;
- Manning roughness;
- inlet type;
- tailwater;
- discharge;
- number of barrels;
- submerged/unsubmerged conditions;
- inlet/outlet control.

HY-8 is an important benchmark, not the definition of correctness.

Any meaningful difference should be investigated against the primary methodology.

---

### 11.2 HEC-RAS

Use selected HEC-RAS cases to independently compare:

- outlet-control behaviour;
- water-surface profiles;
- regime transitions;
- pressurisation;
- hydraulic jumps where applicable.

Focus on cases where HEC-RAS provides useful independent confirmation of the physical solution.

---

### 11.3 SWMM

Use SWMM primarily as:

- a reference implementation for FHWA inlet-control equations;
- an independent check of conduit geometry relationships;
- a source of useful implementation ideas and edge cases.

Do not depend on the fact that SWMM is written in C; language is irrelevant to its usefulness as a reference implementation.

---

### 11.4 STREAM-1D

Where appropriate, compare selected cases with STREAM-1D.

Use it as another independent implementation, particularly for:

- HDS-5 inlet behaviour;
- outlet/control regime logic;
- shape handling;
- profile calculations.

Do not treat agreement with STREAM-1D as authoritative if its result conflicts with the primary literature.

---

## 12. Verification Acceptance

Do not use one global tolerance such as "within 1%".

Establish quantity-specific acceptance criteria for:

- headwater;
- depth;
- discharge;
- velocity;
- energy loss;
- profile elevations.

For each comparison record:

```text
absolute difference
relative difference
methodological notes
control/regime agreement
```

Separate:

- numerical tolerance differences;
- display rounding;
- different coefficient assumptions;
- genuine methodological differences;
- implementation errors.

---

## 13. Engineering Traceability

Every empirical relationship should be traceable.

For coefficient sets and empirical equations, preserve metadata including:

- publication;
- edition/year;
- equation/table/figure identifier where practical;
- applicable culvert shape;
- applicable inlet configuration;
- valid parameter range;
- notes and limitations.

Do not scatter unexplained constants throughout the codebase.

Do not silently extrapolate outside documented applicability.

Use structured warnings or errors where a calculation extends beyond validated methodology.

---

## 14. Results and Future Plotting Support

A complete barrel solution should eventually expose, where applicable:

- headwater elevation;
- headwater depth;
- HW/D;
- tailwater elevation;
- inlet-control headwater;
- outlet-control headwater;
- governing control;
- flow regime;
- barrel depth;
- barrel velocity;
- outlet velocity;
- critical depth;
- normal depth;
- entrance loss;
- friction loss;
- exit loss;
- total energy loss;
- pressurised/free-surface state;
- convergence information;
- structured warnings;
- hydraulic profile.

Profile outputs should preserve:

- station;
- invert elevation;
- crown elevation;
- water level;
- HGL;
- EGL;
- depth;
- velocity;
- Froude number.

This will allow plotting to be added later without changing the solver architecture.

---

## 15. Documentation Requirements

Maintain these documents throughout development:

```text
docs/
    architecture.md
    computational_basis.md
    references.md
    validation.md
    hy8_feature_parity.md
```

Update them as implementation decisions are made.

### `architecture.md`

Document:

- module responsibilities;
- data flow;
- object relationships;
- units boundaries;
- solver sequence.

### `computational_basis.md`

Document:

- governing equations;
- empirical relationships;
- flow regimes;
- methodology selection;
- assumptions and limitations.

### `references.md`

Maintain exact publication details and source hierarchy.

### `validation.md`

Maintain:

- analytical/internal verification cases;
- published reference cases;
- later external-package verification approach;
- acceptance criteria.

### `hy8_feature_parity.md`

Maintain a live feature matrix:

| Capability | HY-8 | New solver | Method | Internal tests | External verification | Status |
|---|---:|---:|---|---|---|---|

---

## 16. Initial Definition of Done

The initial culvert solver should not be described as construction-grade until:

- core geometry is internally validated;
- critical/normal depth calculations are internally validated;
- inlet control is validated against published equations/examples;
- outlet control is internally validated;
- regime-selection logic is tested;
- single-barrel calculations are integrated;
- multi-barrel groups are tested;
- mixed-group crossings are tested;
- rating curves are stable;
- empirical constants are traceable;
- applicability limits are handled;
- convergence failures are explicit;
- internal engineering tests are comprehensive;
- external verification has subsequently been completed against appropriate independent packages;
- significant differences have been investigated and documented.

Agreement with HY-8 alone is not sufficient.

---

## 17. Recommended Implementation Order

The preferred order is:

1. research and computational basis;
2. architecture and source-traceability framework;
3. core data models;
4. numerical/root-solving infrastructure;
5. circular geometry + tests;
6. box geometry + tests;
7. hydraulic primitives + tests;
8. critical depth + tests;
9. normal depth + tests;
10. inlet-control methodology + tests;
11. outlet-control full-flow methodology + tests;
12. free-surface profile solver + tests;
13. regime-selection logic + tests;
14. complete single-barrel solver + integration tests;
15. culvert groups + tests;
16. mixed-group crossings + tests;
17. rating curves + tests;
18. performance work;
19. external HY-8 verification;
20. external HEC-RAS / SWMM / STREAM-1D verification where appropriate;
21. engineering acceptance review;
22. only then consider broader design automation, plotting and roadway overtopping.

This sequence intentionally places verification against external applications near the end, while keeping analytical and internal validation tightly coupled to each stage of implementation.
