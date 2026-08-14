"""Project discovery for the universal CSC/PDVER finalizer."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from .config import ProjectProfile, load_profile

TEXT_SUFFIXES = frozenset(
    {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ps1", ".cmd", ".bat"}
)


def _sha(path: Path) -> str | None:
    try:
        if path.stat().st_size <= 50_000_000:
            return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None
    return None


def _mtime(path: Path) -> str | None:
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime))
    except OSError:
        return None


def _file_record(project_root: Path, path: Path, classification: str) -> dict[str, Any]:
    stat = path.stat()
    return {
        "rel": str(path.relative_to(project_root)).replace("\\", "/"),
        "classification": classification,
        "suffix": path.suffix.lower(),
        "bytes": stat.st_size,
        "mtime_utc": _mtime(path),
        "sha256": _sha(path),
    }


def _classify(project_root: Path, path: Path, profile: ProjectProfile) -> str:
    parts = path.relative_to(project_root).parts
    first = parts[0] if parts else ""
    if path.name.upper() == "PCMMAD_LOCAL_ENV.CMD":
        return "local_config"
    if first in profile.evidence_roots:
        return "generated_evidence"
    if first in profile.doctrine_roots:
        return "doctrine"
    if first in profile.active_roots:
        return "active_source"
    if path.suffix.lower() in {".cmd", ".bat", ".ps1"}:
        return "launcher"
    return "root_misc"


def discover(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    profile = load_profile(project_root)
    files, dirs = _walk_project(project_root, profile)
    return _discovery_payload(project_root, profile, files, dirs)


def _walk_project(
    project_root: Path, profile: ProjectProfile
) -> tuple[list[dict[str, Any]], list[str]]:
    files: list[dict[str, Any]] = []
    dirs: list[str] = []
    for path in sorted(project_root.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if path.is_dir():
            dirs.append(str(path.relative_to(project_root)).replace("\\", "/"))
        elif path.is_file():
            files.append(_file_record(project_root, path, _classify(project_root, path, profile)))
    return files, dirs


def _discovery_payload(
    project_root: Path, profile: ProjectProfile, files: list[dict[str, Any]], dirs: list[str]
) -> dict[str, Any]:
    return {
        "project_root": str(project_root),
        "canonical_name": project_root.name,
        "profile": _profile_payload(profile),
        "active_roots": _existing(project_root, profile.active_roots),
        "doctrine_roots": _existing(project_root, profile.doctrine_roots),
        "evidence_roots": _existing(project_root, profile.evidence_roots),
        "directories": dirs,
        "files": files,
        "file_count": len(files),
        "gate_scripts": _gate_scripts(files),
        "has_reports": (project_root / "reports").exists(),
        "has_data": (project_root / "data").exists(),
        "has_tests": (project_root / "tests").exists(),
        "has_docs_or_spec": any((project_root / root).exists() for root in profile.doctrine_roots),
    }


def _existing(project_root: Path, roots: tuple[str, ...]) -> list[str]:
    return [name for name in roots if (project_root / name).exists()]


def _gate_scripts(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in files
        if item["rel"].startswith("tools/csc_native/") and item["suffix"] == ".py"
    ]


def _profile_payload(profile: ProjectProfile) -> dict[str, Any]:
    return {
        "project_name": profile.project_name,
        "active_roots": list(profile.active_roots),
        "doctrine_roots": list(profile.doctrine_roots),
        "evidence_roots": list(profile.evidence_roots),
        "command_gates": [gate.id for gate in profile.command_gates],
        "report_gates": [gate.id for gate in profile.report_gates],
        "sidecars": [sidecar.id for sidecar in profile.sidecars],
    }
