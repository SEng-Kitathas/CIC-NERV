from __future__ import annotations

import json
from pathlib import Path
import time

from .config import ProjectProfile
from .model import AuditReport, GateResult, to_jsonable


def build_report(project_root: Path, profile_path: Path, profile: ProjectProfile, gates: list[GateResult]) -> AuditReport:
    remediation = tuple(
        finding.remediation
        for gate in gates
        for finding in gate.findings
        if finding.blocking
    )
    final_clean = all(gate.clean for gate in gates if gate.gate_id != 'recursive_remediation')
    return AuditReport(
        format='personal-cic.csc-audit.v1',
        created_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        project_root=str(project_root.resolve()),
        profile_path=str(profile_path.resolve()),
        authority_mode=profile.authority_mode,
        final_clean=final_clean,
        veto_authority='NONE',
        gates=tuple(gates),
        remediation=remediation,
    )


def write_report(report: AuditReport, output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / 'CIC_CSC_AUDIT_REPORT.json'
    path.write_text(json.dumps(to_jsonable(report), indent=2) + '\n', encoding='utf-8')
    return path
