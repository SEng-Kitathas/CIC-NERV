from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .config import ProjectProfile

IGNORED_NAMES = {
    '.git', '.venv', '.tox', '.nox', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    '__pycache__', 'build', 'dist',
}


def discover(project_root: Path, profile: ProjectProfile) -> dict[str, Any]:
    root = project_root.resolve()
    files: dict[str, dict[str, Any]] = {}
    for root_name in profile.source_roots:
        _walk_declared_root(root, root_name, 'active_source', files)
    for root_name in profile.doctrine_roots:
        _walk_declared_root(root, root_name, 'doctrine', files)

    anchor = root / profile.lineage_anchor
    if anchor.is_file():
        rel = anchor.relative_to(root)
        files[rel.as_posix()] = _record(anchor, rel, 'lineage_anchor')

    return {
        'project_root': str(root),
        'project_name': profile.project_name,
        'file_count': len(files),
        'files': [files[key] for key in sorted(files)],
        'source_roots_present': [name for name in profile.source_roots if (root / name).exists()],
        'doctrine_roots_present': [name for name in profile.doctrine_roots if (root / name).exists()],
        'lineage_anchor_present': anchor.is_file(),
    }


def _walk_declared_root(
    project_root: Path,
    root_name: str,
    classification: str,
    files: dict[str, dict[str, Any]],
) -> None:
    declared = project_root / root_name
    if not declared.exists():
        return
    if declared.is_file():
        rel = declared.relative_to(project_root)
        files[rel.as_posix()] = _record(declared, rel, classification)
        return
    for path in sorted(declared.rglob('*')):
        rel = path.relative_to(project_root)
        if any(part in IGNORED_NAMES or part.endswith('.egg-info') for part in rel.parts):
            continue
        if path.is_file():
            files[rel.as_posix()] = _record(path, rel, classification)


def _record(path: Path, rel: Path, classification: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        'rel': rel.as_posix(),
        'classification': classification,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'suffix': path.suffix.lower(),
    }
