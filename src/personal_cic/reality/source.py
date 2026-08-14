from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class SourceAgentKind(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    DEVICE = "device"
    SYSTEM = "system"
    DATASET = "dataset"
    UNKNOWN = "unknown"


class InformationOrigin(str, Enum):
    HUMAN_AUTHORED = "human_authored"
    SENSOR_MEASURED = "sensor_measured"
    INSTITUTIONAL_RECORD = "institutional_record"
    COMPUTATIONAL_MODEL = "computational_model"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class AcquisitionRegime(str, Enum):
    PUBLICLY_ACCESSIBLE = "publicly_accessible"
    DIRECT_OPERATOR = "direct_operator"
    PARTNER_PROVIDED = "partner_provided"
    COMMERCIAL_LICENSED = "commercial_licensed"
    LOCAL_SENSOR = "local_sensor"
    INTERNAL_SYSTEM = "internal_system"
    UNKNOWN = "unknown"


class ObservationModality(str, Enum):
    REPORTED_VISUAL_OBSERVATION = "reported_visual_observation"
    DIRECT_SENSOR_MEASUREMENT = "direct_sensor_measurement"
    DOCUMENT_RECORD = "document_record"
    IMAGERY = "imagery"
    TELEMETRY = "telemetry"
    MODEL_OUTPUT = "model_output"
    PUBLIC_STATEMENT = "public_statement"
    UNKNOWN = "unknown"


class PublicationMedium(str, Enum):
    PUBLIC_SOCIAL_PLATFORM = "public_social_platform"
    PUBLIC_WEB = "public_web"
    OFFICIAL_API = "official_api"
    DOCUMENT = "document"
    DIRECT_REPORT = "direct_report"
    SENSOR_CHANNEL = "sensor_channel"
    INTERNAL_SYSTEM = "internal_system"
    UNKNOWN = "unknown"


class LineageRelationKind(str, Enum):
    KNOWN_COMMON_ORIGIN = "known_common_origin"
    PROBABLE_COMMON_ORIGIN = "probable_common_origin"
    POSSIBLE_COMMON_ORIGIN = "possible_common_origin"
    INDEPENDENCE_UNPROVEN = "independence_unproven"
    QUALIFIED_INDEPENDENT = "qualified_independent"


@dataclass(frozen=True, slots=True)
class SourceAgent:
    agent_ref: str
    kind: SourceAgentKind
    display_label: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.agent_ref, "agent_ref")


@dataclass(frozen=True, slots=True)
class SourceLineage:
    lineage_id: str
    source_agent_ref: str | None = None
    native_lineage_ref: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.lineage_id, "lineage_id")


@dataclass(frozen=True, slots=True)
class LineageRelation:
    left_lineage_id: str
    right_lineage_id: str
    relation: LineageRelationKind
    basis: str
    confidence: float | None = None
    as_of: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.left_lineage_id, "left_lineage_id")
        _require_text(self.right_lineage_id, "right_lineage_id")
        _require_text(self.basis, "basis")
        if self.left_lineage_id == self.right_lineage_id:
            raise ValueError("lineage relation endpoints must be distinct")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("lineage relation confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class HandlingPolicy:
    policy_id: str
    pseudonymize_source: bool = False
    retention_class: str | None = None
    access_scope: tuple[str, ...] = ()
    consent_basis: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.policy_id, "policy_id")


@dataclass(frozen=True, slots=True)
class SourceRecord:
    record_id: str
    source_agent_ref: str | None
    information_origin: InformationOrigin
    acquisition_regime: AcquisitionRegime
    observation_modality: ObservationModality
    publication_medium: PublicationMedium
    lineage_id: str
    provider_record_id: str | None = None
    native_semantic_type: str | None = None
    phenomenon_time: str | None = None
    observation_time: str | None = None
    publication_time: str | None = None
    retrieval_attempt_time: str | None = None
    successful_retrieval_time: str | None = None
    native_geometry_ref: str | None = None
    native_units: str | None = None
    native_confidence: str | float | int | None = None
    native_status: str | None = None
    transformation_chain: tuple[str, ...] = ()
    raw_reference: str | None = None
    raw_digest_sha256: str | None = None
    handling_policy_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.record_id, "record_id")
        _require_text(self.lineage_id, "lineage_id")
        if self.raw_digest_sha256 is not None and not re.fullmatch(
            r"[0-9a-fA-F]{64}", self.raw_digest_sha256
        ):
            raise ValueError("raw_digest_sha256 must be a 64-character hex digest")


def known_common_origin_components(
    lineage_ids: tuple[str, ...],
    relations: tuple[LineageRelation, ...],
) -> tuple[frozenset[str], ...]:
    """Group only lineages whose common origin is explicitly known.

    Separate components are not thereby asserted independent.
    """
    unique = tuple(dict.fromkeys(lineage_ids))
    parent = {lineage_id: lineage_id for lineage_id in unique}

    def find(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for relation in relations:
        if relation.relation is not LineageRelationKind.KNOWN_COMMON_ORIGIN:
            continue
        if relation.left_lineage_id in parent and relation.right_lineage_id in parent:
            union(relation.left_lineage_id, relation.right_lineage_id)

    groups: dict[str, set[str]] = {}
    for lineage_id in unique:
        groups.setdefault(find(lineage_id), set()).add(lineage_id)

    return tuple(
        sorted(
            (frozenset(group) for group in groups.values()),
            key=lambda group: tuple(sorted(group)),
        )
    )


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
