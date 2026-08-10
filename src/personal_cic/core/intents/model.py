from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Intent:
    """A normalized request to change the world. UI never calls adapters directly."""

    target_entity_id: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    authority: str = "routine"
    intent_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
