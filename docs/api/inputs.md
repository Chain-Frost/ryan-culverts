# Inputs and configuration

Public types used to describe culverts, crossings, boundaries, and solver policy.

`TailwaterInput` is the public input contract for forward barrel, group, crossing, and
rating-curve solvers. It accepts either an absolute water-surface elevation in metres or a
`TailwaterBoundary` that resolves elevation and provenance for the applicable discharge.
`TailwaterRatingCurve` accepts at least two `TailwaterRatingPoint` values with strictly
increasing discharge and nondecreasing absolute elevation. It returns exact tabulated
stages or linear interpolation inside the supplied range and rejects extrapolation.

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
