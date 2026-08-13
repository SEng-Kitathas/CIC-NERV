from __future__ import annotations
from hashlib import sha256
from typing import Iterable
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world.components import ObservationState, TrafficFlowCollectionState, TrafficSituationState
from personal_cic.core.world.entity import Entity
from personal_cic.core.world.store import WorldState
from .model import SemanticAssertion, SemanticKind

def _id(*parts: object) -> str:
    return "sem:" + sha256("|".join(str(x) for x in parts).encode()).hexdigest()[:24]

def _observation(entity: Entity, state: ObservationState) -> Iterable[SemanticAssertion]:
    source=f"adapter:{state.adapter_id}"
    yield SemanticAssertion(_id(entity.entity_id,"observation",state.adapter_id,state.checked_at),
        SemanticKind.OBSERVATION_STATE,"Observation boundary",entity.entity_id,"observation_availability",
        state.availability.value,(source,),{"checked_at":state.checked_at,"last_success_at":state.last_success_at,"reasons":state.reasons})
    if state.availability is ObservationAvailability.UNAVAILABLE:
        yield SemanticAssertion(_id(entity.entity_id,"absence",state.adapter_id,state.checked_at),
            SemanticKind.ABSENCE,"Absence assertion",entity.entity_id,"new_observation_unavailable",True,(source,),
            {"absence_role":"collection_failure_or_unavailability","does_not_assert_negative_world_state":True,"reasons":state.reasons})

def _traffic_flow(entity: Entity, state: TrafficFlowCollectionState) -> Iterable[SemanticAssertion]:
    for probe in state.probes:
        subject=f"{entity.entity_id}:flow-probe:{probe.probe_id}"
        common={"provider":probe.provider,"source_family":probe.source_family,"collection_class":probe.collection_class,
                "match_method":probe.match_method,"openlr":probe.openlr}
        for prop,value,qk,unit in (
            ("current_speed",probe.current_speed_mph,"velocity","mile_per_hour"),
            ("free_flow_speed",probe.free_flow_speed_mph,"velocity","mile_per_hour"),
            ("current_travel_time",probe.current_travel_time_seconds,"duration","second"),
            ("free_flow_travel_time",probe.free_flow_travel_time_seconds,"duration","second")):
            if value is not None:
                yield SemanticAssertion(_id(subject,prop,value),SemanticKind.MEASUREMENT,"Measurement assertion",
                    subject,prop,value,(f"provider:{probe.provider}",),
                    {**common,"quantity_kind":qk,"unit":unit,"scale_type":"ratio","measurement_kind":"provider_modeled_telemetry"})
        if probe.confidence is not None:
            yield SemanticAssertion(_id(subject,"provider-native-confidence",probe.confidence),SemanticKind.FOREIGN_NATIVE,
                "Foreign semantic preservation",subject,"tomtom_flow_confidence",probe.confidence,(f"provider:{probe.provider}",),
                {**common,"local_semantic_role":"unresolved","not_claim_confidence":True,"not_source_reliability":True,
                 "not_data_product_quality":True,"not_measurement_uncertainty_without_provider_contract":True})

def _traffic_situation(entity: Entity, state: TrafficSituationState) -> Iterable[SemanticAssertion]:
    for i,gap in enumerate(state.collection_gaps):
        yield SemanticAssertion(_id(entity.entity_id,"collection-gap",i,gap),SemanticKind.COLLECTION_GAP,"Collection gap",
            entity.entity_id,"known_collection_gap",gap,("derivation:traffic.fusion",),{"derived_at":state.derived_at})
    for kernel in state.kernels:
        if kernel.association_basis=="same-lineage upstream identifier":
            yield SemanticAssertion(_id(entity.entity_id,kernel.kernel_id,"same-lineage"),SemanticKind.IDENTITY_ASSOCIATION,
                "Identity assertion",f"{entity.entity_id}:kernel:{kernel.kernel_id}","same_upstream_event_representation",
                kernel.source_record_refs,kernel.source_record_refs,
                {"mapping_strength":"same_lineage_identifier_only","source_families":kernel.source_families,
                 "not_independent_corroboration":True,"not_cross_lineage_equivalence":True,"not_causal_inference":True})

def project_entity_semantics(entity: Entity) -> tuple[SemanticAssertion,...]:
    out=[]
    x=entity.get(ObservationState)
    if x is not None: out.extend(_observation(entity,x))
    x=entity.get(TrafficFlowCollectionState)
    if x is not None: out.extend(_traffic_flow(entity,x))
    x=entity.get(TrafficSituationState)
    if x is not None: out.extend(_traffic_situation(entity,x))
    return tuple(out)

def project_world_semantics(world: WorldState) -> tuple[SemanticAssertion,...]:
    out=[]
    for entity_id in sorted(world.entities): out.extend(project_entity_semantics(world.entities[entity_id]))
    return tuple(out)
