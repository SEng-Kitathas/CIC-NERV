from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import threading
import time
from typing import Callable

from personal_cic.adapters.world import (
    CharlotteStreetClosuresAdapter,
    CMPDTrafficCADAdapter,
    DriveNCCamerasAdapter,
    DriveNCEventsAdapter,
    DriveNCMessageSignsAdapter,
    DriveNCWZDxAdapter,
    FlowProbeSpec,
    TomTomFlowAdapter,
    TomTomIncidentsAdapter,
)
from personal_cic.bootstrap import RuntimeContext, ingest_observation_batch
from personal_cic.core.config import TrafficConfig
from personal_cic.core.observations import Observation, ObservationAvailability
from personal_cic.core.world.components import (
    ObservationState,
    TrafficCameraCollectionState,
    TrafficEventCollectionState,
    TrafficEventKernel,
    TrafficFlowCollectionState,
    TrafficMessageSignCollectionState,
    TrafficSituationState,
)

from personal_cic.runtime_authority import (
    WorkerLifecycle,
    WorkerLiveness,
    WorkerRuntimeStatus,
)


DRIVENC_EVENTS_ENTITY_ID = "local-traffic-drivenc-events"
WZDX_ENTITY_ID = "local-traffic-wzdx"
CMPD_ENTITY_ID = "local-traffic-cmpd-cad"
CHARLOTTE_CLOSURES_ENTITY_ID = "local-traffic-charlotte-closures"
TOMTOM_INCIDENTS_ENTITY_ID = "local-traffic-tomtom-incidents"
TOMTOM_FLOW_ENTITY_ID = "local-traffic-tomtom-flow"
CAMERAS_ENTITY_ID = "local-traffic-drivenc-cameras"
SIGNS_ENTITY_ID = "local-traffic-drivenc-signs"
SITUATION_ENTITY_ID = "local-traffic-situation"


_EVENT_ENTITIES = (
    DRIVENC_EVENTS_ENTITY_ID,
    WZDX_ENTITY_ID,
    CMPD_ENTITY_ID,
    CHARLOTTE_CLOSURES_ENTITY_ID,
    TOMTOM_INCIDENTS_ENTITY_ID,
)


def _usable(observation: ObservationState | None) -> bool:
    return bool(
        observation
        and observation.availability
        in (ObservationAvailability.CURRENT, ObservationAvailability.DEGRADED)
    )


def _kernel_id(parts: tuple[str, ...]) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]


def derive_traffic_situation(
    *,
    location_label: str,
    center_latitude: float,
    center_longitude: float,
    radius_miles: float,
    event_sources: tuple[tuple[TrafficEventCollectionState, ObservationState], ...],
    cameras: TrafficCameraCollectionState | None,
    cameras_observation: ObservationState | None,
    signs: TrafficMessageSignCollectionState | None,
    signs_observation: ObservationState | None,
    flow: TrafficFlowCollectionState | None = None,
    flow_observation: ObservationState | None = None,
    configured_unavailable: tuple[str, ...],
    external_waze_visual_enabled: bool = True,
    external_waze_zoom: int = 11,
) -> TrafficSituationState | None:
    usable_event_sources = [
        state for state, obs in event_sources if _usable(obs)
    ]
    usable_cameras = cameras if cameras is not None and _usable(cameras_observation) else None
    usable_signs = signs if signs is not None and _usable(signs_observation) else None
    usable_flow = flow if flow is not None and _usable(flow_observation) else None

    if not usable_event_sources and usable_cameras is None and usable_signs is None and usable_flow is None:
        return None

    grouped: dict[tuple[str, ...], list] = {}
    for state in usable_event_sources:
        for event in state.events:
            if event.upstream_event_id:
                key = ("lineage-id", event.source_family, event.upstream_event_id)
            else:
                key = (
                    "source-record",
                    event.source_family,
                    event.provider,
                    event.source_record_id,
                )
            grouped.setdefault(key, []).append(event)

    kernels: list[TrafficEventKernel] = []
    for key, events in grouped.items():
        representative = max(events, key=lambda item: len(item.description or ""))
        point = next(
            (point for event in events for point in event.geometry),
            None,
        )
        source_families = tuple(sorted({event.source_family for event in events}))
        refs = tuple(
            sorted(
                f"{event.provider}|{event.source_record_id}"
                for event in events
            )
        )
        kernels.append(
            TrafficEventKernel(
                kernel_id=_kernel_id(key),
                roadway=representative.roadway,
                summary=representative.description,
                latitude=None if point is None else point.latitude,
                longitude=None if point is None else point.longitude,
                source_families=source_families,
                source_record_refs=refs,
                association_basis=(
                    "same-lineage upstream identifier"
                    if key[0] == "lineage-id"
                    else "unassociated source record"
                ),
            )
        )
    kernels.sort(key=lambda item: (item.roadway or "", item.kernel_id))

    # Count physical/event kernels rather than source records so DriveNC +
    # WZDx representations of the same NCDOT closure cannot double-count it.
    full_closures = sum(
        1
        for events in grouped.values()
        if any(event.full_closure is True for event in events)
    )
    # A fresh empty collection is still current negative evidence. Preserve its
    # source family in the coverage picture even when it contributed no events.
    current_families = {state.source_family for state in usable_event_sources}
    current_families.update(
        event.source_family
        for state in usable_event_sources
        for event in state.events
    )
    if usable_cameras is not None:
        current_families.add(usable_cameras.source_family)
    if usable_signs is not None:
        current_families.add(usable_signs.source_family)
    if usable_flow is not None:
        current_families.add(usable_flow.source_family)

    source_observation_count = sum(
        state.local_record_count for state in usable_event_sources
    )
    if usable_cameras is not None:
        source_observation_count += usable_cameras.local_record_count
    if usable_signs is not None:
        source_observation_count += usable_signs.local_record_count
    if usable_flow is not None:
        source_observation_count += usable_flow.successful_probe_count

    collection_gaps = [
        "Waze crowdsourced incidents/police/hazards are not yet available through a supported normalized machine feed; optional Live Map remains external visual evidence",
        "TomTom flow is currently a sparse nearest-segment probe set, not continuous network coverage or route ETA",
        "CMPD CAD locations remain address-only until a lawful geocoding seam is added",
        "cross-lineage event agreement is visible but source independence/event equivalence is not yet inferred",
    ]
    collection_gaps.extend(configured_unavailable)

    return TrafficSituationState(
        location_label=location_label,
        derived_at=datetime.now(timezone.utc).isoformat(),
        scope_center_latitude=center_latitude,
        scope_center_longitude=center_longitude,
        scope_radius_miles=radius_miles,
        source_observation_count=source_observation_count,
        event_kernel_count=len(kernels),
        full_closure_count=full_closures,
        camera_count=0 if usable_cameras is None else usable_cameras.local_record_count,
        active_message_sign_count=0 if usable_signs is None else usable_signs.active_message_count,
        flow_probe_count=0 if usable_flow is None else usable_flow.successful_probe_count,
        current_source_families=tuple(sorted(current_families)),
        collection_gaps=tuple(collection_gaps),
        correlation_mode=(
            "exact same-lineage upstream identifiers only; no cross-lineage causal or event-equivalence inference"
        ),
        external_waze_visual_enabled=external_waze_visual_enabled,
        external_waze_zoom=external_waze_zoom,
        kernels=tuple(kernels),
    )


class TrafficAwarenessWorker:
    """Remote traffic collection loop with source-preserving traffic semantics."""

    def __init__(
        self,
        *,
        context: RuntimeContext,
        config: TrafficConfig,
        location_label: str,
        latitude: float,
        longitude: float,
        on_terminal_failure: Callable[[WorkerRuntimeStatus], None] | None = None,
    ) -> None:
        self.context = context
        self.config = config
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude

        common = {
            "location_label": location_label,
            "latitude": latitude,
            "longitude": longitude,
            "radius_miles": config.radius_miles,
        }
        self.drivenc_events_adapter = DriveNCEventsAdapter(
            **common,
            api_key_env=config.drivenc.api_key_env,
            timeout_seconds=config.drivenc.timeout_seconds,
            scope_counties=config.scope_counties,
        )
        self.wzdx_adapter = DriveNCWZDxAdapter(
            **common,
            timeout_seconds=config.wzdx.timeout_seconds,
        )
        self.cmpd_adapter = CMPDTrafficCADAdapter(
            **common,
            timeout_seconds=config.cmpd.timeout_seconds,
        )
        self.charlotte_adapter = CharlotteStreetClosuresAdapter(
            **common,
            timeout_seconds=config.charlotte_closures.timeout_seconds,
        )
        self.cameras_adapter = DriveNCCamerasAdapter(
            **common,
            api_key_env=config.drivenc.api_key_env,
            timeout_seconds=config.drivenc.timeout_seconds,
            scope_counties=config.scope_counties,
        )
        self.signs_adapter = DriveNCMessageSignsAdapter(
            **common,
            api_key_env=config.drivenc.api_key_env,
            timeout_seconds=config.drivenc.timeout_seconds,
            scope_counties=config.scope_counties,
        )
        self.tomtom_incidents_adapter = TomTomIncidentsAdapter(
            **common,
            api_key_env=config.tomtom.api_key_env,
            timeout_seconds=config.tomtom.timeout_seconds,
        )
        self.tomtom_flow_adapter = TomTomFlowAdapter(
            **common,
            api_key_env=config.tomtom.api_key_env,
            timeout_seconds=config.tomtom.timeout_seconds,
            probes=tuple(
                FlowProbeSpec(probe.probe_id, probe.label, probe.latitude, probe.longitude)
                for probe in config.tomtom.flow_probes
            ),
        )
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._on_terminal_failure = on_terminal_failure
        self._liveness = WorkerLiveness("traffic-awareness")

    def _ensure_entities(self) -> None:
        labels = {
            DRIVENC_EVENTS_ENTITY_ID: "DriveNC Traffic Events",
            WZDX_ENTITY_ID: "DriveNC WZDx Work Zones",
            CMPD_ENTITY_ID: "CMPD Traffic CAD",
            CHARLOTTE_CLOSURES_ENTITY_ID: "Charlotte Street Closures",
            TOMTOM_INCIDENTS_ENTITY_ID: "TomTom Traffic Incidents",
            TOMTOM_FLOW_ENTITY_ID: "TomTom Flow Probes",
            CAMERAS_ENTITY_ID: "DriveNC Traffic Cameras",
            SIGNS_ENTITY_ID: "DriveNC Message Signs",
            SITUATION_ENTITY_ID: "Local Traffic Situation",
        }
        for entity_id, label in labels.items():
            self.context.world.ensure_entity(entity_id, label)

    def _withdraw(self, entity_id: str, adapter_id: str, reason: str) -> None:
        ingest_observation_batch(
            self.context,
            entity_id=entity_id,
            adapter_id=adapter_id,
            observations=(Observation.unavailable("reentry", reason),),
            publish_cycle=False,
        )

    def prepare_reentry(self) -> None:
        if not self.config.enabled:
            return
        self._ensure_entities()
        if self.config.drivenc.enabled:
            self._withdraw(DRIVENC_EVENTS_ENTITY_ID, self.drivenc_events_adapter.ADAPTER_ID, "awaiting fresh DriveNC traffic-event observation")
            self._withdraw(CAMERAS_ENTITY_ID, self.cameras_adapter.ADAPTER_ID, "awaiting fresh DriveNC camera observation")
            self._withdraw(SIGNS_ENTITY_ID, self.signs_adapter.ADAPTER_ID, "awaiting fresh DriveNC message-sign observation")
        if self.config.wzdx.enabled:
            self._withdraw(WZDX_ENTITY_ID, self.wzdx_adapter.ADAPTER_ID, "awaiting fresh DriveNC WZDx observation")
        if self.config.cmpd.enabled:
            self._withdraw(CMPD_ENTITY_ID, self.cmpd_adapter.ADAPTER_ID, "awaiting fresh CMPD traffic-CAD observation")
        if self.config.charlotte_closures.enabled:
            self._withdraw(CHARLOTTE_CLOSURES_ENTITY_ID, self.charlotte_adapter.ADAPTER_ID, "awaiting fresh Charlotte street-closure observation")
        if self.config.tomtom.enabled:
            self._withdraw(TOMTOM_INCIDENTS_ENTITY_ID, self.tomtom_incidents_adapter.ADAPTER_ID, "awaiting fresh TomTom incident observation")
            self._withdraw(TOMTOM_FLOW_ENTITY_ID, self.tomtom_flow_adapter.ADAPTER_ID, "awaiting fresh TomTom flow observation")
        self._withdraw(SITUATION_ENTITY_ID, "traffic.fusion", "awaiting fresh traffic collection source")

    def runtime_status(self) -> WorkerRuntimeStatus:
        """Return a read-only liveness snapshot for presentation/inspection."""
        return self._liveness.snapshot()

    def supervision_status(self) -> WorkerRuntimeStatus:
        """Return liveness while converting silent thread death into failure."""
        thread = self._thread
        status = self._liveness.snapshot()
        if (
            thread is not None
            and not thread.is_alive()
            and status.lifecycle
            not in (WorkerLifecycle.FAILED, WorkerLifecycle.STOPPED, WorkerLifecycle.STOPPING)
        ):
            status = self._liveness.mark_failed(
                "worker thread exited without a terminal liveness transition"
            )
        return status

    def _notify_failure(self, status: WorkerRuntimeStatus) -> None:
        callback = self._on_terminal_failure
        if callback is not None:
            callback(status)

    def _run_guarded(self) -> None:
        self._liveness.mark_running()
        try:
            self._run()
        except Exception as exc:
            # Do not persist or project arbitrary provider exception text: request
            # failures can contain credentials or source-native sensitive details.
            status = self._liveness.mark_failed(
                f"terminal worker exception: {type(exc).__name__}"
            )
            self._notify_failure(status)
            return

        if self._stop.is_set():
            self._liveness.mark_stopped()
            return

        status = self._liveness.mark_failed(
            "worker loop returned without a stop request"
        )
        self._notify_failure(status)

    def start(self) -> None:
        if not self.config.enabled or self._thread is not None:
            return
        self._ensure_entities()
        self._liveness.mark_starting()
        self._thread = threading.Thread(
            target=self._run_guarded,
            name="personal-cic-traffic-awareness",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> bool:
        """Request bounded shutdown and report whether the worker actually stopped.

        TomTom incident collection may perform several bounded requests in one
        collection pass. The join budget therefore cannot be treated as proof of
        thread termination. A still-live worker remains explicitly represented.
        """
        self._liveness.mark_stopping()
        self._stop.set()
        thread = self._thread
        if thread is None:
            return True
        timeout = max(
            self.config.drivenc.timeout_seconds,
            self.config.wzdx.timeout_seconds,
            self.config.cmpd.timeout_seconds,
            self.config.charlotte_closures.timeout_seconds,
            self.config.tomtom.timeout_seconds,
        ) + 4.0
        thread.join(timeout=timeout)
        stopped = not thread.is_alive()
        if stopped:
            self._thread = None
            self._liveness.mark_stopped()
        return stopped

    def _source(self, entity_id: str, component_type: type):
        state = self.context.world.get_component(entity_id, component_type)
        observation = self.context.world.get_component(entity_id, ObservationState)
        return state, observation

    def _recompute_situation(self) -> None:
        event_sources = []
        configured = []
        source_specs = (
            (self.config.drivenc.enabled, DRIVENC_EVENTS_ENTITY_ID, "DriveNC events"),
            (self.config.wzdx.enabled, WZDX_ENTITY_ID, "DriveNC WZDx"),
            (self.config.cmpd.enabled, CMPD_ENTITY_ID, "CMPD traffic CAD"),
            (self.config.charlotte_closures.enabled, CHARLOTTE_CLOSURES_ENTITY_ID, "Charlotte street closures"),
            (self.config.tomtom.enabled, TOMTOM_INCIDENTS_ENTITY_ID, "TomTom incidents"),
        )
        for enabled, entity_id, label in source_specs:
            if not enabled:
                continue
            state, obs = self._source(entity_id, TrafficEventCollectionState)
            if state is not None and obs is not None:
                event_sources.append((state, obs))
            if obs is None or obs.availability is ObservationAvailability.UNAVAILABLE:
                configured.append(f"configured source unavailable: {label}")

        cameras, cameras_obs = self._source(CAMERAS_ENTITY_ID, TrafficCameraCollectionState)
        signs, signs_obs = self._source(SIGNS_ENTITY_ID, TrafficMessageSignCollectionState)
        flow, flow_obs = self._source(TOMTOM_FLOW_ENTITY_ID, TrafficFlowCollectionState)
        if self.config.drivenc.enabled:
            if cameras_obs is None or cameras_obs.availability is ObservationAvailability.UNAVAILABLE:
                configured.append("configured source unavailable: DriveNC cameras")
            if signs_obs is None or signs_obs.availability is ObservationAvailability.UNAVAILABLE:
                configured.append("configured source unavailable: DriveNC message signs")
        if self.config.tomtom.enabled and (flow_obs is None or flow_obs.availability is ObservationAvailability.UNAVAILABLE):
            configured.append("configured source unavailable: TomTom flow")

        situation = derive_traffic_situation(
            location_label=self.location_label,
            center_latitude=self.latitude,
            center_longitude=self.longitude,
            radius_miles=self.config.radius_miles,
            event_sources=tuple(event_sources),
            cameras=cameras,
            cameras_observation=cameras_obs,
            signs=signs,
            signs_observation=signs_obs,
            flow=flow,
            flow_observation=flow_obs,
            configured_unavailable=tuple(configured),
            external_waze_visual_enabled=self.config.external_waze_visual_enabled,
            external_waze_zoom=self.config.external_waze_zoom,
        )
        if situation is None:
            observations = (
                Observation.unavailable(
                    "traffic.fusion",
                    "no current traffic collection source available",
                ),
            )
        elif configured or any(obs.availability is ObservationAvailability.DEGRADED for _, obs in event_sources) or (
            cameras_obs is not None and cameras_obs.availability is ObservationAvailability.DEGRADED
        ) or (
            signs_obs is not None and signs_obs.availability is ObservationAvailability.DEGRADED
        ) or (
            flow_obs is not None and flow_obs.availability is ObservationAvailability.DEGRADED
        ):
            observations = (
                Observation.partial(
                    "traffic.fusion",
                    situation,
                    "traffic picture is usable but one or more configured collection sources are degraded or unavailable",
                ),
            )
        else:
            observations = (Observation.observed("traffic.fusion", situation),)

        ingest_observation_batch(
            self.context,
            entity_id=SITUATION_ENTITY_ID,
            adapter_id="traffic.fusion",
            observations=observations,
            publish_cycle=False,
        )

    def _collect(self, *, entity_id: str, adapter) -> None:
        ingest_observation_batch(
            self.context,
            entity_id=entity_id,
            adapter_id=adapter.ADAPTER_ID,
            observations=adapter.collect(),
            publish_cycle=False,
        )
        self._recompute_situation()

    def _run(self) -> None:
        next_due = {
            "events": 0.0,
            "signs": 0.0,
            "cameras": 0.0,
            "cmpd": 0.0,
            "wzdx": 0.0,
            "charlotte": 0.0,
            "tomtom_incidents": 0.0,
            "tomtom_flow": 0.0,
        }
        intervals = {
            "events": self.config.drivenc.events_interval_seconds,
            "signs": self.config.drivenc.signs_interval_seconds,
            "cameras": self.config.drivenc.cameras_interval_seconds,
            "cmpd": self.config.cmpd.interval_seconds,
            "wzdx": self.config.wzdx.interval_seconds,
            "charlotte": self.config.charlotte_closures.interval_seconds,
            "tomtom_incidents": self.config.tomtom.incidents_interval_seconds,
            "tomtom_flow": self.config.tomtom.flow_interval_seconds,
        }
        enabled = {
            "events": self.config.drivenc.enabled,
            "signs": self.config.drivenc.enabled,
            "cameras": self.config.drivenc.enabled,
            "cmpd": self.config.cmpd.enabled,
            "wzdx": self.config.wzdx.enabled,
            "charlotte": self.config.charlotte_closures.enabled,
            "tomtom_incidents": self.config.tomtom.enabled,
            "tomtom_flow": self.config.tomtom.enabled,
        }
        collectors = {
            "events": (DRIVENC_EVENTS_ENTITY_ID, self.drivenc_events_adapter),
            "signs": (SIGNS_ENTITY_ID, self.signs_adapter),
            "cameras": (CAMERAS_ENTITY_ID, self.cameras_adapter),
            "cmpd": (CMPD_ENTITY_ID, self.cmpd_adapter),
            "wzdx": (WZDX_ENTITY_ID, self.wzdx_adapter),
            "charlotte": (CHARLOTTE_CLOSURES_ENTITY_ID, self.charlotte_adapter),
            "tomtom_incidents": (TOMTOM_INCIDENTS_ENTITY_ID, self.tomtom_incidents_adapter),
            "tomtom_flow": (TOMTOM_FLOW_ENTITY_ID, self.tomtom_flow_adapter),
        }
        # Fast-changing event/sign/CAD state is attempted first; slower work-zone
        # and municipal context follows. All remain independently observable.
        order = (
            "events", "signs", "cmpd", "tomtom_flow", "cameras",
            "wzdx", "charlotte", "tomtom_incidents",
        )

        while not self._stop.is_set():
            self._liveness.mark_cycle_started()
            now = time.monotonic()
            for name in order:
                if not enabled[name] or now < next_due[name]:
                    continue
                entity_id, adapter = collectors[name]
                self._collect(entity_id=entity_id, adapter=adapter)
                next_due[name] = time.monotonic() + intervals[name]
                if self._stop.is_set():
                    break
                now = time.monotonic()

            self._liveness.mark_cycle_completed()
            due = [next_due[name] for name in order if enabled[name]]
            wait_for = 1.0 if not due else max(0.1, min(due) - time.monotonic())
            self._stop.wait(min(wait_for, 1.0))
