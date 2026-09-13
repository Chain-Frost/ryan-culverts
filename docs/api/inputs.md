# Inputs and configuration

Public types used to describe culverts, crossings, boundaries, and solver policy.

`TailwaterInput` is the public input contract for forward barrel, group, crossing, and
rating-curve solvers. It accepts either an absolute water-surface elevation in metres or a
`TailwaterBoundary` that resolves elevation and provenance for the applicable discharge.
`TailwaterRatingCurve` accepts at least two `TailwaterRatingPoint` values with strictly
increasing discharge and nondecreasing absolute elevation. It returns exact tabulated
stages or linear interpolation inside the supplied range and rejects extrapolation.

Roadway overtopping accepts either a constant-elevation `RoadwayWeir` or an irregular
`RoadwayProfileWeir`. Irregular profiles use a `RoadwayCrestProfile` of strictly increasing
`RoadwayCrestPoint` station/elevation coordinates. Free overflow does not require a surface
class. Downstream-submerged roadway flow requires `RoadwaySurface.PAVED` or
`RoadwaySurface.GRAVEL`, because the implemented correction is limited to those sourced
FHWA relationships.

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
