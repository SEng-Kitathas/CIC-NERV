"""Universal CSC runner that executes hardening, doctrine, freshness, and holonic checks."""

from __future__ import annotations

import argparse
from collections.abc import MutableMapping
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
CSC_NATIVE_ROOT = HERE.parent
CSC_ENTRYPOINT = CSC_NATIVE_ROOT / "code_slop_cleanup_csc.py"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local Ergo-Light CSC against a target project root"
    )
    parser.add_argument("--target-project-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--docs-root", default=None)
    parser.add_argument("--max-cycles", type=int, default=2)
    return parser.parse_args()


def _resolve_docs_root(args: argparse.Namespace, target_project_root: Path) -> Path:
    if args.docs_root:
        return Path(args.docs_root).resolve()
    return (target_project_root / "docs" / "csc_sop").resolve()


def _runner_env(
    target_project_root: Path, output_root: Path, docs_root: Path
) -> MutableMapping[str, str]:
    env = os.environ.copy()
    env["CSC_TARGET_PROJECT_ROOT"] = str(target_project_root)
    env["CSC_DOCS_ROOT"] = str(docs_root)
    env["CSC_OUTPUT_ROOT"] = str(output_root)
    env["CSC_HOLON_PROFILE"] = target_project_root.name
    return env


def _runner_command(max_cycles: int, output_root: Path) -> list[str]:
    return [
        sys.executable,
        str(CSC_ENTRYPOINT),
        "--max-cycles",
        str(max_cycles),
        "--output-dir",
        str(output_root),
        "--report-path",
        str(output_root / "CSC_EVENT_REPORT.json"),
    ]


def main() -> None:
    args = _parse_args()
    target_project_root = Path(args.target_project_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    docs_root = _resolve_docs_root(args, target_project_root)
    proc = subprocess.run(
        _runner_command(args.max_cycles, output_root),
        cwd=str(CSC_NATIVE_ROOT),
        env=_runner_env(target_project_root, output_root, docs_root),
        check=False,
    )
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
