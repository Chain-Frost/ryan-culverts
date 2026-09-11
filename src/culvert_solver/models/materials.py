"""Culvert barrel material specifications and Manning roughness values."""

from __future__ import annotations

from dataclasses import dataclass

from .._validation import finite
from ..exceptions import InvalidInputError
from ..references.models import SourceReference
from .enums import ApplicabilityNoticeCode, CspCorrugation, RoughnessSelectionBasis

_HDS5_TABLE_B1_REF = SourceReference(
    source_id="FHWA-HDS5-2012-TABLE-B1",
    publication="Hydraulic Design of Highway Culverts",
    edition="Third Edition, April 2012",
    locator=("Appendix B, Table B.1 (printed page B.6; PDF page 208): Manning's n Values for Culverts"),
    url="https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf",
    applicability="Laboratory-derived Manning roughness ranges for identified culvert materials.",
    notes=(
        "Field values may differ with abrasion, corrosion, deflection, and joint condition; "
        "corrugated-metal roughness also varies with barrel size."
    ),
)

MRWA_CSP_REFERENCE = SourceReference(
    source_id="MRWA-CULVERT-DESIGN-PROCEDURE-TABLE-2.2",
    publication="Design Procedure - Culverts",
    edition="Website reviewed 6 September 2026",
    locator="Section 2.8, Table 2.2: Manning's n for helically wound CSP",
    url=(
        "https://www.mainroads.wa.gov.au/technical-commercial/technical-library/"
        "road-traffic-engineering/drainage-waterways/culverts/design-procedure/"
    ),
    applicability=("Nominal circular CSP diameters and corrugation sizes listed in MRWA Table 2.2."),
    notes=(
        "MRWA attributes the table to AISI (1999). The MRWA Part 5B supplement directs "
        "designers to manufacturer data first and this table when manufacturer data is absent. "
        "A hydraulic lookup does not establish current MRWA product or construction compliance."
    ),
)

MRWA_CONCRETE_REFERENCE = SourceReference(
    source_id="MRWA-CULVERT-DESIGN-PROCEDURE-TABLE-2.1-V2E",
    publication="Design Procedure - Culverts",
    edition="Version 2E, 5 May 2026",
    locator="Section 2.8, Table 2.1: Manning's n for RCP and RCB",
    url=(
        "https://www.mainroads.wa.gov.au/technical-commercial/technical-library/"
        "road-traffic-engineering/drainage-waterways/culverts/design-procedure/"
    ),
    applicability="Smooth reinforced-concrete pipe and box culverts used in MRWA design.",
    notes=("The table gives 0.011-0.013 for concrete pipe and 0.012-0.015 for concrete box."),
)

MRWA_PART5B_REFERENCE = SourceReference(
    source_id="MRWA-SUPPLEMENT-AGRD-PART5B-1F",
    publication=(
        "MRWA Supplement to Austroads Guide to Road Design Part 5B: Drainage, Open Channels, Culverts and Floodways"
    ),
    edition="Version 1F, 3 July 2020; live page reviewed 8 September 2026",
    locator="Section 3.2: Information Required",
    url=(
        "https://www.mainroads.wa.gov.au/technical-commercial/technical-library/"
        "road-traffic-engineering/guide-to-road-design/"
        "mrwa-supplement-to-austroads-guide-to-road-design-part-5b/"
    ),
    applicability="MRWA culvert-design roughness source precedence.",
    notes="Plastic-pipe Manning roughness is to be sourced from the applicable manufacturer.",
)

MRWA_SPEC404_REFERENCE = SourceReference(
    source_id="MRWA-SPECIFICATION-404-2026-07-17",
    publication="Specification 404 Culverts",
    edition="05/6181-003, issued 17 July 2026",
    locator="Scope, products and materials, and contract-specific requirements",
    url=(
        "https://www.mainroads.wa.gov.au/globalassets/technical-commercial/"
        "technical-library/specifications/400-series-drainage/"
        "specification-404-culverts.pdf"
    ),
    applicability="Product and construction requirements for MRWA culverts.",
    notes="Hydraulic roughness selection alone does not demonstrate specification compliance.",
)


@dataclass(frozen=True, slots=True)
class CulvertMaterial:
    """A culvert barrel material and its documented Manning roughness range."""

    name: str
    typical_n: float
    range_n: tuple[float, float]
    reference: SourceReference = _HDS5_TABLE_B1_REF
    contextual_roughness_required: bool = False
    manufacturer_roughness_required: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "name must be nonempty text."
            raise InvalidInputError(msg)
        typ = finite(self.typical_n, "typical_n")
        if typ <= 0:
            msg = "typical_n must be strictly positive."
            raise InvalidInputError(msg)
        if len(self.range_n) != 2:
            msg = "range_n must be a 2-tuple of (min_n, max_n)."
            raise InvalidInputError(msg)
        min_n = finite(self.range_n[0], "range_n[0]")
        max_n = finite(self.range_n[1], "range_n[1]")
        if min_n <= 0:
            msg = "range_n minimum must be strictly positive."
            raise InvalidInputError(msg)
        if min_n > max_n:
            msg = "range_n minimum cannot exceed maximum."
            raise InvalidInputError(msg)
        if not min_n <= typ <= max_n:
            msg = "typical_n must lie within range_n."
            raise InvalidInputError(msg)
        object.__setattr__(self, "typical_n", typ)
        object.__setattr__(self, "range_n", (min_n, max_n))


@dataclass(frozen=True, slots=True)
class CspManningEntry:
    """One available diameter/corrugation Manning value from MRWA Table 2.2."""

    nominal_diameter_mm: int
    corrugation: CspCorrugation
    manning_n: float


@dataclass(frozen=True, slots=True)
class ManningRoughnessSelection:
    """Resolved Manning value with its selection basis and source provenance."""

    value: float
    basis: RoughnessSelectionBasis
    material_name: str
    source: SourceReference | None
    notices: tuple[RoughnessApplicabilityNotice, ...] = ()

    def __post_init__(self) -> None:
        value = finite(self.value, "value")
        if value <= 0:
            msg = "value must be strictly positive."
            raise InvalidInputError(msg)
        if not self.material_name.strip():
            msg = "material_name must be nonempty text."
            raise InvalidInputError(msg)
        if self.basis is not RoughnessSelectionBasis.USER_OVERRIDE and self.source is None:
            msg = "A library default must identify its source."
            raise InvalidInputError(msg)
        object.__setattr__(self, "value", value)

    @property
    def used_default(self) -> bool:
        """Return whether the value came from a library default rather than an override."""
        return self.basis is not RoughnessSelectionBasis.USER_OVERRIDE


@dataclass(frozen=True, slots=True)
class RoughnessApplicabilityNotice:
    """Machine-readable limitation attached to a roughness fallback."""

    code: ApplicabilityNoticeCode
    message: str
    source: SourceReference


MRWA_CSP_MANNING_TABLE: tuple[CspManningEntry, ...] = (
    CspManningEntry(300, CspCorrugation.PITCH_68_DEPTH_13, 0.011),
    CspManningEntry(375, CspCorrugation.PITCH_68_DEPTH_13, 0.012),
    CspManningEntry(450, CspCorrugation.PITCH_68_DEPTH_13, 0.013),
    CspManningEntry(600, CspCorrugation.PITCH_68_DEPTH_13, 0.015),
    CspManningEntry(750, CspCorrugation.PITCH_68_DEPTH_13, 0.017),
    CspManningEntry(900, CspCorrugation.PITCH_68_DEPTH_13, 0.018),
    CspManningEntry(900, CspCorrugation.PITCH_75_DEPTH_25, 0.022),
    CspManningEntry(1050, CspCorrugation.PITCH_68_DEPTH_13, 0.019),
    CspManningEntry(1050, CspCorrugation.PITCH_75_DEPTH_25, 0.022),
    CspManningEntry(1200, CspCorrugation.PITCH_68_DEPTH_13, 0.020),
    CspManningEntry(1200, CspCorrugation.PITCH_75_DEPTH_25, 0.023),
    CspManningEntry(1200, CspCorrugation.PITCH_125_DEPTH_25, 0.022),
    CspManningEntry(1350, CspCorrugation.PITCH_68_DEPTH_13, 0.021),
    CspManningEntry(1350, CspCorrugation.PITCH_75_DEPTH_25, 0.023),
    CspManningEntry(1350, CspCorrugation.PITCH_125_DEPTH_25, 0.022),
    CspManningEntry(1500, CspCorrugation.PITCH_68_DEPTH_13, 0.021),
    CspManningEntry(1500, CspCorrugation.PITCH_75_DEPTH_25, 0.024),
    CspManningEntry(1500, CspCorrugation.PITCH_125_DEPTH_25, 0.023),
    CspManningEntry(1650, CspCorrugation.PITCH_68_DEPTH_13, 0.021),
    CspManningEntry(1650, CspCorrugation.PITCH_75_DEPTH_25, 0.025),
    CspManningEntry(1650, CspCorrugation.PITCH_125_DEPTH_25, 0.024),
    CspManningEntry(1800, CspCorrugation.PITCH_68_DEPTH_13, 0.021),
    CspManningEntry(1800, CspCorrugation.PITCH_75_DEPTH_25, 0.026),
    CspManningEntry(1800, CspCorrugation.PITCH_125_DEPTH_25, 0.024),
    CspManningEntry(1950, CspCorrugation.PITCH_68_DEPTH_13, 0.021),
    CspManningEntry(1950, CspCorrugation.PITCH_75_DEPTH_25, 0.027),
    CspManningEntry(1950, CspCorrugation.PITCH_125_DEPTH_25, 0.025),
)


def resolve_csp_manning_roughness(
    nominal_diameter_mm: float,
    corrugation: CspCorrugation | str,
    *,
    override: float | None = None,
) -> float:
    """Resolve CSP Manning roughness using an override or MRWA Table 2.2.

    A positive finite ``override`` always wins. Otherwise the diameter must be a
    listed MRWA nominal size; diameters at or above 1950 mm use the table's
    ``1950 & Larger`` row. Unavailable corrugation/diameter combinations fail
    explicitly instead of borrowing a value from another pipe.
    """
    if override is not None:
        override_value = finite(override, "override")
        if override_value <= 0:
            msg = "override must be strictly positive."
            raise InvalidInputError(msg)
        return override_value

    diameter = finite(nominal_diameter_mm, "nominal_diameter_mm")
    if diameter <= 0:
        msg = "nominal_diameter_mm must be strictly positive."
        raise InvalidInputError(msg)
    try:
        selected_corrugation = CspCorrugation(corrugation)
    except TypeError, ValueError:
        msg = "corrugation must be a recognized CspCorrugation value."
        raise InvalidInputError(msg) from None

    lookup_diameter = min(1950, diameter)
    for entry in MRWA_CSP_MANNING_TABLE:
        if entry.nominal_diameter_mm == lookup_diameter and entry.corrugation is selected_corrugation:
            return entry.manning_n

    msg = (
        "No MRWA Table 2.2 CSP Manning value exists for "
        f"diameter {diameter:g} mm and corrugation {selected_corrugation.value}. "
        "Supply a positive project or manufacturer override explicitly."
    )
    raise InvalidInputError(msg)


def resolve_manning_roughness(
    material: CulvertMaterial,
    *,
    override: float | None = None,
    override_source: SourceReference | None = None,
    nominal_diameter_mm: float | None = None,
    csp_corrugation: CspCorrugation | str | None = None,
    allow_documented_fallback: bool = False,
) -> ManningRoughnessSelection:
    """Resolve an overridable preliminary Manning value for hydraulic calculations.

    Explicit positive overrides always win and may include a manufacturer or project
    source. Concrete pipe and box records use the current MRWA ranges. Context-dependent
    CSP requires diameter and corrugation. Plastic requires manufacturer data unless the
    caller explicitly opts into the documented HDS-5 fallback, which carries a notice.
    """
    if override is not None:
        return ManningRoughnessSelection(
            value=override,
            basis=RoughnessSelectionBasis.USER_OVERRIDE,
            material_name=material.name,
            source=override_source,
        )
    if override_source is not None:
        msg = "override_source requires an override value."
        raise InvalidInputError(msg)

    if material == CONCRETE:
        msg = (
            "Generic concrete has no unambiguous roughness default; select "
            "CONCRETE_PIPE or CONCRETE_BOX, or provide an explicit override."
        )
        raise InvalidInputError(msg)

    if material.manufacturer_roughness_required:
        if not allow_documented_fallback:
            msg = (
                "Plastic-pipe Manning roughness must be supplied from the applicable "
                "manufacturer. Pass an explicit override, or set allow_documented_fallback=True "
                "to adopt the HDS-5 laboratory value with an applicability notice."
            )
            raise InvalidInputError(msg)
        return ManningRoughnessSelection(
            value=material.typical_n,
            basis=RoughnessSelectionBasis.HDS5_DOCUMENTED_FALLBACK,
            material_name=material.name,
            source=material.reference,
            notices=(
                RoughnessApplicabilityNotice(
                    code=ApplicabilityNoticeCode.MANUFACTURER_DATA_NOT_SUPPLIED,
                    message=(
                        "Applicable manufacturer roughness was not supplied; this value is "
                        "an explicitly accepted HDS-5 laboratory fallback."
                    ),
                    source=MRWA_PART5B_REFERENCE,
                ),
                RoughnessApplicabilityNotice(
                    code=ApplicabilityNoticeCode.HYDRAULIC_VALUE_NOT_CONSTRUCTION_COMPLIANCE,
                    message=(
                        "A hydraulic roughness fallback does not establish MRWA product or construction compliance."
                    ),
                    source=MRWA_SPEC404_REFERENCE,
                ),
            ),
        )

    if material.contextual_roughness_required:
        if material != CORRUGATED_STEEL:
            msg = f"No contextual roughness resolver is registered for material {material.name!r}."
            raise InvalidInputError(msg)
        if nominal_diameter_mm is None or csp_corrugation is None:
            msg = "CSP preliminary roughness requires nominal_diameter_mm and csp_corrugation, or an explicit override."
            raise InvalidInputError(msg)
        return ManningRoughnessSelection(
            value=resolve_csp_manning_roughness(nominal_diameter_mm, csp_corrugation),
            basis=RoughnessSelectionBasis.MRWA_CSP_TABLE,
            material_name=material.name,
            source=MRWA_CSP_REFERENCE,
            notices=(
                RoughnessApplicabilityNotice(
                    code=ApplicabilityNoticeCode.HYDRAULIC_VALUE_NOT_CONSTRUCTION_COMPLIANCE,
                    message=(
                        "The MRWA hydraulic lookup does not establish current product or construction compliance."
                    ),
                    source=MRWA_SPEC404_REFERENCE,
                ),
            ),
        )

    basis = (
        RoughnessSelectionBasis.MRWA_CONCRETE_TABLE
        if material in {CONCRETE_PIPE, CONCRETE_BOX}
        else RoughnessSelectionBasis.MATERIAL_TYPICAL
    )
    return ManningRoughnessSelection(
        value=material.typical_n,
        basis=basis,
        material_name=material.name,
        source=material.reference,
    )


# Standard materials from HDS-5 Appendix B / Table B.1 (Manning roughness)
CONCRETE = CulvertMaterial(
    name="Concrete (select pipe or box for roughness resolution)",
    typical_n=0.012,
    range_n=(0.010, 0.015),
)

CONCRETE_PIPE = CulvertMaterial(
    name="Smooth Reinforced Concrete Pipe",
    typical_n=0.012,
    range_n=(0.011, 0.013),
    reference=MRWA_CONCRETE_REFERENCE,
)

CONCRETE_BOX = CulvertMaterial(
    name="Smooth Reinforced Concrete Box",
    typical_n=0.012,
    range_n=(0.012, 0.015),
    reference=MRWA_CONCRETE_REFERENCE,
)

SMOOTH_HDPE = CulvertMaterial(
    name="Smooth Interior Corrugated Polyethylene",
    typical_n=0.012,
    range_n=(0.009, 0.015),
    manufacturer_roughness_required=True,
)

CORRUGATED_STEEL = CulvertMaterial(
    name="Corrugated Steel Pipe (diameter/corrugation-specific n required)",
    # Catalog value retained for compatibility; do not use it as an automatic CSP default.
    typical_n=0.024,
    range_n=(0.011, 0.027),
    reference=MRWA_CSP_REFERENCE,
    contextual_roughness_required=True,
)
