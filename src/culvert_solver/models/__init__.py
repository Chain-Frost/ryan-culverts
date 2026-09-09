"""Domain models for culvert barrels, groups, crossings, and materials."""

from .barrel import CulvertBarrel
from .crossing import CulvertCrossing
from .enums import (
    ApplicabilityNoticeCode,
    ControlType,
    CspCorrugation,
    ExitLossSelectionBasis,
    GeometryShape,
    InletEquationForm,
    ProfileCurve,
    RoughnessSelectionBasis,
)
from .group import CulvertGroup
from .materials import (
    CONCRETE,
    CONCRETE_BOX,
    CONCRETE_PIPE,
    CORRUGATED_STEEL,
    MRWA_CONCRETE_REFERENCE,
    MRWA_CSP_MANNING_TABLE,
    MRWA_CSP_REFERENCE,
    MRWA_PART5B_REFERENCE,
    MRWA_SPEC404_REFERENCE,
    SMOOTH_HDPE,
    CspManningEntry,
    CulvertMaterial,
    ManningRoughnessSelection,
    RoughnessApplicabilityNotice,
    resolve_csp_manning_roughness,
    resolve_manning_roughness,
)
from .results import (
    BarrelHydraulicResult,
    CrossingHydraulicResult,
    FlowRegime,
    GroupHydraulicResult,
)
from .roadway import FHWA_HDS5_ROADWAY_OVERTOPPING, RoadwayWeir
from .tailwater import TailwaterCondition

__all__: list[str] = [
    "CONCRETE",
    "CONCRETE_BOX",
    "CONCRETE_PIPE",
    "CORRUGATED_STEEL",
    "MRWA_CSP_MANNING_TABLE",
    "MRWA_CSP_REFERENCE",
    "MRWA_CONCRETE_REFERENCE",
    "MRWA_PART5B_REFERENCE",
    "MRWA_SPEC404_REFERENCE",
    "SMOOTH_HDPE",
    "BarrelHydraulicResult",
    "ApplicabilityNoticeCode",
    "CrossingHydraulicResult",
    "CulvertBarrel",
    "CulvertCrossing",
    "CulvertGroup",
    "CulvertMaterial",
    "CspCorrugation",
    "CspManningEntry",
    "ExitLossSelectionBasis",
    "ControlType",
    "FlowRegime",
    "FHWA_HDS5_ROADWAY_OVERTOPPING",
    "GeometryShape",
    "GroupHydraulicResult",
    "InletEquationForm",
    "ManningRoughnessSelection",
    "ProfileCurve",
    "RoughnessSelectionBasis",
    "RoughnessApplicabilityNotice",
    "RoadwayWeir",
    "TailwaterCondition",
    "resolve_csp_manning_roughness",
    "resolve_manning_roughness",
]
