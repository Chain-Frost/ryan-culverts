# Architecture and decisions

Status: implementation snapshot under review, 2026-09-06.

## Implemented package boundary

The distribution remains `ryan-culverts`; the new import is `culvert_solver`.
Use the `src/` layout and Python 3.14. The runtime has no third-party dependencies.
There is no compatibility layer for the retired `culvertflow` package.

| Module | Responsibility |
| --- | --- |
| `channel.geometry` | Rectangular and asymmetric trapezoidal prismatic open-channel sections |
| `channel.uniform` | Manning normal depth, section factor, conveyance, and root diagnostics |
| `constants` | Standard gravitational acceleration and water properties with source records |
| `geometry.base` | Cross-section geometry interface and crown/closed-conduit contract |
| `geometry.circular` | Analytical circular segment geometry |
| `geometry.rectangular` | Analytical rectangular box culvert geometry |
| `geometry.filleted_rectangular` | Rectangular boxes with equal 45-degree internal corner fillets and net area |
| `hydraulics.primitives` | Velocity, velocity head, specific energy, Froude and Manning formulas |
| `hydraulics.critical` | Critical depth analytical and bracketed root solvers |
| `hydraulics.normal` | Uniform flow normal depth with circular conveyance branch selection |
| `hydraulics.momentum` | Hydrostatic momentum function and free-surface sequent-depth solver |
| `models.materials` | Material records and source-traceable Manning roughness data/lookups |
| `models.enums` | Closed control, geometry, equation, profile, and CSP-corrugation categories |
| `models.barrel` | Physical culvert barrel with authoritative inverts and derived slope |
| `models.group` | Parallel identical culvert barrels with quantity scaling |
| `models.tailwater` | Fixed and discharge-dependent tailwater boundaries and provenance |
| `models.crossing` | Multi-group culvert crossing aggregation |
| `models.roadway` | Constant-elevation roadway crest and coefficient provenance |
| `models.results` | Results, adopted parameter selections, and flow classifications |
| `models.collection` | Road inventory, normalized summaries, and parameter catalogues |
| `inlet_control.coefficients` | Empirical regression constants and source records from HDS-5 Table A.1 |
| `inlet_control.fhwa` | Pure SI equations for Form 1/2 unsubmerged, submerged, and transition |
| `inlet_control.solver` | Inlet headwater, regime, headwater ratio, and high-head applicability warnings |
| `inlet_control.modern_box` | Typed FHWA-HRT-06-138 Figure 93 configurations and bounded Table 11/12 relationships |
| `outlet_control.losses` | Entrance (HDS-5 Table C.2), friction, and exit head loss formulations |
| `outlet_control.full_flow` | Full-flow energy balance, effective tailwater depth, and headwater solver |
| `outlet_control.partial_flow` | Partially full outlet-control headwater solver using backwater profiles |
| `profiles.direct_step` | Direct-step free-surface water profile solver for prismatic culverts |
| `roadway.overtopping` | Unsubmerged HDS-5 broad-crested roadway-weir flow |
| `solver.regime` | Hydraulic regime selection comparing inlet and outlet control headwaters |
| `solver.barrel` | Single-barrel culvert hydraulic solver generating BarrelHydraulicResult |
| `solver.group` | Culvert group hydraulic solver scaling identical parallel barrels |
| `solver.crossing` | Multi-group crossing solver finding common upstream headwater elevation |
| `solver.rating_curve` | Monotonic rating curve generator for barrels and crossings |
| `numerical.roots` | Bounded scalar bisection (`solve_bracketed`) and Brent's method (`solve_brent`) |
| `numerical.tolerances` | Independent-variable and residual tolerances |
| `units.conversion` | Positive dimension conversion from mm to m |
| `references.models` | Immutable source/locator/applicability records |
| `exceptions` | Input and convergence failure types |

Public names are exported once from `culvert_solver`. No environment flags or
mutable global runner registration affect calculations. Immutable default
tolerances may safely be shared across concurrent calls.

`CulvertCrossing` may carry one optional `RoadwayWeir`. The common-headwater solver
evaluates culvert capacity and roadway capacity independently at each trial elevation, then
solves their sum against the specified crossing discharge. Results preserve culvert and
roadway flow separately. The initial roadway boundary is intentionally narrow: one
constant-elevation crest, an explicit user-selected SI coefficient, and tailwater no higher
than the crest. Irregular sag segmentation and submerged-weir correction belong to CS-028.

Open-channel sections deliberately use a separate `OpenChannelSection` protocol rather
than pretending to be closed culvert geometry. A Manning channel boundary resolves stage
from the receiving flow before culvert allocation: barrel flow for a standalone barrel,
total group flow for a standalone group, and total crossing flow once for a crossing.
Each rating point resolves the boundary again. The resulting method, discharge, channel
invert, normal depth, parameter sources, and root diagnostics are retained on results.
`method_source` identifies the hydraulic method; independent `roughness_source`,
`slope_source`, `geometry_source`, and `channel_invert_source` fields prevent HDS-5 from
being misreported as the source of project inputs. The ambiguous `source` field is not
supported. Inverse discharge-for-headwater helpers still require fixed tailwater because
accepting a flow-dependent boundary there would create a different nested solve.

The same crossing capacity function is public in the inverse direction: callers may obtain
total culvert-plus-roadway discharge for an absolute target headwater. Group and barrel
forms are also public. HW/D convenience is intentionally barrel-only because a mixed
crossing has no unique invert or rise.

## Defaults and applicability boundary

Defaults require enough typed context to remain inspectable. Inlet and entrance-loss
resolvers no longer treat a missing material as concrete; callers must identify the
material or supply the relevant coefficients explicitly. Explicit overrides and
barrel-attached values retain precedence over `SolverConfiguration` defaults.

Concrete roughness records are separated into `CONCRETE_PIPE` and `CONCRETE_BOX`, with
the current MRWA Table 2.1 ranges and source metadata. The compatibility-level
`CONCRETE` category remains usable for geometry-specific inlet and entrance-loss
resolution, but its combined roughness range is intentionally rejected as ambiguous by
`resolve_manning_roughness`.

Plastic-pipe roughness is manufacturer-led. `SMOOTH_HDPE` therefore fails closed without
an explicit override. A caller may deliberately request the HDS-5 laboratory fallback
with `allow_documented_fallback=True`; the returned selection then carries stable,
source-bearing notices that manufacturer data was absent and that hydraulic roughness
does not prove MRWA product or construction compliance. The same compliance distinction
is attached to MRWA CSP table selections. Passing a `ManningRoughnessSelection` through
a barrel's `roughness_selection` field preserves its basis, source, and notices in the
solved result. No HY-8 roughness fallback is currently defined.

## Inventory and reporting boundary

`CulvertInventory` collects independent crossings along a road without implying
hydraulic connectivity. `InventorySummary` emits crossing and group rows that
reference deduplicated `AdoptedParameterSet` records. IDs are either caller
supplied or deterministic content fingerprints; source metadata is part of the
identity, and conflicting caller IDs or source IDs fail explicitly.

Solved barrel results retain the selected inlet coefficients, entrance-loss
coefficient, Manning roughness, selection bases, and optional sources. A caller
can therefore cite a manufacturer or project specification without losing that
reference during calculation. `SourceReference.url` may be `None` for a controlled
or non-public specification, while publication, edition, locator, and applicability
remain mandatory. File, JSON, spreadsheet, GIS, and presentation
adapters remain outside the core until a downstream interface is chosen. See
CS-005 and CS-011 in the work plan.

Crossing summaries retain configured roadway crest elevation and calculated roadway flow,
and roadway coefficient provenance participates in the inventory source register.

For a group containing more than one hydraulically identical barrel,
`GroupHydraulicResult.applicability_notices` records the representative-barrel/equal-flow
assumption and its NCHRP 734 source. `CrossingHydraulicResult` aggregates those notices.
Inventory group and crossing rows propagate their stable codes, and the source catalogue
retains the supporting reference. This describes the limits of barrel-specific flow and
velocity certainty without changing total discharge or applying an efficiency factor.

Barrel results also retain the evaluated inlet-, outlet-, and full-flow headwater
candidates where physically applicable, the selected profile curve, hydraulic-jump
station, pressurised-reach length, and typed hydraulic warnings. The length is upstream
of an M2-to-full transition or downstream of an S1f/JS1f transition. Rating-curve points
preserve the warnings. Inventory summaries expose
deduplicated warning codes at group and crossing level so a compact road inventory does
not hide provisional hydraulic states.

`HydraulicResultStatus` provides the machine-readable computational resolution state:
`valid`, `valid_with_advisory`, `approximate`, or `unresolved`. Barrel status is derived
from stable warning codes, group status follows its representative barrel, and crossing
status conservatively aggregates active groups. Rating-curve points and inventory rows
retain the resulting status so downstream screening does not reinterpret warning text.
This status is not regulatory approval or engineering design acceptance.

`HeadLossComponents` preserves the scalar losses that a calculation actually evaluates.
`full_flow_losses` describes the always-evaluated full-flow candidate;
`outlet_control_losses` describes the physically selected outlet-control candidate. Full
flow supplies entrance, friction, exit, and total loss. A free-surface direct-step result
supplies its separately evaluated entrance loss, while friction is represented throughout
the retained profile rather than collapsed into a new scalar. In these records, `None`
means "not separately calculated by this method" and never means zero.

`exit_loss_selection` records the adopted `Ko`, whether it is the sourced HDS-5
reservoir/pool standard or a user override, and the source when one applies. The standard
is `Ko = 1.0` from HDS-5 Equation 3.4c. Inventory `AdoptedParameterSet` records include
this selection and register its source alongside roughness, inlet-control, and entrance-loss
provenance; callers therefore do not need to inspect package globals to audit defaults.

Numerically solved critical and normal depths retain their `RootResult`. Barrel results
also expose labelled `ConvergenceRecord` entries for applicable depth, profile-boundary,
and hydraulic-jump roots, while multi-group crossing results retain the common-headwater
root and each active group's discharge root. Analytical, capacity-boundary, fast-path,
inactive, and documented interpolation-fallback outcomes have no fabricated root record.
The actual free-surface or inlet-control profile used by regime selection is retained on
the barrel result, including its ordered points and its own convergence evidence. A
full-flow candidate has no profile object because the current method does not calculate
longitudinal profile points.

## Numerical root solving architecture

The library provides two complementary root solvers in `culvert_solver.numerical.roots`:

1. **Certified Bisection (`solve_bracketed`)**:
   Guaranteed linear bisection halving bracket intervals. Used for baseline validation,
   precision benchmarks, and analytical contract tests where step-by-step interval
   diagnostics are required.
2. **Superlinear Brent's Method (`solve_brent`)**:
   Combines bisection, secant, and inverse quadratic interpolation. Concurrently maintains
   a strict bracket while achieving superlinear convergence (typically 4 to 7 iterations
   instead of 25 to 35). Used throughout the high-level engineering core (crossing headwater
   solver, rating curves, critical depth, and normal depth) to achieve rapid design iteration.

Both solvers enforce strict contracts: finite ordered bounds, opposite endpoint signs
(or exact endpoint root), and nonfinite evaluation traps raising `InvalidInputError`.

## Design decision: Enums vs. dataclasses vs. JSON for bulk domain constants

Future auditing agents must note the deliberate design rationale for domain constants:

### 1. Enums for closed vocabularies

- `FlowRegime`, `ControlType`, `GeometryShape`, and `ProfileCurve` inherit from
  `StrEnum`; `InletEquationForm` inherits from `IntEnum`.
- **Rationale**: Culvert flow regimes (`INLET_CONTROL_UNSUBMERGED`, `INLET_CONTROL_TRANSITION`,
  `INLET_CONTROL_SUBMERGED`, `OUTLET_CONTROL_FULL`, and `OUTLET_CONTROL_FREE_SURFACE`)
  form a closed, immutable, universally recognized discrete state category in hydraulic theory.
- An Enum provides compile-time verification under Pyright strict mode, supports exhaustive
  pattern matching (`match ... case`), prevents string typos, and serializes transparently to
  plain strings for JSON or tabular export.

### 2. Frozen dataclasses for materials (`CulvertMaterial`)

- `CulvertMaterial` is a frozen dataclass with standard singletons (`CONCRETE`, `SMOOTH_HDPE`,
  `CORRUGATED_STEEL`).
- Diameter-dependent CSP values are records in `MRWA_CSP_MANNING_TABLE`, selected with a
  `CspCorrugation` enum. This retains the closed vocabulary without pretending the engineering
  values themselves form an enum.
- `resolve_manning_roughness` supports quick calculation defaults and explicit overrides. It
  returns `ManningRoughnessSelection`, including the source and a typed selection basis; it does
  not introduce wrapper, JSON, or mutable global configuration concerns into the calculation core.
- **Why not an Enum?**
  An Enum would prohibit users from defining custom materials (e.g. aged brick, vitrified clay,
  weathered iron, timber) without modifying package source code. A frozen dataclass allows
  the library to provide standard verified materials as typed singletons while treating
  user-defined materials as first-class citizens.

### 3. Frozen dataclasses with metadata for empirical coefficients

- `InletCoefficients` and `EntranceLossCoefficient` are frozen dataclasses with `slots=True`.
- Predefined constants (e.g. `CIRCULAR_CONCRETE_SQUARE_EDGE`, `BOX_LOSS_FLARED_30_75`) are
  defined in Python modules rather than loose external JSON files.
- **Why not JSON files?**
  1. **Static typing and compile-time linting**: Pyright strict mode validates numeric types,
     formula form selectors (`form=1` vs `form=2`), and field existence at lint time without
     runtime schema deserialization overhead.
  2. **Zero runtime I/O overhead**: Eliminates filesystem reads, `importlib.resources` path
     resolution quirks, and missing-asset packaging errors when built into wheels or frozen
     executables.
  3. **Engineering traceability (Work Plan Section 13)**: Every coefficient set contains an
     explicit, immutable `SourceReference` instance with exact publication, table, equation,
     and page citation directly attached.
  4. **Extensibility**: Engineers requiring custom or non-standard inlet configurations
     (e.g. bespoke Australian headwalls, custom wingwall tapers) can instantiate
     `InletCoefficients(...)` directly in code.
  5. JSON serialization can be added at an explicit input/output boundary if external data
     persistence is needed. The computational core does not currently require JSON I/O.

## Performance optimizations (Item 18 / Phase 10)

Brent's method remains the numerical optimisation for nested crossing, critical-depth, and
normal-depth roots. Performance tests bound deterministic work rather than elapsed time:
the fixed M2 case permits at most 20 recorded root iterations, the fixed two-group crossing
permits at most 10 iterations for each exposed root, and rating generation permits exactly
one scalar hydraulic solve per requested point. These thresholds detect algorithmic
regressions without depending on processor speed or machine load.

The former candidate short-circuit has been removed. A fixed counterexample has
`HW_inlet >= HW_full` while the physically routed M2 outlet-control headwater is higher
than both. Enabling the old shortcut would therefore change the headwater and classify the
case as inlet control. The performance suite preserves this comparison explicitly.

Wall-clock results are observational and are collected separately from test gates:

```powershell
$env:PYTHONPATH = "src"
python benchmarks/benchmark_solver.py --samples 7 --single-iterations 500 `
    --crossing-iterations 10 --warmup-batches 2
```

The benchmark warms both fixed cases, disables garbage collection only during samples,
uses `time.perf_counter_ns`, reports minimum/median/p95 milliseconds per operation as JSON,
and records Python, OS, processor, logical CPU count, and clock resolution. Results must be
compared only between equivalently configured environments; they are not portable pass/fail
limits.
