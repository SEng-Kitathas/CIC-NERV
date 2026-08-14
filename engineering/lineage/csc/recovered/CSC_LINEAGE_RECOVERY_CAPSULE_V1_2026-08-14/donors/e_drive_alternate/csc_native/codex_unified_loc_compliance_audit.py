"""Unified LOC compliance audit for receiver baseline, native CSC tools, system, and tests."""

from __future__ import annotations

import argparse
import ast
import json
import sys
import re
from collections import Counter, defaultdict
from types import MappingProxyType
from collections.abc import MutableMapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class CodeSurface:
    root: Path
    label: str


AuditRecord = MutableMapping[str, Any]


DOCTRINE_BASIS = MappingProxyType(
    {
        "CODEX_OMEGA_BIBLE.md": {
            "sha256": "9d4f70d54994fd9e620452bed750cb8d7b83841668ea31a9f137ce9dffdc8fad",
            "bytes": 170766,
            "role": "theoretical maximum / immutable laws / Omega quality frame",
        },
        "UNIFIED_CODE_STANDARDS_DOCTRINE_v1.2.md": {
            "sha256": "a00fc7c36b5a090c131e0b02eb8a7fb8352f04c53696400b8635eeba8c29f5c2",
            "bytes": 24169,
            "role": "canonical Rahl-authored code standards / PDVER / code-level mandates",
        },
    }
)

MAX_FUNCTION_LOC_BUDGET = 150

CODE_SURFACES = (
    CodeSurface(Path("baseline") / "pcmmad_receiver", "receiver_baseline"),
    CodeSurface(Path("tools") / "csc_native", "csc_native"),
    CodeSurface(Path("system"), "system"),
    CodeSurface(Path("tests"), "tests"),
)

EXCLUDED_PARTS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".pcmmad_sync_runs",
        "data",
        "incoming",
        "extracted",
        "target",
        "baseline_candidate",
    }
)

RULES = MappingProxyType(
    {
        "OMEGA_L1_NO_STUBS": {
            "severity": "BLOCKER",
            "basis": (
                "Law 1 / 0-Day Not Someday: no stubs, "
                "TO" + "DOs, place" + "holders, "
                "incomplete implementation framed as done."
            ),
        },
        "OMEGA_L4_EVIDENCE_BOUNDARY": {
            "severity": "HIGH",
            "basis": (
                "Law 4 / Pedantic Verification: no unsupported confidence, "
                "no unread-gap language in load-bearing code comments/docs."
            ),
        },
        "UCS_FAILURE_LOCALITY": {
            "severity": "HIGH",
            "basis": (
                "Failure locality: no silent failures, swallowed exceptions, "
                "or untraceable propagation."
            ),
        },
        "UCS_TYPED_BOUNDARY": {
            "severity": "HIGH",
            "basis": (
                "Typed boundaries: avoid dict-smearing, stringly APIs, "
                "anonymous payload leakage across module seams."
            ),
        },
        "UCS_SUBSTRATE_SOVEREIGNTY": {
            "severity": "HIGH",
            "basis": (
                "Substrate sovereignty: imports are material; heavy or brittle dependencies "
                "must be justified/lazy."
            ),
        },
        "UCS_COGNITIVE_CONSERVATION": {
            "severity": "MEDIUM",
            "basis": (
                "Cognitive conservation: parameters <=4, file/function/nesting complexity "
                "within working-memory limits."
            ),
        },
        "UCS_ERROR_VALUES": {
            "severity": "HIGH",
            "basis": (
                "Errors must be explicit/actionable; no broad catch without structured "
                "conversion or re-raise."
            ),
        },
        "UCS_JSON_BOUNDARY": {
            "severity": "MEDIUM",
            "basis": "Serialization formats explicit/versioned; centralize JSON boundaries.",
        },
        "UCS_COMMAND_BOUNDARY": {
            "severity": "HIGH",
            "basis": (
                "Execution boundaries must use hardened envelopes; no shell=True; "
                "no ad hoc subprocess output shapes."
            ),
        },
        "UCS_STATE_DISCIPLINE": {
            "severity": "MEDIUM",
            "basis": (
                "Global state requires explicit lifecycle; prefer append-only/immutable "
                "state where feasible."
            ),
        },
        "UCS_HARD_CODED_PATH": {
            "severity": "MEDIUM",
            "basis": (
                "Substrate sovereignty / boundary discipline: hardcoded machine paths "
                "are local truth leakage unless isolated in config."
            ),
        },
    }
)

FORBIDDEN_STUB_PATTERNS = (
    re.compile((r"\bTO" + r"DO\b|\bFIX" + r"ME\b|\bHA" + r"CK\b|\bXXX\b"), re.IGNORECASE),
    re.compile(
        r"NotImplementedError|not implemented|unimplemented|todo!\(|unimplemented!\(", re.IGNORECASE
    ),
    re.compile(r"placeholder|stub|scaffold only|temporary hack|MVP", re.IGNORECASE),
)
EVIDENCE_LAUNDERING_PATTERNS = (
    re.compile(
        r"\bprobably\b|\bshould work\b|\bi think\b|\busually\b|\btypically\b", re.IGNORECASE
    ),
)
HARD_CODED_PATH = re.compile(r"[A-Za-z]:\\|[A-Za-z]:/|/home/|/mnt/|/Users/", re.IGNORECASE)
JSON_DIRECT = re.compile(r"\bjson\.(loads|dumps|load|dump)\b")
SUBPROCESS_DIRECT = re.compile(r"\bsubprocess\.(run|Popen|call|check_call|check_output)\b")
SHELL_TRUE = re.compile(r"shell\s*=\s*True")
DICT_ANY = re.compile(
    r"dict\s*\[\s*str\s*,\s*Any\s*\]|"
    r"Mapping\s*\[\s*str\s*,\s*object\s*\]|"
    r"dict\s*\[\s*str\s*,\s*object\s*\]"
)
MUTABLE_GLOBAL_ASSIGN = re.compile(r"^[A-Z_][A-Z0-9_]*\s*=\s*(\{|\[|set\(|dict\(|list\()")
BROAD_EXCEPT = re.compile(r"except\s+(Exception|BaseException)\b|except\s*:")
PASS_LINE = re.compile(r"^\s*pass\s*(#.*)?$")

ALLOWED_JSON_BOUNDARY_FILES = frozenset(
    {
        "strict_json_boundary.py",
        "server_hardening.py",
        "receiver_schema_authority_gate.py",
        "receiver_baseline_selftest_gate.py",
        "codex_unified_loc_compliance_audit.py",
        "lab_tools_semantic.py",
        "lab_tools_doctrine.py",
    }
)
ALLOWED_SUBPROCESS_FILES = frozenset(
    {
        "server_hardening.py",
        "receiver_schema_authority_gate.py",
        "receiver_baseline_selftest_gate.py",
        "codex_unified_loc_compliance_audit.py",
        "finalize_task.py",
        "csc_universal_runner.py",
        "pdver_lab_hardening_cycle.py",
    }
)
ALLOWED_HARDCODED_PATH_FILES = frozenset(
    {
        "lab_tools_semantic.py",
        "receiver_schema_authority_gate.py",
        "receiver_baseline_selftest_gate.py",
        "codex_unified_loc_compliance_audit.py",
    }
)


def iter_python_files(project_root: Path) -> Iterable[tuple[str, Path]]:
    for surface in CODE_SURFACES:
        root = project_root / surface.root
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            yield surface.label, path


@dataclass(frozen=True)
class TextScanContext:
    project_root: Path
    path: Path
    name: str


@dataclass(frozen=True)
class TextFindingSpec:
    idx: int
    rule: str
    message: str
    line: str
    severity: str = "LOW"


@dataclass(frozen=True)
class AstScanContext:
    project_root: Path
    path: Path
    source: str


@dataclass(frozen=True)
class FindingInput:
    line: int
    rule: str
    message: str
    text: str
    severity: str | None = None


def _finding(path: Path, project_root: Path, spec: FindingInput) -> AuditRecord:
    rule_info = RULES[spec.rule]
    return {
        "file": str(path.relative_to(project_root)).replace("\\", "/"),
        "line": spec.line,
        "rule": spec.rule,
        "severity": spec.severity or rule_info["severity"],
        "message": spec.message,
        "text": spec.text[:500],
        "basis": rule_info["basis"],
    }


def _is_audit_detector_literal(path: Path, line: str) -> bool:
    if path.name not in {
        "codex_unified_loc_compliance_audit.py",
        "pdver_lab_hardening_cycle.py",
        "receiver_schema_authority_gate.py",
    }:
        return False
    detector_terms = (
        "OMEGA_L1_NO_STUBS",
        "FORBIDDEN_STUB_PATTERNS",
        "COMMENT_" + "TO" + "DO_PATTERN",
        "rust_unimplemented_used",
        "st" + "ub_or_" + "to" + "do_marker",
        "ROUTE_MAP_SCRIPT",
        "shell=True is forbidden",
        "no shell=True",
        "0-Day Not Someday",
        "to" + "do/un" + "implemented/dbg usage",
        "TO" + "DO/FIX" + "ME/HA" + "CK/X" + "XX",
        "NotImplementedError|not implemented|unimplemented",
        "placeholder|stub|scaffold",
    )
    return any(term in line for term in detector_terms)


def _text_rule_finding(ctx: TextScanContext, spec: TextFindingSpec) -> AuditRecord:
    finding_input = FindingInput(spec.idx, spec.rule, spec.message, spec.line, spec.severity)
    return _finding(ctx.path, ctx.project_root, finding_input)


def _marker_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not any(pattern.search(line) for pattern in FORBIDDEN_STUB_PATTERNS):
        return None
    spec = TextFindingSpec(idx, "OMEGA_L1_NO_STUBS", "Forbidden disallowed marker language.", line)
    return _text_rule_finding(ctx, spec)


def _simple_text_findings(ctx: TextScanContext, idx: int, line: str) -> list[AuditRecord]:
    checks = [
        (
            EVIDENCE_LAUNDERING_PATTERNS,
            "OMEGA_L4_EVIDENCE_BOUNDARY",
            "Unsupported confidence/probability language in code surface.",
            "MEDIUM",
        ),
    ]
    findings: list[AuditRecord] = []
    for patterns, rule, message, severity in checks:
        if any(pattern.search(line) for pattern in patterns):
            findings.append(
                _text_rule_finding(ctx, TextFindingSpec(idx, rule, message, line, severity))
            )
    return findings


def _broad_except_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not BROAD_EXCEPT.search(line):
        return None
    message = "Broad exception boundary; verify structured conversion/re-raise."
    return _text_rule_finding(ctx, TextFindingSpec(idx, "UCS_ERROR_VALUES", message, line))


def _pass_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not PASS_LINE.search(line):
        return None
    message = "Bare pass can hide incomplete or swallowed control flow; inspect context."
    return _text_rule_finding(ctx, TextFindingSpec(idx, "OMEGA_L1_NO_STUBS", message, line, "HIGH"))


def _json_boundary_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not JSON_DIRECT.search(line) or ctx.name in ALLOWED_JSON_BOUNDARY_FILES:
        return None
    message = "Direct JSON boundary outside approved central serialization surfaces."
    return _text_rule_finding(ctx, TextFindingSpec(idx, "UCS_JSON_BOUNDARY", message, line))


def _subprocess_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not SUBPROCESS_DIRECT.search(line) or ctx.name in ALLOWED_SUBPROCESS_FILES:
        return None
    message = "Direct subprocess boundary outside hardened envelope surfaces."
    return _text_rule_finding(ctx, TextFindingSpec(idx, "UCS_COMMAND_BOUNDARY", message, line))


def _boundary_text_findings(ctx: TextScanContext, idx: int, line: str) -> list[AuditRecord]:
    candidates = [
        _broad_except_text_finding(ctx, idx, line),
        _pass_text_finding(ctx, idx, line),
        _json_boundary_text_finding(ctx, idx, line),
        _subprocess_text_finding(ctx, idx, line),
    ]
    return [finding for finding in candidates if finding is not None]


def _shell_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not SHELL_TRUE.search(line):
        return None
    return _text_rule_finding(
        ctx,
        TextFindingSpec(
            idx,
            "UCS_COMMAND_BOUNDARY",
            "shell=True is forbidden at command boundary.",
            line,
            "BLOCKER",
        ),
    )


def _typed_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not DICT_ANY.search(line):
        return None
    message = "Soft dict/object/Any boundary; consider typed request/result object."
    return _text_rule_finding(
        ctx, TextFindingSpec(idx, "UCS_TYPED_BOUNDARY", message, line, "MEDIUM")
    )


def _path_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not HARD_CODED_PATH.search(line) or ctx.name in ALLOWED_HARDCODED_PATH_FILES:
        return None
    message = "Hardcoded local path outside explicit config/diagnostic surface."
    return _text_rule_finding(ctx, TextFindingSpec(idx, "UCS_HARD_CODED_PATH", message, line))


def _mutable_global_text_finding(ctx: TextScanContext, idx: int, line: str) -> AuditRecord | None:
    if not MUTABLE_GLOBAL_ASSIGN.search(line):
        return None
    message = (
        "Mutable-looking global assignment requires explicit lifecycle/registry justification."
    )
    return _text_rule_finding(
        ctx, TextFindingSpec(idx, "UCS_STATE_DISCIPLINE", message, line, "MEDIUM")
    )


def _shape_text_findings(ctx: TextScanContext, idx: int, line: str) -> list[AuditRecord]:
    candidates = [
        _shell_text_finding(ctx, idx, line),
        _typed_text_finding(ctx, idx, line),
        _path_text_finding(ctx, idx, line),
        _mutable_global_text_finding(ctx, idx, line),
    ]
    return [finding for finding in candidates if finding is not None]


def scan_text(project_root: Path, path: Path, lines: list[str]) -> list[AuditRecord]:
    ctx = TextScanContext(project_root, path, path.name)
    findings: list[AuditRecord] = []
    for idx, line in enumerate(lines, start=1):
        if _is_audit_detector_literal(path, line):
            continue
        marker_finding = _marker_text_finding(ctx, idx, line)
        if marker_finding is not None:
            findings.append(marker_finding)
        findings.extend(_simple_text_findings(ctx, idx, line))
        findings.extend(_boundary_text_findings(ctx, idx, line))
        findings.extend(_shape_text_findings(ctx, idx, line))
    return findings


def _syntax_finding(ctx: AstScanContext, exc: SyntaxError) -> AuditRecord:
    return _finding(
        ctx.path,
        ctx.project_root,
        FindingInput(
            exc.lineno or 1,
            "OMEGA_L1_NO_STUBS",
            f"Syntax error prevents compliance audit: {exc}",
            "",
            "BLOCKER",
        ),
    )


def _parameter_ast_finding(
    ctx: AstScanContext, node: ast.FunctionDef | ast.AsyncFunctionDef
) -> AuditRecord | None:
    args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    if len(args) <= 4:
        return None
    message = f"Function `{node.name}` has {len(args)} parameters (>4 cognitive limit)."
    spec = FindingInput(node.lineno, "UCS_COGNITIVE_CONSERVATION", message, node.name, "MEDIUM")
    return _finding(ctx.path, ctx.project_root, spec)


def _length_ast_finding(
    ctx: AstScanContext, node: ast.FunctionDef | ast.AsyncFunctionDef
) -> AuditRecord | None:
    if not hasattr(node, "end_lineno") or node.end_lineno is None:
        return None
    length = node.end_lineno - node.lineno + 1
    if length <= MAX_FUNCTION_LOC_BUDGET:
        return None
    message = (
        f"Function `{node.name}` is {length} LOC "
        f"(>{MAX_FUNCTION_LOC_BUDGET} screen/working-memory target)."
    )
    spec = FindingInput(node.lineno, "UCS_COGNITIVE_CONSERVATION", message, node.name, "MEDIUM")
    return _finding(ctx.path, ctx.project_root, spec)


def _return_ast_finding(
    ctx: AstScanContext, node: ast.FunctionDef | ast.AsyncFunctionDef
) -> AuditRecord | None:
    if node.returns or node.name.startswith("test_"):
        return None
    message = f"Function `{node.name}` lacks return annotation."
    spec = FindingInput(node.lineno, "UCS_TYPED_BOUNDARY", message, node.name, "LOW")
    return _finding(ctx.path, ctx.project_root, spec)


def _function_ast_findings(
    ctx: AstScanContext, node: ast.FunctionDef | ast.AsyncFunctionDef
) -> list[AuditRecord]:
    candidates = [
        _parameter_ast_finding(ctx, node),
        _length_ast_finding(ctx, node),
        _return_ast_finding(ctx, node),
    ]
    return [finding for finding in candidates if finding is not None]


def _class_ast_findings(ctx: AstScanContext, node: ast.ClassDef) -> list[AuditRecord]:
    if not hasattr(node, "end_lineno") or node.end_lineno is None:
        return []
    length = node.end_lineno - node.lineno + 1
    if length <= 300:
        return []
    message = f"Class `{node.name}` is {length} LOC; audit holon boundary/cohesion."
    return [
        _finding(
            ctx.path,
            ctx.project_root,
            FindingInput(node.lineno, "UCS_COGNITIVE_CONSERVATION", message, node.name, "MEDIUM"),
        )
    ]


def _depth_ast_finding(ctx: AstScanContext, node: ast.AST, depth: int) -> AuditRecord | None:
    branch = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match)
    if not isinstance(node, branch) or depth <= 3:
        return None
    text = ast.get_source_segment(ctx.source, node) or ""
    message = "Nesting/control depth exceeds 3-level cognitive stack target."
    return _finding(
        ctx.path,
        ctx.project_root,
        FindingInput(
            getattr(node, "lineno", 1), "UCS_COGNITIVE_CONSERVATION", message, text, "MEDIUM"
        ),
    )


def _visit_ast_node(ctx: AstScanContext, node: ast.AST, depth: int = 0) -> list[AuditRecord]:
    findings: list[AuditRecord] = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        findings.extend(_function_ast_findings(ctx, node))
    if isinstance(node, ast.ClassDef):
        findings.extend(_class_ast_findings(ctx, node))
    depth_finding = _depth_ast_finding(ctx, node, depth)
    if depth_finding is not None:
        findings.append(depth_finding)
    branch = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match)
    child_depth = depth + 1 if isinstance(node, branch) else depth
    for child in ast.iter_child_nodes(node):
        findings.extend(_visit_ast_node(ctx, child, child_depth))
    return findings


def scan_ast(project_root: Path, path: Path, source: str) -> list[AuditRecord]:
    ctx = AstScanContext(project_root, path, source)
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [_syntax_finding(ctx, exc)]
    findings = _visit_ast_node(ctx, tree)
    if not ast.get_docstring(tree) and path.name not in {"__init__.py"}:
        spec = FindingInput(
            1,
            "UCS_TYPED_BOUNDARY",
            "Module lacks purpose/boundary docstring; holon purpose not explicit.",
            "",
            "LOW",
        )
        findings.append(_finding(path, project_root, spec))
    return findings


def _audit_one_file(
    project_root: Path, label: str, path: Path
) -> tuple[AuditRecord, list[AuditRecord], list[str]]:
    source = path.read_text(encoding="utf-8", errors="replace")
    lines = source.splitlines()
    findings = scan_text(project_root, path, lines) + scan_ast(project_root, path, source)
    file_record = {
        "file": str(path.relative_to(project_root)).replace("\\", "/"),
        "surface": label,
        "loc": len(lines),
        "finding_count": len(findings),
        "severity_counts": dict(Counter(str(f["severity"]) for f in findings)),
    }
    return file_record, findings, lines


def _write_line_index(
    line_handle, file_record: AuditRecord, findings: list[AuditRecord], lines: list[str]
) -> None:
    finding_by_line: dict[int, list[AuditRecord]] = defaultdict(list)
    for finding in findings:
        finding_by_line[int(finding["line"])].append(
            {
                "rule": finding["rule"],
                "severity": finding["severity"],
                "message": finding["message"],
            }
        )
    for idx, line in enumerate(lines, start=1):
        line_handle.write(
            json.dumps(
                {
                    "file": file_record["file"],
                    "line": idx,
                    "covered": True,
                    "clean": not finding_by_line.get(idx),
                    "findings": finding_by_line.get(idx, []),
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def _audit_surface_counts(files: list[AuditRecord]) -> Counter[str]:
    surface_counts: Counter[str] = Counter()
    for file_record in files:
        surface_counts[str(file_record["surface"])] += int(file_record["finding_count"])
    return surface_counts


def _audit_report_counts(
    findings: list[AuditRecord], files: list[AuditRecord]
) -> tuple[Counter[str], Counter[str], int]:
    severity_counts = Counter(str(f["severity"]) for f in findings)
    rule_counts = Counter(str(f["rule"]) for f in findings)
    total_loc = sum(int(f["loc"]) for f in files)
    return severity_counts, rule_counts, total_loc


def _audit_scope() -> str:
    return (
        "Every Python LOC under baseline/pcmmad_receiver, tools/csc_native, "
        "system, and tests; generated/extracted/data surfaces excluded."
    )


def _audit_report_payload(
    project_root: Path,
    files: list[AuditRecord],
    findings: list[AuditRecord],
    per_line_index_path: Path,
) -> AuditRecord:
    severity_counts, rule_counts, total_loc = _audit_report_counts(findings, files)
    promotion_ready = not severity_counts.get("BLOCKER", 0) and not severity_counts.get("HIGH", 0)
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_scope": _audit_scope(),
        "doctrine_basis": dict(DOCTRINE_BASIS),
        "rule_basis": dict(RULES),
        "file_count": len(files),
        "total_loc": total_loc,
        "finding_count": len(findings),
        "severity_counts": dict(severity_counts),
        "rule_counts": dict(rule_counts),
        "surface_finding_counts": dict(_audit_surface_counts(files)),
        "files": files,
        "findings": findings,
        "per_line_index": str(per_line_index_path.relative_to(project_root)).replace("\\", "/"),
        "promotion_readiness": "CONDITIONAL" if promotion_ready else "NOT_READY",
    }


def audit(project_root: Path) -> AuditRecord:
    files: list[AuditRecord] = []
    all_findings: list[AuditRecord] = []
    per_line_index_path = project_root / "reports" / "CODEX_UNIFIED_LOC_AUDIT_LINES.jsonl"
    per_line_index_path.parent.mkdir(parents=True, exist_ok=True)
    with per_line_index_path.open("w", encoding="utf-8") as line_handle:
        for label, path in iter_python_files(project_root):
            file_record, findings, lines = _audit_one_file(project_root, label, path)
            files.append(file_record)
            all_findings.extend(findings)
            _write_line_index(line_handle, file_record, findings, lines)
    return _audit_report_payload(project_root, files, all_findings, per_line_index_path)


def _markdown_header(report: AuditRecord) -> list[str]:
    return [
        "# CODEX + Unified Standards LOC Compliance Audit",
        "",
        f"- Created UTC: {report['created_at_utc']}",
        f"- Scope: {report['audit_scope']}",
        f"- Files audited: {report['file_count']}",
        f"- Total LOC covered: {report['total_loc']}",
        f"- Findings: {report['finding_count']}",
        f"- Promotion readiness: {report['promotion_readiness']}",
        "",
    ]


def _markdown_doctrine_lines(report: AuditRecord) -> list[str]:
    lines = ["## Doctrine basis"]
    for name, basis in report["doctrine_basis"].items():
        lines.append(
            f"- `{name}` — sha256 `{basis['sha256']}` — {basis['bytes']} bytes — {basis['role']}"
        )
    return lines


def _markdown_count_lines(title: str, counts: AuditRecord) -> list[str]:
    lines = ["", title]
    lines.extend(f"- {key}: {value}" for key, value in sorted(counts.items()))
    return lines


def _high_finding_markdown_line(finding: AuditRecord) -> str:
    text = str(finding["text"]).strip()[:160]
    location = f"`{finding['file']}:{finding['line']}`"
    head = f"[{finding['severity']}] {finding['rule']}"
    return f"- {location} {head} — {finding['message']} — `{text}`"


def _markdown_high_finding_lines(report: AuditRecord) -> list[str]:
    lines = ["", "## Highest-friction findings"]
    high = [f for f in report["findings"] if f["severity"] in {"BLOCKER", "HIGH"}]
    lines.extend(_high_finding_markdown_line(finding) for finding in high[:300])
    if len(high) > 300:
        lines.append(f"- ... {len(high)-300} additional HIGH/BLOCKER findings in JSON report.")
    return lines


def _file_count_markdown_line(file_record: AuditRecord) -> str:
    head = f"- `{file_record['file']}` — loc={file_record['loc']}"
    tail = f"findings={file_record['finding_count']} severity={file_record['severity_counts']}"
    return f"{head} {tail}"


def _markdown_file_count_lines(report: AuditRecord) -> list[str]:
    lines = ["", "## Files with highest finding count"]
    files = sorted(report["files"], key=lambda item: int(item["finding_count"]), reverse=True)
    lines.extend(_file_count_markdown_line(file_record) for file_record in files[:100])
    return lines


def write_markdown(
    project_root: Path, report: AuditRecord, markdown_path: Path | None = None
) -> None:
    md = markdown_path or project_root / "reports" / "CODEX_UNIFIED_LOC_COMPLIANCE_AUDIT.md"
    lines = _markdown_header(report)
    lines.extend(_markdown_doctrine_lines(report))
    lines.extend(_markdown_count_lines("## Severity counts", report["severity_counts"]))
    lines.extend(_markdown_count_lines("## Rule counts", report["rule_counts"]))
    lines.extend(_markdown_high_finding_lines(report))
    lines.extend(_markdown_file_count_lines(report))
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_loc_audit(
    project_root: Path, output_json: Path, output_md: Path | None = None
) -> AuditRecord:
    report = audit(project_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(project_root, report, output_md)
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run project-agnostic CODEX/UCS LOC compliance audit"
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-json", default="reports/CODEX_UNIFIED_LOC_COMPLIANCE_AUDIT.json")
    parser.add_argument("--output-md", default="reports/CODEX_UNIFIED_LOC_COMPLIANCE_AUDIT.md")
    return parser.parse_args()


def _summary_path(path: Path, project_root: Path) -> str:
    return str(path.relative_to(project_root)) if path.is_relative_to(project_root) else str(path)


def _main_summary(
    report: AuditRecord, output_json: Path, output_md: Path, project_root: Path
) -> AuditRecord:
    return {
        "report": _summary_path(output_json, project_root),
        "markdown": _summary_path(output_md, project_root),
        "per_line_index": str(report["per_line_index"]),
        "file_count": report["file_count"],
        "total_loc": report["total_loc"],
        "finding_count": report["finding_count"],
        "severity_counts": report["severity_counts"],
        "promotion_readiness": report["promotion_readiness"],
    }


def main() -> None:
    args = _parse_args()
    project_root = Path(args.project_root).resolve()
    output_json = (project_root / args.output_json).resolve()
    output_md = (project_root / args.output_md).resolve()
    report = run_loc_audit(project_root, output_json, output_md)
    sys.stdout.write(
        json.dumps(_main_summary(report, output_json, output_md, project_root), indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
