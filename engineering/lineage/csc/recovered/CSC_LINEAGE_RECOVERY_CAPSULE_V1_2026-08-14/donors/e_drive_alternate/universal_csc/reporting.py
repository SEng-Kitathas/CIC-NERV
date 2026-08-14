"""Report generation for universal CSC/PDVER finalizer."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .json_io import write_json, write_text
from .model import ClaimPermission, GateResult, to_jsonable

CLAIMS = {
    "reply_claim_clean": (
        "project_contract",
        "active_source_inventory",
        "doctrine_surface",
        "doctrine_coverage",
        "code_shape_loc",
        "style_quality",
        "semantic_footgun_dataflow",
        "claim_governor",
    ),
    "runtime_working": (
        "project_contract",
        "route_runtime_trace",
        "process_launcher_runtime",
        "security_config",
        "tests_resilience",
        "project_local_finalizer",
    ),
    "promotion_clean": (
        "project_contract",
        "active_source_inventory",
        "doctrine_surface",
        "doctrine_coverage",
        "code_shape_loc",
        "style_quality",
        "semantic_footgun_dataflow",
        "schema_contract_authority",
        "tests_resilience",
        "report_freshness_lineage",
        "project_local_finalizer",
        "claim_governor",
    ),
    "package_clean": (
        "project_contract",
        "active_source_inventory",
        "report_freshness_lineage",
        "claim_governor",
    ),
}


def _claim_permissions(gates: list[GateResult]) -> list[ClaimPermission]:
    by_id = {gate.gate_id: gate for gate in gates}
    out = []
    for claim, required in CLAIMS.items():
        blocking = tuple(g for g in required if g not in by_id or not by_id[g].clean)
        status = "blocked" if blocking else "allowed"
        out.append(ClaimPermission(claim, status, required, blocking))  # type: ignore[arg-type]
    return out


def _summary(gates: list[GateResult]) -> dict[str, Any]:
    failing = [gate.gate_id for gate in gates if not gate.clean]
    return {
        "gate_count": len(gates),
        "passing_gates": sum(1 for gate in gates if gate.clean),
        "failing_gates": len(failing),
        "failing_gate_ids": failing,
    }


def write_reports(
    project_root: Path, discovery: dict[str, Any], gates: list[GateResult]
) -> dict[str, Any]:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    paths = _report_paths(project_root, now)
    payload = _payload(project_root, discovery, gates, now)
    trace = _trace(project_root, discovery, gates, now)
    claim_payload = _claim_payload(payload, now)
    _write_report_set(paths, payload, trace, claim_payload)
    return payload


def _report_paths(project_root: Path, now: str) -> dict[str, Path]:
    run_root = project_root / "data" / "csc_runs" / ("universal_" + now.replace(":", "-"))
    report_root = project_root / "reports"
    run_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)
    return {
        "json": report_root / "UNIVERSAL_CSC_FINALIZER_REPORT.json",
        "md": report_root / "UNIVERSAL_CSC_FINALIZER_REPORT.md",
        "trace": report_root / "UNIVERSAL_CSC_TRACE_MATRIX.json",
        "claims": report_root / "UNIVERSAL_CSC_CLAIM_GOVERNOR.json",
        "run_json": run_root / "UNIVERSAL_CSC_FINALIZER_REPORT.json",
        "run_md": run_root / "UNIVERSAL_CSC_FINALIZER_REPORT.md",
    }


def _payload(
    project_root: Path, discovery: dict[str, Any], gates: list[GateResult], now: str
) -> dict[str, Any]:
    claims = _claim_permissions(gates)
    final_clean = _final_clean(claims)
    return {
        "created_at_utc": now,
        "project_root": str(project_root),
        "pdver_algorithm": "PROBE_DERIVE_VERIFY_EMBODY_RECURSE",
        "pdver_levels": _pdver_levels(),
        "final_clean": final_clean,
        "required_action": "none" if final_clean else "recurse_remediate_and_rerun",
        "summary": _summary(gates),
        "discovery_summary": _discovery_summary(discovery),
        "gates": [to_jsonable(gate) for gate in gates],
        "claims": [to_jsonable(claim) for claim in claims],
    }


def _final_clean(claims: list[ClaimPermission]) -> bool:
    return all(
        claim.status == "allowed"
        for claim in claims
        if claim.claim in {"reply_claim_clean", "promotion_clean"}
    )


def _pdver_levels() -> dict[str, str]:
    return {
        "nano": "line/function/script/route/schema/payload invariant",
        "micro": "single gate/tool/module/subsystem",
        "meso": "cross-surface consistency",
        "macro": "project-level claim governance",
    }


def _discovery_summary(discovery: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "project_root",
        "active_roots",
        "evidence_roots",
        "file_count",
        "has_reports",
        "has_data",
        "has_tests",
        "has_docs_or_spec",
        "profile",
    ]
    return {key: discovery.get(key) for key in keys}


def _trace(
    project_root: Path, discovery: dict[str, Any], gates: list[GateResult], now: str
) -> dict[str, Any]:
    return {
        "created_at_utc": now,
        "project_root": str(project_root),
        "gate_to_pdver": {gate.gate_id: _gate_trace(gate) for gate in gates},
        "discovery": discovery,
    }


def _gate_trace(gate: GateResult) -> dict[str, str]:
    return {
        "phase": gate.pdver_phase,
        "level": gate.level,
        "family": gate.family,
        "status": gate.status,
    }


def _claim_payload(payload: dict[str, Any], now: str) -> dict[str, Any]:
    return {
        "created_at_utc": now,
        "final_clean": payload["final_clean"],
        "claims": payload["claims"],
    }


def _write_report_set(
    paths: dict[str, Path], payload: dict[str, Any], trace: dict[str, Any], claims: dict[str, Any]
) -> None:
    markdown = _markdown(payload)
    write_json(paths["json"], payload)
    write_json(paths["trace"], trace)
    write_json(paths["claims"], claims)
    write_json(paths["run_json"], payload)
    write_text(paths["md"], markdown)
    write_text(paths["run_md"], markdown)


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Universal CSC Finalizer Report",
        "",
        f"Created: {payload['created_at_utc']}",
        f"Project: `{payload['project_root']}`",
        f"Final clean: `{payload['final_clean']}`",
        f"Required action: `{payload['required_action']}`",
        "",
        "## Gates",
        "",
    ]
    for gate in payload["gates"]:
        lines.append(
            f"- `{gate['gate_id']}`: `{gate['status']}` clean={gate.get('clean', 'n/a')} family={gate['family']} level={gate['level']} phase={gate['pdver_phase']}"
        )
        for finding in gate.get("findings", [])[:8]:
            lines.append(
                f"  - {finding['severity']} blocking={finding['blocking']}: {finding['evidence']} -> {finding['remediation']}"
            )
    lines.extend(["", "## Claims", ""])
    for claim in payload["claims"]:
        lines.append(
            f"- `{claim['claim']}`: `{claim['status']}` blocking={claim.get('blocking_gates', [])}"
        )
    return "\n".join(lines) + "\n"
