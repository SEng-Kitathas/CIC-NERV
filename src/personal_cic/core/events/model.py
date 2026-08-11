from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from personal_cic.core.observations import ObservationAvailability


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
class ObservationCycleCompleted:
    """Internal derivation barrier for one adapter collection cycle.

    This event is intentionally a sample-level scheduling fact. The durable journal
    keeps material ComponentUpdated events and derived health changes, not every
    heartbeat boundary.
    """

    entity_id: str
    adapter_id: str
    availability: ObservationAvailability
    significance: Literal["sample"] = "sample"
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True, slots=True)
class RuntimeStarted:
    pid: int
    config_path: str
    restored_entities: int
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True, slots=True)
class RuntimeStopping:
    reason: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=utc_now_iso)
