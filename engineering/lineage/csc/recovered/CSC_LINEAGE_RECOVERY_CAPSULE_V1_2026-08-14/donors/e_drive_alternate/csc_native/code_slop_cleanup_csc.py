"""Code cleanup CSC helper for scanning and reporting broad slop-pattern remediation targets."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import TypeAlias

from codex_unified_loc_compliance_audit import run_loc_audit
from csc_doctrine_passes import write_all_outputs
from csc_runtime_bindings import get_bindings
from guide_quality_audit import run_audit
from pdver_lab_hardening_cycle import REPORT_PATH as PDVER_REPORT_PATH, run_cycle
from strict_json_boundary import write_json_boundary

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | Mapping[str, "JsonValue"]
)

BINDINGS = get_bindings()
DEFAULT_REPORT_PATH = BINDINGS.output_root / "CSC_EVENT_REPORT.json"
DEFAULT_OUTPUT_DIR = BINDINGS.output_root


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Code-Slop Cleanup (CSC) event runner")
    parser.add_argument("--max-cycles", type=int, default=3)
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def _prepare_output_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    report_path = Path(args.report_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    return report_path, output_dir


def _run_expanded_audits(output_dir: Path) -> tuple[JsonValue, JsonValue, JsonValue]:
    doctrine_outputs = write_all_outputs(output_dir)
    loc_compliance = run_loc_audit(
        BINDINGS.target_project_root,
        output_dir / "LOC_COMPLIANCE_AUDIT.json",
        output_dir / "LOC_COMPLIANCE_AUDIT.md",
    )
    guide_quality = run_audit(
        BINDINGS.target_project_root,
        output_dir / "GUIDE_QUALITY_AUDIT.json",
        output_dir / "GUIDE_QUALITY_AUDIT.md",
        line_length=100,
    )
    return doctrine_outputs, loc_compliance, guide_quality


def _event_report(
    core_cycle: JsonValue,
    doctrine_outputs: Mapping[str, JsonValue],
    loc_compliance: JsonValue,
    guide_quality: JsonValue,
) -> JsonValue:
    return {
        "tool_name": "CSC",
        "core_cycle": core_cycle,
        "tri_doctrine_authority": doctrine_outputs["tri_doctrine_authority"],
        "sop_availability": doctrine_outputs["sop_availability"],
        "sop_freshness": doctrine_outputs["sop_freshness"],
        "antipattern_inversion": doctrine_outputs["antipattern_inversion"],
        "holonic_audit": doctrine_outputs["holonic_audit"],
        "doctrine_coverage": doctrine_outputs["doctrine_coverage"],
        "loc_compliance": loc_compliance,
        "guide_quality": guide_quality,
    }


def main() -> None:
    args = _parse_args()
    report_path, output_dir = _prepare_output_paths(args)
    core_cycle = run_cycle(max_cycles=args.max_cycles)
    write_json_boundary(PDVER_REPORT_PATH, core_cycle)
    doctrine_outputs, loc_compliance, guide_quality = _run_expanded_audits(output_dir)
    write_json_boundary(
        report_path,
        _event_report(core_cycle, doctrine_outputs, loc_compliance, guide_quality),
    )


if __name__ == "__main__":
    main()
