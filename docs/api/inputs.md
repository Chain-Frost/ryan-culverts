# Inputs and configuration

Public types used to describe culverts, crossings, boundaries, and solver policy.

`TailwaterInput` is the public input contract for forward barrel, group, crossing, and
rating-curve solvers. It accepts either an absolute water-surface elevation in metres or a
`TailwaterBoundary` that resolves elevation and provenance for the applicable discharge.
`TailwaterRatingCurve` accepts at least two `TailwaterRatingPoint` values with strictly
increasing discharge and nondecreasing absolute elevation. It returns exact tabulated
stages or linear interpolation inside the supplied range and rejects extrapolation.

## Standard culvert defaults

When inlet-control coefficients and entrance-loss coefficients are omitted, the default
solver configuration resolves the following common physical arrangements from geometry and
material:

| Geometry/material | Default arrangement | Entrance loss |
| --- | --- | ---: |
| Circular `CORRUGATED_STEEL` | CSP projecting from fill | `Ke = 0.9` |
| Circular `CONCRETE_PIPE` | Square-edge headwall or headwall with wingwalls | `Ke = 0.5` |
| Rectangular `CONCRETE_BOX` | Square top edge with 30–75° flared wingwalls, including 45° | `Ke = 0.4` |

Explicit barrel or resolver values override these defaults. For CSP roughness, an explicit
project/manufacturer value wins; otherwise an explicit diameter/corrugation pair uses the
MRWA table. Diameter-only standard MRWA CSP uses the Specification 404 corrugation before
the MRWA table. Other unresolved CSP context fails closed unless `allow_documented_fallback=True`
explicitly accepts Austroads `n = 0.024` for plain or unpaved small-corrugation
corrugated metal pipe; the selection then carries an applicability notice.
HDPE does not receive an automatic inlet/loss arrangement.

### Canonical CSP barrel construction

`CulvertBarrel.roughness` remains an explicit SI input. The core barrel dataclass does
not silently resolve material roughness because the selected value, source, and
applicability notices are part of the engineering input record. Resolve the roughness
first, then attach the complete selection to the barrel:

```python
roughness = resolve_manning_roughness(
    CORRUGATED_STEEL,
    nominal_diameter_mm=1200,
)

barrel = CulvertBarrel(
    geometry=CircularGeometry.from_mm(1200),
    length=20.0,
    inlet_invert=10.0,
    outlet_invert=9.8,
    roughness=roughness.value,
    material=CORRUGATED_STEEL,
    roughness_selection=roughness,
)

result = solve_barrel_hydraulics(
    barrel,
    discharge=1.0,
    tailwater=9.8,
)
```

For the adopted MRWA schedule in this release, the example resolves to `n = 0.020`
and retains both the MRWA roughness source and the notice that the standard
Specification 404 corrugation was assumed. Explicit project/manufacturer roughness or
an explicit corrugation takes precedence. Broader CSP product schedules and presets are
outside this PR and can be added separately.

Roadway overtopping accepts either a constant-elevation `RoadwayWeir` or an irregular
`RoadwayProfileWeir`. Irregular profiles use a `RoadwayCrestProfile` of strictly increasing
`RoadwayCrestPoint` station/elevation coordinates. Free overflow does not require a surface
class. Downstream-submerged roadway flow requires `RoadwaySurface.PAVED` or
`RoadwaySurface.GRAVEL`, because the implemented correction is limited to those sourced
FHWA relationships. The correction is bounded to a local downstream/upstream head ratio of
0.99. Ratios between 0.99 and equal stage fail closed rather than extrapolating the sourced
curve; exactly equal upstream and downstream water levels produce zero roadway flow. For a
crossing, the common-headwater solve is bounded to this same supported domain and rejects a
requested discharge below the minimum evaluable submerged-roadway capacity.

::: culvert_solver
    options:
      members:
        - CircularGeometry
        - RectangularGeometry
        - FilletedRectangularGeometry
        - CrossSectionGeometry
        - CulvertBarrel
        - CulvertGroup
        - CulvertCrossing
        - CulvertInventory
        - CulvertInventoryItem
        - RoadwayWeir
        - RoadwayProfileWeir
        - RoadwayCrestProfile
        - RoadwayCrestPoint
        - RoadwaySurface
        - RoadwayOvertoppingInput
        - TailwaterBoundary
        - TailwaterCondition
        - TailwaterInput
        - ManningChannelTailwater
        - TailwaterRatingCurve
        - TailwaterRatingPoint
        - OpenChannelSection
        - RectangularChannel
        - TrapezoidalChannel
        - CulvertMaterial
        - InletCoefficients
        - EntranceLossCoefficient
        - ModernBoxInlet
        - SolverConfiguration
        - RootTolerances
        - SourceReference
        - ControlType
        - GeometryShape
        - CspCorrugation
        - InletEquationForm
        - BoxCrownTreatment
        - BoxWingwallTreatment
      show_root_heading: false
      heading_level: 2
