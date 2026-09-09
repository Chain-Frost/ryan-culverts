"""Road-level inventory and summary models for independent culvert crossings."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from typing import TYPE_CHECKING, cast

from ..exceptions import InvalidInputError
from ..inlet_control.coefficients import InletCoefficients
from ..outlet_control.losses import EntranceLossCoefficient, ExitLossSelection
from ..references.models import SourceReference
from .crossing import CulvertCrossing
from .enums import (
    ApplicabilityNoticeCode,
    ControlType,
    HydraulicWarningCode,
    RoughnessSelectionBasis,
)
from .materials import CulvertMaterial
from .results import BarrelHydraulicResult, CrossingHydraulicResult, FlowRegime

if TYPE_CHECKING:
    from ..solver.resolvers import EntranceLossSelection, InletCoefficientSelection
    from .materials import RoughnessApplicabilityNotice


@dataclass(frozen=True, slots=True)
class CulvertInventoryItem:
    """One stably identified road crossing and its optional hydraulic result."""

    crossing_id: str
    configuration: CulvertCrossing
    result: CrossingHydraulicResult | None = None

    def __post_init__(self) -> None:
        if not self.crossing_id.strip():
            raise InvalidInputError("crossing_id must be nonempty text.")
        if self.result is not None:
            result_groups = tuple(group_result.group for group_result in self.result.group_results)
            if result_groups != self.configuration.groups:
                raise InvalidInputError(
                    "The hydraulic result groups do not match this crossing configuration."
                )
            result_roadway = (
                None if self.result.roadway_result is None else self.result.roadway_result.roadway
            )
            if result_roadway != self.configuration.roadway:
                raise InvalidInputError(
                    "The hydraulic result roadway does not match this crossing configuration."
                )


@dataclass(frozen=True, slots=True)
class CulvertInventory:
    """Independent road crossings collected for calculation and compact reporting."""

    items: tuple[CulvertInventoryItem, ...]
    name: str = ""

    def __init__(self, items: Sequence[CulvertInventoryItem], name: str = "") -> None:
        processed_items = tuple(items)
        untyped_items = cast("tuple[object, ...]", processed_items)
        if not all(isinstance(item, CulvertInventoryItem) for item in untyped_items):
            raise InvalidInputError("items must contain only CulvertInventoryItem values.")
        crossing_ids = tuple(item.crossing_id for item in processed_items)
        if len(set(crossing_ids)) != len(crossing_ids):
            raise InvalidInputError("crossing_id values must be unique within an inventory.")
        object.__setattr__(self, "items", processed_items)
        object.__setattr__(self, "name", name)

    def _index_for(self, crossing_id: str) -> int:
        """Return the position for a stable crossing identifier or fail explicitly."""
        if not crossing_id.strip():
            raise InvalidInputError("crossing_id must be nonempty text.")
        for index, item in enumerate(self.items):
            if item.crossing_id == crossing_id:
                return index
        raise InvalidInputError(f"Unknown crossing_id {crossing_id!r}.")

    def update_configuration(
        self, crossing_id: str, new_configuration: CulvertCrossing
    ) -> CulvertInventory:
        """Replace a crossing configuration and discard its now-stale result."""
        index = self._index_for(crossing_id)
        new_items = list(self.items)
        new_items[index] = CulvertInventoryItem(
            crossing_id=crossing_id,
            configuration=new_configuration,
        )
        return CulvertInventory(items=new_items, name=self.name)

    def update_result(self, crossing_id: str, result: CrossingHydraulicResult) -> CulvertInventory:
        """Attach a result to the matching crossing configuration."""
        index = self._index_for(crossing_id)
        current = self.items[index]
        new_items = list(self.items)
        new_items[index] = CulvertInventoryItem(
            crossing_id=crossing_id,
            configuration=current.configuration,
            result=result,
        )
        return CulvertInventory(items=new_items, name=self.name)


@dataclass(frozen=True, slots=True)
class CrossingSummary:
    """Compact calculation summary for one identified crossing."""

    crossing_id: str
    solved: bool
    num_groups: int
    total_barrels: int
    total_full_area: float
    headwater_elevation: float | None
    total_discharge: float | None
    tailwater_elevation: float | None
    roadway_crest_elevation: float | None = None
    roadway_discharge: float | None = None
    parameter_set_ids: tuple[str, ...] = ()
    warning_codes: tuple[HydraulicWarningCode, ...] = ()
    applicability_notice_codes: tuple[ApplicabilityNoticeCode, ...] = ()


@dataclass(frozen=True, slots=True)
class AdoptedParameterSet:
    """One canonical set of empirical values actually adopted by a solved barrel."""

    parameter_set_id: str
    material: CulvertMaterial | None
    roughness: float
    roughness_basis: RoughnessSelectionBasis
    roughness_source: SourceReference | None
    inlet: InletCoefficientSelection
    entrance_loss: EntranceLossSelection
    exit_loss: ExitLossSelection
    roughness_notices: tuple[RoughnessApplicabilityNotice, ...] = ()


@dataclass(frozen=True, slots=True)
class GroupSummary:
    """Compact solved result for one crossing group."""

    crossing_id: str
    group_index: int
    barrel_label: str
    quantity: int
    parameter_set_id: str | None
    total_discharge: float
    barrel_discharge: float
    headwater_elevation: float
    outlet_velocity: float
    control_type: ControlType
    regime: FlowRegime
    warning_codes: tuple[HydraulicWarningCode, ...] = ()
    applicability_notice_codes: tuple[ApplicabilityNoticeCode, ...] = ()
    hydraulic_jump_station: float | None = None
    full_flow_length: float = 0.0


def _adopted_parameter_key(result: BarrelHydraulicResult) -> tuple[object, ...] | None:
    """Return a complete hashable identity for adopted empirical parameters."""
    if (
        result.adopted_roughness is None
        or result.roughness_selection_basis is None
        or result.inlet_coefficient_selection is None
        or result.entrance_loss_selection is None
        or result.exit_loss_selection is None
    ):
        return None
    return (
        result.barrel.parameter_set_id,
        result.barrel.material,
        result.adopted_roughness,
        result.roughness_selection_basis,
        result.roughness_source,
        result.inlet_coefficient_selection,
        result.entrance_loss_selection,
        result.exit_loss_selection,
        result.roughness_notices,
    )


def _parameter_set_id(key: tuple[object, ...]) -> str:
    """Generate a deterministic content identifier for a complete parameter key."""
    return f"aps-{sha256(repr(key).encode('utf-8')).hexdigest()}"


@dataclass(frozen=True, slots=True)
class InventorySummary:
    """Normalized crossing rows and deduplicated adopted calculation parameters."""

    inventory: CulvertInventory
    crossings: tuple[CrossingSummary, ...]
    groups: tuple[GroupSummary, ...]
    parameter_sets: tuple[AdoptedParameterSet, ...]
    materials: tuple[CulvertMaterial, ...]
    inlet_coefficients: tuple[InletCoefficients, ...]
    entrance_loss_coefficients: tuple[EntranceLossCoefficient, ...]
    source_references: tuple[SourceReference, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_inventory(
        cls,
        inventory: CulvertInventory,
        warnings: Sequence[str] = (),
    ) -> InventorySummary:
        """Build deterministic summaries and deduplicate typed configured components."""
        materials: set[CulvertMaterial] = set()
        inlet_coefficients: set[InletCoefficients] = set()
        entrance_losses: set[EntranceLossCoefficient] = set()
        sources_by_id: dict[str, SourceReference] = {}
        crossing_rows: list[CrossingSummary] = []
        group_rows: list[GroupSummary] = []
        parameter_sets_by_key: dict[tuple[object, ...], AdoptedParameterSet] = {}
        parameter_keys_by_id: dict[str, tuple[object, ...]] = {}

        def register_source(source: SourceReference) -> None:
            existing = sources_by_id.get(source.source_id)
            if existing is not None and existing != source:
                raise InvalidInputError(
                    f"Conflicting source metadata uses source_id {source.source_id!r}."
                )
            sources_by_id[source.source_id] = source

        for item in inventory.items:
            result = item.result
            crossing_parameter_ids: list[str] = []
            crossing_warning_codes: list[HydraulicWarningCode] = []
            crossing_applicability_notice_codes: list[ApplicabilityNoticeCode] = []
            if result is not None:
                for group_index, group_result in enumerate(result.group_results):
                    barrel_result = group_result.barrel_result
                    key = _adopted_parameter_key(barrel_result)
                    adopted_parameter_set_id: str | None = None
                    if key is None:
                        parameter_set = None
                    else:
                        parameter_set = parameter_sets_by_key.get(key)
                        if parameter_set is None:
                            inlet = barrel_result.inlet_coefficient_selection
                            entrance_loss = barrel_result.entrance_loss_selection
                            exit_loss = barrel_result.exit_loss_selection
                            roughness = barrel_result.adopted_roughness
                            roughness_basis = barrel_result.roughness_selection_basis
                            assert inlet is not None
                            assert entrance_loss is not None
                            assert exit_loss is not None
                            assert roughness is not None
                            assert roughness_basis is not None
                            generated_id = (
                                barrel_result.barrel.parameter_set_id or _parameter_set_id(key)
                            )
                            colliding_key = parameter_keys_by_id.get(generated_id)
                            if colliding_key is not None and colliding_key != key:
                                raise InvalidInputError(
                                    f"Parameter-set ID collision for {generated_id!r}."
                                )
                            parameter_set = AdoptedParameterSet(
                                parameter_set_id=generated_id,
                                material=barrel_result.barrel.material,
                                roughness=roughness,
                                roughness_basis=roughness_basis,
                                roughness_source=barrel_result.roughness_source,
                                inlet=inlet,
                                entrance_loss=entrance_loss,
                                exit_loss=exit_loss,
                                roughness_notices=barrel_result.roughness_notices,
                            )
                            parameter_sets_by_key[key] = parameter_set
                            parameter_keys_by_id[generated_id] = key
                        adopted_parameter_set_id = parameter_set.parameter_set_id
                        if adopted_parameter_set_id not in crossing_parameter_ids:
                            crossing_parameter_ids.append(adopted_parameter_set_id)
                        inlet_coefficients.add(parameter_set.inlet.coefficients)
                        register_source(parameter_set.inlet.source)
                        if parameter_set.entrance_loss.source is not None:
                            register_source(parameter_set.entrance_loss.source)
                        if parameter_set.exit_loss.source is not None:
                            register_source(parameter_set.exit_loss.source)
                        if parameter_set.roughness_source is not None:
                            register_source(parameter_set.roughness_source)
                    group_notice_codes = tuple(
                        dict.fromkeys(notice.code for notice in barrel_result.roughness_notices)
                    )
                    for notice in barrel_result.roughness_notices:
                        register_source(notice.source)
                        if notice.code not in crossing_applicability_notice_codes:
                            crossing_applicability_notice_codes.append(notice.code)
                    group_rows.append(
                        GroupSummary(
                            crossing_id=item.crossing_id,
                            group_index=group_index,
                            barrel_label=group_result.group.barrel.label,
                            quantity=group_result.group.quantity,
                            parameter_set_id=adopted_parameter_set_id,
                            total_discharge=group_result.total_discharge,
                            barrel_discharge=group_result.barrel_discharge,
                            headwater_elevation=barrel_result.headwater_elevation,
                            outlet_velocity=barrel_result.velocity_outlet,
                            control_type=barrel_result.control_type,
                            regime=barrel_result.regime,
                            warning_codes=tuple(
                                dict.fromkeys(warning.code for warning in barrel_result.warnings)
                            ),
                            applicability_notice_codes=group_notice_codes,
                            hydraulic_jump_station=barrel_result.hydraulic_jump_station,
                            full_flow_length=barrel_result.full_flow_length,
                        )
                    )
                    for warning in barrel_result.warnings:
                        if warning.code not in crossing_warning_codes:
                            crossing_warning_codes.append(warning.code)
            crossing_rows.append(
                CrossingSummary(
                    crossing_id=item.crossing_id,
                    solved=result is not None,
                    num_groups=item.configuration.num_groups,
                    total_barrels=item.configuration.total_barrels,
                    total_full_area=item.configuration.total_full_area,
                    headwater_elevation=(None if result is None else result.headwater_elevation),
                    total_discharge=None if result is None else result.total_discharge,
                    tailwater_elevation=(None if result is None else result.tailwater_elevation),
                    roadway_crest_elevation=(
                        None
                        if item.configuration.roadway is None
                        else item.configuration.roadway.crest_elevation
                    ),
                    roadway_discharge=(None if result is None else result.roadway_discharge),
                    parameter_set_ids=tuple(crossing_parameter_ids),
                    warning_codes=tuple(crossing_warning_codes),
                    applicability_notice_codes=tuple(crossing_applicability_notice_codes),
                )
            )
            if item.configuration.roadway is not None:
                register_source(item.configuration.roadway.coefficient_source)
            for group in item.configuration.groups:
                barrel = group.barrel
                if barrel.material is not None:
                    materials.add(barrel.material)
                    register_source(barrel.material.reference)
                if barrel.inlet_coefficients is not None:
                    inlet_coefficients.add(barrel.inlet_coefficients)
                    register_source(barrel.inlet_coefficients.reference)
                entrance_loss = barrel.entrance_loss_coefficient
                if isinstance(entrance_loss, EntranceLossCoefficient):
                    entrance_losses.add(entrance_loss)
                    register_source(entrance_loss.reference)

        return cls(
            inventory=inventory,
            crossings=tuple(crossing_rows),
            groups=tuple(group_rows),
            parameter_sets=tuple(parameter_sets_by_key.values()),
            materials=tuple(sorted(materials, key=lambda material: material.name)),
            inlet_coefficients=tuple(
                sorted(inlet_coefficients, key=lambda coefficients: coefficients.name)
            ),
            entrance_loss_coefficients=tuple(
                sorted(entrance_losses, key=lambda coefficient: coefficient.name)
            ),
            source_references=tuple(
                sources_by_id[source_id] for source_id in sorted(sources_by_id)
            ),
            warnings=tuple(warnings),
        )
