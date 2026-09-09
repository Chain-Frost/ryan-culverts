"""Inlet control coefficient sets and metadata from FHWA HDS-5."""

from dataclasses import dataclass

from .._validation import finite, positive_integer
from ..exceptions import InvalidInputError
from ..models.enums import GeometryShape, InletEquationForm
from ..references.models import SourceReference

_HDS5_TABLE_A1_INLET_REF = SourceReference(
    source_id="FHWA-HDS5-2012-TABLE-A1",
    publication="Hydraulic Design of Highway Culverts",
    edition="Third Edition, April 2012",
    locator="Appendix A, Table A.1: Constants for Inlet Control Equations",
    url="https://www.fhwa.dot.gov/engineering/hydraulics/pubs/12026/hif12026.pdf",
    applicability=(
        "Empirical constants K, M, c, Y and equation forms for conventional culvert inlets."
    ),
    notes="Adopted from NBS research (French, Bossy) and published in FHWA HDS-5 Appendix A.",
)


@dataclass(frozen=True, slots=True)
class InletCoefficients:
    """Empirical regression constants and equation form for culvert inlet control."""

    name: str
    chart: int | None
    scale: int | None
    form: InletEquationForm
    k: float
    m: float
    c: float
    y: float
    slope_correction: float = -0.5
    shape: GeometryShape = GeometryShape.ANY
    reference: SourceReference = _HDS5_TABLE_A1_INLET_REF

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidInputError("name must be nonempty text.")
        chart_val: None | int = (
            None if self.chart is None else positive_integer(self.chart, "chart")
        )
        scale_val: None | int = (
            None if self.scale is None else positive_integer(self.scale, "scale")
        )
        try:
            form_val = InletEquationForm(self.form)
        except (TypeError, ValueError) as exc:
            raise InvalidInputError(
                "form must be InletEquationForm.SPECIFIC_HEAD or WEIR."
            ) from exc
        k_val: float = finite(self.k, "k")
        if k_val <= 0:
            raise InvalidInputError("k must be strictly positive.")
        m_val: float = finite(self.m, "m")
        if m_val <= 0:
            raise InvalidInputError("m must be strictly positive.")
        c_val: float = finite(self.c, "c")
        if c_val <= 0:
            raise InvalidInputError("c must be strictly positive.")
        y_val: float = finite(self.y, "y")
        if y_val <= 0:
            raise InvalidInputError("y must be strictly positive.")
        ks_val: float = finite(self.slope_correction, "slope_correction")
        try:
            shape_val = GeometryShape(self.shape)
        except (TypeError, ValueError) as exc:
            raise InvalidInputError(
                "shape must be GeometryShape.CIRCULAR, RECTANGULAR, or ANY."
            ) from exc

        object.__setattr__(self, "chart", chart_val)
        object.__setattr__(self, "scale", scale_val)
        object.__setattr__(self, "form", form_val)
        object.__setattr__(self, "k", k_val)
        object.__setattr__(self, "m", m_val)
        object.__setattr__(self, "c", c_val)
        object.__setattr__(self, "y", y_val)
        object.__setattr__(self, "slope_correction", ks_val)
        object.__setattr__(self, "shape", shape_val)


# Predefined coefficients from FHWA HDS-5 Table A.1
CIRCULAR_CONCRETE_SQUARE_EDGE = InletCoefficients(
    name="Circular Concrete, Square edge with headwall",
    chart=1,
    scale=1,
    form=InletEquationForm.SPECIFIC_HEAD,
    k=0.0098,
    m=2.0,
    c=0.0398,
    y=0.67,
    shape=GeometryShape.CIRCULAR,
)

CIRCULAR_CONCRETE_GROOVE_END = InletCoefficients(
    name="Circular Concrete, Groove end with headwall",
    chart=1,
    scale=2,
    form=InletEquationForm.SPECIFIC_HEAD,
    k=0.0018,
    m=2.0,
    c=0.0292,
    y=0.74,
    shape=GeometryShape.CIRCULAR,
)

CIRCULAR_CMP_HEADWALL = InletCoefficients(
    name="Circular Corrugated Metal, Headwall",
    chart=2,
    scale=1,
    form=InletEquationForm.SPECIFIC_HEAD,
    k=0.0078,
    m=2.0,
    c=0.0379,
    y=0.69,
    shape=GeometryShape.CIRCULAR,
)

CIRCULAR_CMP_MITERED = InletCoefficients(
    name="Circular Corrugated Metal, Mitered to slope",
    chart=2,
    scale=2,
    form=InletEquationForm.SPECIFIC_HEAD,
    k=0.0210,
    m=1.33,
    c=0.0463,
    y=0.75,
    slope_correction=0.7,
    shape=GeometryShape.CIRCULAR,
)

CIRCULAR_CMP_PROJECTING = InletCoefficients(
    name="Circular Corrugated Metal, Projecting",
    chart=2,
    scale=3,
    form=InletEquationForm.SPECIFIC_HEAD,
    k=0.0340,
    m=1.50,
    c=0.0553,
    y=0.54,
    shape=GeometryShape.CIRCULAR,
)

BOX_CONCRETE_FLARED_WINGWALLS_30_75 = InletCoefficients(
    name="Box Concrete, 30° to 75° wingwall flares",
    chart=8,
    scale=1,
    form=InletEquationForm.SPECIFIC_HEAD,
    k=0.026,
    m=1.0,
    c=0.0347,
    y=0.81,
    shape=GeometryShape.RECTANGULAR,
)

BOX_CONCRETE_PARALLEL_WINGWALLS_0 = InletCoefficients(
    name="Box Concrete, 0° wingwall flares (parallel wingwalls)",
    chart=8,
    scale=3,
    form=InletEquationForm.SPECIFIC_HEAD,
    k=0.061,
    m=0.75,
    c=0.0423,
    y=0.82,
    shape=GeometryShape.RECTANGULAR,
)

BOX_CONCRETE_CHAMFER_90_HEADWALL = InletCoefficients(
    name='Box Concrete, 90° headwall with 3/4" chamfers',
    chart=10,
    scale=1,
    form=InletEquationForm.WEIR,
    k=0.515,
    m=0.667,
    c=0.0375,
    y=0.79,
    shape=GeometryShape.RECTANGULAR,
)

BOX_CONCRETE_BEVEL_45_HEADWALL = InletCoefficients(
    name="Box Concrete, 90° headwall with 45° bevels",
    chart=10,
    scale=2,
    form=InletEquationForm.WEIR,
    k=0.495,
    m=0.667,
    c=0.0314,
    y=0.82,
    shape=GeometryShape.RECTANGULAR,
)


STANDARD_INLET_COEFFICIENTS: tuple[InletCoefficients, ...] = (
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    CIRCULAR_CONCRETE_GROOVE_END,
    CIRCULAR_CMP_HEADWALL,
    CIRCULAR_CMP_MITERED,
    CIRCULAR_CMP_PROJECTING,
    BOX_CONCRETE_FLARED_WINGWALLS_30_75,
    BOX_CONCRETE_PARALLEL_WINGWALLS_0,
    BOX_CONCRETE_CHAMFER_90_HEADWALL,
    BOX_CONCRETE_BEVEL_45_HEADWALL,
)
