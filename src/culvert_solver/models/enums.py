"""Closed categorical values used by hydraulic inputs and results."""

from enum import IntEnum, StrEnum


class ControlType(StrEnum):
    """Location of the hydraulic control governing a result."""

    NONE = "none"
    MIXED = "mixed"
    INLET = "inlet_control"
    OUTLET = "outlet_control"


class GeometryShape(StrEnum):
    """Geometry families to which empirical coefficients may apply."""

    ANY = "any"
    CIRCULAR = "circular"
    RECTANGULAR = "rectangular"


class CspCorrugation(StrEnum):
    """MRWA helically wound CSP corrugation pitch by depth in millimetres."""

    PITCH_68_DEPTH_13 = "68x13"
    PITCH_75_DEPTH_25 = "75x25"
    PITCH_125_DEPTH_25 = "125x25"


class RoughnessSelectionBasis(StrEnum):
    """How a resolved Manning roughness value was selected."""

    USER_OVERRIDE = "user_override"
    MATERIAL_TYPICAL = "material_typical"
    MRWA_CONCRETE_TABLE = "mrwa_concrete_table"
    MRWA_CSP_TABLE = "mrwa_csp_table"
    HDS5_DOCUMENTED_FALLBACK = "hds5_documented_fallback"


class ApplicabilityNoticeCode(StrEnum):
    """Stable codes for limitations attached to adopted defaults."""

    MANUFACTURER_DATA_NOT_SUPPLIED = "manufacturer_data_not_supplied"
    HYDRAULIC_VALUE_NOT_CONSTRUCTION_COMPLIANCE = "hydraulic_value_not_construction_compliance"


class InletEquationForm(IntEnum):
    """FHWA HDS-5 unsubmerged inlet-control equation form."""

    SPECIFIC_HEAD = 1
    WEIR = 2


class ProfileCurve(StrEnum):
    """Supported gradually varied flow profile classifications."""

    FULL = "FULL"
    H2 = "H2"
    JS1 = "JS1"
    M1 = "M1"
    M2 = "M2"
    S1 = "S1"
    S2 = "S2"


class InletSelectionBasis(StrEnum):
    """How a resolved inlet-control coefficient set was selected."""

    USER_OVERRIDE = "user_override"
    BARREL_ATTACHED = "barrel_attached"
    GEOMETRY_MATERIAL_DEFAULT = "geometry_material_default"


class EntranceLossSelectionBasis(StrEnum):
    """How a resolved entrance-loss coefficient was selected."""

    USER_OVERRIDE = "user_override"
    BARREL_ATTACHED = "barrel_attached"
    GEOMETRY_DEFAULT = "geometry_default"


class HydraulicWarningCode(StrEnum):
    """Stable codes for supported calculations that retain a documented limitation."""

    INLET_CONTROL_HIGH_HEAD_EXTENSION = "inlet_control_high_head_extension"
    INLET_CONTROL_EXTREME_HEADWATER = "inlet_control_extreme_headwater"
    INLET_OUTLET_DEPTH_APPROXIMATION = "inlet_outlet_depth_approximation"
    MIXED_FLOW_NOT_RESOLVED = "mixed_flow_not_resolved"


class ConvergenceCalculation(StrEnum):
    """Hydraulic calculation associated with a numerical root result."""

    CRITICAL_DEPTH = "critical_depth"
    NORMAL_DEPTH = "normal_depth"
    PROFILE_INLET_BOUNDARY = "profile_inlet_boundary"
    PROFILE_OUTLET_BOUNDARY = "profile_outlet_boundary"
    HYDRAULIC_JUMP = "hydraulic_jump"
    BARREL_DISCHARGE = "barrel_discharge"
    CROSSING_HEADWATER = "crossing_headwater"
