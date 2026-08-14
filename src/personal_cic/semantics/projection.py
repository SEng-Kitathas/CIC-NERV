from __future__ import annotations

from hashlib import sha256
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world.components import (
    ComputeState,
    CurrentWeatherEstimateState,
    HealthState,
    MemoryState,
    ObservationState,
    NWSHourlyForecastState,
    RadarContextState,
    RadarMosaicState,
    TrafficCameraCollectionState,
    TrafficMessageSignCollectionState,
    WeatherForecastState,
    StorageState,
    SurfaceObservationNetworkState,
    TemperatureState,
    TrafficEventCollectionState,
    TrafficFlowCollectionState,
    TrafficSituationState,
    UsbDeviceState,
    WeatherAlertState,
    WeatherState,
    WifiLinkState,
)
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


def _source(
    ref_id: str,
    role: SemanticSourceRole,
    *,
    authority: str | None = None,
    native_id: str | None = None,
) -> SemanticSourceRef:
    return SemanticSourceRef(ref_id, role, authority, native_id)


def _authority_qualifiers(observation: ObservationState | None) -> dict[str, Any]:
    if observation is None:
        return {"semantic_authority_state": "unscoped", "current_authority": None}
    if observation.availability is ObservationAvailability.CURRENT:
        return {
            "semantic_authority_state": "current",
            "current_authority": True,
            "observation_checked_at": observation.checked_at,
            "observation_last_success_at": observation.last_success_at,
        }
    if observation.availability is ObservationAvailability.DEGRADED:
        return {
            "semantic_authority_state": "degraded_or_mixed",
            "current_authority": "qualified",
            "observation_checked_at": observation.checked_at,
            "observation_last_success_at": observation.last_success_at,
            "observation_reasons": observation.reasons,
        }
    if observation.availability is ObservationAvailability.RETAINED:
        return {
            "semantic_authority_state": "retained_by_policy",
            "current_authority": "policy_qualified",
            "observation_checked_at": observation.checked_at,
            "observation_last_success_at": observation.last_success_at,
            "observation_reasons": observation.reasons,
        }
    return {
        "semantic_authority_state": "last_known_noncurrent",
        "current_authority": False,
        "observation_checked_at": observation.checked_at,
        "observation_last_success_at": observation.last_success_at,
        "observation_reasons": observation.reasons,
    }


def _adapter_sources(entity: Entity, observation: ObservationState | None) -> tuple[SemanticSourceRef, ...]:
    world = _source(
        entity.entity_id,
        SemanticSourceRole.WORLD_ENTITY_REFERENCE,
        native_id=entity.entity_id,
    )
    if observation is None:
        return (world,)
    adapter = _source(
        f"adapter:{observation.adapter_id}",
        SemanticSourceRole.ADAPTER,
        native_id=observation.adapter_id,
    )
    return (adapter, world)


def _provider_provenance(
    entity: Entity,
    provider: str,
    observation: ObservationState | None,
    *,
    record_ref: str | None = None,
    native_record_id: str | None = None,
) -> SemanticProvenance:
    provider_ref = _source(
        f"provider:{provider}",
        SemanticSourceRole.PROVIDER,
        authority=provider,
    )
    sources: list[SemanticSourceRef] = [provider_ref, *_adapter_sources(entity, observation)]
    if record_ref is not None:
        sources.insert(
            1,
            _source(
                record_ref,
                SemanticSourceRole.SOURCE_RECORD,
                authority=provider,
                native_id=native_record_id,
            ),
        )
    return SemanticProvenance(SemanticAssertionOrigin.SOURCE_OBSERVED, tuple(sources))


def _derived_provenance(entity: Entity, process: str) -> SemanticProvenance:
    derivation = _source(
        f"derivation:{process}",
        SemanticSourceRole.DERIVATION_PROCESS,
        native_id=process,
    )
    world = _source(
        entity.entity_id,
        SemanticSourceRole.WORLD_ENTITY_REFERENCE,
        native_id=entity.entity_id,
    )
    return SemanticProvenance(
        SemanticAssertionOrigin.CIC_DERIVED,
        (derivation, world),
        derivation.ref_id,
    )


def _measurement(
    *,
    subject: str,
    predicate: str,
    value: object,
    provenance: SemanticProvenance,
    temporal: SemanticTemporalContext,
    quantity_kind: str,
    unit: str | None,
    measurement_kind: str,
    identity_parts: tuple[object, ...],
    qualifiers: Mapping[str, Any] | None = None,
) -> SemanticAssertion:
    proposition = _proposition(subject, predicate)
    q: dict[str, Any] = {
        "quantity_kind": quantity_kind,
        "unit": unit,
        "measurement_kind": measurement_kind,
    }
    if qualifiers:
        q.update(qualifiers)
    return SemanticAssertion(
        _id(proposition, *identity_parts),
        proposition,
        SemanticKind.MEASUREMENT,
        "Measurement assertion",
        subject,
        predicate,
        value,
        provenance,
        temporal,
        _q(q),
    )




def _point(latitude: float, longitude: float) -> tuple[float, float]:
    return (float(latitude), float(longitude))


def _line_geometry(points: Iterable[object]) -> tuple[tuple[float, float], ...]:
    return tuple(
        (float(point.latitude), float(point.longitude))
        for point in points
    )


def _spatial_assertion(
    *,
    subject: str,
    predicate: str,
    value: object,
    provenance: SemanticProvenance,
    temporal: SemanticTemporalContext,
    identity_parts: tuple[object, ...],
    spatial_role: str,
    qualifiers: Mapping[str, Any] | None = None,
) -> SemanticAssertion:
    proposition = _proposition(subject, predicate)
    values: dict[str, Any] = {
        "spatial_role": spatial_role,
        "crs": "EPSG:4326",
        "coordinate_order": "latitude_longitude",
        "no_spatial_identity_inference": True,
        "no_intersection_equivalence_inference": True,
    }
    if qualifiers:
        values.update(qualifiers)
    return SemanticAssertion(
        _id(proposition, *identity_parts),
        proposition,
        SemanticKind.SPATIAL,
        "Spatial assertion",
        subject,
        predicate,
        value,
        provenance,
        temporal,
        _q(values),
    )


def _collection_scope_assertion(
    *,
    subject: str,
    center_latitude: float,
    center_longitude: float,
    radius_miles: float,
    provenance: SemanticProvenance,
    temporal: SemanticTemporalContext,
    identity_parts: tuple[object, ...],
    qualifiers: Mapping[str, Any] | None = None,
) -> SemanticAssertion:
    extra = {
        "radius_miles": radius_miles,
        "scope_is_not_object_location": True,
        "scope_is_not_event_geometry": True,
    }
    if qualifiers:
        extra.update(qualifiers)
    return _spatial_assertion(
        subject=subject,
        predicate="collection_scope",
        value=_point(center_latitude, center_longitude),
        provenance=provenance,
        temporal=temporal,
        identity_parts=identity_parts,
        spatial_role="collection_scope_center_and_radius",
        qualifiers=extra,
    )




def _foreign_native_assertion(
    *,
    subject: str,
    predicate: str,
    value: object,
    provenance: SemanticProvenance,
    temporal: SemanticTemporalContext,
    identity_parts: tuple[object, ...],
    semantic_role: str,
    semantic_authority: str,
    qualifiers: Mapping[str, Any] | None = None,
) -> SemanticAssertion:
    proposition = _proposition(subject, predicate)
    authority_ref = _source(
        f"semantic-authority:{semantic_authority}",
        SemanticSourceRole.FOREIGN_SEMANTIC_AUTHORITY,
        authority=semantic_authority,
        native_id=semantic_authority,
    )
    sources = provenance.sources
    if not any(
        source.role is SemanticSourceRole.FOREIGN_SEMANTIC_AUTHORITY
        and source.ref_id == authority_ref.ref_id
        for source in sources
    ):
        sources = (*sources, authority_ref)
    foreign_provenance = SemanticProvenance(
        SemanticAssertionOrigin.FOREIGN_NATIVE_PRESERVED,
        sources,
    )
    values: dict[str, Any] = {
        "local_semantic_role": semantic_role,
        "mapping_status": "unresolved",
        "foreign_semantic_authority": semantic_authority,
        "not_local_class_identity": True,
        "not_local_condition_without_crosswalk": True,
    }
    if qualifiers:
        values.update(qualifiers)
    return SemanticAssertion(
        _id(proposition, *identity_parts),
        proposition,
        SemanticKind.FOREIGN_NATIVE,
        "Foreign semantic preservation",
        subject,
        predicate,
        value,
        foreign_provenance,
        temporal,
        _q(values),
    )


def _source_report_assertion(
    *,
    subject: str,
    predicate: str,
    value: object,
    provenance: SemanticProvenance,
    temporal: SemanticTemporalContext,
    identity_parts: tuple[object, ...],
    qualifiers: Mapping[str, Any],
) -> SemanticAssertion:
    proposition = _proposition(subject, predicate)
    return SemanticAssertion(
        _id(proposition, *identity_parts),
        proposition,
        SemanticKind.SOURCE_REPORT,
        "Epistemic assertion",
        subject,
        predicate,
        value,
        provenance,
        temporal,
        _q({
            **qualifiers,
            "epistemic_mode": "provider_report",
            "not_direct_physical_verification": True,
        }),
    )


def _observation(entity: Entity, state: ObservationState) -> Iterable[SemanticAssertion]:
    adapter = _source(
        f"adapter:{state.adapter_id}",
        SemanticSourceRole.ADAPTER,
        native_id=state.adapter_id,
    )
    world = _source(
        entity.entity_id,
        SemanticSourceRole.WORLD_ENTITY_REFERENCE,
        native_id=entity.entity_id,
    )
    provenance = SemanticProvenance(
        SemanticAssertionOrigin.SOURCE_OBSERVED,
        (adapter, world),
    )
    temporal = SemanticTemporalContext(observed_at=state.checked_at)
    proposition = _proposition(entity.entity_id, "observation", state.adapter_id, "availability")
    yield SemanticAssertion(
        _id(proposition, state.checked_at, state.availability.value, state.reasons),
        proposition,
        SemanticKind.OBSERVATION_STATE,
        "Observation boundary",
        entity.entity_id,
        "observation_availability",
        state.availability.value,
        provenance,
        temporal,
        _q(
            {
                "checked_at": state.checked_at,
                "last_success_at": state.last_success_at,
                "reasons": state.reasons,
            }
        ),
    )
    if state.availability is ObservationAvailability.UNAVAILABLE:
        proposition = _proposition(
            entity.entity_id,
            "absence",
            state.adapter_id,
            "new_observation_unavailable",
        )
        yield SemanticAssertion(
            _id(proposition, state.checked_at, state.reasons),
            proposition,
            SemanticKind.ABSENCE,
            "Absence assertion",
            entity.entity_id,
            "new_observation_unavailable",
            True,
            provenance,
            temporal,
            _q(
                {
                    "absence_role": "collection_failure_or_unavailability",
                    "does_not_assert_negative_world_state": True,
                    "reasons": state.reasons,
                }
            ),
        )


def _traffic_flow(
    entity: Entity,
    state: TrafficFlowCollectionState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    auth = _authority_qualifiers(observation)
    collection_subject = f"{entity.entity_id}:flow-collection:{state.provider}"
    collection_provenance = _provider_provenance(entity, state.provider, observation)

    yield _collection_scope_assertion(
        subject=collection_subject,
        center_latitude=state.scope_center_latitude,
        center_longitude=state.scope_center_longitude,
        radius_miles=state.scope_radius_miles,
        provenance=collection_provenance,
        temporal=SemanticTemporalContext(observed_at=observed_at),
        identity_parts=(
            observed_at,
            state.scope_center_latitude,
            state.scope_center_longitude,
            state.scope_radius_miles,
        ),
        qualifiers={**auth, "provider": state.provider},
    )

    if state.configured_probe_count > 0:
        proposition = _proposition(collection_subject, "probe_collection_completeness")
        yield SemanticAssertion(
            _id(
                proposition,
                observed_at,
                state.successful_probe_count,
                state.configured_probe_count,
                state.provider,
            ),
            proposition,
            SemanticKind.DATA_QUALITY,
            "Data product quality assessment",
            collection_subject,
            "probe_collection_completeness",
            state.successful_probe_count / state.configured_probe_count,
            collection_provenance,
            SemanticTemporalContext(observed_at=observed_at),
            _q(
                {
                    **auth,
                    "quality_dimension": "collection_completeness",
                    "metric": "successful_probe_count/configured_probe_count",
                    "successful_probe_count": state.successful_probe_count,
                    "configured_probe_count": state.configured_probe_count,
                    "not_claim_confidence": True,
                    "not_source_reliability": True,
                }
            ),
        )

    for probe in state.probes:
        subject = f"{entity.entity_id}:flow-probe:{probe.probe_id}"
        provenance = _provider_provenance(
            entity,
            probe.provider,
            observation,
            record_ref=subject,
            native_record_id=probe.probe_id,
        )
        temporal = SemanticTemporalContext(observed_at=observed_at)
        common = {
            **auth,
            "provider": probe.provider,
            "source_family": probe.source_family,
            "collection_class": probe.collection_class,
            "match_method": probe.match_method,
            "openlr": probe.openlr,
        }

        yield _spatial_assertion(
            subject=subject,
            predicate="flow_query_point",
            value=_point(probe.query_latitude, probe.query_longitude),
            provenance=provenance,
            temporal=temporal,
            identity_parts=(
                observed_at,
                probe.query_latitude,
                probe.query_longitude,
                probe.probe_id,
            ),
            spatial_role="acquisition_query_reference_point",
            qualifiers={
                **common,
                "query_point_is_not_matched_segment_geometry": True,
                "query_point_is_not_road_identity": True,
            },
        )

        if probe.geometry:
            matched_geometry = _line_geometry(probe.geometry)
            yield _spatial_assertion(
                subject=subject,
                predicate="matched_road_geometry",
                value=matched_geometry,
                provenance=provenance,
                temporal=temporal,
                identity_parts=(
                    observed_at,
                    probe.probe_id,
                    matched_geometry,
                    probe.openlr,
                ),
                spatial_role="provider_matched_road_geometry",
                qualifiers={
                    **common,
                    "matched_geometry_is_not_query_point": True,
                    "matched_geometry_is_not_exact_road_identity": True,
                    "openlr_is_provider_segment_reference": probe.openlr is not None,
                },
            )

        for prop, value, qk, unit in (
            ("current_speed", probe.current_speed_mph, "velocity", "mile_per_hour"),
            ("free_flow_speed", probe.free_flow_speed_mph, "velocity", "mile_per_hour"),
            ("current_travel_time", probe.current_travel_time_seconds, "duration", "second"),
            ("free_flow_travel_time", probe.free_flow_travel_time_seconds, "duration", "second"),
        ):
            if value is not None:
                yield _measurement(
                    subject=subject,
                    predicate=prop,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    quantity_kind=qk,
                    unit=unit,
                    measurement_kind="provider_modeled_telemetry",
                    identity_parts=(
                        observed_at,
                        value,
                        probe.provider,
                        probe.probe_id,
                    ),
                    qualifiers={**common, "scale_type": "ratio"},
                )

        if probe.road_closure is not None:
            yield _source_report_assertion(
                subject=subject,
                predicate="provider_reports_road_closure",
                value=probe.road_closure,
                provenance=provenance,
                temporal=temporal,
                identity_parts=(
                    observed_at,
                    probe.provider,
                    probe.probe_id,
                    probe.road_closure,
                    probe.openlr,
                ),
                qualifiers={
                    **common,
                    "condition_scope": "provider_matched_road_segment",
                    "matched_segment_reference": probe.openlr,
                    "false_does_not_prove_unrestricted_road": True,
                    "report_is_not_local_road_state_authority": True,
                },
            )

        if probe.confidence is not None:
            proposition = _proposition(subject, "provider-native-confidence")
            foreign_provenance = SemanticProvenance(
                SemanticAssertionOrigin.FOREIGN_NATIVE_PRESERVED,
                provenance.sources,
            )
            yield SemanticAssertion(
                _id(
                    proposition,
                    observed_at,
                    probe.confidence,
                    probe.provider,
                    probe.probe_id,
                ),
                proposition,
                SemanticKind.FOREIGN_NATIVE,
                "Foreign semantic preservation",
                subject,
                "tomtom_flow_confidence",
                probe.confidence,
                foreign_provenance,
                temporal,
                _q(
                    {
                        **common,
                        "local_semantic_role": "unresolved",
                        "not_claim_confidence": True,
                        "not_source_reliability": True,
                        "not_data_product_quality": True,
                        "not_measurement_uncertainty_without_provider_contract": True,
                    }
                ),
            )


def _traffic_events(
    entity: Entity,
    state: TrafficEventCollectionState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    auth = _authority_qualifiers(observation)
    collection_ref = f"{entity.entity_id}:event-collection:{state.source_family}"
    collection_provenance = _provider_provenance(entity, state.provider, observation)

    yield _collection_scope_assertion(
        subject=collection_ref,
        center_latitude=state.scope_center_latitude,
        center_longitude=state.scope_center_longitude,
        radius_miles=state.scope_radius_miles,
        provenance=collection_provenance,
        temporal=SemanticTemporalContext(observed_at=observed_at),
        identity_parts=(
            observed_at,
            state.scope_center_latitude,
            state.scope_center_longitude,
            state.scope_radius_miles,
        ),
        qualifiers={
            **auth,
            "provider": state.provider,
            "source_family": state.source_family,
        },
    )

    if (
        observation is not None
        and observation.availability is ObservationAvailability.CURRENT
        and state.local_record_count == 0
    ):
        proposition = _proposition(
            collection_ref,
            "current_collection_supports_no_local_records",
        )
        yield SemanticAssertion(
            _id(
                proposition,
                observation.checked_at,
                state.source_record_count,
                state.scope_radius_miles,
            ),
            proposition,
            SemanticKind.EVIDENCE,
            "Evidence relation",
            collection_ref,
            "current_collection_supports_no_local_records",
            True,
            collection_provenance,
            SemanticTemporalContext(observed_at=observation.checked_at),
            _q(
                {
                    **auth,
                    "scope_radius_miles": state.scope_radius_miles,
                    "source_record_count": state.source_record_count,
                    "negative_evidence_scope": (
                        "this provider/source family and configured collection scope only"
                    ),
                    "not_universal_event_absence": True,
                }
            ),
        )

    for event in state.events:
        record_ref = (
            f"{entity.entity_id}:event-record:"
            f"{state.source_family}:{event.source_record_id}"
        )
        provenance = _provider_provenance(
            entity,
            event.provider,
            observation,
            record_ref=record_ref,
            native_record_id=event.source_record_id,
        )
        source_time = event.updated_at or event.reported_at
        temporal = SemanticTemporalContext(
            phenomenon_time=event.start_at,
            source_time=source_time,
            observed_at=observed_at,
        )

        if event.geometry:
            reported_geometry = _line_geometry(event.geometry)
            yield _spatial_assertion(
                subject=record_ref,
                predicate="reported_event_geometry",
                value=reported_geometry,
                provenance=provenance,
                temporal=temporal,
                identity_parts=(
                    event.source_record_id,
                    source_time,
                    observed_at,
                    reported_geometry,
                ),
                spatial_role="source_reported_event_geometry",
                qualifiers={
                    **auth,
                    "provider": event.provider,
                    "source_family": event.source_family,
                    "record_geometry_is_not_world_event_identity": True,
                    "shared_geometry_does_not_establish_same_event": True,
                },
            )


        native_dimensions = (
            ("event_type_classification", event.event_type, "classification"),
            ("event_subtype_classification", event.event_subtype, "classification"),
            ("severity_classification", event.severity, "classification"),
            ("lanes_affected_classification", event.lanes_affected, "classification_or_source_expression"),
            ("major_event_classification", event.major_event, "classification"),
            ("magnitude_of_delay_classification", event.magnitude_of_delay, "classification"),
            ("probability_of_occurrence_classification", event.probability_of_occurrence, "classification"),
            ("time_validity_classification", event.time_validity, "classification"),
            ("event_code_classification", event.event_codes or None, "code_set"),
        )
        for predicate, value, semantic_role in native_dimensions:
            if value is not None:
                yield _foreign_native_assertion(
                    subject=record_ref,
                    predicate=predicate,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    identity_parts=(
                        event.source_record_id,
                        source_time,
                        observed_at,
                        predicate,
                        value,
                    ),
                    semantic_role=semantic_role,
                    semantic_authority=event.provider,
                    qualifiers={
                        **auth,
                        "source_family": event.source_family,
                        "collection_class": event.collection_class,
                        "source_field_semantics_are_provider_native": True,
                        "classification_does_not_create_nerv_class_membership": True,
                    },
                )

        if event.full_closure is not None:
            yield _source_report_assertion(
                subject=record_ref,
                predicate="provider_reports_full_closure",
                value=event.full_closure,
                provenance=provenance,
                temporal=temporal,
                identity_parts=(
                    event.source_record_id,
                    source_time,
                    observed_at,
                    event.full_closure,
                ),
                qualifiers={
                    **auth,
                    "provider": event.provider,
                    "source_family": event.source_family,
                    "condition_scope": "reported_traffic_event",
                    "adapter_normalized_provider_claim": True,
                    "record_is_not_world_event_identity": True,
                    "report_is_not_local_road_state_authority": True,
                    "false_does_not_assert_no_lane_restriction": True,
                },
            )

        for predicate, value, quantity_kind, unit in (
            ("reported_delay", event.delay_seconds, "duration", "second"),
            ("reported_event_length", event.length_meters, "length", "meter"),
        ):
            if value is not None:
                yield _measurement(
                    subject=record_ref,
                    predicate=predicate,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    quantity_kind=quantity_kind,
                    unit=unit,
                    measurement_kind="provider_estimated_event_metric",
                    identity_parts=(
                        event.source_record_id,
                        source_time,
                        observed_at,
                        predicate,
                        value,
                    ),
                    qualifiers={
                        **auth,
                        "provider": event.provider,
                        "source_family": event.source_family,
                        "scale_type": "ratio",
                        "not_direct_physical_measurement": True,
                    },
                )

        if event.community_report_count is not None:
            yield _measurement(
                subject=record_ref,
                predicate="community_report_count",
                value=event.community_report_count,
                provenance=provenance,
                temporal=temporal,
                quantity_kind="count",
                unit="count",
                measurement_kind="provider_reported_count",
                identity_parts=(
                    event.source_record_id,
                    source_time,
                    observed_at,
                    event.community_report_count,
                    event.community_last_report_at,
                ),
                qualifiers={
                    **auth,
                    "provider": event.provider,
                    "source_family": event.source_family,
                    "community_last_report_at": event.community_last_report_at,
                    "scale_type": "ratio",
                    "report_count_is_not_independent_corroboration": True,
                    "report_count_is_not_claim_confidence": True,
                    "report_count_is_not_source_reliability": True,
                    "source_plurality_does_not_prove_independence": True,
                },
            )

        proposition = _proposition(record_ref, "provider_reports_event_record")
        yield SemanticAssertion(
            _id(
                proposition,
                event.source_record_id,
                event.updated_at,
                event.reported_at,
                observed_at,
            ),
            proposition,
            SemanticKind.SOURCE_REPORT,
            "Epistemic assertion",
            record_ref,
            "provider_reports_event_record",
            {
                "event_type": event.event_type,
                "event_subtype": event.event_subtype,
                "description": event.description,
                "roadway": event.roadway,
                "direction": event.direction,
                "county": event.county,
                "severity": event.severity,
                "full_closure": event.full_closure,
            },
            provenance,
            temporal,
            _q(
                {
                    **auth,
                    "source_family": event.source_family,
                    "collection_class": event.collection_class,
                    "source_organization": event.source_organization,
                    "source_id": event.source_id,
                    "upstream_event_id": event.upstream_event_id,
                    "reported_at": event.reported_at,
                    "updated_at": event.updated_at,
                    "event_start_at": event.start_at,
                    "event_end_at": event.end_at,
                    "community_last_report_at": event.community_last_report_at,
                    "record_is_not_world_event_identity": True,
                    "report_does_not_establish_causality": True,
                }
            ),
        )


def _weather_state(
    entity: Entity,
    state: WeatherState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    auth = _authority_qualifiers(observation)
    provenance = _provider_provenance(entity, state.provider, observation)
    observed_at = observation.checked_at if observation is not None else None
    temporal = SemanticTemporalContext(
        phenomenon_time=state.provider_observed_at,
        observed_at=observed_at,
    )
    subject = f"{entity.entity_id}:weather-current:{state.provider}"
    common = {
        **auth,
        "provider": state.provider,
        "provider_observed_at": state.provider_observed_at,
        "provider_timezone": state.provider_timezone,
        "scale_type": "ratio",
        "not_direct_sensor_claim": True,
    }
    if state.weather_code is not None:
        yield _foreign_native_assertion(
            subject=subject,
            predicate="provider_weather_code",
            value=state.weather_code,
            provenance=provenance,
            temporal=temporal,
            identity_parts=(
                state.provider_observed_at,
                observed_at,
                state.provider,
                state.weather_code,
            ),
            semantic_role="weather_classification_code",
            semantic_authority=state.provider,
            qualifiers={
                **auth,
                "provider_timezone": state.provider_timezone,
                "code_is_not_local_weather_condition": True,
                "code_requires_explicit_crosswalk_for_local_condition": True,
            },
        )

    for prop, value, qk, unit in (
        ("temperature", state.temperature_f, "temperature", "degree_fahrenheit"),
        (
            "apparent_temperature",
            state.apparent_temperature_f,
            "temperature",
            "degree_fahrenheit",
        ),
        (
            "relative_humidity",
            state.relative_humidity_percent,
            "relative_humidity",
            "percent",
        ),
        ("precipitation", state.precipitation_in, "length", "inch"),
        ("cloud_cover", state.cloud_cover_percent, "cloud_cover_fraction", "percent"),
        ("wind_speed", state.wind_speed_mph, "velocity", "mile_per_hour"),
        ("wind_direction", state.wind_direction_deg, "plane_angle", "degree"),
        ("wind_gust", state.wind_gust_mph, "velocity", "mile_per_hour"),
    ):
        if value is not None:
            yield _measurement(
                subject=subject,
                predicate=prop,
                value=value,
                provenance=provenance,
                temporal=temporal,
                quantity_kind=qk,
                unit=unit,
                measurement_kind="provider_current_value",
                identity_parts=(
                    state.provider_observed_at,
                    observed_at,
                    value,
                    state.provider,
                ),
                qualifiers=common,
            )


def _surface_network(
    entity: Entity,
    state: SurfaceObservationNetworkState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    auth = _authority_qualifiers(observation)
    observed_at = observation.checked_at if observation is not None else None
    for station in state.stations:
        subject = f"{entity.entity_id}:surface-station:{station.station_id}"
        record_ref = f"surface-station-record:{station.station_id}:{station.observed_at}"
        provenance = _provider_provenance(
            entity,
            state.provider,
            observation,
            record_ref=record_ref,
            native_record_id=station.station_id,
        )
        temporal = SemanticTemporalContext(
            phenomenon_time=station.observed_at,
            observed_at=observed_at,
        )
        common = {
            **auth,
            "provider": state.provider,
            "station_id": station.station_id,
            "station_name": station.station_name,
            "station_observed_at": station.observed_at,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "distance_mi": station.distance_mi,
            "scale_type": "ratio",
        }

        for predicate, value, role in (
            ("flight_category_classification", station.flight_category, "aviation_classification"),
            ("present_weather_classification", station.present_weather, "weather_code_or_expression"),
        ):
            if value is not None:
                yield _foreign_native_assertion(
                    subject=subject,
                    predicate=predicate,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    identity_parts=(
                        station.station_id,
                        station.observed_at,
                        observed_at,
                        predicate,
                        value,
                    ),
                    semantic_role=role,
                    semantic_authority=state.provider,
                    qualifiers={
                        **auth,
                        "station_id": station.station_id,
                        "source_record": record_ref,
                        "classification_does_not_create_nerv_condition": True,
                    },
                )

        if station.raw_metar is not None:
            proposition = _proposition(subject, "raw_metar_artifact")
            yield SemanticAssertion(
                _id(
                    proposition,
                    station.station_id,
                    station.observed_at,
                    observed_at,
                    station.raw_metar,
                ),
                proposition,
                SemanticKind.INFORMATION_ARTIFACT,
                "Epistemic assertion",
                subject,
                "raw_metar_artifact",
                station.raw_metar,
                provenance,
                temporal,
                _q({
                    **auth,
                    "provider": state.provider,
                    "station_id": station.station_id,
                    "raw_text_is_not_world_state": True,
                    "raw_text_is_not_automatic_condition_identity": True,
                    "parsed_fields_require_explicit_semantic_roles": True,
                }),
            )

        for prop, value, qk, unit in (
            ("temperature", station.temperature_f, "temperature", "degree_fahrenheit"),
            ("dewpoint", station.dewpoint_f, "temperature", "degree_fahrenheit"),
            (
                "relative_humidity",
                station.relative_humidity_percent,
                "relative_humidity",
                "percent",
            ),
            ("wind_direction", station.wind_direction_deg, "plane_angle", "degree"),
            ("wind_speed", station.wind_speed_mph, "velocity", "mile_per_hour"),
            ("wind_gust", station.wind_gust_mph, "velocity", "mile_per_hour"),
            ("visibility", station.visibility_sm, "length", "statute_mile"),
            ("altimeter", station.altimeter_inhg, "pressure", "inch_of_mercury"),
            (
                "sea_level_pressure",
                station.sea_level_pressure_hpa,
                "pressure",
                "hectopascal",
            ),
            ("ceiling", station.ceiling_ft_agl, "length", "foot"),
        ):
            if value is not None:
                yield _measurement(
                    subject=subject,
                    predicate=prop,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    quantity_kind=qk,
                    unit=unit,
                    measurement_kind="direct_station_observation",
                    identity_parts=(
                        station.station_id,
                        station.observed_at,
                        observed_at,
                        value,
                    ),
                    qualifiers=common,
                )


def _weather_estimate(
    entity: Entity,
    state: CurrentWeatherEstimateState,
) -> Iterable[SemanticAssertion]:
    provenance = _derived_provenance(entity, state.method)
    temporal = SemanticTemporalContext(derived_at=state.derived_at)
    subject = f"{entity.entity_id}:current-weather-estimate"
    common = {
        "semantic_authority_state": "locally_derived",
        "current_authority": True,
        "derived_at": state.derived_at,
        "derivation_method": state.method,
        "primary_source": state.primary_source,
        "surface_station_count": state.surface_station_count,
        "scale_type": "ratio",
        "not_direct_observation": True,
    }
    for prop, value, qk, unit in (
        ("temperature", state.temperature_f, "temperature", "degree_fahrenheit"),
        ("dewpoint", state.dewpoint_f, "temperature", "degree_fahrenheit"),
        (
            "relative_humidity",
            state.relative_humidity_percent,
            "relative_humidity",
            "percent",
        ),
        ("wind_direction", state.wind_direction_deg, "plane_angle", "degree"),
        ("wind_speed", state.wind_speed_mph, "velocity", "mile_per_hour"),
        ("wind_gust", state.wind_gust_mph, "velocity", "mile_per_hour"),
        ("visibility", state.visibility_sm, "length", "statute_mile"),
        ("altimeter", state.altimeter_inhg, "pressure", "inch_of_mercury"),
        ("ceiling", state.ceiling_ft_agl, "length", "foot"),
        (
            "surface_temperature_spread",
            state.surface_temperature_spread_f,
            "temperature_difference",
            "degree_fahrenheit",
        ),
    ):
        if value is not None:
            yield _measurement(
                subject=subject,
                predicate=prop,
                value=value,
                provenance=provenance,
                temporal=temporal,
                quantity_kind=qk,
                unit=unit,
                measurement_kind="derived_estimate",
                identity_parts=(state.derived_at, state.method, value),
                qualifiers=common,
            )


def _weather_alerts(
    entity: Entity,
    state: WeatherAlertState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    auth = _authority_qualifiers(observation)
    for alert in state.alerts:
        record_ref = f"{entity.entity_id}:weather-alert-record:{alert.alert_id}"
        provenance = _provider_provenance(
            entity,
            state.provider,
            observation,
            record_ref=record_ref,
            native_record_id=alert.alert_id,
        )
        temporal = SemanticTemporalContext(
            phenomenon_time=alert.effective_at,
            source_time=alert.sent_at,
            observed_at=observed_at,
        )

        for predicate, value, role in (
            ("alert_event_classification", alert.event, "hazard_or_alert_classification"),
            ("alert_severity_classification", alert.severity, "severity_classification"),
            ("alert_urgency_classification", alert.urgency, "urgency_classification"),
        ):
            if value is not None:
                yield _foreign_native_assertion(
                    subject=record_ref,
                    predicate=predicate,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    identity_parts=(
                        alert.alert_id,
                        alert.sent_at,
                        alert.effective_at,
                        observed_at,
                        predicate,
                        value,
                    ),
                    semantic_role=role,
                    semantic_authority=state.provider,
                    qualifiers={
                        **auth,
                        "provider": state.provider,
                        "classification_does_not_create_local_hazard_identity": True,
                        "severity_does_not_equal_local_operational_priority": True,
                    },
                )

        proposition = _proposition(record_ref, "provider_reports_alert")
        yield SemanticAssertion(
            _id(
                proposition,
                alert.alert_id,
                alert.sent_at,
                alert.effective_at,
                alert.expires_at,
                observed_at,
            ),
            proposition,
            SemanticKind.SOURCE_REPORT,
            "Epistemic assertion",
            record_ref,
            "provider_reports_alert",
            {
                "event": alert.event,
                "severity": alert.severity,
                "urgency": alert.urgency,
                "headline": alert.headline,
            },
            provenance,
            temporal,
            _q(
                {
                    **auth,
                    "sent_at": alert.sent_at,
                    "effective_at": alert.effective_at,
                    "expires_at": alert.expires_at,
                    "provider_updated_at": state.provider_updated_at,
                    "record_is_not_hazard_identity": True,
                }
            ),
        )


def _system_state(
    entity: Entity,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    auth = _authority_qualifiers(observation)
    observed_at = observation.checked_at if observation is not None else None
    provenance = SemanticProvenance(
        SemanticAssertionOrigin.SOURCE_OBSERVED,
        _adapter_sources(entity, observation),
    )
    temporal = SemanticTemporalContext(observed_at=observed_at)

    health = entity.get(HealthState)
    if health is not None:
        derived = _derived_provenance(entity, "health-system")
        proposition = _proposition(entity.entity_id, "health_status")
        yield SemanticAssertion(
            _id(proposition, health.status.value, health.reasons),
            proposition,
            SemanticKind.STATE_CONDITION,
            "State condition",
            entity.entity_id,
            "health_status",
            health.status.value,
            derived,
            SemanticTemporalContext(derived_at=observed_at),
            _q(
                {
                    "semantic_authority_state": "locally_derived",
                    "current_authority": True,
                    "reasons": health.reasons,
                    "condition_scope": "derived operational health",
                    "health_is_not_raw_telemetry": True,
                }
            ),
        )

    compute = entity.get(ComputeState)
    if compute is not None:
        for prop, value, qk, unit, extra in (
            (
                "cpu_utilization",
                compute.cpu_percent,
                "dimensionless_ratio",
                "percent",
                {"logical_cpus": compute.logical_cpus},
            ),
            (
                "load_per_cpu",
                compute.load_per_cpu,
                "dimensionless_ratio",
                None,
                {"load_1m": compute.load_1m},
            ),
        ):
            yield _measurement(
                subject=entity.entity_id,
                predicate=prop,
                value=value,
                provenance=provenance,
                temporal=temporal,
                quantity_kind=qk,
                unit=unit,
                measurement_kind=(
                    "host_telemetry"
                    if prop == "cpu_utilization"
                    else "derived_host_telemetry"
                ),
                identity_parts=(observed_at, value, prop),
                qualifiers={**auth, "scale_type": "ratio", **extra},
            )

    memory = entity.get(MemoryState)
    if memory is not None:
        yield _measurement(
            subject=entity.entity_id,
            predicate="memory_used",
            value=memory.used_percent,
            provenance=provenance,
            temporal=temporal,
            quantity_kind="dimensionless_ratio",
            unit="percent",
            measurement_kind="host_telemetry",
            identity_parts=(observed_at, memory.used_percent, "memory"),
            qualifiers={**auth, "scale_type": "ratio"},
        )

    storage = entity.get(StorageState)
    if storage is not None:
        yield _measurement(
            subject=f"{entity.entity_id}:storage:{storage.mountpoint}",
            predicate="storage_used",
            value=storage.used_percent,
            provenance=provenance,
            temporal=temporal,
            quantity_kind="dimensionless_ratio",
            unit="percent",
            measurement_kind="host_telemetry",
            identity_parts=(observed_at, storage.mountpoint, storage.used_percent),
            qualifiers={
                **auth,
                "scale_type": "ratio",
                "mountpoint": storage.mountpoint,
            },
        )

    temperature = entity.get(TemperatureState)
    if temperature is not None and temperature.celsius is not None:
        temp_source = _source(
            f"sensor:{temperature.source or 'unknown'}",
            SemanticSourceRole.SOURCE_RECORD,
            native_id=temperature.source,
        )
        temp_provenance = SemanticProvenance(
            SemanticAssertionOrigin.SOURCE_OBSERVED,
            (temp_source, *_adapter_sources(entity, observation)),
        )
        yield _measurement(
            subject=entity.entity_id,
            predicate="temperature",
            value=temperature.celsius,
            provenance=temp_provenance,
            temporal=temporal,
            quantity_kind="temperature",
            unit="degree_celsius",
            measurement_kind="host_sensor_telemetry",
            identity_parts=(
                observed_at,
                temperature.source,
                temperature.celsius,
            ),
            qualifiers={**auth, "scale_type": "interval"},
        )

    usb = entity.get(UsbDeviceState)
    if usb is not None:
        proposition = _proposition(entity.entity_id, "usb_device_present")
        yield SemanticAssertion(
            _id(proposition, observed_at, usb.usb_id, usb.present, usb.mode),
            proposition,
            SemanticKind.STATE_CONDITION,
            "State condition",
            entity.entity_id,
            "usb_device_present",
            usb.present,
            provenance,
            temporal,
            _q(
                {
                    **auth,
                    "usb_id": usb.usb_id,
                    "mode": usb.mode,
                    "description": usb.description,
                    "successful_absence_is_world_evidence_only_when_current": True,
                }
            ),
        )

    wifi = entity.get(WifiLinkState)
    if wifi is not None:
        proposition = _proposition(entity.entity_id, "wifi_connected")
        yield SemanticAssertion(
            _id(proposition, observed_at, wifi.interface, wifi.ssid, wifi.connected),
            proposition,
            SemanticKind.STATE_CONDITION,
            "State condition",
            entity.entity_id,
            "wifi_connected",
            wifi.connected,
            provenance,
            temporal,
            _q(
                {
                    **auth,
                    "interface": wifi.interface,
                    "ssid": wifi.ssid,
                    "frequency_mhz": wifi.frequency_mhz,
                    "ipv4": wifi.ipv4,
                }
            ),
        )
        if wifi.signal_dbm is not None:
            yield _measurement(
                subject=f"{entity.entity_id}:wifi-link",
                predicate="wifi_signal",
                value=wifi.signal_dbm,
                provenance=provenance,
                temporal=temporal,
                quantity_kind="signal_level",
                unit="dBm",
                measurement_kind="wifi_link_telemetry",
                identity_parts=(
                    observed_at,
                    wifi.interface,
                    wifi.signal_dbm,
                ),
                qualifiers={
                    **auth,
                    "scale_type": "interval",
                    "interface": wifi.interface,
                },
            )
        for prop, value in (
            ("wifi_rx_rate", wifi.rx_mbps),
            ("wifi_tx_rate", wifi.tx_mbps),
        ):
            if value is not None:
                yield _measurement(
                    subject=f"{entity.entity_id}:wifi-link",
                    predicate=prop,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    quantity_kind="data_rate",
                    unit="megabit_per_second",
                    measurement_kind="wifi_link_telemetry",
                    identity_parts=(observed_at, wifi.interface, prop, value),
                    qualifiers={
                        **auth,
                        "scale_type": "ratio",
                        "interface": wifi.interface,
                    },
                )




def _prediction_assertion(
    *,
    subject: str,
    predicate: str,
    value: object,
    provenance: SemanticProvenance,
    temporal: SemanticTemporalContext,
    identity_parts: tuple[object, ...],
    qualifiers: Mapping[str, Any],
) -> SemanticAssertion:
    proposition = _proposition(subject, predicate)
    return SemanticAssertion(
        _id(proposition, *identity_parts),
        proposition,
        SemanticKind.PREDICTION,
        "Epistemic assertion",
        subject,
        predicate,
        value,
        provenance,
        temporal,
        _q({
            **qualifiers,
            "epistemic_mode": "prediction",
            "not_observation": True,
            "not_measurement": True,
            "not_present_world_state": True,
        }),
    )


def _daily_weather_forecast(
    entity: Entity,
    state: WeatherForecastState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    provenance = _provider_provenance(entity, state.provider, observation)
    subject = f"{entity.entity_id}:daily-forecast:{state.provider}:{state.forecast_date}"
    temporal = SemanticTemporalContext(
        phenomenon_time=state.forecast_date,
        observed_at=observed_at,
    )
    common = {
        **_authority_qualifiers(observation),
        "provider": state.provider,
        "forecast_date": state.forecast_date,
        "provider_timezone": state.provider_timezone,
        "forecast_granularity": "daily",
    }
    for predicate, value, quantity_kind, unit in (
        ("forecast_high_temperature", state.high_f, "temperature", "degree_fahrenheit"),
        ("forecast_low_temperature", state.low_f, "temperature", "degree_fahrenheit"),
        ("forecast_precipitation_probability_max", state.precipitation_probability_max_percent, "probability", "percent"),
    ):
        if value is not None:
            yield _prediction_assertion(
                subject=subject,
                predicate=predicate,
                value=value,
                provenance=provenance,
                temporal=temporal,
                identity_parts=(state.forecast_date, observed_at, predicate, value, state.provider),
                qualifiers={**common, "quantity_kind": quantity_kind, "unit": unit},
            )
    for predicate, value in (
        ("forecast_sunrise", state.sunrise),
        ("forecast_sunset", state.sunset),
    ):
        if value is not None:
            yield _prediction_assertion(
                subject=subject,
                predicate=predicate,
                value=value,
                provenance=provenance,
                temporal=temporal,
                identity_parts=(state.forecast_date, observed_at, predicate, value, state.provider),
                qualifiers={**common, "value_role": "predicted_astronomical_event_time"},
            )


def _nws_hourly_forecast(
    entity: Entity,
    state: NWSHourlyForecastState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    provenance = _provider_provenance(entity, state.provider, observation)
    source_time = state.updated_at or state.generated_at
    for hour in state.hours:
        subject = f"{entity.entity_id}:hourly-forecast:{hour.start_time}"
        temporal = SemanticTemporalContext(
            phenomenon_time=hour.start_time,
            source_time=source_time,
            observed_at=observed_at,
        )
        common = {
            **_authority_qualifiers(observation),
            "provider": state.provider,
            "office": state.office,
            "grid_x": state.grid_x,
            "grid_y": state.grid_y,
            "generated_at": state.generated_at,
            "updated_at": state.updated_at,
            "forecast_hour_start": hour.start_time,
            "forecast_granularity": "hourly",
        }
        for predicate, value, quantity_kind, unit in (
            ("forecast_temperature", hour.temperature_f, "temperature", "degree_fahrenheit"),
            ("forecast_dewpoint", hour.dewpoint_f, "temperature", "degree_fahrenheit"),
            ("forecast_relative_humidity", hour.relative_humidity_percent, "relative_humidity", "percent"),
            ("forecast_precipitation_probability", hour.precipitation_probability_percent, "probability", "percent"),
            ("forecast_wind_speed_min", hour.wind_speed_min_mph, "velocity", "mile_per_hour"),
            ("forecast_wind_speed_max", hour.wind_speed_max_mph, "velocity", "mile_per_hour"),
        ):
            if value is not None:
                yield _prediction_assertion(
                    subject=subject,
                    predicate=predicate,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    identity_parts=(hour.start_time, source_time, observed_at, predicate, value),
                    qualifiers={**common, "quantity_kind": quantity_kind, "unit": unit},
                )
        for predicate, value in (
            ("forecast_wind_direction", hour.wind_direction),
            ("forecast_summary", hour.short_forecast),
        ):
            if value is not None:
                yield _prediction_assertion(
                    subject=subject,
                    predicate=predicate,
                    value=value,
                    provenance=provenance,
                    temporal=temporal,
                    identity_parts=(hour.start_time, source_time, observed_at, predicate, value),
                    qualifiers=common,
                )


def _radar_mosaic(
    entity: Entity,
    state: RadarMosaicState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    provenance = _provider_provenance(entity, state.provider, observation)
    subject = f"{entity.entity_id}:radar-mosaic:{state.product}:{state.layer}"
    temporal = SemanticTemporalContext(
        source_time=state.stream_latest_at,
        retrieved_at=state.frame_retrieved_at or observed_at,
        observed_at=observed_at,
    )
    proposition = _proposition(subject, "radar_image_artifact")
    yield SemanticAssertion(
        _id(proposition, state.image_sha256, state.stream_latest_at, state.frame_retrieved_at),
        proposition,
        SemanticKind.INFORMATION_ARTIFACT,
        "Epistemic assertion",
        subject,
        "radar_image_artifact",
        state.image_sha256,
        provenance,
        temporal,
        _q({
            **_authority_qualifiers(observation),
            "provider": state.provider,
            "product": state.product,
            "layer": state.layer,
            "stream_latest_filename": state.stream_latest_filename,
            "west": state.west,
            "south": state.south,
            "east": state.east,
            "north": state.north,
            "range_miles": state.range_miles,
            "image_width": state.image_width,
            "image_height": state.image_height,
            "warning_overlay_available": state.warning_overlay_available,
            "legend_available": state.legend_available,
            "artifact_is_not_weather_event_identity": True,
            "artifact_is_not_direct_weather_measurement": True,
            "requires_interpretation_for_world_claims": True,
        }),
    )




def _radar_mosaic_spatial(
    entity: Entity,
    state: RadarMosaicState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    provenance = _provider_provenance(entity, state.provider, observation)
    subject = f"{entity.entity_id}:radar-mosaic:{state.product}:{state.layer}"
    temporal = SemanticTemporalContext(
        source_time=state.stream_latest_at,
        retrieved_at=state.frame_retrieved_at or observed_at,
        observed_at=observed_at,
    )
    envelope = (
        float(state.west),
        float(state.south),
        float(state.east),
        float(state.north),
    )
    yield _spatial_assertion(
        subject=subject,
        predicate="radar_product_coverage",
        value=envelope,
        provenance=provenance,
        temporal=temporal,
        identity_parts=(
            state.image_sha256,
            state.stream_latest_at,
            envelope,
        ),
        spatial_role="product_coverage_envelope",
        qualifiers={
            **_authority_qualifiers(observation),
            "coordinate_order": "west_south_east_north",
            "range_miles": state.range_miles,
            "coverage_is_not_storm_footprint": True,
            "coverage_is_not_warning_geometry": True,
        },
    )


def _radar_context(
    entity: Entity,
    state: RadarContextState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    provenance = _provider_provenance(entity, state.provider, observation)
    subject = f"{entity.entity_id}:radar-context"
    temporal = SemanticTemporalContext(retrieved_at=state.retrieved_at)
    proposition = _proposition(subject, "radar_context_artifact")
    yield SemanticAssertion(
        _id(proposition, state.context_sha256, state.content_sha256, state.retrieved_at),
        proposition,
        SemanticKind.INFORMATION_ARTIFACT,
        "Epistemic assertion",
        subject,
        "radar_context_artifact",
        state.context_sha256,
        provenance,
        temporal,
        _q({
            **_authority_qualifiers(observation),
            "provider": state.provider,
            "content_sha256": state.content_sha256,
            "west": state.west,
            "south": state.south,
            "east": state.east,
            "north": state.north,
            "county_count": state.county_count,
            "primary_road_count": state.primary_road_count,
            "secondary_road_count": state.secondary_road_count,
            "place_count": state.place_count,
            "context_is_reference_information": True,
            "not_dynamic_weather_state": True,
        }),
    )




def _radar_context_spatial(
    entity: Entity,
    state: RadarContextState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    provenance = _provider_provenance(entity, state.provider, observation)
    subject = f"{entity.entity_id}:radar-context"
    envelope = (
        float(state.west),
        float(state.south),
        float(state.east),
        float(state.north),
    )
    yield _spatial_assertion(
        subject=subject,
        predicate="reference_context_coverage",
        value=envelope,
        provenance=provenance,
        temporal=SemanticTemporalContext(retrieved_at=state.retrieved_at),
        identity_parts=(state.context_sha256, state.retrieved_at, envelope),
        spatial_role="reference_context_envelope",
        qualifiers={
            **_authority_qualifiers(observation),
            "coordinate_order": "west_south_east_north",
            "reference_geometry_has_no_meteorological_authority": True,
            "reference_geometry_has_no_traffic_event_authority": True,
        },
    )


def _traffic_cameras(
    entity: Entity,
    state: TrafficCameraCollectionState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    collection_subject = f"{entity.entity_id}:camera-collection:{state.source_family}"
    collection_provenance = _provider_provenance(entity, state.provider, observation)
    yield _collection_scope_assertion(
        subject=collection_subject,
        center_latitude=state.scope_center_latitude,
        center_longitude=state.scope_center_longitude,
        radius_miles=state.scope_radius_miles,
        provenance=collection_provenance,
        temporal=SemanticTemporalContext(observed_at=observed_at),
        identity_parts=(
            observed_at,
            state.scope_center_latitude,
            state.scope_center_longitude,
            state.scope_radius_miles,
        ),
        qualifiers={
            **_authority_qualifiers(observation),
            "provider": state.provider,
            "source_family": state.source_family,
        },
    )
    for camera in state.cameras:
        subject = f"{entity.entity_id}:camera-record:{camera.camera_id}"
        provenance = _provider_provenance(
            entity, camera.provider, observation,
            record_ref=subject, native_record_id=camera.camera_id,
        )
        temporal = SemanticTemporalContext(observed_at=observed_at)
        yield _spatial_assertion(
            subject=subject,
            predicate="reported_infrastructure_location",
            value=_point(camera.latitude, camera.longitude),
            provenance=provenance,
            temporal=temporal,
            identity_parts=(
                observed_at,
                camera.camera_id,
                camera.latitude,
                camera.longitude,
            ),
            spatial_role="provider_reported_infrastructure_point",
            qualifiers={
                **_authority_qualifiers(observation),
                "infrastructure_type": "traffic_camera",
                "location_is_not_visual_observation_result": True,
                "location_does_not_assert_camera_field_of_view": True,
            },
        )
        proposition = _proposition(subject, "provider_reports_camera")
        yield SemanticAssertion(
            _id(proposition, observed_at, camera.camera_id, camera.status, camera.video_url),
            proposition,
            SemanticKind.INFORMATION_ARTIFACT,
            "Epistemic assertion",
            subject,
            "provider_reports_camera",
            {
                "status": camera.status,
                "roadway": camera.roadway,
                "direction": camera.direction,
                "location": camera.location,
                "latitude": camera.latitude,
                "longitude": camera.longitude,
                "page_url": camera.page_url,
                "video_url": camera.video_url,
            },
            provenance,
            temporal,
            _q({
                **_authority_qualifiers(observation),
                "source_family": camera.source_family,
                "source_id": camera.source_id,
                "county": camera.county,
                "record_is_infrastructure_description": True,
                "camera_record_is_not_visual_observation_result": True,
                "video_url_is_not_interpreted_world_evidence": True,
            }),
        )


def _traffic_message_signs(
    entity: Entity,
    state: TrafficMessageSignCollectionState,
    observation: ObservationState | None,
) -> Iterable[SemanticAssertion]:
    observed_at = observation.checked_at if observation is not None else None
    collection_subject = f"{entity.entity_id}:message-sign-collection:{state.source_family}"
    collection_provenance = _provider_provenance(entity, state.provider, observation)
    yield _collection_scope_assertion(
        subject=collection_subject,
        center_latitude=state.scope_center_latitude,
        center_longitude=state.scope_center_longitude,
        radius_miles=state.scope_radius_miles,
        provenance=collection_provenance,
        temporal=SemanticTemporalContext(observed_at=observed_at),
        identity_parts=(
            observed_at,
            state.scope_center_latitude,
            state.scope_center_longitude,
            state.scope_radius_miles,
        ),
        qualifiers={
            **_authority_qualifiers(observation),
            "provider": state.provider,
            "source_family": state.source_family,
        },
    )
    for sign in state.signs:
        subject = f"{entity.entity_id}:message-sign-record:{sign.sign_id}"
        provenance = _provider_provenance(
            entity, sign.provider, observation,
            record_ref=subject, native_record_id=sign.sign_id,
        )
        temporal = SemanticTemporalContext(
            source_time=sign.updated_at,
            observed_at=observed_at,
        )
        yield _spatial_assertion(
            subject=subject,
            predicate="reported_infrastructure_location",
            value=_point(sign.latitude, sign.longitude),
            provenance=provenance,
            temporal=temporal,
            identity_parts=(
                sign.updated_at,
                observed_at,
                sign.sign_id,
                sign.latitude,
                sign.longitude,
            ),
            spatial_role="provider_reported_infrastructure_point",
            qualifiers={
                **_authority_qualifiers(observation),
                "infrastructure_type": "dynamic_message_sign",
                "location_is_not_message_content_location": True,
                "location_does_not_assert_event_location": True,
            },
        )
        proposition = _proposition(subject, "provider_reports_message_sign")
        yield SemanticAssertion(
            _id(proposition, sign.updated_at, observed_at, sign.sign_id, sign.messages),
            proposition,
            SemanticKind.INFORMATION_ARTIFACT,
            "Epistemic assertion",
            subject,
            "provider_reports_message_sign",
            sign.messages,
            provenance,
            temporal,
            _q({
                **_authority_qualifiers(observation),
                "source_family": sign.source_family,
                "county": sign.county,
                "roadway": sign.roadway,
                "direction": sign.direction,
                "name": sign.name,
                "latitude": sign.latitude,
                "longitude": sign.longitude,
                "message_text_is_information_artifact": True,
                "message_text_is_not_automatic_event_truth": True,
            }),
        )


def _traffic_situation(
    entity: Entity,
    state: TrafficSituationState,
) -> Iterable[SemanticAssertion]:
    provenance = _derived_provenance(entity, "traffic.fusion")
    temporal = SemanticTemporalContext(derived_at=state.derived_at)

    yield _collection_scope_assertion(
        subject=f"{entity.entity_id}:traffic-situation-scope",
        center_latitude=state.scope_center_latitude,
        center_longitude=state.scope_center_longitude,
        radius_miles=state.scope_radius_miles,
        provenance=provenance,
        temporal=temporal,
        identity_parts=(
            state.derived_at,
            state.scope_center_latitude,
            state.scope_center_longitude,
            state.scope_radius_miles,
        ),
        qualifiers={
            "semantic_authority_state": "locally_derived",
            "current_authority": True,
            "scope_is_awareness_domain": True,
            "scope_is_not_event_location": True,
        },
    )

    for i, gap in enumerate(state.collection_gaps):
        proposition = _proposition(entity.entity_id, "collection-gap", i)
        yield SemanticAssertion(
            _id(proposition, state.derived_at, gap),
            proposition,
            SemanticKind.COLLECTION_GAP,
            "Collection gap",
            entity.entity_id,
            "known_collection_gap",
            gap,
            provenance,
            temporal,
            _q(
                {
                    "derived_at": state.derived_at,
                    "semantic_authority_state": "locally_derived",
                    "current_authority": True,
                }
            ),
        )
    for kernel in state.kernels:
        if kernel.association_basis == "same-lineage upstream identifier":
            subject = f"{entity.entity_id}:kernel:{kernel.kernel_id}"
            records = tuple(
                _source(
                    ref,
                    SemanticSourceRole.SOURCE_RECORD,
                    native_id=ref,
                )
                for ref in kernel.source_record_refs
            )
            derivation = _source(
                "derivation:traffic.fusion",
                SemanticSourceRole.DERIVATION_PROCESS,
                native_id="traffic.fusion",
            )
            world = _source(
                entity.entity_id,
                SemanticSourceRole.WORLD_ENTITY_REFERENCE,
                native_id=entity.entity_id,
            )
            kernel_provenance = SemanticProvenance(
                SemanticAssertionOrigin.CIC_DERIVED,
                (derivation, *records, world),
                derivation.ref_id,
            )
            proposition = _proposition(
                subject,
                "same_upstream_event_representation",
            )
            yield SemanticAssertion(
                _id(
                    proposition,
                    state.derived_at,
                    kernel.source_record_refs,
                ),
                proposition,
                SemanticKind.IDENTITY_ASSOCIATION,
                "Identity assertion",
                subject,
                "same_upstream_event_representation",
                kernel.source_record_refs,
                kernel_provenance,
                temporal,
                _q(
                    {
                        "mapping_strength": "same_lineage_identifier_only",
                        "source_families": kernel.source_families,
                        "not_independent_corroboration": True,
                        "not_cross_lineage_equivalence": True,
                        "not_causal_inference": True,
                        "semantic_authority_state": "locally_derived",
                        "current_authority": True,
                    }
                ),
            )


def project_entity_semantics(entity: Entity) -> tuple[SemanticAssertion, ...]:
    out: list[SemanticAssertion] = []
    observation = entity.get(ObservationState)
    if observation is not None:
        out.extend(_observation(entity, observation))

    flow = entity.get(TrafficFlowCollectionState)
    if flow is not None:
        out.extend(_traffic_flow(entity, flow, observation))

    traffic_events = entity.get(TrafficEventCollectionState)
    if traffic_events is not None:
        out.extend(_traffic_events(entity, traffic_events, observation))

    weather = entity.get(WeatherState)
    if weather is not None:
        out.extend(_weather_state(entity, weather, observation))

    daily_forecast = entity.get(WeatherForecastState)
    if daily_forecast is not None:
        out.extend(_daily_weather_forecast(entity, daily_forecast, observation))

    hourly_forecast = entity.get(NWSHourlyForecastState)
    if hourly_forecast is not None:
        out.extend(_nws_hourly_forecast(entity, hourly_forecast, observation))

    surface = entity.get(SurfaceObservationNetworkState)
    if surface is not None:
        out.extend(_surface_network(entity, surface, observation))

    estimate = entity.get(CurrentWeatherEstimateState)
    if estimate is not None:
        out.extend(_weather_estimate(entity, estimate))

    alerts = entity.get(WeatherAlertState)
    if alerts is not None:
        out.extend(_weather_alerts(entity, alerts, observation))

    radar = entity.get(RadarMosaicState)
    if radar is not None:
        out.extend(_radar_mosaic(entity, radar, observation))
        out.extend(_radar_mosaic_spatial(entity, radar, observation))

    radar_context = entity.get(RadarContextState)
    if radar_context is not None:
        out.extend(_radar_context(entity, radar_context, observation))
        out.extend(_radar_context_spatial(entity, radar_context, observation))

    cameras = entity.get(TrafficCameraCollectionState)
    if cameras is not None:
        out.extend(_traffic_cameras(entity, cameras, observation))

    signs = entity.get(TrafficMessageSignCollectionState)
    if signs is not None:
        out.extend(_traffic_message_signs(entity, signs, observation))

    situation = entity.get(TrafficSituationState)
    if situation is not None:
        out.extend(_traffic_situation(entity, situation))

    out.extend(_system_state(entity, observation))
    return tuple(out)


def project_world_semantics(world: WorldState) -> tuple[SemanticAssertion, ...]:
    out: list[SemanticAssertion] = []
    for entity_id in sorted(world.entities):
        out.extend(project_entity_semantics(world.entities[entity_id]))
    return tuple(out)
