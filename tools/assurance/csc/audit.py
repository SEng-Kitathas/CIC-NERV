from __future__ import annotations

from pathlib import Path

from .config import load_profile
from .discovery import discover
from .gates import run_all
from .reporting import build_report, write_report


def run_audit(project_root: Path, profile_path: Path, output_root: Path) -> tuple[Path, bool]:
    profile = load_profile(profile_path)
    discovery = discover(project_root, profile)
    gates = run_all(project_root, profile, discovery)
    report = build_report(project_root, profile_path, profile, gates)
    return write_report(report, output_root), report.final_clean
