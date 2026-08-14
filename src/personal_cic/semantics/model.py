from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class SemanticKind(str, Enum):
    OBSERVATION_STATE = "observation_state"
    ABSENCE = "absence"
    COLLECTION_GAP = "collection_gap"
    MEASUREMENT = "measurement"
    DATA_QUALITY = "data_quality"
    SOURCE_REPORT = "source_report"
    PREDICTION = "prediction"
    INFORMATION_ARTIFACT = "information_artifact"
    TEMPORAL = "temporal"
    EVIDENCE = "evidence"
    STATE_CONDITION = "state_condition"
    IDENTITY_ASSOCIATION = "identity_association"
    FOREIGN_NATIVE = "foreign_native"


class SemanticSourceRole(str, Enum):
    PROVIDER = "provider"
    ADAPTER = "adapter"
    SOURCE_RECORD = "source_record"
    DERIVATION_PROCESS = "derivation_process"
    WORLD_ENTITY_REFERENCE = "world_entity_reference"
    FOREIGN_SEMANTIC_AUTHORITY = "foreign_semantic_authority"


class SemanticAssertionOrigin(str, Enum):
    SOURCE_OBSERVED = "source_observed"
    CIC_DERIVED = "cic_derived"
    FOREIGN_NATIVE_PRESERVED = "foreign_native_preserved"


@dataclass(frozen=True, slots=True)
class SemanticSourceRef:
    ref_id: str
    role: SemanticSourceRole
    authority: str | None = None
    native_id: str | None = None


@dataclass(frozen=True, slots=True)
class SemanticProvenance:
    origin: SemanticAssertionOrigin
    sources: tuple[SemanticSourceRef, ...] = ()
    derivation_ref: str | None = None


@dataclass(frozen=True, slots=True)
class SemanticTemporalContext:
    phenomenon_time: str | None = None
    source_time: str | None = None
    observed_at: str | None = None
    retrieved_at: str | None = None
    derived_at: str | None = None


@dataclass(frozen=True, slots=True)
class SemanticAssertion:
    """Read-only semantic projection; never a second WorldState writer."""
    assertion_id: str
    proposition_key: str
    kind: SemanticKind
    home: str
    subject_ref: str
    predicate: str
    value: Any
    provenance: SemanticProvenance
    temporal: SemanticTemporalContext = field(default_factory=SemanticTemporalContext)
    qualifiers: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    @property
    def source_refs(self) -> tuple[str, ...]:
        """RC1-compatible projection of typed provenance references."""
        return tuple(source.ref_id for source in self.provenance.sources)
