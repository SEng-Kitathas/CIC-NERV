from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StatementBasis(str, Enum):
    DIRECT_OBSERVATION = "direct_observation"
    SECONDHAND_REPORT = "secondhand_report"
    THIRD_PARTY_ATTRIBUTION = "third_party_attribution"
    INFERENCE = "inference"
    BELIEF = "belief"
    EXPECTATION = "expectation"
    INTENTION = "intention"


class EvidenceRelationKind(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXTUALIZES = "contextualizes"
    REPORTS = "reports"
    OBSERVES = "observes"
    DERIVED_FROM = "derived_from"


@dataclass(frozen=True, slots=True)
class Statement:
    statement_id: str
    proposition: str
    basis: StatementBasis
    source_record_ref: str
    subject_ref: str | None = None
    phenomenon_time: str | None = None
    claimed_location_ref: str | None = None
    source_claimed_confidence: str | float | int | None = None
    attribution_chain: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.statement_id, "statement_id")
        _require_text(self.proposition, "proposition")
        _require_text(self.source_record_ref, "source_record_ref")


@dataclass(frozen=True, slots=True)
class EvidenceRelation:
    relation_id: str
    evidence_ref: str
    proposition_ref: str
    kind: EvidenceRelationKind
    basis: str
    warrant_class: str = "unqualified"

    def __post_init__(self) -> None:
        _require_text(self.relation_id, "relation_id")
        _require_text(self.evidence_ref, "evidence_ref")
        _require_text(self.proposition_ref, "proposition_ref")
        _require_text(self.basis, "basis")
        _require_text(self.warrant_class, "warrant_class")

    @property
    def world_mutation_authority(self) -> str:
        return "NONE"


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
