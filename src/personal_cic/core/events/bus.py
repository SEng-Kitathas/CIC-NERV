from collections import defaultdict
from threading import Lock
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
        self._lock = Lock()
        self.published_count = 0

    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None:
        with self._lock:
            self._subscribers[event_type].append(handler)

    def observe_all(self, observer: Callable[[Any], None]) -> None:
        with self._lock:
            self._observers.append(observer)

    # Compatibility alias retained for Slice 002 callers/tests.
    def subscribe_all(self, handler: Callable[[Any], None]) -> None:
        self.observe_all(handler)

    def publish(self, event: T) -> None:
        # Protect registry snapshots and the count, but never hold the lock while
        # invoking callbacks. Handlers may touch WorldState and may recursively
        # publish; holding a bus lock across callbacks would create a lock-order
        # hazard with the world's own RLock.
        with self._lock:
            self.published_count += 1
            observers = tuple(self._observers)
            handlers = tuple(self._subscribers.get(type(event), ()))

        # First preserve/observe this cause. Unrelated events from other threads
        # may interleave, but this event's derived effects cannot precede its own
        # observer path.
        for observer in observers:
            observer(event)

        # Then allow systems to derive consequences, which may recursively publish.
        for handler in handlers:
            handler(event)
