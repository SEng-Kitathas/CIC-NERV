from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class ComponentUpdated:
    entity_id: str
    component_name: str
    previous: Any
    current: Any
    significance: Literal["material", "sample"] = "material"
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True, slots=True)
class RuntimeStarted:
    pid: int
    config_path: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True, slots=True)
class RuntimeStopping:
    reason: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=utc_now_iso)
