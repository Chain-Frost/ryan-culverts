# Results and diagnostics

Return types retain adopted values, source provenance, warnings, and convergence evidence.

`RoadwayOvertoppingResult.segment_results` preserves the horizontal integration pieces used
for roadway flow. Each `RoadwayOvertoppingSegmentResult` records the local crest elevation,
effective horizontal length, local upstream/downstream heads, discharge contribution and
integration source. Where downstream submergence applies, the segment also retains a
`RoadwaySubmergenceCorrection` with the interpolated factor plus the governing FHWA source
and the digital-ordinate source used by the implementation.

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
