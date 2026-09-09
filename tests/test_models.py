"""Unit and contract tests for core domain models."""

import json
import math
from dataclasses import FrozenInstanceError

import pytest

from culvert_solver import (
    CONCRETE,
    CONCRETE_BOX,
    CONCRETE_PIPE,
    CORRUGATED_STEEL,
    MRWA_CSP_MANNING_TABLE,
    SMOOTH_HDPE,
    ApplicabilityNoticeCode,
    BarrelHydraulicResult,
    CircularGeometry,
    ControlType,
    CrossingHydraulicResult,
    CspCorrugation,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    CulvertMaterial,
    FlowRegime,
    GroupHydraulicResult,
    InvalidInputError,
    ManningRoughnessSelection,
    RectangularGeometry,
    RoughnessSelectionBasis,
    TailwaterCondition,
    resolve_csp_manning_roughness,
    resolve_manning_roughness,
)


def test_standard_materials() -> None:
    assert CONCRETE.typical_n == pytest.approx(0.012)
    assert CONCRETE.range_n == (0.010, 0.015)
    assert SMOOTH_HDPE.typical_n == pytest.approx(0.012)
    assert CORRUGATED_STEEL.typical_n == pytest.approx(0.024)
    assert CORRUGATED_STEEL.contextual_roughness_required
    assert CONCRETE_PIPE.range_n == (0.011, 0.013)
    assert CONCRETE_BOX.range_n == (0.012, 0.015)
    assert SMOOTH_HDPE.manufacturer_roughness_required

    custom = CulvertMaterial(
        name="Custom Lining",
        typical_n=0.015,
        range_n=(0.014, 0.016),
    )
    assert custom.typical_n == 0.015

    with pytest.raises(InvalidInputError, match="name"):
        CulvertMaterial(name="", typical_n=0.015, range_n=(0.014, 0.016))
    with pytest.raises(InvalidInputError, match="typical_n"):
        CulvertMaterial(name="Test", typical_n=-0.01, range_n=(0.01, 0.02))
    with pytest.raises(InvalidInputError, match="range_n"):
        CulvertMaterial(name="Test", typical_n=0.015, range_n=(0.02, 0.01))
    with pytest.raises(InvalidInputError, match="within"):
        CulvertMaterial(name="Test", typical_n=0.03, range_n=(0.01, 0.02))


@pytest.mark.parametrize(
    ("diameter_mm", "expected_values"),
    [
        (300, (0.011, None, None)),
        (375, (0.012, None, None)),
        (450, (0.013, None, None)),
        (600, (0.015, None, None)),
        (750, (0.017, None, None)),
        (900, (0.018, 0.022, None)),
        (1050, (0.019, 0.022, None)),
        (1200, (0.020, 0.023, 0.022)),
        (1350, (0.021, 0.023, 0.022)),
        (1500, (0.021, 0.024, 0.023)),
        (1650, (0.021, 0.025, 0.024)),
        (1800, (0.021, 0.026, 0.024)),
        (1950, (0.021, 0.027, 0.025)),
    ],
)
def test_complete_mrwa_csp_manning_lookup(
    diameter_mm: float,
    expected_values: tuple[float | None, float | None, float | None],
) -> None:
    corrugations = tuple(CspCorrugation)
    assert len(MRWA_CSP_MANNING_TABLE) == 27
    for corrugation, expected_n in zip(corrugations, expected_values, strict=True):
        if expected_n is None:
            with pytest.raises(InvalidInputError, match="No MRWA Table 2.2"):
                resolve_csp_manning_roughness(diameter_mm, corrugation)
        else:
            assert resolve_csp_manning_roughness(diameter_mm, corrugation) == pytest.approx(
                expected_n
            )


def test_mrwa_csp_larger_row_and_string_enum_value() -> None:
    assert resolve_csp_manning_roughness(2400, "125x25") == pytest.approx(0.025)


def test_mrwa_csp_manning_lookup_fails_closed_but_allows_override() -> None:
    with pytest.raises(InvalidInputError, match="No MRWA Table 2.2"):
        resolve_csp_manning_roughness(600, CspCorrugation.PITCH_75_DEPTH_25)
    with pytest.raises(InvalidInputError, match="No MRWA Table 2.2"):
        resolve_csp_manning_roughness(500, CspCorrugation.PITCH_68_DEPTH_13)

    assert resolve_csp_manning_roughness(
        500,
        CspCorrugation.PITCH_68_DEPTH_13,
        override=0.019,
    ) == pytest.approx(0.019)
    with pytest.raises(InvalidInputError, match="override"):
        resolve_csp_manning_roughness(
            500,
            CspCorrugation.PITCH_68_DEPTH_13,
            override=0.0,
        )


def test_preliminary_roughness_resolver_reports_default_provenance() -> None:
    concrete = resolve_manning_roughness(CONCRETE_PIPE)
    assert concrete.value == pytest.approx(0.012)
    assert concrete.basis is RoughnessSelectionBasis.MRWA_CONCRETE_TABLE
    assert concrete.source == CONCRETE_PIPE.reference
    assert concrete.used_default

    csp = resolve_manning_roughness(
        CORRUGATED_STEEL,
        nominal_diameter_mm=1500,
        csp_corrugation=CspCorrugation.PITCH_75_DEPTH_25,
    )
    assert csp.value == pytest.approx(0.024)
    assert csp.basis is RoughnessSelectionBasis.MRWA_CSP_TABLE
    assert csp.source is not None
    assert csp.source.source_id == "MRWA-CULVERT-DESIGN-PROCEDURE-TABLE-2.2"
    assert [notice.code for notice in csp.notices] == [
        ApplicabilityNoticeCode.HYDRAULIC_VALUE_NOT_CONSTRUCTION_COMPLIANCE
    ]
    assert csp.notices[0].source.source_id == "MRWA-SPECIFICATION-404-2026-07-17"


def test_roughness_resolution_requires_specific_concrete_and_manufacturer_plastic_data() -> None:
    with pytest.raises(InvalidInputError, match="CONCRETE_PIPE or CONCRETE_BOX"):
        resolve_manning_roughness(CONCRETE)
    with pytest.raises(InvalidInputError, match="applicable manufacturer"):
        resolve_manning_roughness(SMOOTH_HDPE)

    fallback = resolve_manning_roughness(SMOOTH_HDPE, allow_documented_fallback=True)
    assert fallback.value == SMOOTH_HDPE.typical_n
    assert fallback.basis is RoughnessSelectionBasis.HDS5_DOCUMENTED_FALLBACK
    assert [notice.code for notice in fallback.notices] == [
        ApplicabilityNoticeCode.MANUFACTURER_DATA_NOT_SUPPLIED,
        ApplicabilityNoticeCode.HYDRAULIC_VALUE_NOT_CONSTRUCTION_COMPLIANCE,
    ]
    assert fallback.notices[0].source.source_id == "MRWA-SUPPLEMENT-AGRD-PART5B-1F"
    assert fallback.notices[1].source.source_id == "MRWA-SPECIFICATION-404-2026-07-17"
    assert json.loads(json.dumps(fallback.notices[0].code)) == "manufacturer_data_not_supplied"


def test_manufacturer_plastic_override_wins_without_fallback_notice() -> None:
    selection = resolve_manning_roughness(
        SMOOTH_HDPE,
        override=0.0105,
        override_source=SMOOTH_HDPE.reference,
    )
    assert selection.value == pytest.approx(0.0105)
    assert selection.basis is RoughnessSelectionBasis.USER_OVERRIDE
    assert not selection.notices


def test_barrel_rejects_mismatched_roughness_selection_value() -> None:
    selection = resolve_manning_roughness(CONCRETE_PIPE)
    with pytest.raises(InvalidInputError, match="must equal"):
        CulvertBarrel(
            geometry=CircularGeometry(diameter=1.0),
            length=20.0,
            inlet_invert=10.0,
            outlet_invert=9.8,
            roughness=selection.value + 0.001,
            material=CONCRETE_PIPE,
            roughness_selection=selection,
        )


def test_preliminary_roughness_resolver_prioritizes_user_override() -> None:
    selection = resolve_manning_roughness(
        CORRUGATED_STEEL,
        override=0.031,
        override_source=CONCRETE.reference,
    )
    assert selection.value == pytest.approx(0.031)
    assert selection.basis is RoughnessSelectionBasis.USER_OVERRIDE
    assert selection.source == CONCRETE.reference
    assert not selection.used_default

    with pytest.raises(InvalidInputError, match="CSP preliminary roughness"):
        resolve_manning_roughness(CORRUGATED_STEEL)
    with pytest.raises(InvalidInputError, match="value"):
        resolve_manning_roughness(CONCRETE, override=0.0)
    with pytest.raises(InvalidInputError, match="override_source requires"):
        resolve_manning_roughness(CONCRETE, override_source=CONCRETE.reference)


def test_roughness_selection_accepts_referenced_override_and_requires_default_source() -> None:
    referenced_override = ManningRoughnessSelection(
        value=0.013,
        basis=RoughnessSelectionBasis.USER_OVERRIDE,
        material_name="Concrete",
        source=CONCRETE.reference,
    )
    assert referenced_override.source == CONCRETE.reference
    assert not referenced_override.used_default

    with pytest.raises(InvalidInputError, match="default must identify"):
        ManningRoughnessSelection(
            value=0.013,
            basis=RoughnessSelectionBasis.MATERIAL_TYPICAL,
            material_name="Concrete",
            source=None,
        )


def test_culvert_barrel_valid_and_derived_properties() -> None:
    geom = CircularGeometry(diameter=1.2)
    barrel = CulvertBarrel(
        geometry=geom,
        length=50.0,
        inlet_invert=100.0,
        outlet_invert=99.5,
        roughness=0.013,
        material=CONCRETE,
        label="Group A Barrel",
    )

    assert barrel.geometry == geom
    assert barrel.length == 50.0
    assert barrel.inlet_invert == 100.0
    assert barrel.outlet_invert == 99.5
    assert barrel.drop == pytest.approx(0.5)
    assert barrel.slope == pytest.approx(0.5 / 50.0)  # 0.01
    assert not barrel.is_horizontal
    assert barrel.inlet_crown == pytest.approx(101.2)
    assert barrel.outlet_crown == pytest.approx(100.7)


def test_horizontal_barrel() -> None:
    geom = RectangularGeometry(span=2.4, rise=1.2)
    barrel = CulvertBarrel(
        geometry=geom,
        length=30.0,
        inlet_invert=50.0,
        outlet_invert=50.0,
        roughness=0.012,
    )
    assert barrel.drop == 0.0
    assert barrel.slope == 0.0
    assert barrel.is_horizontal


def test_adverse_slope_rejected() -> None:
    geom = CircularGeometry(diameter=1.0)
    with pytest.raises(InvalidInputError, match="Adverse slope"):
        CulvertBarrel(
            geometry=geom,
            length=25.0,
            inlet_invert=10.0,
            outlet_invert=10.5,
            roughness=0.013,
        )


@pytest.mark.parametrize("length_val", [0.0, -10.0, math.nan])
def test_invalid_barrel_length_rejected(length_val: float) -> None:
    geom = CircularGeometry(diameter=1.0)
    with pytest.raises(InvalidInputError):
        CulvertBarrel(
            geometry=geom,
            length=length_val,
            inlet_invert=10.0,
            outlet_invert=9.0,
            roughness=0.013,
        )


@pytest.mark.parametrize("n_val", [0.0, -0.013, math.nan])
def test_invalid_barrel_roughness_rejected(n_val: float) -> None:
    geom = CircularGeometry(diameter=1.0)
    with pytest.raises(InvalidInputError):
        CulvertBarrel(
            geometry=geom,
            length=20.0,
            inlet_invert=10.0,
            outlet_invert=9.0,
            roughness=n_val,
        )


def test_culvert_group() -> None:
    geom = CircularGeometry(diameter=1.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=15.0,
        outlet_invert=14.5,
        roughness=0.012,
    )
    group = CulvertGroup(barrel=barrel, quantity=3)

    assert group.quantity == 3
    assert group.total_full_area == pytest.approx(3.0 * geom.area_full)
    assert group.total_span == pytest.approx(3.0 * 1.0)

    with pytest.raises(InvalidInputError):
        CulvertGroup(barrel=barrel, quantity=0)
    with pytest.raises(InvalidInputError):
        CulvertGroup(barrel=barrel, quantity=-2)
    with pytest.raises(InvalidInputError):
        CulvertGroup(barrel=barrel, quantity=True)  # type: ignore[arg-type]


def test_tailwater_condition() -> None:
    tw = TailwaterCondition(elevation=12.5)
    assert tw.elevation == 12.5

    # Tailwater above outlet invert
    assert tw.depth_at_invert(outlet_invert=11.0) == pytest.approx(1.5)

    # Tailwater below outlet invert (dry / free outfall)
    assert tw.depth_at_invert(outlet_invert=13.0) == 0.0
    assert tw.depth_at_invert(outlet_invert=12.5) == 0.0

    with pytest.raises(InvalidInputError):
        TailwaterCondition(elevation=math.nan)


def test_culvert_crossing() -> None:
    # Group 1: 3 x Circular DN1200
    b1 = CulvertBarrel(
        geometry=CircularGeometry.from_mm(1200),
        length=50.0,
        inlet_invert=100.0,
        outlet_invert=99.0,
        roughness=0.012,
    )
    g1 = CulvertGroup(barrel=b1, quantity=3)

    # Group 2: 2 x RCBC 2400x1200 with lower invert
    b2 = CulvertBarrel(
        geometry=RectangularGeometry.from_mm(2400, 1200),
        length=50.0,
        inlet_invert=99.5,
        outlet_invert=98.5,
        roughness=0.013,
    )
    g2 = CulvertGroup(barrel=b2, quantity=2)

    crossing = CulvertCrossing(groups=[g1, g2])
    assert crossing.num_groups == 2
    assert crossing.total_barrels == 5
    assert crossing.total_full_area == pytest.approx(g1.total_full_area + g2.total_full_area)
    assert crossing.min_inlet_invert == pytest.approx(99.5)
    assert crossing.max_inlet_invert == pytest.approx(100.0)
    assert crossing.min_outlet_invert == pytest.approx(98.5)
    assert crossing.max_outlet_invert == pytest.approx(99.0)

    with pytest.raises(InvalidInputError, match="at least one"):
        CulvertCrossing(groups=[])


def test_result_contracts_and_flow_regimes() -> None:
    geom = CircularGeometry(diameter=1.2)
    barrel = CulvertBarrel(
        geometry=geom,
        length=40.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.012,
    )
    group = CulvertGroup(barrel=barrel, quantity=2)

    b_res = BarrelHydraulicResult(
        barrel=barrel,
        discharge=2.5,
        headwater_elevation=11.5,
        headwater_depth=1.5,
        tailwater_elevation=10.0,
        tailwater_depth=0.5,
        regime=FlowRegime.INLET_CONTROL_UNSUBMERGED,
        control_type=ControlType.INLET,
        velocity_outlet=2.8,
        outlet_depth=0.7,
        critical_depth=0.8,
        normal_depth=0.7,
    )
    assert b_res.discharge == 2.5
    assert b_res.regime == FlowRegime.INLET_CONTROL_UNSUBMERGED

    g_res = GroupHydraulicResult(
        group=group,
        total_discharge=5.0,
        barrel_discharge=2.5,
        barrel_result=b_res,
    )
    assert g_res.total_discharge == 5.0

    c_res = CrossingHydraulicResult(
        headwater_elevation=11.5,
        total_discharge=5.0,
        tailwater_elevation=10.0,
        group_results=(g_res,),
    )
    assert c_res.headwater_elevation == 11.5
    assert len(c_res.group_results) == 1


def test_domain_models_immutability() -> None:
    geom = CircularGeometry(diameter=1.0)
    barrel = CulvertBarrel(
        geometry=geom,
        length=30.0,
        inlet_invert=10.0,
        outlet_invert=9.5,
        roughness=0.012,
    )
    group = CulvertGroup(barrel=barrel, quantity=2)
    tw = TailwaterCondition(elevation=10.0)

    with pytest.raises(FrozenInstanceError):
        field = "length"
        setattr(barrel, field, 40.0)
    with pytest.raises(FrozenInstanceError):
        field = "quantity"
        setattr(group, field, 4)
    with pytest.raises(FrozenInstanceError):
        field = "elevation"
        setattr(tw, field, 12.0)
