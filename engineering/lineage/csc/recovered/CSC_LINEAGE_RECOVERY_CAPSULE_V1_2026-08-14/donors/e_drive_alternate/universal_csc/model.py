"""Data model for the universal CSC/PDVER finalizer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal["pass", "fail", "stale", "missing", "not_applicable"]
Severity = Literal["BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO"]
PdverPhase = Literal["PROBE", "DERIVE", "VERIFY", "EMBODY", "RECURSE"]
Level = Literal["nano", "micro", "meso", "macro"]


@dataclass(frozen=True)
class Finding:
    id: str
    severity: Severity
    blocking: bool
    family: str
    level: Level
    pdver_phase: PdverPhase
    source: str
    evidence: str
    remediation: str


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    family: str
    status: Status
    blocking: bool
    level: Level
    pdver_phase: PdverPhase
    summary: str
    findings: tuple[Finding, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def clean(self) -> bool:
        return self.status in {"pass", "not_applicable"} and not any(
            f.blocking for f in self.findings
        )


@dataclass(frozen=True)
class ClaimPermission:
    claim: str
    status: Literal["allowed", "blocked"]
    required_gates: tuple[str, ...]
    blocking_gates: tuple[str, ...] = ()


def to_jsonable(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    return value
