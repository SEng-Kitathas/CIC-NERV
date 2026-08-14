"""CSC gate command wrapper for running native checks and emitting gate result envelopes."""

from __future__ import annotations

import argparse
from pathlib import Path

from strict_json_boundary import read_json_boundary


def main() -> None:
    parser = argparse.ArgumentParser(description="Require CSC-clean state before proceeding")
    parser.add_argument("--report-path", required=True)
    args = parser.parse_args()

    report_path = Path(args.report_path)
    raw = read_json_boundary(report_path)
    if not isinstance(raw, dict):
        raise TypeError(f"expected object at {report_path}")

    core_clean = bool(raw.get("core_cycle", {}).get("final_cycle_clean", False))
    sop_clean = bool(raw.get("sop_availability", {}).get("clean", False))
    freshness_clean = bool(raw.get("sop_freshness", {}).get("clean", False))
    holonic_clean = bool(raw.get("holonic_audit", {}).get("clean", False))
    coverage_clean = bool(raw.get("doctrine_coverage", {}).get("clean", False))

    if not all((core_clean, sop_clean, freshness_clean, holonic_clean, coverage_clean)):
        raise SystemExit("CSC gate blocked: one or more CSC surfaces are not clean")


if __name__ == "__main__":
    main()
