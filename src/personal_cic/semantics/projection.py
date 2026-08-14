from __future__ import annotations
from hashlib import sha256
from types import MappingProxyType
from typing import Iterable, Mapping, Any
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world.components import ObservationState, TrafficFlowCollectionState, TrafficSituationState
from personal_cic.core.world.entity import Entity
from personal_cic.core.world.store import WorldState
from .model import (
    SemanticAssertion,
    SemanticAssertionOrigin,
    SemanticKind,
    SemanticProvenance,
    SemanticSourceRef,
    SemanticSourceRole,
    SemanticTemporalContext,
)


def _id(*parts: object) -> str:
    return "sem:" + sha256("|".join(str(x) for x in parts).encode()).hexdigest()[:24]


def _proposition(*parts: object) -> str:
    return "prop:" + sha256("|".join(str(x) for x in parts).encode()).hexdigest()[:24]


def _q(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))


def _source(ref_id: str, role: SemanticSourceRole, *, authority: str | None = None, native_id: str | None = None) -> SemanticSourceRef:
    return SemanticSourceRef(ref_id, role, authority, native_id)


def _observation(entity: Entity, state: ObservationState) -> Iterable[SemanticAssertion]:
    adapter = _source(f"adapter:{state.adapter_id}", SemanticSourceRole.ADAPTER, native_id=state.adapter_id)
    world = _source(entity.entity_id, SemanticSourceRole.WORLD_ENTITY_REFERENCE, native_id=entity.entity_id)
    provenance = SemanticProvenance(SemanticAssertionOrigin.SOURCE_OBSERVED, (adapter, world))
    temporal = SemanticTemporalContext(observed_at=state.checked_at)
    proposition = _proposition(entity.entity_id, "observation", state.adapter_id, "availability")
    yield SemanticAssertion(
        _id(proposition, state.checked_at, state.availability.value, state.reasons), proposition,
        SemanticKind.OBSERVATION_STATE, "Observation boundary", entity.entity_id, "observation_availability",
        state.availability.value, provenance, temporal,
        _q({"checked_at": state.checked_at, "last_success_at": state.last_success_at, "reasons": state.reasons}),
    )
    if state.availability is ObservationAvailability.UNAVAILABLE:
        proposition = _proposition(entity.entity_id, "absence", state.adapter_id, "new_observation_unavailable")
        yield SemanticAssertion(
            _id(proposition, state.checked_at, state.reasons), proposition,
            SemanticKind.ABSENCE, "Absence assertion", entity.entity_id, "new_observation_unavailable", True,
            provenance, temporal,
            _q({"absence_role": "collection_failure_or_unavailability", "does_not_assert_negative_world_state": True, "reasons": state.reasons}),
        )


def _traffic_flow(entity: Entity, state: TrafficFlowCollectionState, observation: ObservationState | None) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    adapter_source = (
        (_source(f"adapter:{observation.adapter_id}", SemanticSourceRole.ADAPTER, native_id=observation.adapter_id),)
        if observation is not None else ()
    )
    world = _source(entity.entity_id, SemanticSourceRole.WORLD_ENTITY_REFERENCE, native_id=entity.entity_id)
    for probe in state.probes:
        subject = f"{entity.entity_id}:flow-probe:{probe.probe_id}"
        provider = _source(f"provider:{probe.provider}", SemanticSourceRole.PROVIDER, authority=probe.provider)
        record = _source(subject, SemanticSourceRole.SOURCE_RECORD, authority=probe.provider, native_id=probe.probe_id)
        provenance = SemanticProvenance(SemanticAssertionOrigin.SOURCE_OBSERVED, (provider, *adapter_source, record, world))
        temporal = SemanticTemporalContext(observed_at=observed_at)
        common = {"provider": probe.provider, "source_family": probe.source_family, "collection_class": probe.collection_class,
                  "match_method": probe.match_method, "openlr": probe.openlr}
        for prop, value, qk, unit in (
            ("current_speed", probe.current_speed_mph, "velocity", "mile_per_hour"),
            ("free_flow_speed", probe.free_flow_speed_mph, "velocity", "mile_per_hour"),
            ("current_travel_time", probe.current_travel_time_seconds, "duration", "second"),
            ("free_flow_travel_time", probe.free_flow_travel_time_seconds, "duration", "second"),
        ):
            if value is not None:
                proposition = _proposition(subject, prop)
                yield SemanticAssertion(
                    _id(proposition, observed_at, value, probe.provider, probe.probe_id), proposition,
                    SemanticKind.MEASUREMENT, "Measurement assertion", subject, prop, value,
                    provenance, temporal,
                    _q({**common, "quantity_kind": qk, "unit": unit, "scale_type": "ratio", "measurement_kind": "provider_modeled_telemetry"}),
                )
        if probe.confidence is not None:
            proposition = _proposition(subject, "provider-native-confidence")
            foreign_provenance = SemanticProvenance(SemanticAssertionOrigin.FOREIGN_NATIVE_PRESERVED, provenance.sources)
            yield SemanticAssertion(
                _id(proposition, observed_at, probe.confidence, probe.provider, probe.probe_id), proposition,
                SemanticKind.FOREIGN_NATIVE, "Foreign semantic preservation", subject, "tomtom_flow_confidence", probe.confidence,
                foreign_provenance, temporal,
                _q({**common, "local_semantic_role": "unresolved", "not_claim_confidence": True, "not_source_reliability": True,
                    "not_data_product_quality": True, "not_measurement_uncertainty_without_provider_contract": True}),
            )


def _traffic_situation(entity: Entity, state: TrafficSituationState) -> Iterable[SemanticAssertion]:
    derivation = _source("derivation:traffic.fusion", SemanticSourceRole.DERIVATION_PROCESS, native_id="traffic.fusion")
    world = _source(entity.entity_id, SemanticSourceRole.WORLD_ENTITY_REFERENCE, native_id=entity.entity_id)
    provenance = SemanticProvenance(SemanticAssertionOrigin.CIC_DERIVED, (derivation, world), derivation.ref_id)
    temporal = SemanticTemporalContext(derived_at=state.derived_at)
    for i, gap in enumerate(state.collection_gaps):
        proposition = _proposition(entity.entity_id, "collection-gap", i)
        yield SemanticAssertion(
            _id(proposition, state.derived_at, gap), proposition,
            SemanticKind.COLLECTION_GAP, "Collection gap", entity.entity_id, "known_collection_gap", gap,
            provenance, temporal, _q({"derived_at": state.derived_at}),
        )
    for kernel in state.kernels:
        if kernel.association_basis == "same-lineage upstream identifier":
            subject = f"{entity.entity_id}:kernel:{kernel.kernel_id}"
            records = tuple(_source(ref, SemanticSourceRole.SOURCE_RECORD, native_id=ref) for ref in kernel.source_record_refs)
            kernel_provenance = SemanticProvenance(SemanticAssertionOrigin.CIC_DERIVED, (derivation, *records, world), derivation.ref_id)
            proposition = _proposition(subject, "same_upstream_event_representation")
            yield SemanticAssertion(
                _id(proposition, state.derived_at, kernel.source_record_refs), proposition,
                SemanticKind.IDENTITY_ASSOCIATION, "Identity assertion", subject, "same_upstream_event_representation",
                kernel.source_record_refs, kernel_provenance, temporal,
                _q({"mapping_strength": "same_lineage_identifier_only", "source_families": kernel.source_families,
                    "not_independent_corroboration": True, "not_cross_lineage_equivalence": True, "not_causal_inference": True}),
            )


def project_entity_semantics(entity: Entity) -> tuple[SemanticAssertion, ...]:
    out = []
    observation = entity.get(ObservationState)
    if observation is not None:
        out.extend(_observation(entity, observation))
    flow = entity.get(TrafficFlowCollectionState)
    if flow is not None:
        out.extend(_traffic_flow(entity, flow, observation))
    situation = entity.get(TrafficSituationState)
    if situation is not None:
        out.extend(_traffic_situation(entity, situation))
    return tuple(out)


def project_world_semantics(world: WorldState) -> tuple[SemanticAssertion, ...]:
    out = []
    for entity_id in sorted(world.entities):
        out.extend(project_entity_semantics(world.entities[entity_id]))
    return tuple(out)
