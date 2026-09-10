"""Central physical constants with immutable provenance records."""

from .references.models import SourceReference

GRAVITATIONAL_ACCELERATION: float = 9.80665
STANDARD_WATER_DENSITY: float = 998.2
STANDARD_WATER_KINEMATIC_VISCOSITY: float = 1.004e-6

GRAVITATIONAL_ACCELERATION_REFERENCE = SourceReference(
    source_id="ISO-80000-3-2019",
    publication="ISO 80000-3:2019 Quantities and units — Part 3: Space and time",
    edition="Second edition, 2019-08",
    locator="Item 3-10, standard acceleration of free fall (gn)",
    url="https://www.iso.org/standard/64973.html",
    applicability="Standard terrestrial gravitational acceleration in SI units (m/s²).",
    notes=("Adopted by the 3rd CGPM (1901, CR 70). Constant across all hydraulic primitive functions."),
)

STANDARD_WATER_PROPERTIES_REFERENCE = SourceReference(
    source_id="CRC-HANDBOOK-WATER-20°C",
    publication="CRC Handbook of Chemistry and Physics",
    edition="104th Edition, 2023-2024",
    locator="Section 6: Fluid Properties, Thermophysical Properties of Water",
    url="https://hbcponline.com",
    applicability=(
        "Standard pure water density (998.2 kg/m³) and kinematic viscosity (1.004e-6 m²/s) at 20 °C, 101.325 kPa."
    ),
    notes="Reference temperature for standard SI culvert hydraulic evaluations.",
)
