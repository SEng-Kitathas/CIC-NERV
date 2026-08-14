from __future__ import annotations

from pathlib import Path
from typing import Any

from .adapters import run_command_gate
from .config import ProjectProfile
from .model import Finding, GateResult


def native_gates(project_root: Path, profile: ProjectProfile, discovery: dict[str, Any]) -> list[GateResult]:
    return [
        authority_guard(profile),
        project_contract(project_root, profile, discovery),
        lineage_presence(project_root, profile),
        doctrine_surface(project_root, profile),
    ]


def authority_guard(profile: ProjectProfile) -> GateResult:
    evidence = {'authority_mode': profile.authority_mode, 'veto_authority': 'NONE'}
    return GateResult(
        'authority_guard', 'claim_governance', 'pass', True, 'macro', 'VERIFY',
        'CSC is constrained to audit-only authority', (), evidence,
    )


def project_contract(project_root: Path, profile: ProjectProfile, discovery: dict[str, Any]) -> GateResult:
    findings: list[Finding] = []
    missing = [name for name in profile.source_roots if not (project_root / name).exists()]
    if missing:
        findings.append(_finding(
            'missing_source_roots', 'layout', str(project_root),
            f'missing declared source roots: {missing}', 'repair CIC CSC profile or source layout',
        ))
    status = 'fail' if findings else 'pass'
    return GateResult(
        'project_contract', 'layout', status, True, 'macro', 'DERIVE',
        'CIC project/profile contract checked', tuple(findings), {
            'source_roots_present': discovery.get('source_roots_present', []),
            'doctrine_roots_present': discovery.get('doctrine_roots_present', []),
        },
    )


def lineage_presence(project_root: Path, profile: ProjectProfile) -> GateResult:
    anchor = project_root / profile.lineage_anchor
    if anchor.is_file():
        return GateResult(
            'lineage_presence', 'evidence_lineage', 'pass', True, 'meso', 'VERIFY',
            'recovered CSC lineage anchor is present', (), {'anchor': profile.lineage_anchor},
        )
    finding = _finding(
        'missing_lineage_anchor', 'evidence_lineage', str(anchor),
        'configured CSC lineage anchor is absent', 'restore the sealed CSC lineage foundation',
    )
    return GateResult(
        'lineage_presence', 'evidence_lineage', 'fail', True, 'meso', 'VERIFY',
        'recovered CSC lineage anchor is absent', (finding,), {'anchor': profile.lineage_anchor},
    )


def doctrine_surface(project_root: Path, profile: ProjectProfile) -> GateResult:
    files = [
        path for root in profile.doctrine_roots for path in (project_root / root).rglob('*')
        if path.is_file() and path.suffix.lower() in {'.md', '.txt', '.json', '.yaml', '.yml'}
    ]
    if files:
        return GateResult(
            'doctrine_surface', 'doctrine', 'pass', True, 'meso', 'PROBE',
            'declared CIC doctrine surfaces exist', (), {'doctrine_file_count': len(files)},
        )
    finding = _finding(
        'missing_doctrine_surface', 'doctrine', str(project_root),
        'no declared doctrine files found', 'restore or declare CIC doctrine surfaces',
    )
    return GateResult(
        'doctrine_surface', 'doctrine', 'fail', True, 'meso', 'PROBE',
        'declared CIC doctrine surfaces missing', (finding,), {'doctrine_file_count': 0},
    )


def run_all(project_root: Path, profile: ProjectProfile, discovery: dict[str, Any]) -> list[GateResult]:
    gates = native_gates(project_root, profile, discovery)
    gates.extend(run_command_gate(project_root, spec) for spec in profile.command_gates)
    gates.append(recursive_remediation(gates))
    return gates


def recursive_remediation(gates: list[GateResult]) -> GateResult:
    remediation = [
        finding.remediation
        for gate in gates
        for finding in gate.findings
        if finding.blocking
    ]
    return GateResult(
        'recursive_remediation', 'claim_governance', 'fail' if remediation else 'pass',
        False, 'macro', 'RECURSE', 'ordered remediation derived from blocking findings', (),
        {'remediation_count': len(remediation), 'ordered_remediation': remediation},
    )


def _finding(rule_id: str, family: str, source: str, evidence: str, remediation: str) -> Finding:
    return Finding(
        rule_id=rule_id, severity='HIGH', confidence='HIGH', blocking=True,
        family=family, level='meso', pdver_phase='VERIFY', source=source,
        evidence=evidence, remediation=remediation,
    )
