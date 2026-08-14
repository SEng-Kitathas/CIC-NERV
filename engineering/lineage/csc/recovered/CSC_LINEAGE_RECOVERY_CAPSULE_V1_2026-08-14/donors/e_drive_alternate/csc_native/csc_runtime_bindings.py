"""CSC runtime binding helpers for locating project roots, reports, and execution surfaces."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve()
CSC_NATIVE_ROOT = HERE.parent
TOOLS_ROOT = CSC_NATIVE_ROOT.parent
PROJECT_ROOT = TOOLS_ROOT.parent


@dataclass(frozen=True)
class CscRuntimeBindings:
    target_project_root: Path
    target_code_root: Path
    docs_root: Path
    output_root: Path
    holon_profile: str


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).resolve() if value else default.resolve()


def get_bindings() -> CscRuntimeBindings:
    target_project_root = _env_path("CSC_TARGET_PROJECT_ROOT", PROJECT_ROOT)
    docs_root = _env_path("CSC_DOCS_ROOT", target_project_root / "docs" / "csc_sop")
    output_root = _env_path("CSC_OUTPUT_ROOT", target_project_root / "data" / "csc_native")
    holon_profile = os.environ.get("CSC_HOLON_PROFILE") or target_project_root.name
    return CscRuntimeBindings(
        target_project_root=target_project_root,
        target_code_root=target_project_root.resolve(),
        docs_root=docs_root,
        output_root=output_root,
        holon_profile=holon_profile,
    )
