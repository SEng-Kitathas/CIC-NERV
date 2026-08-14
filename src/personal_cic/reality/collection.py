from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AcquisitionAttemptStatus(str, Enum):
    NOT_STARTED = "not_started"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ObservationOpportunity:
    opportunity_id: str
    gap_ref: str
    required_capability_id: str
    candidate_source_ref: str
    geography_ref: str | None = None
    temporal_window: str | None = None
    expected_resolution: str | None = None
    expected_independence: str = "unproven"
    expected_information_gain: float | None = None
    acquisition_cost_class: str | None = None
    policy_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.opportunity_id, "opportunity_id")
        _require_text(self.gap_ref, "gap_ref")
        _require_text(self.required_capability_id, "required_capability_id")
        _require_text(self.candidate_source_ref, "candidate_source_ref")
        if self.expected_information_gain is not None:
            if not 0.0 <= self.expected_information_gain <= 1.0:
                raise ValueError(
                    "expected_information_gain must be between 0 and 1"
                )

    @property
    def target_phenomenon_evidence_authority(self) -> str:
        return "NONE"


@dataclass(frozen=True, slots=True)
class AcquisitionTask:
    task_id: str
    opportunity_ref: str
    authorized_by: str
    created_at: str

    def __post_init__(self) -> None:
        _require_text(self.task_id, "task_id")
        _require_text(self.opportunity_ref, "opportunity_ref")
        _require_text(self.authorized_by, "authorized_by")
        _require_text(self.created_at, "created_at")

    @property
    def target_phenomenon_evidence_authority(self) -> str:
        return "NONE"


@dataclass(frozen=True, slots=True)
class AcquisitionAttempt:
    attempt_id: str
    task_ref: str
    status: AcquisitionAttemptStatus
    attempted_at: str
    completed_at: str | None = None
    result_source_record_refs: tuple[str, ...] = ()
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.attempt_id, "attempt_id")
        _require_text(self.task_ref, "task_ref")
        _require_text(self.attempted_at, "attempted_at")
        if self.status is AcquisitionAttemptStatus.FAILED and not self.failure_reason:
            raise ValueError("failed acquisition attempt requires failure_reason")

    @property
    def target_phenomenon_evidence_authority(self) -> str:
        return "NONE"


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
