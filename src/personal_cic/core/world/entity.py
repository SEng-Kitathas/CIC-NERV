from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class Entity:
    entity_id: str
    label: str
    components: dict[str, Any] = field(default_factory=dict)

    def set_component(self, component: Any) -> Any:
        key = type(component).__name__
        previous = self.components.get(key)
        self.components[key] = component
        return previous

    def get(self, component_type: type[T]) -> T | None:
        value = self.components.get(component_type.__name__)
        return value if isinstance(value, component_type) else None

    def has(self, *component_types: type) -> bool:
        return all(t.__name__ in self.components for t in component_types)
