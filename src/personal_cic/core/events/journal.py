from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
import json
from threading import Lock
from typing import Any

from .model import ComponentUpdated, ObservationCycleCompleted


class EventJournal:
    """Append-only JSONL journal of operationally meaningful typed CIC events."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = Lock()

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        if is_dataclass(value):
            return {
                key: EventJournal._jsonable(item)
                for key, item in asdict(value).items()
            }
        if isinstance(value, dict):
            return {
                str(key): EventJournal._jsonable(item)
                for key, item in value.items()
            }
        if isinstance(value, (tuple, list)):
            return [EventJournal._jsonable(item) for item in value]
        return value

    def record(self, event: Any) -> None:
        # Samples still flow through the internal event bus so systems can react,
        # but durable history is reserved for semantic operational changes.
        if isinstance(event, ComponentUpdated) and event.significance == "sample":
            return
        if isinstance(event, ObservationCycleCompleted):
            return

        record = {
            "event_type": type(event).__name__,
            "payload": self._jsonable(event),
        }
        line = json.dumps(record, separators=(",", ":")) + "\n"
        # Remote-awareness and local collection run on separate threads. Serialize
        # each durable append so one JSONL record remains one atomic journal line.
        with self._write_lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line)
