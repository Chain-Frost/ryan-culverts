"""Tests for road-level culvert inventory and summary models."""

from dataclasses import replace
from typing import cast

import pytest

from culvert_solver import (
    CIRCULAR_CMP_HEADWALL,
    CIRCULAR_CONCRETE_SQUARE_EDGE,
    CONCRETE,
    CORRUGATED_STEEL,
    BarrelHydraulicResult,
    CircularGeometry,
    ControlType,
    CrossingHydraulicResult,
    CulvertBarrel,
    CulvertCrossing,
    CulvertGroup,
    CulvertInventory,
    CulvertInventoryItem,
    CulvertMaterial,
    FlowRegime,
    GroupHydraulicResult,
    HydraulicWarning,
    HydraulicWarningCode,
    InvalidInputError,
    InventorySummary,
    SourceReference,
    resolve_entrance_loss_coefficient,
    resolve_inlet_coefficients,
)
from culvert_solver.inlet_control.coefficients import InletCoefficients
from culvert_solver.outlet_control.losses import PIPE_CMP_PROJECTING, EntranceLossCoefficient


def _test_barrel(
    material: CulvertMaterial,
    inlet_coeffs: InletCoefficients,
    ke: EntranceLossCoefficient | float,
) -> CulvertBarrel:
    return CulvertBarrel(
        geometry=CircularGeometry.from_mm(600),
        length=20.0,
        inlet_invert=100.0,
        outlet_invert=99.8,
        roughness=0.012,
        material=material,
        inlet_coefficients=inlet_coeffs,
        entrance_loss_coefficient=ke,
    )


def _crossing(barrel: CulvertBarrel) -> CulvertCrossing:
    return CulvertCrossing([CulvertGroup(barrel)])


def _mock_crossing_result(barrel: CulvertBarrel) -> CrossingHydraulicResult:
    group = CulvertGroup(barrel=barrel, quantity=1)
    barrel_result = BarrelHydraulicResult(
        barrel=barrel,
        discharge=1.0,
        headwater_elevation=102.0,
        headwater_depth=2.0,
        tailwater_elevation=100.0,
        tailwater_depth=0.2,
        regime=FlowRegime.INLET_CONTROL_UNSUBMERGED,
        control_type=ControlType.INLET,
        velocity_outlet=2.5,
        outlet_depth=0.5,
        critical_depth=0.4,
        normal_depth=0.5,
        inlet_coefficient_selection=resolve_inlet_coefficients(barrel),
        entrance_loss_selection=resolve_entrance_loss_coefficient(barrel),
        adopted_roughness=barrel.roughness,
        roughness_selection_basis=barrel.roughness_selection_basis,
        roughness_source=barrel.roughness_source,
        warnings=(
            HydraulicWarning(
                HydraulicWarningCode.INLET_OUTLET_DEPTH_APPROXIMATION,
                "Test diagnostic.",
            ),
        ),
    )
    group_result = GroupHydraulicResult(
        group=group,
        total_discharge=1.0,
        barrel_discharge=1.0,
        barrel_result=barrel_result,
    )
    return CrossingHydraulicResult(
        headwater_elevation=102.0,
        total_discharge=1.0,
        tailwater_elevation=100.0,
        group_results=(group_result,),
    )


def test_inventory_creation_preserves_stable_identifiers() -> None:
    crossing = _crossing(_test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5))
    inventory = CulvertInventory([CulvertInventoryItem("C-001", crossing)], name="Road inventory")

    assert inventory.name == "Road inventory"
    assert inventory.items[0].crossing_id == "C-001"
    assert inventory.items[0].configuration == crossing
    assert inventory.items[0].result is None


def test_empty_inventory_is_valid() -> None:
    assert CulvertInventory([]).items == ()


def test_inventory_rejects_invalid_or_duplicate_items() -> None:
    crossing = _crossing(_test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5))
    item = CulvertInventoryItem("C-001", crossing)

    with pytest.raises(InvalidInputError, match="nonempty text"):
        CulvertInventoryItem(" ", crossing)
    with pytest.raises(InvalidInputError, match="unique"):
        CulvertInventory([item, item])
    with pytest.raises(InvalidInputError, match="only CulvertInventoryItem"):
        CulvertInventory(cast("list[CulvertInventoryItem]", [crossing]))


def test_update_result_uses_identifier_and_validates_configuration() -> None:
    barrel = _test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5)
    crossing = _crossing(barrel)
    inventory = CulvertInventory([CulvertInventoryItem("C-001", crossing)])
    result = _mock_crossing_result(barrel)

    updated = inventory.update_result("C-001", result)

    assert updated is not inventory
    assert updated.items[0].result is result
    with pytest.raises(InvalidInputError, match="Unknown crossing_id"):
        inventory.update_result("missing", result)

    other_barrel = _test_barrel(CORRUGATED_STEEL, CIRCULAR_CMP_HEADWALL, PIPE_CMP_PROJECTING)
    with pytest.raises(InvalidInputError, match="do not match"):
        inventory.update_result("C-001", _mock_crossing_result(other_barrel))


def test_update_configuration_clears_stale_result() -> None:
    barrel = _test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5)
    inventory = CulvertInventory(
        [CulvertInventoryItem("C-001", _crossing(barrel), _mock_crossing_result(barrel))]
    )
    replacement = _crossing(
        _test_barrel(CORRUGATED_STEEL, CIRCULAR_CMP_HEADWALL, PIPE_CMP_PROJECTING)
    )

    updated = inventory.update_configuration("C-001", replacement)

    assert updated.items[0].configuration is replacement
    assert updated.items[0].result is None


def test_inventory_summary_has_rows_and_deduplicated_basis() -> None:
    concrete = _test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5)
    cmp = _test_barrel(CORRUGATED_STEEL, CIRCULAR_CMP_HEADWALL, PIPE_CMP_PROJECTING)
    inventory = CulvertInventory(
        [
            CulvertInventoryItem("C-001", _crossing(concrete), _mock_crossing_result(concrete)),
            CulvertInventoryItem("C-002", _crossing(concrete)),
            CulvertInventoryItem("C-003", _crossing(cmp), _mock_crossing_result(cmp)),
        ]
    )

    summary = InventorySummary.from_inventory(inventory, warnings=["test warning"])

    assert summary.inventory is inventory
    assert [row.crossing_id for row in summary.crossings] == ["C-001", "C-002", "C-003"]
    assert summary.crossings[0].solved is True
    assert summary.crossings[0].total_discharge == 1.0
    assert summary.crossings[1].solved is False
    assert summary.crossings[1].total_discharge is None
    assert len(summary.parameter_sets) == 2
    assert len(summary.crossings[0].parameter_set_ids) == 1
    assert summary.crossings[1].parameter_set_ids == ()
    assert summary.crossings[0].parameter_set_ids[0] == summary.parameter_sets[0].parameter_set_id
    assert [row.crossing_id for row in summary.groups] == ["C-001", "C-003"]
    assert summary.groups[0].group_index == 0
    assert summary.groups[0].parameter_set_id == summary.crossings[0].parameter_set_ids[0]
    assert summary.groups[0].warning_codes == (
        HydraulicWarningCode.INLET_OUTLET_DEPTH_APPROXIMATION,
    )
    assert summary.groups[0].hydraulic_jump_station is None
    assert summary.groups[0].full_flow_length == 0.0
    assert summary.crossings[0].warning_codes == (
        HydraulicWarningCode.INLET_OUTLET_DEPTH_APPROXIMATION,
    )
    assert summary.crossings[1].warning_codes == ()
    assert set(summary.materials) == {CONCRETE, CORRUGATED_STEEL}
    assert set(summary.inlet_coefficients) == {
        CIRCULAR_CONCRETE_SQUARE_EDGE,
        CIRCULAR_CMP_HEADWALL,
    }
    assert summary.entrance_loss_coefficients == (PIPE_CMP_PROJECTING,)
    assert set(summary.source_references) == {
        CONCRETE.reference,
        CORRUGATED_STEEL.reference,
        CIRCULAR_CONCRETE_SQUARE_EDGE.reference,
        CIRCULAR_CMP_HEADWALL.reference,
        PIPE_CMP_PROJECTING.reference,
    }
    assert summary.warnings == ("test warning",)


def test_fifty_crossings_share_one_stable_adopted_parameter_set() -> None:
    barrel = _test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5)
    crossing = _crossing(barrel)
    result = _mock_crossing_result(barrel)
    inventory = CulvertInventory(
        [CulvertInventoryItem(f"C-{index:03d}", crossing, result) for index in range(50)]
    )

    first = InventorySummary.from_inventory(inventory)
    second = InventorySummary.from_inventory(inventory)

    assert len(first.crossings) == 50
    assert len(first.parameter_sets) == 1
    expected_id = first.parameter_sets[0].parameter_set_id
    assert all(row.parameter_set_ids == (expected_id,) for row in first.crossings)
    assert second.parameter_sets[0].parameter_set_id == expected_id


def test_equal_values_with_different_provenance_do_not_collapse() -> None:
    first_source = SourceReference(
        source_id="manufacturer-a",
        publication="Manufacturer A specification",
        edition="2026",
        locator="Table 1",
        url="https://example.com/manufacturer-a",
        applicability="Test pipe product",
    )
    second_source = SourceReference(
        source_id="manufacturer-b",
        publication="Manufacturer B specification",
        edition="2026",
        locator="Table 1",
        url="https://example.com/manufacturer-b",
        applicability="Test pipe product",
    )
    base = _test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5)
    first_barrel = replace(base, roughness_source=first_source)
    second_barrel = replace(base, roughness_source=second_source)
    inventory = CulvertInventory(
        [
            CulvertInventoryItem(
                "C-001", _crossing(first_barrel), _mock_crossing_result(first_barrel)
            ),
            CulvertInventoryItem(
                "C-002", _crossing(second_barrel), _mock_crossing_result(second_barrel)
            ),
        ]
    )

    summary = InventorySummary.from_inventory(inventory)

    assert len(summary.parameter_sets) == 2
    assert summary.parameter_sets[0].parameter_set_id != summary.parameter_sets[1].parameter_set_id


def test_conflicting_source_ids_fail_explicitly() -> None:
    first_source = SourceReference(
        source_id="manufacturer-spec",
        publication="Manufacturer A specification",
        edition="2026",
        locator="Table 1",
        url="https://example.com/a",
        applicability="Test pipe product",
    )
    conflicting_source = SourceReference(
        source_id="manufacturer-spec",
        publication="Manufacturer B specification",
        edition="2026",
        locator="Table 2",
        url="https://example.com/b",
        applicability="Different test pipe product",
    )
    base = _test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5)
    first_barrel = replace(base, roughness_source=first_source)
    second_barrel = replace(base, roughness_source=conflicting_source)
    inventory = CulvertInventory(
        [
            CulvertInventoryItem(
                "C-001", _crossing(first_barrel), _mock_crossing_result(first_barrel)
            ),
            CulvertInventoryItem(
                "C-002", _crossing(second_barrel), _mock_crossing_result(second_barrel)
            ),
        ]
    )

    with pytest.raises(InvalidInputError, match="Conflicting source metadata"):
        InventorySummary.from_inventory(inventory)


def test_caller_parameter_set_id_is_preserved_and_must_be_unambiguous() -> None:
    base = _test_barrel(CONCRETE, CIRCULAR_CONCRETE_SQUARE_EDGE, 0.5)
    named = replace(base, parameter_set_id="standard-rcp")
    inventory = CulvertInventory(
        [CulvertInventoryItem("C-001", _crossing(named), _mock_crossing_result(named))]
    )

    summary = InventorySummary.from_inventory(inventory)

    assert summary.parameter_sets[0].parameter_set_id == "standard-rcp"
    assert summary.crossings[0].parameter_set_ids == ("standard-rcp",)

    different = replace(named, roughness=0.014)
    conflicting = CulvertInventory(
        [
            CulvertInventoryItem("C-001", _crossing(named), _mock_crossing_result(named)),
            CulvertInventoryItem("C-002", _crossing(different), _mock_crossing_result(different)),
        ]
    )
    with pytest.raises(InvalidInputError, match="Parameter-set ID collision"):
        InventorySummary.from_inventory(conflicting)
