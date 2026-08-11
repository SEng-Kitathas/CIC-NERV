from dataclasses import dataclass
from pathlib import Path

from personal_cic.adapters.linux.host import LinuxHostAdapter
from personal_cic.adapters.tenda.u11_pro import TendaU11ProAdapter
from personal_cic.core.config import HealthThresholds
from personal_cic.core.events import ComponentUpdated, EventBus
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    CICNode,
    LinuxHost,
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


def create_context(
    *,
    events: EventBus | None = None,
    health_config_path: Path = Path("config/health.json"),
) -> RuntimeContext:
    event_bus = events or EventBus()
    world = WorldState(event_bus)
    thresholds = HealthThresholds.load(health_config_path)
    health = HealthSystem(world, thresholds)
    event_bus.subscribe(ComponentUpdated, health.on_component_updated)

    world.ensure_entity(ENGAGE_ID, "HP Engage One Model 145")
    world.ensure_entity(TENDA_ID, "Tenda U11 Pro")

    for component in (CICNode(), LinuxHost()):
        world.upsert_component(ENGAGE_ID, component)

    for component in (USBDevice(), WiFiRadio(), RFObserver()):
        world.upsert_component(TENDA_ID, component)

    return RuntimeContext(
        events=event_bus,
        world=world,
        host_adapter=LinuxHostAdapter(),
        tenda_adapter=TendaU11ProAdapter(),
        thresholds=thresholds,
    )


def _observe(context: RuntimeContext, entity_id: str, component: object) -> None:
    entity = context.world.entities[entity_id]
    previous = entity.components.get(type(component).__name__)
    significance = telemetry_significance(previous, component, context.thresholds)
    context.world.upsert_component(
        entity_id,
        component,
        significance=significance,
    )


def collect_once(context: RuntimeContext) -> None:
    for component in context.host_adapter.collect():
        _observe(context, ENGAGE_ID, component)

    for component in context.tenda_adapter.collect():
        _observe(context, TENDA_ID, component)
