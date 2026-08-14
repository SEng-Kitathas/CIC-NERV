from __future__ import annotations

from dataclasses import dataclass

from .evidence import Statement


@dataclass(frozen=True, slots=True)
class ProtectedSourceRef:
    """Opaque analytical reference, not an ordinary WorldState identity."""

    protected_ref: str
    compartment: str | None = None

    def __post_init__(self) -> None:
        if not self.protected_ref.strip():
            raise ValueError("protected_ref must be a non-empty string")


@dataclass(frozen=True, slots=True)
class HumanReport:
    report_id: str
    protected_source: ProtectedSourceRef
    source_record_ref: str
    statements: tuple[Statement, ...]
    handling_policy_id: str | None = None

    def __post_init__(self) -> None:
        if not self.report_id.strip():
            raise ValueError("report_id must be a non-empty string")
        if not self.source_record_ref.strip():
            raise ValueError("source_record_ref must be a non-empty string")
        if not self.statements:
            raise ValueError("human report must contain at least one statement")
        for statement in self.statements:
            if statement.source_record_ref != self.source_record_ref:
                raise ValueError(
                    "statement source_record_ref must match the report source record"
                )

    @property
    def world_mutation_authority(self) -> str:
        return "NONE"
