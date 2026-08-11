from collections import defaultdict
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class EventBus:
    """Synchronous typed event bus for the local runtime."""

    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[Any], None]]] = defaultdict(list)
        self._all_subscribers: list[Callable[[Any], None]] = []
        self.published_count = 0

    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None:
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[Any], None]) -> None:
        self._all_subscribers.append(handler)

    def publish(self, event: T) -> None:
        self.published_count += 1
        for handler in tuple(self._subscribers.get(type(event), ())):
            handler(event)
        for handler in tuple(self._all_subscribers):
            handler(event)
