# Results and diagnostics

Return types retain adopted values, source provenance, warnings, and convergence evidence.

`RoadwayOvertoppingResult.segment_results` preserves the horizontal integration pieces used
for roadway flow. Each `RoadwayOvertoppingSegmentResult` records the local crest elevation,
effective horizontal length, local upstream/downstream heads, discharge contribution and
integration source. Where downstream submergence applies, the segment also retains a
`RoadwaySubmergenceCorrection` with the interpolated factor plus the governing FHWA source
and the digital-ordinate source used by the implementation.

For downstream floodway analysis, each roadway segment result also exposes local
`unit_discharge` in m²/s, a machine-readable `flow_state`, direct `submergence_ratio` and
`submergence_factor` accessors, and `physical_interval_length`. The supported flow-state
values are `inactive`, `free_unsubmerged`, and `supported_submerged`. The physical interval
length is the horizontal roadway interval represented by the integration point;
`effective_length` is the Gaussian quadrature weight multiplied by that interval and must
not be interpreted as a physical pavement, shoulder, protection, or floodway design-zone
length. No critical-depth, velocity, Froude-number, shear, momentum, or protection-design
quantity is inferred from these integration results because those derived quantities are
not established as generally applicable across the supported roadway-flow states.

## Longitudinal hydraulic profile convention

`BarrelHydraulicResult.longitudinal_profile` is the downstream-consumable profile contract
for plotting and reporting. Stations are SI metres measured along the barrel from the inlet
(`0.0`) to the outlet (`barrel.length`). Invert and crown elevations use the same absolute
datum as the barrel inverts and tailwater boundary.

Each `HydraulicProfilePoint` explicitly identifies its `HydraulicProfileState`:

- `free_surface`: `water_surface_elevation` is the physical water surface and is also the HGL;
- `pressurised`: `water_surface_elevation` is `None`; `hydraulic_grade_elevation` is the
  piezometric HGL and must not be presented as a physical free surface.

`energy_grade_elevation` is HGL plus velocity head. `cumulative_friction_loss` accumulates
barrel friction from the inlet station; entrance and exit losses are retained separately on
`LongitudinalHydraulicProfile` so presentation code does not double count boundary losses.
Supported mixed paths preserve inlet-to-outlet ordering and record their free/full transition
station. The existing `ProfilePoint`, `WaterSurfaceProfile`, and `InletControlProfile` types
remain the direct-step/free-surface calculation records and are not redefined as pressurised
HGL points.

::: culvert_solver
    options:
      members:
        - BarrelHydraulicResult
        - GroupHydraulicResult
        - CrossingHydraulicResult
        - InletControlResult
        - FullFlowOutletResult
        - PartialFlowOutletResult
        - ModernBoxInletResult
        - RoadwayOvertoppingResult
        - RoadwayOvertoppingSegmentResult
        - RoadwaySubmergenceCorrection
        - CriticalDepthResult
        - NormalDepthResult
        - ChannelNormalDepthResult
        - RatingCurveResult
        - RatingCurvePoint
        - WaterSurfaceProfile
        - InletControlProfile
        - ProfilePoint
        - LongitudinalHydraulicProfile
        - HydraulicProfilePoint
        - HydraulicProfileState
        - HeadLossComponents
        - ConvergenceRecord
        - RootResult
        - HydraulicWarning
        - HydraulicApplicabilityNotice
        - REPRESENTATIVE_BARREL_EQUAL_FLOW_NOTICE
        - NCHRP_734_REPRESENTATIVE_BARREL
        - ManningRoughnessSelection
        - RoughnessApplicabilityNotice
        - InletCoefficientSelection
        - EntranceLossSelection
        - ExitLossSelection
        - TailwaterResolution
        - InventorySummary
        - CrossingSummary
        - GroupSummary
        - AdoptedParameterSet
        - FlowRegime
        - ProfileCurve
        - HydraulicWarningCode
        - HydraulicResultStatus
        - ConvergenceCalculation
        - ApplicabilityNoticeCode
        - RoughnessSelectionBasis
        - InletSelectionBasis
        - EntranceLossSelectionBasis
        - ExitLossSelectionBasis
        - TailwaterMethod
        - TailwaterInterpolation
        - InvalidInputError
        - ConvergenceError
      show_root_heading: false
      heading_level: 2
