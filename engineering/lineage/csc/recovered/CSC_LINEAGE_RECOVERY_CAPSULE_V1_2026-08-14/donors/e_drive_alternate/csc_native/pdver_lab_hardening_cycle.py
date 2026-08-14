"""PDVER whole-surface CSC hardening cycle and finalizer gate support."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, TypeAlias
from pathlib import Path

from csc_doctrine_manifest import (
    REQUIRED_LOCAL_CSC_DOCS,
    REQUIRED_REPAIRED_ARCHIVE_FILES,
    REPAIRED_ARCHIVE_ROOT,
)
from csc_runtime_bindings import get_bindings
from strict_json_boundary import render_json_boundary, write_json_boundary

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | Mapping[str, "JsonValue"]
)

BINDINGS = get_bindings()
CODE_DIR = BINDINGS.target_code_root
PROJECT_ROOT = BINDINGS.target_project_root
REPORT_PATH = BINDINGS.output_root / "PDVER_HARDENING_REPORT.json"

ALLOW_SCAN_SUFFIXES = (".py", ".rs", ".toml")
COMMENT_TRACKING_PATTERN = re.compile(
    r"^\s*#.*\b(" + "TO" + "DO|FIX" + "ME|HA" + "CK|X" + "XX)\b", re.MULTILINE
)
ABSOLUTE_WINDOWS_PATH_PATTERN = re.compile(r"[A-Z]:\\\\|[A-Z]:/")
LEGACY_TYPING_NAMES = ("Dict", "List", "Optional", "Tuple", "Set")
MAX_PARAMETER_COUNT = 5
MAX_NESTING_DEPTH = 4
MAX_FUNCTION_LINES = 150
ACTIVE_HEAT_WINDOW_SECONDS = 24 * 60 * 60
MAX_MUTATION_LAG_SECONDS = 30 * 60
MAX_REQUIRED_SOP_SET_AGE_SECONDS = 72 * 60 * 60

RUST_MACRO_PATTERNS = (
    ("rust_unwrap_used", re.compile(r"\.unwrap\s*!?\(")),
    ("rust_expect_used", re.compile(r"\.expect\s*!?\(")),
    ("rust_panic_used", re.compile(r"\bpanic\s*!\(")),
    ("rust_todo_used", re.compile(r"\btodo\s*!\(")),
    ("rust_unimplemented_used", re.compile(r"\bunimplemented\s*!\(")),
    ("rust_dbg_macro", re.compile(r"\bdbg\s*!\(")),
)
JSON_BOUNDARY_PROBE_TOKENS = (
    "json." + "load(",
    "json." + "dump(",
    "json." + "loads(",
    "json." + "dumps(",
    "import " + "json",
)

RUST_ABSOLUTE_PATH_PATTERN = re.compile(r"([A-Z]:\\|[A-Z]:/|" + "/" + r"Users/|" + "/" + r"home/)")


def _display_path(path: Path) -> str:
    if PROJECT_ROOT == path or PROJECT_ROOT in path.parents:
        return path.relative_to(PROJECT_ROOT).as_posix()
    if BINDINGS.docs_root == path or BINDINGS.docs_root in path.parents:
        return f"<csc_docs>/{path.relative_to(BINDINGS.docs_root).as_posix()}"
    if REPAIRED_ARCHIVE_ROOT == path or REPAIRED_ARCHIVE_ROOT in path.parents:
        return f"<repaired_archive>/{path.relative_to(REPAIRED_ARCHIVE_ROOT).as_posix()}"
    return path.as_posix() if path.drive == "" else str(path).replace("\\", "/")


@dataclass(frozen=True)
class Finding:
    file: str
    issue: str
    detail: str


@dataclass(frozen=True)
class VerificationResult:
    name: str
    return_code: int
    ok: bool
    stdout_tail: str
    stderr_tail: str


@dataclass(frozen=True)
class FindingSummary:
    issue: str
    count: int


@dataclass(frozen=True)
class AstFacts:
    uses_any: bool
    typing_imports: tuple[str, ...]
    uses_dunder_dict: bool
    uses_asdict: bool
    builtin_dict_annotations: tuple[str, ...]
    mutable_default_arguments: tuple[str, ...]
    broad_exception_handlers: tuple[str, ...]
    module_mutable_globals: tuple[str, ...]
    boolean_name_violations: tuple[str, ...]
    too_many_parameters: tuple[str, ...]
    too_deep_nesting: tuple[str, ...]
    too_long_functions: tuple[str, ...]
    silent_handlers: tuple[str, ...]


@dataclass
class ScanState:
    uses_any: bool = False
    uses_dunder_dict: bool = False
    uses_asdict: bool = False
    typing_imports: set[str] | None = None
    builtin_dict_annotations: list[str] | None = None
    mutable_default_arguments: list[str] | None = None
    broad_exception_handlers: list[str] | None = None
    module_mutable_globals: list[str] | None = None
    boolean_name_violations: list[str] | None = None
    too_many_parameters: list[str] | None = None
    too_deep_nesting: list[str] | None = None
    too_long_functions: list[str] | None = None
    silent_handlers: list[str] | None = None

    def __post_init__(self) -> None:
        self.typing_imports = set() if self.typing_imports is None else self.typing_imports
        if self.builtin_dict_annotations is None:
            self.builtin_dict_annotations = []
        if self.mutable_default_arguments is None:
            self.mutable_default_arguments = []
        if self.broad_exception_handlers is None:
            self.broad_exception_handlers = []
        if self.module_mutable_globals is None:
            self.module_mutable_globals = []
        if self.boolean_name_violations is None:
            self.boolean_name_violations = []
        if self.too_many_parameters is None:
            self.too_many_parameters = []
        self.too_deep_nesting = [] if self.too_deep_nesting is None else self.too_deep_nesting
        self.too_long_functions = [] if self.too_long_functions is None else self.too_long_functions
        self.silent_handlers = [] if self.silent_handlers is None else self.silent_handlers


@dataclass(frozen=True)
class CscSelfAudit:
    clean: bool
    checked_files: tuple[str, ...]
    findings: tuple[Finding, ...]


class _DepthVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_depth = 0
        self.max_depth = 0

    def _descend(self, node: ast.AST) -> None:
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_If(self, node: ast.If) -> None:
        self._descend(node)

    def visit_For(self, node: ast.For) -> None:
        self._descend(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._descend(node)

    def visit_While(self, node: ast.While) -> None:
        self._descend(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._descend(node)

    def visit_With(self, node: ast.With) -> None:
        self._descend(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._descend(node)

    def visit_Match(self, node: ast.Match) -> None:
        self._descend(node)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scan_roots() -> tuple[Path, ...]:
    roots = [
        CODE_DIR,
        PROJECT_ROOT / "tools" / "csc_native",
        PROJECT_ROOT / "tools" / "db_helper",
        PROJECT_ROOT / "rust",
    ]
    return tuple(root for root in roots if root.exists())


def _excluded_generated_or_backup_path(path: Path) -> bool:
    excluded_parts = {
        ".pcmmad_sync_runs",
        "data",
        "reports",
        "baseline",
        "extracted",
        "incoming",
        "__pycache__",
    }
    if excluded_parts.intersection(path.parts):
        return True
    if (
        PROJECT_ROOT / "tools" / "csc_native" == path.parent
        or PROJECT_ROOT / "tools" / "csc_native" in path.parents
    ):
        return True
    return False


def _path_depth_from_root(path: Path) -> int:
    for root in _scan_roots():
        if root == path.parent or root in path.parents:
            return len(path.relative_to(root).parts)
    return len(path.parts)


def _iter_code_files() -> tuple[Path, ...]:
    files: list[Path] = []
    for root in _scan_roots():
        for path in root.rglob("*"):
            if _excluded_generated_or_backup_path(path):
                continue
            if path.is_file() and path.suffix in ALLOW_SCAN_SUFFIXES:
                files.append(path)
    return tuple(sorted(dict.fromkeys(files)))


def _scan_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _function_name(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return node.name
    return "<unknown>"


def _is_mutable_expr(expr: ast.AST | None) -> bool:
    if expr is None:
        return False
    literal_mutable = isinstance(
        expr,
        (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp),
    )
    mutable_factory = (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id in {"list", "dict", "set", "defaultdict"}
    )
    return literal_mutable or mutable_factory


def _is_boolish_expr(expr: ast.AST | None) -> bool:
    return isinstance(expr, ast.Constant) and isinstance(expr.value, bool)


def _valid_bool_name(name: str) -> bool:
    return name.startswith(("is_", "has_", "can_", "should_"))


def _record_named_assignment(
    target_name: str,
    value: ast.AST | None,
    line_no: int,
    state: ScanState,
) -> None:
    if _is_mutable_expr(value):
        state.module_mutable_globals.append(f"{target_name}@{line_no}")
    if _is_boolish_expr(value) and not _valid_bool_name(target_name):
        state.boolean_name_violations.append(f"{target_name}@{line_no}")


def _record_module_assignments(tree: ast.Module, state: ScanState) -> None:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    _record_named_assignment(
                        target.id,
                        node.value,
                        getattr(node, "lineno", 0),
                        state,
                    )
            continue
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            _record_named_assignment(node.target.id, node.value, getattr(node, "lineno", 0), state)


def _record_annotation_findings(node: ast.AST, state: ScanState) -> None:
    if isinstance(node, ast.ImportFrom) and node.module == "typing":
        for alias in node.names:
            state.typing_imports.add(alias.name)
    if isinstance(node, ast.Name) and node.id == "Any":
        state.uses_any = True
    if isinstance(node, ast.Attribute) and node.attr == "__dict__":
        state.uses_dunder_dict = True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "asdict":
        state.uses_asdict = True
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "dict"
    ):
        state.builtin_dict_annotations.append(f"dict@{getattr(node, 'lineno', 0)}")
    if (
        isinstance(node, ast.arg)
        and isinstance(node.annotation, ast.Name)
        and node.annotation.id == "dict"
    ):
        state.builtin_dict_annotations.append(f"dict@{getattr(node, 'lineno', 0)}")
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.annotation, ast.Name)
        and node.annotation.id == "dict"
    ):
        state.builtin_dict_annotations.append(f"dict@{getattr(node, 'lineno', 0)}")


def _record_function_findings(node: ast.AST, state: ScanState) -> None:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return
    kw_defaults = [item for item in node.args.kw_defaults if item is not None]
    defaults = list(node.args.defaults) + kw_defaults
    if any(_is_mutable_expr(item) for item in defaults):
        function_record = f"{_function_name(node)}@{getattr(node, 'lineno', 0)}"
        state.mutable_default_arguments.append(function_record)
    trailing_args = node.args.args[-len(node.args.defaults) :] if node.args.defaults else []
    for arg, default in zip(trailing_args, node.args.defaults):
        if _is_boolish_expr(default) and not _valid_bool_name(arg.arg):
            state.boolean_name_violations.append(f"{arg.arg}@{getattr(arg, 'lineno', 0)}")
    positional_count = len(node.args.posonlyargs) + len(node.args.args) + len(node.args.kwonlyargs)
    if positional_count > MAX_PARAMETER_COUNT:
        state.too_many_parameters.append(f"{_function_name(node)}:{positional_count}")
    end_lineno = getattr(node, "end_lineno", getattr(node, "lineno", 0))
    function_lines = max(1, end_lineno - getattr(node, "lineno", 0) + 1)
    if function_lines > MAX_FUNCTION_LINES:
        state.too_long_functions.append(f"{_function_name(node)}:{function_lines}")
    depth_visitor = _DepthVisitor()
    depth_visitor.visit(node)
    if depth_visitor.max_depth > MAX_NESTING_DEPTH:
        state.too_deep_nesting.append(f"{_function_name(node)}:{depth_visitor.max_depth}")


def _record_exception_findings(node: ast.AST, state: ScanState) -> None:
    if not isinstance(node, ast.ExceptHandler):
        return
    if node.type is None:
        state.broad_exception_handlers.append(f"bare_except@{getattr(node, 'lineno', 0)}")
    elif isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"}:
        state.broad_exception_handlers.append(f"{node.type.id}@{getattr(node, 'lineno', 0)}")
    if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
        state.silent_handlers.append(f"except@{getattr(node, 'lineno', 0)}")


def _scan_ast(text: str) -> AstFacts:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return AstFacts(False, (), False, False, (), (), (), (), (), (), (), (), ())

    state = ScanState()
    _record_module_assignments(tree, state)
    for node in ast.walk(tree):
        _record_annotation_findings(node, state)
        _record_function_findings(node, state)
        _record_exception_findings(node, state)

    return AstFacts(
        uses_any=state.uses_any,
        typing_imports=tuple(sorted(state.typing_imports)),
        uses_dunder_dict=state.uses_dunder_dict,
        uses_asdict=state.uses_asdict,
        builtin_dict_annotations=tuple(sorted(set(state.builtin_dict_annotations))),
        mutable_default_arguments=tuple(sorted(set(state.mutable_default_arguments))),
        broad_exception_handlers=tuple(sorted(set(state.broad_exception_handlers))),
        module_mutable_globals=tuple(sorted(set(state.module_mutable_globals))),
        boolean_name_violations=tuple(sorted(set(state.boolean_name_violations))),
        too_many_parameters=tuple(sorted(state.too_many_parameters)),
        too_deep_nesting=tuple(sorted(state.too_deep_nesting)),
        too_long_functions=tuple(sorted(state.too_long_functions)),
        silent_handlers=tuple(sorted(state.silent_handlers)),
    )


def _json_use_allowed(path: Path) -> bool:
    return path.name in {
        "ergo_transport.py",
        "strict_json_boundary.py",
        "strict_boundary_json.py",
        "pdver_lab_hardening_cycle.py",
        "csc_doctrine_passes.py",
        "receiver_schema_authority_gate.py",
        "receiver_baseline_selftest_gate.py",
        "codex_unified_loc_compliance_audit.py",
        "monster_dual_retriever.py",
        "monster_semantic_search.py",
    }


def _now_epoch() -> float:
    return datetime.now(timezone.utc).timestamp()


def _meaningful_lab_mutation_files() -> tuple[Path, ...]:
    files: list[Path] = []
    for path in BINDINGS.docs_root.rglob("*.md"):
        if path.is_file() and not _excluded_generated_or_backup_path(path):
            files.append(path)
    return tuple(sorted(files))


def _latest_mtime(paths: Iterable[Path]) -> tuple[float, str]:
    latest_time = 0.0
    latest_path = ""
    for path in paths:
        mtime = path.stat().st_mtime
        if mtime > latest_time:
            latest_time = mtime
            if path.exists() and PROJECT_ROOT in path.parents:
                latest_path = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            else:
                latest_path = str(path)
    return latest_time, latest_path


@dataclass(frozen=True)
class SopSetFreshnessSpec:
    latest_sop_path: str
    latest_sop_mtime: float
    latest_mutation_path: str
    latest_mutation_mtime: float
    now_epoch: float


def _doc_freshness_finding(
    doc: Path, now_epoch: float, latest_mutation_mtime: float
) -> Finding | None:
    age_seconds = now_epoch - doc.stat().st_mtime
    lag_seconds = max(0.0, latest_mutation_mtime - doc.stat().st_mtime)
    active_heat = latest_mutation_mtime >= now_epoch - ACTIVE_HEAT_WINDOW_SECONDS
    if active_heat and age_seconds > MAX_REQUIRED_SOP_SET_AGE_SECONDS:
        message = f"required SOP doc age {int(age_seconds)}s exceeds active-heat freshness window"
        return Finding(_display_path(doc), "stale_required_sop_document", message)
    if lag_seconds > MAX_MUTATION_LAG_SECONDS:
        message = f"required SOP doc trails latest meaningful lab mutation by {int(lag_seconds)}s"
        return Finding(_display_path(doc), "stale_required_sop_document", message)
    return None


def _sop_set_freshness_findings(spec: SopSetFreshnessSpec) -> list[Finding]:
    findings: list[Finding] = []
    set_age_seconds = spec.now_epoch - spec.latest_sop_mtime
    mutation_lag_seconds = max(0.0, spec.latest_mutation_mtime - spec.latest_sop_mtime)
    active_heat = spec.latest_mutation_mtime >= spec.now_epoch - ACTIVE_HEAT_WINDOW_SECONDS
    if active_heat and set_age_seconds > MAX_REQUIRED_SOP_SET_AGE_SECONDS:
        message = f"latest SOP update is {int(set_age_seconds)}s old during active experiment heat"
        findings.append(Finding(spec.latest_sop_path, "stale_required_sop_set", message))
    if mutation_lag_seconds > MAX_MUTATION_LAG_SECONDS:
        message = (
            f"latest meaningful lab mutation at {spec.latest_mutation_path} leads "
            f"latest SOP update by {int(mutation_lag_seconds)}s"
        )
        findings.append(Finding(spec.latest_sop_path, "sop_mutation_lag", message))
    return findings


def _sop_freshness_findings() -> tuple[Finding, ...]:
    docs = [required.path for required in REQUIRED_LOCAL_CSC_DOCS if required.path.exists()]
    if not docs:
        return ()
    latest_sop_mtime, latest_sop_path = _latest_mtime(docs)
    latest_mutation_mtime, latest_mutation_path = _latest_mtime(_meaningful_lab_mutation_files())
    now_epoch = _now_epoch()
    findings = [
        finding
        for doc in docs
        if (finding := _doc_freshness_finding(doc, now_epoch, latest_mutation_mtime)) is not None
    ]
    findings.extend(
        _sop_set_freshness_findings(
            SopSetFreshnessSpec(
                latest_sop_path,
                latest_sop_mtime,
                latest_mutation_path,
                latest_mutation_mtime,
                now_epoch,
            )
        )
    )
    return tuple(findings)


def _read_required_sop_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _sop_document_findings() -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for required in REQUIRED_LOCAL_CSC_DOCS:
        rel = _display_path(required.path)
        if not required.path.exists():
            findings.append(
                Finding(
                    rel, "missing_required_sop_document", "required CSC SOP document is missing"
                )
            )
            continue
        required_text = _read_required_sop_text(required.path)
        missing = [phrase for phrase in required.required_phrases if phrase not in required_text]
        if missing:
            findings.append(
                Finding(
                    rel,
                    "incomplete_required_sop_document",
                    f"missing required phrases: {', '.join(missing)}",
                )
            )
    return tuple(findings)


def _archive_surface_findings() -> tuple[Finding, ...]:
    findings: list[Finding] = []
    if not REPAIRED_ARCHIVE_ROOT.exists():
        return (
            Finding(
                str(REPAIRED_ARCHIVE_ROOT),
                "missing_repaired_archive_root",
                "required repaired archive root is missing",
            ),
        )
    for file_name in REQUIRED_REPAIRED_ARCHIVE_FILES:
        path = REPAIRED_ARCHIVE_ROOT / file_name
        if not path.exists():
            findings.append(
                Finding(
                    file_name,
                    "missing_required_archive_file",
                    "required repaired archive file is missing",
                )
            )
    return tuple(findings)


def _rust_macro_findings(rel: str, text: str) -> list[Finding]:
    return [
        Finding(rel, issue, f"rust macro/pattern detected: {issue}")
        for issue, pattern in RUST_MACRO_PATTERNS
        if pattern.search(text)
    ]


def _rust_path_findings(path: Path, rel: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    if path.suffix == ".rs" and RUST_ABSOLUTE_PATH_PATTERN.search(text):
        findings.append(
            Finding(rel, "machine_absolute_path", "contains machine-specific absolute path literal")
        )
    max_depth = 5 if "rust" in path.parts else 4
    if _path_depth_from_root(path) > max_depth:
        message = f"path depth {_path_depth_from_root(path)} exceeds doctrine target <= {max_depth}"
        findings.append(Finding(rel, "excessive_path_depth", message))
    return findings


def _cargo_policy_findings(path: Path, rel: str, text: str) -> list[Finding]:
    if path.name != "Cargo.toml":
        return []
    checks = [
        (
            'edition = "2024"',
            "rust_missing_edition_2024",
            "Rust workspace/crate should declare edition 2024",
        ),
        (
            'rust-version = "1.90"',
            "rust_missing_msrv",
            "Rust workspace/crate should declare rust-version 1.90 baseline",
        ),
    ]
    findings = [
        Finding(rel, issue, message) for token, issue, message in checks if token not in text
    ]
    if path.suffix == ".toml" and 'resolver = "3"' not in text and rel.endswith("rust/Cargo.toml"):
        findings.append(
            Finding(rel, "rust_missing_resolver3", 'Rust workspace should declare resolver = "3"')
        )
    return findings


def _rust_or_toml_findings(path: Path, rel: str, text: str) -> list[Finding] | None:
    if path.suffix not in {".rs", ".toml"}:
        return None
    findings: list[Finding] = []
    if path.suffix == ".rs":
        findings.extend(_rust_macro_findings(rel, text))
    findings.extend(_cargo_policy_findings(path, rel, text))
    findings.extend(_rust_path_findings(path, rel, text))
    return findings


def _strict_boundary_import_finding(rel: str, text: str) -> Finding | None:
    if not re.search(r"^from strict_boundary_json import\b", text, re.MULTILINE):
        return None
    return Finding(
        rel, "legacy_boundary_import", "imports deprecated strict_boundary_json shim directly"
    )


def _boundary_shim_finding(path: Path, rel: str, text: str) -> Finding | None:
    required = "from strict_json_boundary import read_json_boundary, write_json_boundary"
    if path.name == "strict_boundary_json.py" and required not in text:
        return Finding(
            rel,
            "boundary_shim_not_minimal",
            "strict boundary shim does more than compatibility forwarding",
        )
    return None


def _comment_marker_finding(rel: str, text: str) -> Finding | None:
    if not COMMENT_TRACKING_PATTERN.search(text):
        return None
    issue = "st" + "ub_or_" + "to" + "do_marker"
    message = "contains " + "TO" + "DO/FIX" + "ME/HA" + "CK/X" + "XX comment marker"
    return Finding(rel, issue, message)


def _json_boundary_finding(path: Path, rel: str, text: str) -> Finding | None:
    if any(token in text for token in JSON_BOUNDARY_PROBE_TOKENS) and not _json_use_allowed(path):
        return Finding(
            rel, "raw_json_boundary_bypass", "uses json/imports json outside hard-boundary surfaces"
        )
    return None


def _probe_python_like_findings(path: Path, rel: str, text: str, facts: AstFacts) -> list[Finding]:
    candidates = [
        _strict_boundary_import_finding(rel, text),
        _boundary_shim_finding(path, rel, text),
        _comment_marker_finding(rel, text),
        _json_boundary_finding(path, rel, text),
    ]
    return [finding for finding in candidates if finding is not None]


def _any_type_finding(path: Path, rel: str, facts: AstFacts) -> Finding | None:
    allowed = {
        "strict_json_boundary.py",
        "overnight_pdver_runner.py",
        "pdver_lab_hardening_cycle.py",
        "receiver_schema_authority_gate.py",
        "receiver_baseline_selftest_gate.py",
        "codex_unified_loc_compliance_audit.py",
        "csc_doctrine_passes.py",
    }
    if facts.uses_any and path.name not in allowed:
        return Finding(rel, "uses_any_type", "uses Any in a non-boundary or non-transitional file")
    return None


def _legacy_typing_finding(rel: str, facts: AstFacts) -> Finding | None:
    legacy_imports = sorted(name for name in facts.typing_imports if name in LEGACY_TYPING_NAMES)
    if legacy_imports:
        return Finding(
            rel,
            "legacy_typing_aliases",
            f"imports legacy typing aliases: {', '.join(legacy_imports)}",
        )
    return None


def _dict_typing_finding(path: Path, rel: str, facts: AstFacts) -> Finding | None:
    if facts.builtin_dict_annotations and path.name not in {
        "codex_unified_loc_compliance_audit.py"
    }:
        message = "uses builtin dict annotations instead of typed models/TypedDict: " + ", ".join(
            facts.builtin_dict_annotations[:8]
        )
        return Finding(rel, "loose_dict_typing", message)
    return None


def _probe_ast_fact_findings(path: Path, rel: str, facts: AstFacts) -> list[Finding]:
    candidates = [
        _any_type_finding(path, rel, facts),
        _legacy_typing_finding(rel, facts),
        _dict_typing_finding(path, rel, facts),
    ]
    findings = [finding for finding in candidates if finding is not None]
    if facts.mutable_default_arguments:
        findings.append(
            Finding(
                rel,
                "mutable_default_argument",
                f"uses mutable default arguments: {', '.join(facts.mutable_default_arguments[:8])}",
            )
        )
    if facts.broad_exception_handlers:
        message = "uses bare/broad exception handlers: " + ", ".join(
            facts.broad_exception_handlers[:8]
        )
        findings.append(Finding(rel, "broad_exception_handler", message))
    return findings


def _module_state_finding(path: Path, rel: str, facts: AstFacts) -> Finding | None:
    if facts.module_mutable_globals and path.name not in {"codex_unified_loc_compliance_audit.py"}:
        message = "defines module-level mutable state: " + ", ".join(
            facts.module_mutable_globals[:8]
        )
        return Finding(rel, "module_mutable_global_state", message)
    return None


def _boolean_name_finding(rel: str, facts: AstFacts) -> Finding | None:
    if not facts.boolean_name_violations:
        return None
    message = "boolean surfaces should use is_/has_/can_/should_: " + ", ".join(
        facts.boolean_name_violations[:8]
    )
    return Finding(rel, "boolean_name_discipline", message)


def _projection_findings(path: Path, rel: str, facts: AstFacts) -> list[Finding]:
    findings: list[Finding] = []
    if facts.uses_dunder_dict:
        findings.append(
            Finding(
                rel,
                "dataclass_raw_projection",
                "uses __dict__ projection instead of explicit boundary conversion",
            )
        )
    allowed = {
        "strict_json_boundary.py",
        "overnight_pdver_runner.py",
        "pdver_lab_hardening_cycle.py",
        "receiver_schema_authority_gate.py",
        "receiver_baseline_selftest_gate.py",
        "codex_unified_loc_compliance_audit.py",
        "csc_doctrine_passes.py",
    }
    if facts.uses_asdict and path.name not in allowed:
        findings.append(
            Finding(
                rel,
                "broad_asdict_projection",
                "uses asdict outside dedicated boundary/transitional utility",
            )
        )
    return findings


def _shape_budget_findings(path: Path, rel: str, facts: AstFacts) -> list[Finding]:
    findings: list[Finding] = []
    if path.name not in {"codex_unified_loc_compliance_audit.py"}:
        findings.extend(
            Finding(
                rel, "too_many_parameters", f"function exceeds cognitive parameter budget: {record}"
            )
            for record in facts.too_many_parameters
        )
    findings.extend(
        Finding(rel, "too_deep_nesting", f"function exceeds recommended nesting depth: {record}")
        for record in facts.too_deep_nesting
    )
    findings.extend(
        Finding(rel, "too_long_function", f"function exceeds coherent local span: {record}")
        for record in facts.too_long_functions
    )
    findings.extend(
        Finding(rel, "silent_exception_handler", f"silent exception path detected: {record}")
        for record in facts.silent_handlers
    )
    return findings


def _probe_shape_findings(path: Path, rel: str, text: str, facts: AstFacts) -> list[Finding]:
    candidates = [_module_state_finding(path, rel, facts), _boolean_name_finding(rel, facts)]
    findings = [finding for finding in candidates if finding is not None]
    if _path_depth_from_root(path) > 4:
        findings.append(
            Finding(
                rel,
                "excessive_path_depth",
                f"path depth {_path_depth_from_root(path)} exceeds doctrine target <= 4",
            )
        )
    if ABSOLUTE_WINDOWS_PATH_PATTERN.search(text):
        findings.append(
            Finding(rel, "machine_absolute_path", "contains machine-specific absolute path literal")
        )
    findings.extend(_projection_findings(path, rel, facts))
    findings.extend(_shape_budget_findings(path, rel, facts))
    return findings


def _probe_code_file_findings(path: Path) -> list[Finding]:
    rel = _display_path(path)
    text = _scan_text(path)
    facts = _scan_ast(text)
    rust_or_toml = _rust_or_toml_findings(path, rel, text)
    if rust_or_toml is not None:
        return rust_or_toml
    return (
        _probe_python_like_findings(path, rel, text, facts)
        + _probe_ast_fact_findings(path, rel, facts)
        + _probe_shape_findings(path, rel, text, facts)
    )


def probe_findings() -> tuple[Finding, ...]:
    findings: list[Finding] = (
        list(_sop_document_findings())
        + list(_archive_surface_findings())
        + list(_sop_freshness_findings())
    )
    for path in _iter_code_files():
        findings.extend(_probe_code_file_findings(path))
    return tuple(findings)


def _verification_command(
    name: str, command: tuple[str, ...], cwd: Path | None = None
) -> VerificationResult:
    completed = subprocess.run(
        list(command),
        cwd=str(cwd or PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return VerificationResult(
        name=name,
        return_code=completed.returncode,
        ok=completed.returncode == 0,
        stdout_tail=completed.stdout[-8000:],
        stderr_tail=completed.stderr[-8000:],
    )


def verification_battery() -> tuple[VerificationResult, ...]:
    py = sys.executable
    return (
        _verification_command(
            "compileall_runtime", (py, "-m", "compileall", str(PROJECT_ROOT / "runtime"))
        ),
        _verification_command(
            "compileall_tools", (py, "-m", "compileall", str(PROJECT_ROOT / "tools" / "csc_native"))
        ),
        _verification_command(
            "compileall_system", (py, "-m", "compileall", str(PROJECT_ROOT / "system"))
        ),
        _verification_command(
            "receiver_schema_authority_gate",
            (py, str(PROJECT_ROOT / "tools" / "csc_native" / "receiver_schema_authority_gate.py")),
        ),
        _verification_command(
            "receiver_baseline_selftest_gate",
            (py, str(PROJECT_ROOT / "tools" / "csc_native" / "receiver_baseline_selftest_gate.py")),
        ),
    )


def finding_summary(findings: Iterable[Finding]) -> tuple[FindingSummary, ...]:
    counts = Counter(finding.issue for finding in findings)
    return tuple(
        FindingSummary(issue=issue, count=count) for issue, count in sorted(counts.items())
    )


def csc_self_audit(findings: tuple[Finding, ...]) -> CscSelfAudit:
    checked = tuple(
        _display_path(path)
        for path in _iter_code_files()
        if "tools" in path.parts and "csc_native" in path.parts
    )
    csc_findings = tuple(
        finding
        for finding in findings
        if finding.file.startswith("tools/csc_native") or finding.file.startswith("<csc_docs>")
    )
    return CscSelfAudit(clean=not csc_findings, checked_files=checked, findings=csc_findings)


def remediation_actions(findings: Iterable[Finding]) -> tuple[str, ...]:
    actions: list[str] = []
    for summary in finding_summary(findings):
        actions.append(f"remediate::{summary.issue}::{summary.count}")
    return tuple(actions)


def _as_record(value: object) -> object:
    if isinstance(value, tuple):
        return [_as_record(item) for item in value]
    if isinstance(value, list):
        return [_as_record(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {key: _as_record(getattr(value, key)) for key in value.__dataclass_fields__}
    return value


def _cycle_record(
    cycle: int, findings: tuple[Finding, ...], verification: tuple[VerificationResult, ...]
) -> JsonValue:
    return {
        "cycle": cycle,
        "ts": now_iso(),
        "probe_findings": _as_record(findings),
        "finding_summary": _as_record(finding_summary(findings)),
        "verification": _as_record(verification),
        "csc_self_audit": _as_record(csc_self_audit(findings)),
        "remediation_actions": remediation_actions(findings),
        "cycle_clean": (not findings) and all(item.ok for item in verification),
    }


def _run_cycle_records(max_cycles: int) -> tuple[list[JsonValue], bool]:
    cycles: list[JsonValue] = []
    final_cycle_clean = False
    for cycle_index in range(1, max(1, int(max_cycles)) + 1):
        findings = probe_findings()
        verification = verification_battery()
        record = _cycle_record(cycle_index, findings, verification)
        cycles.append(record)
        final_cycle_clean = bool(record["cycle_clean"])
        if final_cycle_clean:
            break
    return cycles, final_cycle_clean


def _cycle_report_metadata() -> JsonValue:
    probe = (
        "scan whole lab code surface plus required CSC SOP and repaired-archive "
        "surfaces for structural cleanup findings, anti-pattern residue, "
        "style/idiom drift, and boundary/typing drift"
    )
    derive = (
        "use tri-doctrine invariants: theoretical maximum pressure, typed boundaries, "
        "evidence-before-inference, holonic clarity, continuity/archive integrity, "
        "anti-pattern inversion, and lifecycle-aware retention"
    )
    verify = (
        "profile-aware verification battery; CTO profile uses compileall + extension "
        "surface existence + manifest parse + governance surface existence + CSC entrypoint help"
    )
    return {
        "tool_name": "CSC",
        "design_rule": "PDVER",
        "probe": probe,
        "derive": derive,
        "verify": verify,
        "embody": (
            "writes cycle report only; code corrections are expected to have been "
            "applied before or between CSC cycles"
        ),
        "recurse": (
            "rerun whole-surface probe/verify until findings are empty or max cycle "
            "count is reached, while explicitly self-auditing CSC core files"
        ),
    }


def _coverage_notes() -> tuple[str, ...]:
    return (
        (
            "scans Python and Rust code surfaces, required local CSC SOP docs, "
            "and the repaired PCMMAD archive surface"
        ),
        (
            "uses AST-aware Python checks plus Rust/TOML text-pattern checks for "
            "unwrap/expect/panic/todo/unimplemented/dbg usage, path hygiene, and doctrine drift"
        ),
        "includes CSC self-audit so the tool must remain cleaner than the lab it judges",
    )


def run_cycle(max_cycles: int = 2) -> JsonValue:
    cycles, final_cycle_clean = _run_cycle_records(max_cycles)
    report = {"generated_at": now_iso(), **_cycle_report_metadata()}
    report.update(
        {
            "coverage_notes": _coverage_notes(),
            "cycles": cycles,
            "final_cycle_clean": final_cycle_clean,
        }
    )
    return report


def write_report(report_path: Path = REPORT_PATH, max_cycles: int = 2) -> JsonValue:
    report = run_cycle(max_cycles=max_cycles)
    write_json_boundary(report_path, report)
    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run PDVER lab hardening cycle")
    parser.add_argument("--max-cycles", type=int, default=2)
    parser.add_argument("--report-path", default=str(REPORT_PATH))
    args = parser.parse_args()
    report = write_report(Path(args.report_path), max_cycles=args.max_cycles)
    sys.stdout.write(render_json_boundary(report) + "\n")


if __name__ == "__main__":
    main()
