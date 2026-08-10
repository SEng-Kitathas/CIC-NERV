from collections import defaultdict
from typing import Callable, TypeVar, Any

T = TypeVar("T")


class EventBus:
    """Synchronous typed event bus for the initial local runtime."""

    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[Any], None]]] = defaultdict(list)
        self.published_count = 0

    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: T) -> None:
        self.published_count += 1
        for handler in tuple(self._subscribers.get(type(event), ())):
            handler(event)
