from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class SemanticKind(str, Enum):
    OBSERVATION_STATE = "observation_state"
    ABSENCE = "absence"
    COLLECTION_GAP = "collection_gap"
    MEASUREMENT = "measurement"
    IDENTITY_ASSOCIATION = "identity_association"
    FOREIGN_NATIVE = "foreign_native"

@dataclass(frozen=True, slots=True)
class SemanticAssertion:
    """Read-only semantic projection; never a second WorldState writer."""
    assertion_id: str
    kind: SemanticKind
    home: str
    subject_ref: str
    predicate: str
    value: Any
    source_refs: tuple[str, ...] = ()
    qualifiers: dict[str, Any] = field(default_factory=dict)
