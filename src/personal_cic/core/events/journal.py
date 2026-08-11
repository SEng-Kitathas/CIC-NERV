from dataclasses import asdict, is_dataclass
from pathlib import Path
import json
from typing import Any

from .model import ComponentUpdated


class EventJournal:
    """Append-only JSONL journal of operationally meaningful typed CIC events."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _jsonable(value: Any) -> Any:
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
        # but the durable event journal is for meaningful operational changes.
        if isinstance(event, ComponentUpdated) and event.significance == "sample":
            return

        record = {
            "event_type": type(event).__name__,
            "payload": self._jsonable(event),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
