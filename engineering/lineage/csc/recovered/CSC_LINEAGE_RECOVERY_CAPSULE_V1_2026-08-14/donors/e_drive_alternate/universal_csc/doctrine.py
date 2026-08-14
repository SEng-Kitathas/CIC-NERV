"""Doctrine extraction and coverage mapping for universal CSC."""

from __future__ import annotations

import hashlib
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .json_io import write_json

TEXT_SUFFIXES = {".md", ".txt", ".rst", ".json", ".yaml", ".yml"}
REQ_RE = re.compile(
    r"\b(must|shall|should|required|requires|never|always|forbid|forbidden|block|blocking|"
    r"blocker|gate|finalizer|claim|clean|verify|audit|test|contract|invariant|canonical|"
    r"style|quality|hygiene|PDVER|probe|derive|embody|recurse)\b",
    re.I,
)
FAMILY_PATTERNS = {
    "doctrine_contract": r"doctrine|sop|protocol|shall|must|never|always|invariant|contract",
    "style_quality": r"style|quality|hygiene|readability|maintainability|clean code|idiomatic|naming|documentation",
    "structure_architecture": r"architecture|structure|layout|module|boundary|adapter|interface|canonical|source root",
    "gate_finalizer": r"gate|finalizer|claim|final_clean|blocker|blocking|required_action|runner|pipeline",
    "pdver": r"pdver|probe|derive|verify|embody|recurse",
    "runtime_route": r"runtime|route|health|port|listener|restart|launcher|ngrok|browser|sidecar",
    "schema_contract": r"schema|contract|api|payload|capability|authority|openapi",
    "semantic_dataflow": r"semantic|footgun|dataflow|stale|silent|fallback|global state|mutation",
    "security_config": r"secret|credential|token|api key|auth|security|local config",
    "testing_resilience": r"test|smoke|negative|resilience|coverage|failure|parity|selftest",
    "evidence_lineage": r"report|freshness|stale|lineage|sha256|hash|evidence|trace|ledger|manifest",
}
FAMILY_RE = {key: re.compile(value, re.I) for key, value in FAMILY_PATTERNS.items()}


def build_doctrine_coverage(project_root: Path, doctrine_roots: list[str]) -> dict[str, Any]:
    files = _doctrine_files(project_root, doctrine_roots)
    clauses = [clause for path in files for clause in _clauses(path, project_root)]
    families = Counter(family for clause in clauses for family in clause["families"])
    report = {
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project_root": str(project_root),
        "doctrine_roots": doctrine_roots,
        "doctrine_file_count": len(files),
        "requirement_clause_count": len(clauses),
        "family_counts": dict(families.most_common()),
        "clean": bool(files and clauses and families),
        "clauses": clauses[:2500],
        "files": [_file_record(path, project_root) for path in files],
    }
    write_json(project_root / "reports" / "UNIVERSAL_CSC_DOCTRINE_COVERAGE.json", report)
    return report


def _doctrine_files(project_root: Path, doctrine_roots: list[str]) -> list[Path]:
    files: list[Path] = []
    for root_name in doctrine_roots:
        root = project_root / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                files.append(path)
    return sorted(files)


def _clauses(path: Path, project_root: Path) -> list[dict[str, Any]]:
    text = _read_text(path)
    clauses: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        clean = re.sub(r"\s+", " ", line).strip()
        if 30 <= len(clean) <= 900 and REQ_RE.search(clean):
            families = _families(clean)
            clauses.append(
                {
                    "source": str(path.relative_to(project_root)).replace("\\", "/"),
                    "line": number,
                    "text": clean[:900],
                    "families": families,
                }
            )
        if len(clauses) >= 800:
            break
    return clauses


def _families(text: str) -> list[str]:
    hits = [key for key, regex in FAMILY_RE.items() if regex.search(text)]
    return hits or ["unclassified_doctrine"]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _file_record(path: Path, project_root: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "rel": str(path.relative_to(project_root)).replace("\\", "/"),
        "bytes": stat.st_size,
        "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)),
        "sha256": _sha(path),
    }


def _sha(path: Path) -> str | None:
    try:
        if path.stat().st_size > 25_000_000:
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None
