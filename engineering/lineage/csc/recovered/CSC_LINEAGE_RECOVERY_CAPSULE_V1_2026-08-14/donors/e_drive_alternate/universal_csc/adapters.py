"""Generic gate adapters for commands, reports, and declared sidecars."""

from __future__ import annotations

import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, cast

from .config import CommandGateSpec, ProjectProfile, ReportGateSpec, SidecarSpec
from .json_io import read_json
from .model import Finding, GateResult, Status


def command_adapter_gates(project_root: Path, profile: ProjectProfile) -> list[GateResult]:
    return [_command_gate(project_root, spec) for spec in profile.command_gates]


def report_adapter_gates(project_root: Path, profile: ProjectProfile) -> list[GateResult]:
    return [_report_gate(project_root, spec) for spec in profile.report_gates]


def sidecar_adapter_gates(profile: ProjectProfile) -> list[GateResult]:
    return [_sidecar_gate(spec) for spec in profile.sidecars]


def _command_gate(project_root: Path, spec: CommandGateSpec) -> GateResult:
    if not spec.command:
        return _adapter_result(
            spec.id, "fail", [_finding(spec.id, "missing command", "declare command argv")]
        )
    proc = _run_command(project_root, spec)
    clean = proc.returncode in spec.clean_exit_codes
    findings = [] if clean else [_finding(spec.id, _tail(proc), "remediate command gate")]
    return _adapter_result(
        spec.id, "pass" if clean else "fail", findings, _proc_evidence(proc, spec)
    )


def _run_command(project_root: Path, spec: CommandGateSpec) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        _expanded_command(spec.command),
        cwd=(project_root / spec.cwd).resolve(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=900,
    )


def _expanded_command(command: tuple[str, ...]) -> list[str]:
    return [sys.executable if item == "{python}" else item for item in command]


def _tail(proc: subprocess.CompletedProcess[bytes]) -> str:
    out = proc.stdout.decode("utf-8", "replace")[-1200:]
    err = proc.stderr.decode("utf-8", "replace")[-1200:]
    return (out + err).strip() or f"return code {proc.returncode}"


def _proc_evidence(
    proc: subprocess.CompletedProcess[bytes], spec: CommandGateSpec
) -> dict[str, Any]:
    return {"command": list(spec.command), "returncode": proc.returncode, "required": spec.required}


def _report_gate(project_root: Path, spec: ReportGateSpec) -> GateResult:
    report = read_json(project_root / spec.path)
    if report is None:
        return _missing_report_gate(spec)
    clean = _field_value(report, spec.clean_field) is spec.expected
    findings = _report_findings(project_root, spec, clean)
    return _adapter_result(
        spec.id,
        "pass" if not findings else "fail",
        findings,
        {"path": spec.path, "required": spec.required, "inputs": list(spec.inputs)},
    )


def _report_findings(project_root: Path, spec: ReportGateSpec, clean: bool) -> list[Finding]:
    findings: list[Finding] = []
    if not clean:
        findings.append(
            _finding(spec.id, f"{spec.clean_field} != {spec.expected}", "remediate report gate")
        )
    if _report_stale(project_root, spec):
        findings.append(
            _finding(spec.id, "report older than declared inputs", "rerun stale report gate")
        )
    return findings


def _report_stale(project_root: Path, spec: ReportGateSpec) -> bool:
    report_path = project_root / spec.path
    if not spec.inputs or not report_path.exists():
        return False
    try:
        report_mtime = report_path.stat().st_mtime
    except OSError:
        return True
    for rel in spec.inputs:
        input_path = project_root / rel
        if input_path.exists() and _newer_than(input_path, report_mtime):
            return True
    return False


def _newer_than(path: Path, timestamp: float) -> bool:
    if path.is_file():
        return path.stat().st_mtime > timestamp
    if not path.is_dir():
        return False
    return any(child.is_file() and child.stat().st_mtime > timestamp for child in path.rglob("*"))


def _field_value(report: dict[str, Any], dotted: str) -> object:
    value: object = report
    for part in dotted.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _missing_report_gate(spec: ReportGateSpec) -> GateResult:
    status = "fail" if spec.required else "not_applicable"
    findings = [_finding(spec.id, "report missing", "run/report gate")] if spec.required else []
    return _adapter_result(
        spec.id, status, findings, {"path": spec.path, "required": spec.required}
    )


def _sidecar_gate(spec: SidecarSpec) -> GateResult:
    if not spec.required and spec.manual_start:
        return _adapter_result(
            spec.id, "not_applicable", [], {"health_url": spec.health_url, "manual_start": True}
        )
    ok, evidence = _probe_url(spec.health_url)
    findings = [] if ok else [_finding(spec.id, evidence, "start/remediate sidecar")]
    return _adapter_result(
        spec.id,
        "pass" if ok else "fail",
        findings,
        {"health_url": spec.health_url, "evidence": evidence},
    )


def _probe_url(url: str) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _adapter_result(
    gate_id: str, status: str, findings: list[Finding], evidence: dict[str, Any] | None = None
) -> GateResult:
    return GateResult(
        gate_id,
        "external_adapter",
        cast(Status, status),
        True,
        "micro",
        "VERIFY",
        "external adapter gate",
        tuple(findings),
        evidence or {},
    )


def _finding(gate_id: str, evidence: str, remediation: str) -> Finding:
    return Finding(
        f"{gate_id}_adapter_failure",
        "HIGH",
        True,
        "external_adapter",
        "micro",
        "VERIFY",
        gate_id,
        evidence,
        remediation,
    )
