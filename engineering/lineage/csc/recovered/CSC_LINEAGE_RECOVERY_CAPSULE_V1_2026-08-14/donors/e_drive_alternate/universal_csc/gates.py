"""Universal CSC/PDVER gates."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from .adapters import command_adapter_gates, report_adapter_gates, sidecar_adapter_gates
from .config import load_profile
from .discovery import TEXT_SUFFIXES
from .doctrine import build_doctrine_coverage
from .json_io import read_json
from .model import Finding, GateResult, Level, PdverPhase, Severity

MAX_FUNCTION_LINES = 35
MAX_FUNCTION_ARGS = 5
PY_LIMIT = 400


@dataclass(frozen=True)
class FindingDraft:
    rule: str
    severity: Severity
    family: str
    level: Level
    phase: PdverPhase
    source: str
    evidence: str
    remediation: str
    blocking: bool = True


@dataclass(frozen=True)
class GateDraft:
    gate_id: str
    family: str
    level: Level
    phase: PdverPhase
    summary: str
    blocking: bool = True
    evidence: Mapping[str, Any] = field(default_factory=dict)


def _finding(draft: FindingDraft) -> Finding:
    return Finding(
        draft.rule,
        draft.severity,
        draft.blocking,
        draft.family,
        draft.level,
        draft.phase,
        draft.source,
        draft.evidence,
        draft.remediation,
    )


def _gate(draft: GateDraft, findings: Sequence[Finding]) -> GateResult:
    status = "fail" if any(item.blocking for item in findings) else "pass"
    return GateResult(
        draft.gate_id,
        draft.family,
        status,
        draft.blocking,
        draft.level,
        draft.phase,
        draft.summary,
        tuple(findings),
        dict(draft.evidence),
    )


def _fail(rule: str, source: Path | str, evidence: str, remediation: str) -> Finding:
    return _finding(
        FindingDraft(rule, "HIGH", "layout", "meso", "VERIFY", str(source), evidence, remediation)
    )


def _records(discovery: Mapping[str, object]) -> list[Mapping[str, object]]:
    records = discovery.get("files", [])
    return (
        [item for item in records if isinstance(item, Mapping)] if isinstance(records, list) else []
    )


def _records_by_class(
    discovery: Mapping[str, object], classes: set[str]
) -> list[Mapping[str, object]]:
    return [record for record in _records(discovery) if record.get("classification") in classes]


def _rel_path(project_root: Path, record: Mapping[str, object]) -> Path:
    return project_root / str(record.get("rel", ""))


def _text_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _json_report_clean(project_root: Path, rel_path: str) -> bool | None:
    report = read_json(project_root / rel_path)
    if report is None:
        return None
    return bool(report.get("clean"))


def project_contract(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    findings = _contract_findings(project_root, discovery)
    evidence = {
        "active_roots": discovery.get("active_roots"),
        "doctrine_roots": discovery.get("doctrine_roots"),
        "evidence_roots": discovery.get("evidence_roots"),
    }
    return _gate(
        GateDraft(
            "project_contract",
            "layout_canonical_root",
            "macro",
            "DERIVE",
            "canonical project contract checked",
            evidence=evidence,
        ),
        findings,
    )


def _contract_findings(project_root: Path, discovery: Mapping[str, object]) -> list[Finding]:
    findings: list[Finding] = []
    if not project_root.exists():
        findings.append(
            _fail("missing_project_root", project_root, "root does not exist", "select valid root")
        )
    if not discovery.get("active_roots"):
        findings.append(
            _fail(
                "missing_active_roots",
                project_root,
                "no active roots found",
                "declare active roots",
            )
        )
    for name in ("reports", "data"):
        if not (project_root / name).exists():
            findings.append(
                _fail(
                    f"missing_{name}_root",
                    project_root / name,
                    "required root missing",
                    f"create {name}/",
                )
            )
    return findings


def active_source_inventory(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    active = _records_by_class(discovery, {"active_source", "launcher"})
    findings = (
        []
        if active
        else [_fail("empty_active_inventory", project_root, "no active files", "add active source")]
    )
    evidence = {"active_file_count": len(active), "total_file_count": discovery.get("file_count")}
    return _gate(
        GateDraft(
            "active_source_inventory",
            "source_inventory",
            "meso",
            "PROBE",
            "active files inventoried",
            evidence=evidence,
        ),
        findings,
    )


def doctrine_surface(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    docs = _records_by_class(discovery, {"doctrine"})
    hits = [record for record in docs if _doctrine_like(str(record.get("rel", "")))]
    findings = _doctrine_findings(project_root, docs, hits)
    evidence = {"docs_count": len(docs), "doctrine_like_count": len(hits)}
    return _gate(
        GateDraft(
            "doctrine_surface",
            "doctrine_sop",
            "meso",
            "DERIVE",
            "doctrine/spec surfaces checked",
            evidence=evidence,
        ),
        findings,
    )


def doctrine_coverage(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    roots = [str(item) for item in discovery.get("doctrine_roots", [])]
    report = build_doctrine_coverage(project_root, roots)
    findings = _doctrine_coverage_findings(project_root, report)
    return _gate(_doctrine_coverage_draft(report), findings)


def _doctrine_coverage_findings(project_root: Path, report: Mapping[str, object]) -> list[Finding]:
    if report.get("clean"):
        return []
    return [
        _finding(
            FindingDraft(
                "doctrine_coverage_missing",
                "HIGH",
                "doctrine",
                "meso",
                "VERIFY",
                str(project_root / "reports" / "UNIVERSAL_CSC_DOCTRINE_COVERAGE.json"),
                "no mapped doctrine requirement clauses",
                "add doctrine clauses or declare doctrine coverage profile",
            )
        )
    ]


def _doctrine_coverage_draft(report: Mapping[str, object]) -> GateDraft:
    return GateDraft(
        "doctrine_coverage",
        "doctrine_sop",
        "meso",
        "VERIFY",
        "doctrine requirement coverage mapped",
        evidence=_doctrine_coverage_evidence(report),
    )


def _doctrine_coverage_evidence(report: Mapping[str, object]) -> dict[str, object]:
    return {
        "report": "reports/UNIVERSAL_CSC_DOCTRINE_COVERAGE.json",
        "doctrine_file_count": report.get("doctrine_file_count"),
        "requirement_clause_count": report.get("requirement_clause_count"),
        "family_counts": report.get("family_counts"),
    }


def _doctrine_like(path: str) -> bool:
    return bool(re.search(r"doctrine|sop|protocol|shall|style|quality|spec|finalizer", path, re.I))


def _doctrine_findings(
    project_root: Path, docs: list[Mapping[str, object]], hits: list[Mapping[str, object]]
) -> list[Finding]:
    if not docs:
        return [
            _fail(
                "missing_docs_or_spec",
                project_root,
                "no docs/spec surfaces",
                "add doctrine/spec docs",
            )
        ]
    if not hits:
        return [
            _fail(
                "unmapped_doctrine",
                project_root / "docs",
                "docs exist but no doctrine naming",
                "declare doctrine docs",
            )
        ]
    return []


def _python_files(project_root: Path, discovery: Mapping[str, object]) -> list[Path]:
    return [
        _rel_path(project_root, rec)
        for rec in _records_by_class(discovery, {"active_source"})
        if rec.get("suffix") == ".py"
    ]


def _parse_python(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return None


def _function_length(node: ast.AST) -> int:
    end = getattr(node, "end_lineno", getattr(node, "lineno", 0)) or getattr(node, "lineno", 0)
    return end - getattr(node, "lineno", end) + 1


def _function_metrics(path: Path) -> list[dict[str, object]]:
    tree = _parse_python(path)
    if tree is None:
        return []
    return [
        _metric(path, node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _metric(path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, object]:
    return {
        "file": str(path),
        "function": node.name,
        "line": node.lineno,
        "length": _function_length(node),
        "args": len(node.args.args),
    }


def _shape_findings(metrics: Sequence[Mapping[str, object]]) -> list[Finding]:
    findings: list[Finding] = []
    for metric in metrics:
        findings.extend(_length_finding(metric))
        findings.extend(_args_finding(metric))
    return findings


def _length_finding(metric: Mapping[str, object]) -> list[Finding]:
    length = int(metric.get("length") or 0)
    if length <= MAX_FUNCTION_LINES:
        return []
    return [
        _shape_failure(
            "function_too_long",
            metric,
            f"{metric.get('function')} is {length} lines",
            "split function",
        )
    ]


def _args_finding(metric: Mapping[str, object]) -> list[Finding]:
    count = int(metric.get("args") or 0)
    if count <= MAX_FUNCTION_ARGS:
        return []
    return [
        _shape_failure(
            "too_many_parameters",
            metric,
            f"{metric.get('function')} has {count} args",
            "use typed spec object",
        )
    ]


def _shape_failure(
    rule: str, metric: Mapping[str, object], evidence: str, remediation: str
) -> Finding:
    return _finding(
        FindingDraft(
            rule,
            "HIGH",
            "code_shape",
            "nano",
            "VERIFY",
            str(metric.get("file")),
            evidence,
            remediation,
        )
    )


def code_shape_loc(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    metrics = [
        metric
        for path in _python_files(project_root, discovery)
        for metric in _function_metrics(path)
    ]
    findings = _shape_findings(metrics)
    longest = sorted(metrics, key=lambda item: int(item["length"]), reverse=True)[:20]
    evidence = {"function_count": len(metrics), "longest": longest}
    return _gate(
        GateDraft(
            "code_shape_loc",
            "code_shape_loc",
            "nano",
            "VERIFY",
            "Python code shape checked",
            evidence=evidence,
        ),
        findings,
    )


def style_quality(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    py_files = _python_files(project_root, discovery)[:PY_LIMIT]
    findings = _compile_findings(project_root, py_files)
    evidence = {"python_files_checked": len(py_files)}
    return _gate(
        GateDraft(
            "style_quality",
            "style_quality",
            "micro",
            "VERIFY",
            "style/compile quality checked",
            evidence=evidence,
        ),
        findings,
    )


def _compile_findings(project_root: Path, py_files: Sequence[Path]) -> list[Finding]:
    if not py_files:
        return []
    proc = subprocess.run(
        [sys.executable, "-m", "compileall", *map(str, py_files)],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return []
    return [
        _finding(
            FindingDraft(
                "compileall_failed",
                "BLOCKER",
                "style_quality",
                "micro",
                "VERIFY",
                str(project_root),
                proc.stderr[-1000:] or proc.stdout[-1000:],
                "fix compile errors",
            )
        )
    ]


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _has_shell_true(node: ast.Call) -> bool:
    return any(
        kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
        for kw in node.keywords
    )


def _shell_findings(path: Path) -> list[Finding]:
    tree = _parse_python(path)
    if tree is None:
        return []
    calls = [
        node for node in ast.walk(tree) if isinstance(node, ast.Call) and _has_shell_true(node)
    ]
    return [
        _shell_finding(path, call)
        for call in calls
        if _call_name(call.func) in {"subprocess.run", "subprocess.Popen", "run", "Popen"}
    ]


def _shell_finding(path: Path, call: ast.Call) -> Finding:
    return _finding(
        FindingDraft(
            "shell_passthrough",
            "HIGH",
            "semantic_dataflow",
            "nano",
            "VERIFY",
            str(path),
            f"line {call.lineno}: real shell passthrough",
            "use argv-list execution",
        )
    )


def _bounded_kill(line: str) -> bool:
    lowered = line.lower()
    return any(token in lowered for token in ("pid", "processid", "ngrok", "owningprocess"))


def _script_findings(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for idx, line in enumerate(_text_lines(path), 1):
        if "8787" in line:
            findings.append(
                _script_failure(
                    "hardcoded_old_port", path, idx, "stale port 8787", "use declared config"
                )
            )
        if "Stop-Process" in line and "-Force" in line and not _bounded_kill(line):
            findings.append(
                _script_failure(
                    "broad_force_kill", path, idx, "unbounded force kill", "bound by PID/process"
                )
            )
    return findings


def _script_failure(
    rule: str, path: Path, line_no: int, evidence: str, remediation: str
) -> Finding:
    return _finding(
        FindingDraft(
            rule,
            "HIGH",
            "semantic_dataflow",
            "micro",
            "VERIFY",
            str(path),
            f"line {line_no}: {evidence}",
            remediation,
        )
    )


def semantic_footgun_dataflow(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    paths = [
        _rel_path(project_root, rec)
        for rec in _records_by_class(discovery, {"active_source", "launcher"})
        if _text_record(rec)
    ]
    findings = [finding for path in paths for finding in _semantic_findings(path)]
    return _gate(
        GateDraft(
            "semantic_footgun_dataflow",
            "semantic_dataflow",
            "micro",
            "VERIFY",
            "semantic footgun patterns checked",
        ),
        findings,
    )


def _text_record(record: Mapping[str, object]) -> bool:
    return record.get("suffix") in TEXT_SUFFIXES and int(record.get("bytes") or 0) <= 1_500_000


def _semantic_findings(path: Path) -> list[Finding]:
    return _shell_findings(path) if path.suffix == ".py" else _script_findings(path)


def schema_contract_authority(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    surfaces = [
        record
        for record in _records(discovery)
        if re.search(r"schema|contract|openapi|capabil", str(record.get("rel", "")), re.I)
    ]
    if not surfaces:
        return GateResult(
            "schema_contract_authority",
            "schema_contract",
            "not_applicable",
            True,
            "micro",
            "VERIFY",
            "no schema/contract surfaces discovered",
        )
    evidence = {"count": len(surfaces), "sample": surfaces[:20]}
    return _gate(
        GateDraft(
            "schema_contract_authority",
            "schema_contract",
            "micro",
            "VERIFY",
            "schema/contract surfaces discovered",
            evidence=evidence,
        ),
        [],
    )


def route_runtime_trace(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    report_path = "reports/RECEIVER_FULL_ROUTE_TRACE_GATE_REPORT.json"
    clean = _json_report_clean(project_root, report_path)
    if clean is not None:
        return _route_report_gate(clean, report_path)
    return _route_discovery_gate(project_root, discovery)


def _route_discovery_gate(project_root: Path, discovery: Mapping[str, object]) -> GateResult:
    route_files = _route_like_files(discovery)
    if not route_files:
        return GateResult(
            "route_runtime_trace",
            "route_runtime",
            "not_applicable",
            True,
            "micro",
            "VERIFY",
            "no route/runtime surfaces discovered",
        )
    finding = _missing_route_trace(project_root)
    draft = GateDraft(
        "route_runtime_trace",
        "route_runtime",
        "micro",
        "VERIFY",
        "route/runtime surfaces checked",
        evidence={"route_like_file_count": len(route_files)},
    )
    return _gate(draft, [finding])


def _missing_route_trace(project_root: Path) -> Finding:
    return _finding(
        FindingDraft(
            "missing_route_trace_report",
            "HIGH",
            "route_runtime",
            "micro",
            "VERIFY",
            str(project_root),
            "route-like files without route trace report",
            "add route trace gate",
        )
    )


def _route_report_gate(clean: bool, report_path: str) -> GateResult:
    findings = (
        []
        if clean
        else [
            _finding(
                FindingDraft(
                    "route_trace_not_clean",
                    "HIGH",
                    "route_runtime",
                    "micro",
                    "VERIFY",
                    report_path,
                    "route trace dirty",
                    "rerun/remediate route trace",
                )
            )
        ]
    )
    evidence = {"report": report_path, "clean": clean}
    return _gate(
        GateDraft(
            "route_runtime_trace",
            "route_runtime",
            "micro",
            "VERIFY",
            "project route trace report checked",
            evidence=evidence,
        ),
        findings,
    )


def _route_like_files(discovery: Mapping[str, object]) -> list[Mapping[str, object]]:
    return [
        rec
        for rec in _records_by_class(discovery, {"active_source"})
        if "route" in str(rec.get("rel", "")).lower()
    ]


def process_launcher_runtime(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    launchers = _records_by_class(discovery, {"launcher"})
    findings = [
        finding for rec in launchers for finding in _launcher_findings(_rel_path(project_root, rec))
    ]
    return _gate(
        GateDraft(
            "process_launcher_runtime",
            "process_launcher",
            "micro",
            "VERIFY",
            "launcher/process scripts checked",
            evidence={"launcher_count": len(launchers)},
        ),
        findings,
    )


def _launcher_findings(path: Path) -> list[Finding]:
    text = "\n".join(_text_lines(path))
    findings: list[Finding] = []
    findings.extend(_launcher_secret_findings(path, text))
    findings.extend(_launcher_kill_findings(path, text))
    return findings


def _launcher_secret_findings(path: Path, text: str) -> list[Finding]:
    if "GITHOME_API_KEY=" not in text or "PCMMAD_LOCAL_ENV" in text:
        return []
    return [
        _finding(
            FindingDraft(
                "secret_in_launcher",
                "HIGH",
                "process_launcher",
                "micro",
                "VERIFY",
                str(path),
                "launcher sets API key directly",
                "move secret to local config",
            )
        )
    ]


def _launcher_kill_findings(path: Path, text: str) -> list[Finding]:
    if "Stop-Process" not in text or "-Force" not in text:
        return []
    if re.search(r"pid|processid|ngrok", text, re.I):
        return []
    return [
        _finding(
            FindingDraft(
                "unbounded_force_kill",
                "HIGH",
                "process_launcher",
                "micro",
                "VERIFY",
                str(path),
                "force stop lacks bound",
                "bound process stop",
            )
        )
    ]


def _credential_assignment_line(line: str) -> bool:
    lowered = line.lower()
    return bool(
        re.search(r"(api[_-]?key|token|password|secret|credential)\s*=", lowered)
        and re.search(r"[A-Za-z0-9_\-]{32,}", line)
    )


def security_config(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    records = _records_by_class(discovery, {"active_source", "launcher"})
    findings = [
        finding
        for rec in records
        if _text_record(rec)
        for finding in _credential_findings(_rel_path(project_root, rec))
    ]
    return _gate(
        GateDraft(
            "security_config", "security", "micro", "VERIFY", "secret/config surfaces checked"
        ),
        findings,
    )


def _credential_findings(path: Path) -> list[Finding]:
    findings = []
    for idx, line in enumerate(_text_lines(path), 1):
        if _credential_assignment_line(line):
            evidence = f"line {idx}: credential-like assignment"
            findings.append(
                _finding(
                    FindingDraft(
                        "credential_literal",
                        "HIGH",
                        "security",
                        "micro",
                        "VERIFY",
                        str(path),
                        evidence,
                        "move credential to local config",
                    )
                )
            )
    return findings


def tests_resilience(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    tests = [
        rec
        for rec in _records(discovery)
        if str(rec.get("rel", "")).startswith("tests/") and rec.get("suffix") == ".py"
    ]
    if not tests:
        return GateResult(
            "tests_resilience",
            "tests_resilience",
            "not_applicable",
            True,
            "micro",
            "VERIFY",
            "no Python tests discovered",
        )
    findings = _test_compile_findings(project_root)
    return _gate(
        GateDraft(
            "tests_resilience",
            "tests_resilience",
            "micro",
            "VERIFY",
            "test surfaces checked",
            evidence={"test_file_count": len(tests)},
        ),
        findings,
    )


def _test_compile_findings(project_root: Path) -> list[Finding]:
    proc = subprocess.run(
        [sys.executable, "-m", "compileall", "tests"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return []
    evidence = proc.stderr[-1000:] or proc.stdout[-1000:]
    return [
        _finding(
            FindingDraft(
                "tests_compile_failed",
                "HIGH",
                "tests_resilience",
                "micro",
                "VERIFY",
                str(project_root / "tests"),
                evidence,
                "fix test compile failure",
            )
        )
    ]


def _required_reports(project_root: Path) -> tuple[str, ...]:
    required = ["UNIVERSAL_CSC_DISCOVERY_REPORT.json"]
    if (project_root / "system" / "finalize_task.py").exists():
        required.append("CONSTRAINT_FINALIZER_EXPRESSION_REPORT.json")
    if (project_root / "baseline" / "pcmmad_receiver").exists():
        required.extend(
            [
                "RECEIVER_LAUNCHER_SCRIPT_AUDIT_REPORT.json",
                "RECEIVER_FULL_ROUTE_TRACE_GATE_REPORT.json",
            ]
        )
    return tuple(required)


def report_freshness_lineage(project_root: Path, discovery: dict[str, Any]) -> GateResult:
    required = _required_reports(project_root)
    present = [name for name in required if (project_root / "reports" / name).exists()]
    missing = [name for name in required if name not in present]
    findings = [_missing_report(project_root, name) for name in missing]
    evidence = {"required_reports": required, "present_reports": present}
    return _gate(
        GateDraft(
            "report_freshness_lineage",
            "report_freshness",
            "meso",
            "VERIFY",
            "required report lineage checked",
            evidence=evidence,
        ),
        findings,
    )


def _missing_report(project_root: Path, name: str) -> Finding:
    return _finding(
        FindingDraft(
            "missing_required_report",
            "HIGH",
            "report_freshness",
            "meso",
            "EMBODY",
            str(project_root / "reports" / name),
            f"required report missing: {name}",
            "run corresponding gate/finalizer",
        )
    )


def project_local_finalizer(project_root: Path) -> GateResult:
    finalizer = project_root / "system" / "finalize_task.py"
    if not finalizer.exists():
        return GateResult(
            "project_local_finalizer",
            "claim_governance",
            "not_applicable",
            True,
            "macro",
            "VERIFY",
            "no project-local finalizer discovered",
        )
    proc = _run_finalizer(project_root, finalizer)
    findings = [] if proc.returncode == 0 else [_finalizer_failed(finalizer, proc)]
    evidence = {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }
    return _gate(
        GateDraft(
            "project_local_finalizer",
            "claim_governance",
            "macro",
            "VERIFY",
            "project-local finalizer executed",
            evidence=evidence,
        ),
        findings,
    )


def _run_finalizer(project_root: Path, finalizer: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(finalizer)],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=900,
    )


def _finalizer_failed(finalizer: Path, proc: subprocess.CompletedProcess[str]) -> Finding:
    evidence = proc.stdout[-2000:] + proc.stderr[-2000:]
    return _finding(
        FindingDraft(
            "project_finalizer_failed",
            "BLOCKER",
            "claim_governance",
            "macro",
            "VERIFY",
            str(finalizer),
            evidence,
            "remediate project finalizer",
        )
    )


def claim_governor(gates: list[GateResult]) -> GateResult:
    failing = [gate.gate_id for gate in gates if not gate.clean]
    findings = [_blocked_claims(failing)] if failing else []
    return _gate(
        GateDraft(
            "claim_governor",
            "claim_governance",
            "macro",
            "EMBODY",
            "claim permissions derived",
            evidence={"blocking_gates": failing},
        ),
        findings,
    )


def _blocked_claims(failing: list[str]) -> Finding:
    return _finding(
        FindingDraft(
            "blocked_claims",
            "BLOCKER",
            "claim_governance",
            "macro",
            "EMBODY",
            "universal_claim_governor",
            ", ".join(failing),
            "remediate failing gates and rerun",
        )
    )


def recursive_remediation(gates: list[GateResult]) -> GateResult:
    remediation = [item.remediation for gate in gates for item in gate.findings if item.blocking]
    status = "fail" if remediation else "pass"
    evidence = {"remediation_count": len(remediation), "ordered_remediation": remediation[:80]}
    return GateResult(
        "recursive_remediation",
        "claim_governance",
        cast(Any, status),
        True,
        "macro",
        "RECURSE",
        "recursive remediation plan derived",
        (),
        evidence,
    )


def run_all(project_root: Path, discovery: dict[str, Any]) -> list[GateResult]:
    profile = load_profile(project_root)
    gates = _native_gates(project_root, discovery)
    gates.extend(command_adapter_gates(project_root, profile))
    gates.extend(report_adapter_gates(project_root, profile))
    gates.extend(sidecar_adapter_gates(profile))
    gates.append(claim_governor(gates))
    gates.append(recursive_remediation(gates))
    return gates


def _native_gates(project_root: Path, discovery: dict[str, Any]) -> list[GateResult]:
    return [
        project_contract(project_root, discovery),
        active_source_inventory(project_root, discovery),
        doctrine_surface(project_root, discovery),
        doctrine_coverage(project_root, discovery),
        code_shape_loc(project_root, discovery),
        style_quality(project_root, discovery),
        semantic_footgun_dataflow(project_root, discovery),
        schema_contract_authority(project_root, discovery),
        route_runtime_trace(project_root, discovery),
        process_launcher_runtime(project_root, discovery),
        security_config(project_root, discovery),
        tests_resilience(project_root, discovery),
        report_freshness_lineage(project_root, discovery),
        project_local_finalizer(project_root),
    ]
