from dataclasses import asdict, is_dataclass
from pathlib import Path
import json
from threading import RLock
from typing import Any, Literal

from personal_cic.core.events import ComponentUpdated, EventBus
from .codec import decode_component, encode_value
from .entity import Entity


class WorldState:
    # Current writer remains v2 because deployed target evidence shows v2 on disk.
    # Historical hydration tests require v1 and a radar-era v3 fixture. Until the
    # lineage is deliberately normalized, read those explicitly and reject unknown
    # future versions rather than silently interpreting them as today's schema.
    SCHEMA_VERSION = 2
    READABLE_SCHEMA_VERSIONS = frozenset({1, 2, 3})

    def __init__(self, events: EventBus) -> None:
        self.events = events
        self.entities: dict[str, Entity] = {}
        self._lock = RLock()

    def ensure_entity(self, entity_id: str, label: str) -> Entity:
        with self._lock:
            entity = self.entities.get(entity_id)
            if entity is None:
                entity = Entity(entity_id=entity_id, label=label)
                self.entities[entity_id] = entity
            else:
                entity.label = label
            return entity

    def upsert_component(
        self,
        entity_id: str,
        component: Any,
        *,
        significance: Literal["material", "sample"] = "material",
    ) -> bool:
        with self._lock:
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
                    significance=significance,
                )
            )
            return True

    def get_component(self, entity_id: str, component_type: type):
        with self._lock:
            entity = self.entities.get(entity_id)
            return None if entity is None else entity.get(component_type)

    def query(self, *component_types: type) -> list[Entity]:
        with self._lock:
            return [
                entity
                for entity in self.entities.values()
                if entity.has(*component_types)
            ]

    @staticmethod
    def _component_json(component: Any) -> Any:
        if is_dataclass(component):
            return {key: encode_value(value) for key, value in asdict(component).items()}
        return repr(component)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "schema_version": self.SCHEMA_VERSION,
                "entities": {
                    entity_id: {
                        "label": entity.label,
                        "components": {
                            name: self._component_json(component)
                            for name, component in sorted(entity.components.items())
                        },
                    }
                    for entity_id, entity in sorted(self.entities.items())
                },
            }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

    def hydrate_json(self, path: Path) -> int:
        """Restore the last embodied world without emitting synthetic events.

        Unknown future component types are ignored rather than preventing startup.
        Returns the number of restored entities.
        """
        if not path.exists():
            return 0

        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("world snapshot root must be a JSON object")
        version = data.get("schema_version")
        if isinstance(version, bool) or not isinstance(version, int):
            raise ValueError("world snapshot schema_version must be an integer")
        if version not in self.READABLE_SCHEMA_VERSIONS:
            raise ValueError(
                f"unsupported world snapshot schema_version {version}; "
                f"readable versions are {sorted(self.READABLE_SCHEMA_VERSIONS)}"
            )
        entities = data.get("entities")
        if not isinstance(entities, dict):
            raise ValueError("world snapshot entities must be a JSON object")

        with self._lock:
            restored = 0
            for entity_id, entity_data in entities.items():
                if not isinstance(entity_id, str) or not isinstance(entity_data, dict):
                    raise ValueError("world snapshot entity records must be keyed JSON objects")
                components = entity_data.get("components", {})
                if not isinstance(components, dict):
                    raise ValueError(f"world snapshot components for {entity_id!r} must be a JSON object")
                label = entity_data.get("label", entity_id)
                if not isinstance(label, str):
                    raise ValueError(f"world snapshot label for {entity_id!r} must be a string")
                entity = self.ensure_entity(entity_id, label)
                for name, payload in components.items():
                    if not isinstance(name, str):
                        raise ValueError(f"world snapshot component name for {entity_id!r} must be a string")
                    if not isinstance(payload, dict):
                        # Preserve the historical tolerance for unknown/non-object
                        # component payloads; they cannot be safely reconstructed.
                        continue
                    component = decode_component(name, payload)
                    if component is not None:
                        entity.set_component(component)
                restored += 1
            return restored
