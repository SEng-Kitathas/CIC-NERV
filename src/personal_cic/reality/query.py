from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CoverageStatus(str, Enum):
    GAP = "gap"
    PARTIAL = "partial"
    SATISFIED = "satisfied"
    STRONG = "strong"


class CoverageIndependence(str, Enum):
    UNPROVEN = "unproven"
    PARTIAL = "partial"
    QUALIFIED = "qualified"


@dataclass(frozen=True, slots=True)
class InformationRequirement:
    requirement_id: str
    proposition: str
    target_ref: str
    required_capability_ids: tuple[str, ...]
    geography_ref: str | None = None
    time_horizon: str | None = None
    required_warrant_class: str = "qualified"
    required_currentness: str = "current"

    def __post_init__(self) -> None:
        _require_text(self.requirement_id, "requirement_id")
        _require_text(self.proposition, "proposition")
        _require_text(self.target_ref, "target_ref")
        if not self.required_capability_ids:
            raise ValueError(
                "information requirement must declare at least one capability"
            )


@dataclass(frozen=True, slots=True)
class ObservationCapability:
    capability_id: str
    name: str
    description: str

    def __post_init__(self) -> None:
        _require_text(self.capability_id, "capability_id")
        _require_text(self.name, "name")
        _require_text(self.description, "description")


@dataclass(frozen=True, slots=True)
class CoverageClaim:
    requirement_id: str
    capability_id: str
    status: CoverageStatus
    record_refs: tuple[str, ...] = ()
    qualified_independent_lineage_ids: tuple[str, ...] = ()
    independence: CoverageIndependence = CoverageIndependence.UNPROVEN
    currentness: str = "unknown"
    spatial_resolution: str | None = None
    temporal_resolution: str | None = None
    warrant_class: str = "unqualified"
    confounds: tuple[str, ...] = ()
    blind_spots: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.requirement_id, "requirement_id")
        _require_text(self.capability_id, "capability_id")
        _require_text(self.currentness, "currentness")
        _require_text(self.warrant_class, "warrant_class")
        if (
            self.independence is not CoverageIndependence.QUALIFIED
            and self.qualified_independent_lineage_ids
        ):
            raise ValueError(
                "qualified independent lineage ids require QUALIFIED independence"
            )

    @property
    def record_count(self) -> int:
        return len(self.record_refs)


@dataclass(frozen=True, slots=True)
class CollectionGap:
    gap_id: str
    requirement_id: str
    capability_id: str
    reason: str
    observed_status: CoverageStatus | None = None

    def __post_init__(self) -> None:
        _require_text(self.gap_id, "gap_id")
        _require_text(self.requirement_id, "requirement_id")
        _require_text(self.capability_id, "capability_id")
        _require_text(self.reason, "reason")


def assess_requirement_coverage(
    requirement: InformationRequirement,
    claims: tuple[CoverageClaim, ...],
) -> tuple[CollectionGap, ...]:
    """Find requirement-relative gaps without treating source count as coverage."""
    claims_by_capability: dict[str, list[CoverageClaim]] = {}
    for claim in claims:
        if claim.requirement_id != requirement.requirement_id:
            continue
        claims_by_capability.setdefault(claim.capability_id, []).append(claim)

    gaps: list[CollectionGap] = []
    for capability_id in requirement.required_capability_ids:
        matching = claims_by_capability.get(capability_id, [])
        if not matching:
            gaps.append(
                CollectionGap(
                    gap_id=f"{requirement.requirement_id}:{capability_id}:missing",
                    requirement_id=requirement.requirement_id,
                    capability_id=capability_id,
                    reason=(
                        "no qualified coverage claim exists for required capability"
                    ),
                    observed_status=None,
                )
            )
            continue

        best = max(matching, key=lambda claim: _coverage_rank(claim.status))
        if best.status in {CoverageStatus.GAP, CoverageStatus.PARTIAL}:
            gaps.append(
                CollectionGap(
                    gap_id=f"{requirement.requirement_id}:{capability_id}:insufficient",
                    requirement_id=requirement.requirement_id,
                    capability_id=capability_id,
                    reason=(
                        "available coverage is insufficient for the declared "
                        "information requirement"
                    ),
                    observed_status=best.status,
                )
            )
    return tuple(gaps)


def _coverage_rank(status: CoverageStatus) -> int:
    return {
        CoverageStatus.GAP: 0,
        CoverageStatus.PARTIAL: 1,
        CoverageStatus.SATISFIED: 2,
        CoverageStatus.STRONG: 3,
    }[status]


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
