from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .config import CommandGateSpec
from .model import Finding, GateResult


def run_command_gate(project_root: Path, spec: CommandGateSpec) -> GateResult:
    if not spec.command:
        return _failed(spec, 'command argv is empty', 'declare an explicit argv')
    command = [sys.executable if item == '{python}' else item for item in spec.command]
    try:
        proc = subprocess.run(
            command,
            cwd=(project_root / spec.cwd).resolve(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=900,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _failed(spec, f'{type(exc).__name__}: {exc}', 'repair command execution')
    clean = proc.returncode in spec.clean_exit_codes
    evidence = {
        'command': list(spec.command),
        'returncode': proc.returncode,
        'required': spec.required,
        'output_tail': proc.stdout[-4000:],
    }
    if clean:
        return GateResult(
            spec.gate_id, 'command_adapter', 'pass', spec.required, 'micro', 'VERIFY',
            'declared verification command passed', (), evidence,
        )
    finding = Finding(
        rule_id=f'{spec.gate_id}_command_failure',
        severity='HIGH',
        confidence='HIGH',
        blocking=spec.required,
        family='command_adapter',
        level='micro',
        pdver_phase='VERIFY',
        source=spec.gate_id,
        evidence=f'return code {proc.returncode}: {proc.stdout[-1200:]}',
        remediation='remediate the underlying verification command and rerun CSC audit',
    )
    return GateResult(
        spec.gate_id, 'command_adapter', 'fail', spec.required, 'micro', 'VERIFY',
        'declared verification command failed', (finding,), evidence,
    )


def _failed(spec: CommandGateSpec, evidence: str, remediation: str) -> GateResult:
    finding = Finding(
        rule_id=f'{spec.gate_id}_adapter_failure', severity='HIGH', confidence='HIGH',
        blocking=spec.required, family='command_adapter', level='micro', pdver_phase='VERIFY',
        source=spec.gate_id, evidence=evidence, remediation=remediation,
    )
    return GateResult(
        spec.gate_id, 'command_adapter', 'fail', spec.required, 'micro', 'VERIFY',
        'declared verification command could not execute', (finding,), {},
    )
