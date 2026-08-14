from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal['pass', 'fail', 'not_applicable']
Severity = Literal['BLOCKER', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
Confidence = Literal['HIGH', 'MEDIUM', 'LOW']
PdverPhase = Literal['PROBE', 'DERIVE', 'VERIFY', 'EMBODY', 'RECURSE']
Level = Literal['nano', 'micro', 'meso', 'macro']
AuthorityMode = Literal['audit_only']


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    confidence: Confidence
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
        return self.status in {'pass', 'not_applicable'} and not any(
            finding.blocking for finding in self.findings
        )


@dataclass(frozen=True)
class AuditReport:
    format: str
    created_at_utc: str
    project_root: str
    profile_path: str
    authority_mode: AuthorityMode
    final_clean: bool
    veto_authority: Literal['NONE']
    gates: tuple[GateResult, ...]
    remediation: tuple[str, ...]


def to_jsonable(value: object) -> object:
    if hasattr(value, '__dataclass_fields__'):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value
