from argparse import ArgumentParser
from pathlib import Path

from personal_cic.adapters.linux.host import LinuxHostAdapter
from personal_cic.adapters.tenda.u11_pro import TendaU11ProAdapter
from personal_cic.core.events import ComponentUpdated, EventBus
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import CICNode, LinuxHost, RFObserver, USBDevice, WiFiRadio
from personal_cic.holons.systems.health import HealthSystem
from personal_cic.ui.main.console import render


ENGAGE_ID = "engage-one"
TENDA_ID = "tenda-u11-pro"


def build_world() -> tuple[WorldState, EventBus]:
    events = EventBus()
    world = WorldState(events)
    health = HealthSystem(world)
    events.subscribe(ComponentUpdated, health.on_component_updated)

    world.ensure_entity(ENGAGE_ID, "HP Engage One Model 145")
    world.ensure_entity(TENDA_ID, "Tenda U11 Pro")

    for component in (CICNode(), LinuxHost()):
        world.upsert_component(ENGAGE_ID, component)

    for component in (USBDevice(), WiFiRadio(), RFObserver()):
        world.upsert_component(TENDA_ID, component)

    for component in LinuxHostAdapter().collect():
        world.upsert_component(ENGAGE_ID, component)

    for component in TendaU11ProAdapter().collect():
        world.upsert_component(TENDA_ID, component)

    return world, events


def main() -> None:
    parser = ArgumentParser(description="Personal CIC self-awareness vertical slice")
    parser.add_argument("--state", default="state/world.json", help="durable world-state snapshot path")
    args = parser.parse_args()

    world, events = build_world()
    world.write_json(Path(args.state))
    render(world, events.published_count)


if __name__ == "__main__":
    main()
