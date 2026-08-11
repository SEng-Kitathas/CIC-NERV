from dataclasses import dataclass
from pathlib import Path

from personal_cic.adapters.linux.host import LinuxHostAdapter
from personal_cic.adapters.tenda.u11_pro import TendaU11ProAdapter
from personal_cic.core.config import HealthThresholds
from personal_cic.core.events import EventBus, ObservationCycleCompleted, utc_now_iso
from personal_cic.core.observations import Observation, ObservationAvailability, ObservationStatus
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    CICNode,
    LinuxHost,
    ObservationState,
    RFObserver,
    USBDevice,
    WiFiRadio,
)
from personal_cic.holons.systems.health import HealthSystem
from personal_cic.holons.systems.materiality import telemetry_significance


ENGAGE_ID = "engage-one"
TENDA_ID = "tenda-u11-pro"


@dataclass(slots=True)
class RuntimeContext:
    events: EventBus
    world: WorldState
    host_adapter: LinuxHostAdapter
    tenda_adapter: TendaU11ProAdapter
    thresholds: HealthThresholds
    restored_entities: int = 0


def create_context(
    *,
    events: EventBus | None = None,
    health_config_path: Path = Path("config/health.json"),
    restore_state_path: Path | None = None,
) -> RuntimeContext:
    event_bus = events or EventBus()
    world = WorldState(event_bus)
    restored_entities = 0
    if restore_state_path is not None:
        restored_entities = world.hydrate_json(restore_state_path)

    thresholds = HealthThresholds.load(health_config_path)
    health = HealthSystem(world, thresholds)
    event_bus.subscribe(
        ObservationCycleCompleted,
        health.on_observation_cycle_completed,
    )

    return RuntimeContext(
        events=event_bus,
        world=world,
        host_adapter=LinuxHostAdapter(),
        tenda_adapter=TendaU11ProAdapter(),
        thresholds=thresholds,
        restored_entities=restored_entities,
    )


def reconcile_topology(context: RuntimeContext) -> None:
    context.world.ensure_entity(ENGAGE_ID, "HP Engage One Model 145")
    context.world.ensure_entity(TENDA_ID, "Tenda U11 Pro")

    for component in (CICNode(), LinuxHost()):
        context.world.upsert_component(ENGAGE_ID, component)

    for component in (USBDevice(), WiFiRadio(), RFObserver()):
        context.world.upsert_component(TENDA_ID, component)


def _observe(context: RuntimeContext, entity_id: str, component: object) -> str:
    entity = context.world.entities[entity_id]
    previous = entity.components.get(type(component).__name__)
    significance = telemetry_significance(previous, component, context.thresholds)
    context.world.upsert_component(
        entity_id,
        component,
        significance=significance,
    )
    return significance


def _ingest_observation_batch(
    context: RuntimeContext,
    *,
    entity_id: str,
    adapter_id: str,
    observations: tuple[Observation[object], ...],
) -> None:
    checked_at = utc_now_iso()
    previous_state = context.world.entities[entity_id].get(ObservationState)

    reasons = tuple(
        f"{observation.source}: {observation.detail}"
        for observation in observations
        if observation.detail
    )
    unavailable_count = sum(
        observation.status is ObservationStatus.UNAVAILABLE
        for observation in observations
    )
    partial = any(
        observation.status is ObservationStatus.PARTIAL
        for observation in observations
    )

    if observations and unavailable_count == len(observations):
        availability = ObservationAvailability.UNAVAILABLE
    elif unavailable_count or partial:
        availability = ObservationAvailability.DEGRADED
    else:
        availability = ObservationAvailability.CURRENT

    successful = any(
        observation.status in (ObservationStatus.OBSERVED, ObservationStatus.PARTIAL)
        for observation in observations
    )
    last_success_at = (
        checked_at
        if successful
        else previous_state.last_success_at if previous_state is not None else None
    )

    for observation in observations:
        # Critical invariant: inability to observe is not evidence of a domain value.
        if observation.value is not None:
            _observe(context, entity_id, observation.value)

    observation_state = ObservationState(
        adapter_id=adapter_id,
        availability=availability,
        checked_at=checked_at,
        last_success_at=last_success_at,
        reasons=reasons,
    )
    _observe(context, entity_id, observation_state)

    context.events.publish(
        ObservationCycleCompleted(
            entity_id=entity_id,
            adapter_id=adapter_id,
            availability=availability,
        )
    )


def collect_once(context: RuntimeContext) -> None:
    _ingest_observation_batch(
        context,
        entity_id=ENGAGE_ID,
        adapter_id=context.host_adapter.ADAPTER_ID,
        observations=context.host_adapter.collect(),
    )
    _ingest_observation_batch(
        context,
        entity_id=TENDA_ID,
        adapter_id=context.tenda_adapter.ADAPTER_ID,
        observations=context.tenda_adapter.collect(),
    )
