"""Project-agnostic guide-derived style, quality, and hygiene audit."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import Counter
from types import MappingProxyType
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Mapping
from typing import Iterable, TypeAlias

from strict_json_boundary import read_json_boundary, write_json_boundary


GuideJson: TypeAlias = str | int | bool | None | list["GuideJson"] | Mapping[str, "GuideJson"]


@dataclass(frozen=True)
class GuideSurface:
    path: Path
    label: str


@dataclass(frozen=True)
class FunctionShapeSpec:
    path: Path
    node: ast.FunctionDef | ast.AsyncFunctionDef
    source: str


@dataclass(frozen=True)
class LineCheckSpec:
    path: Path
    line_no: int
    line: str
    stripped: str


@dataclass(frozen=True)
class AuditContext:
    project_root: Path
    basis: Mapping[str, str]
    severity: Mapping[str, str]
    line_length: int


@dataclass(frozen=True)
class GuideFindingSpec:
    rule: str
    line: int
    message: str
    text: str = ""
    severity_override: str | None = None


@dataclass(frozen=True)
class GuideFinding:
    rule: str
    severity: str
    file: str
    line: int
    message: str
    text: str
    basis: str

    def to_dict(self) -> Mapping[str, str | int]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "text": self.text,
            "basis": self.basis,
        }


DEFAULT_SURFACES = (
    GuideSurface(Path("baseline") / "pcmmad_receiver", "receiver_baseline"),
    GuideSurface(Path("tools") / "csc_native", "csc_native"),
    GuideSurface(Path("system"), "system"),
    GuideSurface(Path("tests"), "tests"),
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
DEFAULT_RULE_BASIS = MappingProxyType(
    {
        "GEM_STYLE_NAMING_CLARITY": (
            "Intention-revealing names; avoid cryptic identifiers where domain names exist."
        ),
        "GEM_STYLE_VISUAL_SCAN": (
            "Spatial rhythm, bounded lines, bounded function length, and shallow indentation "
            "improve readability."
        ),
        "GEM_STYLE_COMMENTS_WHY": "Comments should explain why, invariant, or boundary intent.",
        "GEM_QUALITY_MODULARITY": (
            "Functions above 20-30 lines often indicate split pressure unless cohesive."
        ),
        "GEM_QUALITY_RESOURCE_EFFICIENCY": (
            "Avoid unnecessary repeated work inside loops; prefer cached/indexed forms."
        ),
        "GEM_QUALITY_FALLIBILITY": (
            "Use explicit error handling; no bare except, silent pass, or broad swallowing."
        ),
        "GEM_QUALITY_INPUT_SECURITY": (
            "Treat external input as malicious; avoid hardcoded credentials or secrets."
        ),
        "GEM_QUALITY_TEST_COVERAGE": (
            "Critical behavior should have clear tests and fail for the right reason."
        ),
        "GEM_TEST_TRACEABILITY": "Unresolved intent markers should be tracked or removed.",
        "GEM_HYGIENE_NO_VAGUE_PRIMITIVES": (
            "Domain values should cross seams through typed request/result/value objects."
        ),
        "GEM_HYGIENE_NO_PYRAMID": "Avoid deep nested control flow; keep the happy path visible.",
        "GEM_HYGIENE_NO_REP_LEAK": (
            "Avoid mutable public representation leakage and mutable global truth surfaces."
        ),
    }
)
DEFAULT_RULE_SEVERITY = MappingProxyType(
    {
        "GEM_QUALITY_FALLIBILITY": "MEDIUM",
        "GEM_QUALITY_INPUT_SECURITY": "MEDIUM",
        "GEM_HYGIENE_NO_VAGUE_PRIMITIVES": "MEDIUM",
        "GEM_HYGIENE_NO_PYRAMID": "MEDIUM",
        "GEM_HYGIENE_NO_REP_LEAK": "MEDIUM",
    }
)
SEVERITY_ORDER = MappingProxyType({"BLOCKER": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "ADVISORY": 4})
NOISY_SINGLE_LETTERS = frozenset({"d", "r", "n", "m", "s", "t", "v", "k", "q"})
LOOP_RESOURCE_CALLS = frozenset({"read_text", "write_text", "open"})
COMMENT_MARKERS = ("TO" + "DO", "FIX" + "ME", "HA" + "CK")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relative(project_root: Path, path: Path) -> str:
    return str(path.relative_to(project_root)).replace("\\", "/")


def _load_rule_maps(project_root: Path) -> tuple[Mapping[str, str], Mapping[str, str], str | None]:
    rubric_path = project_root / "docs" / "external_guides" / "GEMINI_GUIDES_EVALUATION_RUBRIC.json"
    basis = dict(DEFAULT_RULE_BASIS)
    severity = {rule: DEFAULT_RULE_SEVERITY.get(rule, "LOW") for rule in DEFAULT_RULE_BASIS}
    if not rubric_path.exists():
        return basis, severity, None
    raw = read_json_boundary(rubric_path)
    if not isinstance(raw, dict):
        return basis, severity, str(rubric_path)
    for rule in raw.get("rules", []):
        if isinstance(rule, dict) and isinstance(rule.get("id"), str):
            rule_id = str(rule["id"])
            if isinstance(rule.get("basis"), str):
                basis[rule_id] = str(rule["basis"])
            if isinstance(rule.get("severity"), str):
                severity[rule_id] = str(rule["severity"])
    return basis, severity, str(rubric_path)


def _iter_python_files(project_root: Path, surfaces: tuple[GuideSurface, ...]) -> Iterable[Path]:
    for surface in surfaces:
        root = project_root / surface.path
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if not any(part in EXCLUDED_PARTS for part in path.parts):
                yield path


def _max_nesting(node: ast.AST, depth: int = 0) -> int:
    branch_nodes = (
        ast.If,
        ast.For,
        ast.While,
        ast.Try,
        ast.With,
        ast.Match,
        ast.AsyncFor,
        ast.AsyncWith,
    )
    next_depth = depth + (1 if isinstance(node, branch_nodes) else 0)
    return max(
        [next_depth] + [_max_nesting(child, next_depth) for child in ast.iter_child_nodes(node)]
    )


def _finding(ctx: AuditContext, path: Path, spec: GuideFindingSpec) -> GuideFinding:
    return GuideFinding(
        rule=spec.rule,
        severity=spec.severity_override or ctx.severity.get(spec.rule, "LOW"),
        file=_relative(ctx.project_root, path),
        line=spec.line,
        message=spec.message,
        text=spec.text[:240],
        basis=ctx.basis.get(spec.rule, "Guide-derived quality/style/hygiene rule."),
    )


def _empty_function_metrics() -> dict[str, int]:
    return {
        "functions": 0,
        "classes": 0,
        "max_function_lines": 0,
        "max_parameters": 0,
        "max_nesting": 0,
        "long_functions_over_30": 0,
    }


def _parameter_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    count = len(node.args.args) + len(node.args.kwonlyargs) + len(node.args.posonlyargs)
    return count + int(bool(node.args.vararg)) + int(bool(node.args.kwarg))


def _long_function_finding(ctx: AuditContext, spec: FunctionShapeSpec, length: int) -> GuideFinding:
    message = f"Function `{spec.node.name}` is {length} lines; consider cohesive extraction."
    finding_spec = GuideFindingSpec(
        "GEM_QUALITY_MODULARITY", spec.node.lineno, message, spec.source
    )
    return _finding(ctx, spec.path, finding_spec)


def _parameter_finding(ctx: AuditContext, spec: FunctionShapeSpec, count: int) -> GuideFinding:
    message = f"Function `{spec.node.name}` has {count} parameters; consider a request/spec object."
    finding_spec = GuideFindingSpec(
        "GEM_HYGIENE_NO_VAGUE_PRIMITIVES", spec.node.lineno, message, spec.source
    )
    return _finding(ctx, spec.path, finding_spec)


def _nesting_finding(ctx: AuditContext, spec: FunctionShapeSpec, nesting: int) -> GuideFinding:
    message = (
        f"Function `{spec.node.name}` nesting depth is {nesting}; "
        "consider guard clauses or extraction."
    )
    finding_spec = GuideFindingSpec(
        "GEM_HYGIENE_NO_PYRAMID", spec.node.lineno, message, spec.source
    )
    return _finding(ctx, spec.path, finding_spec)


def _function_shape_findings(
    ctx: AuditContext, path: Path, lines: list[str], node: ast.FunctionDef | ast.AsyncFunctionDef
) -> list[GuideFinding]:
    length = int(getattr(node, "end_lineno", node.lineno)) - node.lineno + 1
    spec = FunctionShapeSpec(path, node, lines[node.lineno - 1].strip())
    findings: list[GuideFinding] = []
    if length > 30:
        findings.append(_long_function_finding(ctx, spec, length))
    parameter_count = _parameter_count(node)
    if parameter_count > 6:
        findings.append(_parameter_finding(ctx, spec, parameter_count))
    nesting = _max_nesting(node)
    if nesting > 4:
        findings.append(_nesting_finding(ctx, spec, nesting))
    return findings


def _update_function_metrics(
    metrics: dict[str, int], node: ast.FunctionDef | ast.AsyncFunctionDef
) -> None:
    end_line = int(getattr(node, "end_lineno", node.lineno))
    function_length = end_line - node.lineno + 1
    metrics["functions"] += 1
    metrics["max_function_lines"] = max(metrics["max_function_lines"], function_length)
    metrics["max_parameters"] = max(metrics["max_parameters"], _parameter_count(node))
    metrics["max_nesting"] = max(metrics["max_nesting"], _max_nesting(node))
    metrics["long_functions_over_30"] += int(function_length > 30)


def _function_findings(
    ctx: AuditContext,
    path: Path,
    lines: list[str],
    tree: ast.Module,
) -> tuple[list[GuideFinding], Mapping[str, int]]:
    findings: list[GuideFinding] = []
    metrics = _empty_function_metrics()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            metrics["classes"] += 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _update_function_metrics(metrics, node)
            findings.extend(_function_shape_findings(ctx, path, lines, node))
    return findings, metrics


def _line_length_finding(ctx: AuditContext, spec: LineCheckSpec) -> GuideFinding | None:
    if len(spec.line) <= ctx.line_length:
        return None
    message = f"Line length {len(spec.line)} exceeds {ctx.line_length}-character guide target."
    finding_spec = GuideFindingSpec("GEM_STYLE_VISUAL_SCAN", spec.line_no, message, spec.stripped)
    return _finding(ctx, spec.path, finding_spec)


def _line_print_finding(
    ctx: AuditContext, path: Path, line_no: int, stripped: str
) -> GuideFinding | None:
    if not re.search(r"\b(print|pprint)\s*\(", stripped):
        return None
    if "tests/" in _relative(ctx.project_root, path):
        return None
    message = (
        "Production code contains print-style output; verify explicit CLI/report boundary intent."
    )
    return _finding(
        ctx, path, GuideFindingSpec("GEM_STYLE_COMMENTS_WHY", line_no, message, stripped)
    )


def _line_marker_finding(
    ctx: AuditContext, path: Path, line_no: int, stripped: str
) -> GuideFinding | None:
    if not any(marker in stripped for marker in COMMENT_MARKERS):
        return None
    message = "Unresolved traceability marker requires owner, issue link, or removal."
    return _finding(
        ctx, path, GuideFindingSpec("GEM_TEST_TRACEABILITY", line_no, message, stripped)
    )


def _line_secret_finding(
    ctx: AuditContext, path: Path, line_no: int, stripped: str
) -> GuideFinding | None:
    pattern = r"(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}"
    if not re.search(pattern, stripped, re.IGNORECASE):
        return None
    return _finding(
        ctx,
        path,
        GuideFindingSpec(
            "GEM_QUALITY_INPUT_SECURITY",
            line_no,
            "Possible hardcoded credential-like assignment.",
            stripped,
            "HIGH",
        ),
    )


def _line_findings(
    ctx: AuditContext, path: Path, lines: list[str]
) -> tuple[list[GuideFinding], Mapping[str, int]]:
    findings: list[GuideFinding] = []
    metrics = {"lines_over_limit": 0}
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        spec = LineCheckSpec(path, line_no, line, stripped)
        line_finding = _line_length_finding(ctx, spec)
        metrics["lines_over_limit"] += int(line_finding is not None)
        candidates = [
            line_finding,
            _line_print_finding(ctx, path, line_no, stripped),
            _line_marker_finding(ctx, path, line_no, stripped),
            _line_secret_finding(ctx, path, line_no, stripped),
        ]
        findings.extend(finding for finding in candidates if finding is not None)
    return findings, metrics


def _bare_except_finding(
    ctx: AuditContext, path: Path, source: str, node: ast.ExceptHandler
) -> GuideFinding:
    spec = GuideFindingSpec(
        "GEM_QUALITY_FALLIBILITY",
        node.lineno,
        "Bare except catches all failures without explicit fallibility model.",
        source,
        "HIGH",
    )
    return _finding(ctx, path, spec)


def _broad_except_finding(
    ctx: AuditContext, path: Path, source: str, node: ast.ExceptHandler
) -> GuideFinding:
    name = node.type.id if isinstance(node.type, ast.Name) else "Exception"
    message = f"Broad `{name}` handler should preserve diagnostics or re-raise."
    return _finding(
        ctx, path, GuideFindingSpec("GEM_QUALITY_FALLIBILITY", node.lineno, message, source)
    )


def _silent_pass_finding(
    ctx: AuditContext, path: Path, lines: list[str], child: ast.Pass
) -> GuideFinding:
    spec = GuideFindingSpec(
        "GEM_QUALITY_FALLIBILITY",
        child.lineno,
        "Exception handler silently passes.",
        lines[child.lineno - 1].strip(),
        "HIGH",
    )
    return _finding(ctx, path, spec)


def _except_handler_findings(
    ctx: AuditContext, path: Path, lines: list[str], node: ast.ExceptHandler
) -> list[GuideFinding]:
    source = lines[node.lineno - 1].strip()
    findings: list[GuideFinding] = []
    if node.type is None:
        findings.append(_bare_except_finding(ctx, path, source, node))
    elif isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"}:
        findings.append(_broad_except_finding(ctx, path, source, node))
    findings.extend(
        _silent_pass_finding(ctx, path, lines, child)
        for child in node.body
        if isinstance(child, ast.Pass)
    )
    return findings


def _single_letter_name_finding(
    ctx: AuditContext, path: Path, lines: list[str], node: ast.AST
) -> GuideFinding | None:
    if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Store):
        return None
    if len(node.id) != 1 or node.id not in NOISY_SINGLE_LETTERS:
        return None
    message = f"Single-letter variable `{node.id}` may reduce clarity outside tiny loops."
    return _finding(
        ctx,
        path,
        GuideFindingSpec(
            "GEM_STYLE_NAMING_CLARITY", node.lineno, message, lines[node.lineno - 1].strip()
        ),
    )


def _ast_quality_findings(
    ctx: AuditContext,
    path: Path,
    lines: list[str],
    tree: ast.Module,
) -> list[GuideFinding]:
    findings: list[GuideFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            findings.extend(_except_handler_findings(ctx, path, lines, node))
        name_finding = _single_letter_name_finding(ctx, path, lines, node)
        if name_finding is not None:
            findings.append(name_finding)
        if isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            findings.extend(_loop_resource_findings(ctx, path, lines, node))
    findings.extend(_module_representation_findings(ctx, path, lines, tree))
    findings.extend(_test_shape_findings(ctx, path, lines))
    return findings


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def _loop_resource_findings(
    ctx: AuditContext,
    path: Path,
    lines: list[str],
    loop: ast.AST,
) -> list[GuideFinding]:
    findings: list[GuideFinding] = []
    for node in ast.walk(loop):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name not in LOOP_RESOURCE_CALLS:
            continue
        line_no = int(getattr(node, "lineno", getattr(loop, "lineno", 1)))
        message = f"Potential repeated `{name}` call inside loop; verify resource/caching intent."
        findings.append(
            _finding(
                ctx,
                path,
                GuideFindingSpec(
                    "GEM_QUALITY_RESOURCE_EFFICIENCY", line_no, message, lines[line_no - 1].strip()
                ),
            )
        )
    return findings


def _module_representation_findings(
    ctx: AuditContext,
    path: Path,
    lines: list[str],
    tree: ast.Module,
) -> list[GuideFinding]:
    findings: list[GuideFinding] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        mutable = isinstance(node.value, (ast.List, ast.Dict, ast.Set))
        for target in node.targets:
            if isinstance(target, ast.Name) and mutable and target.id.isupper():
                findings.append(
                    _finding(
                        ctx,
                        path,
                        GuideFindingSpec(
                            "GEM_HYGIENE_NO_REP_LEAK",
                            node.lineno,
                            (
                                f"Uppercase constant `{target.id}` is initialized "
                                "with mutable literal."
                            ),
                            lines[node.lineno - 1].strip(),
                        ),
                    )
                )
    return findings


def _test_shape_findings(ctx: AuditContext, path: Path, lines: list[str]) -> list[GuideFinding]:
    rel_path = _relative(ctx.project_root, path)
    if "tests/" not in rel_path:
        return []
    lower_text = "\n".join(lines).lower()
    if all(word in lower_text for word in ("arrange", "act", "assert")):
        return []
    return [
        _finding(
            ctx,
            path,
            GuideFindingSpec(
                "GEM_QUALITY_TEST_COVERAGE",
                1,
                (
                    "Test file does not explicitly mark Arrange/Act/Assert sections "
                    "for critical readability."
                ),
            ),
        )
    ]


def _empty_file_metrics(lines: list[str]) -> dict[str, int]:
    metrics = _empty_function_metrics()
    metrics.update({"loc": len(lines), "lines_over_limit": 0})
    return metrics


def _merge_file_metrics(metrics: dict[str, int], updates: Mapping[str, int]) -> None:
    for key, value in updates.items():
        metrics[key] = (
            max(metrics[key], value) if key.startswith("max_") else metrics.get(key, 0) + value
        )


def _syntax_error_result(
    ctx: AuditContext, path: Path, lines: list[str], exc: SyntaxError
) -> tuple[list[GuideFinding], Mapping[str, int]]:
    spec = GuideFindingSpec(
        "GEM_STYLE_VISUAL_SCAN",
        exc.lineno or 1,
        f"Syntax parse failed: {exc.msg}",
        severity_override="HIGH",
    )
    return [_finding(ctx, path, spec)], _empty_file_metrics(lines)


def _audit_file(ctx: AuditContext, path: Path) -> tuple[list[GuideFinding], Mapping[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    metrics = _empty_file_metrics(lines)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return _syntax_error_result(ctx, path, lines, exc)
    function_findings, function_metrics = _function_findings(ctx, path, lines, tree)
    line_findings, line_metrics = _line_findings(ctx, path, lines)
    _merge_file_metrics(metrics, function_metrics)
    metrics["lines_over_limit"] = line_metrics["lines_over_limit"]
    findings = function_findings + line_findings + _ast_quality_findings(ctx, path, lines, tree)
    return findings, metrics


def _empty_run_metrics() -> dict[str, int]:
    metrics = _empty_file_metrics([])
    metrics["files"] = 0
    return metrics


def _merge_run_metrics(metrics: dict[str, int], file_metrics: Mapping[str, int]) -> None:
    metrics["files"] += 1
    for key in ("loc", "functions", "classes", "long_functions_over_30", "lines_over_limit"):
        metrics[key] += int(file_metrics[key])
    for key in ("max_function_lines", "max_parameters", "max_nesting"):
        metrics[key] = max(metrics[key], int(file_metrics[key]))


def _report_payload(
    rubric_path: str,
    line_length: int,
    metrics: Mapping[str, int],
    finding_dicts: list[dict[str, GuideJson]],
) -> Mapping[str, GuideJson]:
    severity_counts = Counter(str(finding["severity"]) for finding in finding_dicts)
    rule_counts = Counter(str(finding["rule"]) for finding in finding_dicts)
    file_counts = Counter(str(finding["file"]) for finding in finding_dicts)
    strict_count = sum(severity_counts.get(level, 0) for level in ("BLOCKER", "HIGH", "MEDIUM"))
    scope = (
        "Project-agnostic Python surfaces when present: baseline/pcmmad_receiver, "
        "tools/csc_native, system, tests."
    )
    return {
        "created_at_utc": _utc_now(),
        "audit_name": "CSC guide-derived style/quality/hygiene audit",
        "audit_scope": scope,
        "rubric_path": rubric_path,
        "line_length": line_length,
        "metrics": dict(metrics),
        "finding_count": len(finding_dicts),
        "severity_counts": dict(severity_counts),
        "rule_counts": dict(rule_counts),
        "file_counts": dict(file_counts),
        "findings": finding_dicts,
        "strict_failure_count": strict_count,
        "advisory_only": strict_count == 0,
    }


def run_audit(
    project_root: Path, output_json: Path, output_md: Path, line_length: int
) -> Mapping[str, GuideJson]:
    basis, severity, rubric_path = _load_rule_maps(project_root)
    findings: list[GuideFinding] = []
    metrics = _empty_run_metrics()
    ctx = AuditContext(project_root, basis, severity, line_length)
    for path in _iter_python_files(project_root, DEFAULT_SURFACES):
        file_findings, file_metrics = _audit_file(ctx, path)
        findings.extend(file_findings)
        _merge_run_metrics(metrics, file_metrics)
    finding_dicts = [finding.to_dict() for finding in sorted(findings, key=_finding_sort_key)]
    report = _report_payload(rubric_path, line_length, metrics, finding_dicts)
    write_json_boundary(output_json, report)
    output_md.write_text(_render_markdown(report), encoding="utf-8")
    return report


def _finding_sort_key(finding: GuideFinding) -> tuple[int, str, int, str]:
    return (SEVERITY_ORDER.get(finding.severity, 9), finding.file, finding.line, finding.rule)


def _top_files(report: Mapping[str, GuideJson]) -> list[tuple[str, int]]:
    file_counts = report.get("file_counts", {})
    if not isinstance(file_counts, dict):
        return []
    return sorted(file_counts.items(), key=lambda item: int(item[1]), reverse=True)[:10]


def _markdown_summary_lines(report: Mapping[str, GuideJson]) -> list[str]:
    return [
        "# CSC Guide-Derived Style/Quality/Hygiene Audit",
        "",
        f"Created: {report.get('created_at_utc')}",
        "",
        "## Summary",
        f"- Findings: {report.get('finding_count')}",
        f"- Severity counts: `{report.get('severity_counts')}`",
        f"- Rule counts: `{report.get('rule_counts')}`",
        f"- Metrics: `{report.get('metrics')}`",
        f"- Advisory only: `{report.get('advisory_only')}`",
        "",
        "## Top files",
    ]


def _markdown_finding_line(raw: dict[str, GuideJson]) -> str:
    head = f"- **{raw.get('severity')} / {raw.get('rule')}**"
    where = f"`{raw.get('file')}:{raw.get('line')}`"
    return f"{head} {where} — {raw.get('message')}"


def _markdown_finding_lines(findings: GuideJson) -> list[str]:
    if not isinstance(findings, list):
        return []
    lines: list[str] = []
    for raw in findings[:100]:
        if isinstance(raw, dict):
            lines.append(_markdown_finding_line(raw))
    if len(findings) > 100:
        lines.append(f"- ... {len(findings) - 100} additional findings in JSON report.")
    return lines


def _render_markdown(report: Mapping[str, GuideJson]) -> str:
    lines = _markdown_summary_lines(report)
    lines.extend(f"- `{path}`: {count}" for path, count in _top_files(report))
    lines.extend(["", "## Top findings"])
    lines.extend(_markdown_finding_lines(report.get("findings", [])))
    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run project-agnostic guide-derived quality/style/hygiene audit"
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-json", default="reports/GEMINI_GUIDE_CODEBASE_EVALUATION.json")
    parser.add_argument("--output-md", default="reports/GEMINI_GUIDE_CODEBASE_EVALUATION.md")
    parser.add_argument("--line-length", type=int, default=100)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def _path_for_summary(path: Path, project_root: Path) -> str:
    return str(path.relative_to(project_root)) if path.is_relative_to(project_root) else str(path)


def _main_summary(
    report: Mapping[str, GuideJson], output_json: Path, output_md: Path, project_root: Path
) -> dict[str, GuideJson]:
    return {
        "report": _path_for_summary(output_json, project_root),
        "markdown": _path_for_summary(output_md, project_root),
        "finding_count": report.get("finding_count"),
        "severity_counts": report.get("severity_counts"),
        "strict_failure_count": report.get("strict_failure_count"),
        "advisory_only": report.get("advisory_only"),
    }


def main() -> None:
    args = _parse_args()
    project_root = Path(args.project_root).resolve()
    output_json = (project_root / args.output_json).resolve()
    output_md = (project_root / args.output_md).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    report = run_audit(project_root, output_json, output_md, args.line_length)
    sys.stdout.write(str(_main_summary(report, output_json, output_md, project_root)) + "\n")
    if args.strict and int(report.get("strict_failure_count", 0)):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
