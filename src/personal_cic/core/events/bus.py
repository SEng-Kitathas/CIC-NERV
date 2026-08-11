from collections import defaultdict
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class EventBus:
    """Synchronous typed event bus with explicit causal observation ordering.

    Observers see the published cause before typed handlers are allowed to emit
    derived effects. This keeps durable journals causally readable.
    """

    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[Any], None]]] = defaultdict(list)
        self._observers: list[Callable[[Any], None]] = []
        self.published_count = 0

    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None:
        self._subscribers[event_type].append(handler)

    def observe_all(self, observer: Callable[[Any], None]) -> None:
        self._observers.append(observer)

    # Compatibility alias retained for Slice 002 callers/tests.
    def subscribe_all(self, handler: Callable[[Any], None]) -> None:
        self.observe_all(handler)

    def publish(self, event: T) -> None:
        self.published_count += 1

        # First preserve/observe the cause.
        for observer in tuple(self._observers):
            observer(event)

        # Then allow systems to derive consequences, which may recursively publish.
        for handler in tuple(self._subscribers.get(type(event), ())):
            handler(event)
