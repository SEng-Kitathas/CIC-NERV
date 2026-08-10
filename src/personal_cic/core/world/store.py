from dataclasses import asdict, is_dataclass
from pathlib import Path
import json
from typing import Any

from personal_cic.core.events import ComponentUpdated, EventBus
from .entity import Entity


class WorldState:
    def __init__(self, events: EventBus) -> None:
        self.events = events
        self.entities: dict[str, Entity] = {}

    def ensure_entity(self, entity_id: str, label: str) -> Entity:
        entity = self.entities.get(entity_id)
        if entity is None:
            entity = Entity(entity_id=entity_id, label=label)
            self.entities[entity_id] = entity
        return entity

    def upsert_component(self, entity_id: str, component: Any) -> bool:
        entity = self.entities[entity_id]
        previous = entity.components.get(type(component).__name__)
        if previous == component:
            return False

        entity.set_component(component)
        self.events.publish(
            ComponentUpdated(
                entity_id=entity_id,
                component_name=type(component).__name__,
                previous=previous,
                current=component,
            )
        )
        return True

    def query(self, *component_types: type) -> list[Entity]:
        return [entity for entity in self.entities.values() if entity.has(*component_types)]

    @staticmethod
    def _component_json(component: Any) -> Any:
        if is_dataclass(component):
            return asdict(component)
        return repr(component)

    def snapshot(self) -> dict[str, Any]:
        return {
            "entities": {
                entity_id: {
                    "label": entity.label,
                    "components": {
                        name: self._component_json(component)
                        for name, component in sorted(entity.components.items())
                    },
                }
                for entity_id, entity in sorted(self.entities.items())
            }
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
