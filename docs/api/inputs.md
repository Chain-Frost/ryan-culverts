# Inputs and configuration

Public types used to describe culverts, crossings, boundaries, and solver policy.

`TailwaterInput` is the public input contract for forward barrel, group, crossing, and
rating-curve solvers. It accepts either an absolute water-surface elevation in metres or a
`TailwaterBoundary` that resolves elevation and provenance for the applicable discharge.

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
