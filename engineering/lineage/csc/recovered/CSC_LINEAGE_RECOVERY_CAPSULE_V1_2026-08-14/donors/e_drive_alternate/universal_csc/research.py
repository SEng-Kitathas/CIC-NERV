"""Research/evidence synthesis plane for universal CSC."""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .json_io import write_json, write_text

PASS5 = "UNIVERSAL_CSC_PASS5_FAST_PATH_ONLY_ALL_DRIVES_LEDGER.json"
PASS6 = "UNIVERSAL_CSC_PASS6_DEEP_EXTRACT_SYNTHESIS.json"
PASS7 = "UNIVERSAL_CSC_PASS7_FINAL_ENFORCEMENT_DELTA_SYNTHESIS.json"


def write_research_synthesis(
    project_root: Path,
    pass5: Path | None = None,
    pass6: Path | None = None,
    pass7: Path | None = None,
) -> dict[str, Any]:
    inputs = _input_paths(project_root, pass5, pass6, pass7)
    loaded = {name: _load_json(path) for name, path in inputs.items()}
    payload = _payload(project_root, inputs, loaded)
    paths = _output_paths(project_root)
    _write_outputs(paths, payload)
    return payload


def _input_paths(
    project_root: Path, pass5: Path | None, pass6: Path | None, pass7: Path | None
) -> dict[str, Path]:
    reports = project_root / "reports"
    return {
        "pass5_path_ledger": pass5 or reports / PASS5,
        "pass6_deep_extract": pass6 or reports / PASS6,
        "pass7_delta_synthesis": pass7 or reports / PASS7,
    }


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _payload(
    project_root: Path, inputs: dict[str, Path], loaded: dict[str, dict[str, Any] | None]
) -> dict[str, Any]:
    missing = [name for name, value in loaded.items() if value is None]
    return {
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project_root": str(project_root),
        "mode": "UNIVERSAL_CSC_RESEARCH_SYNTHESIS",
        "clean": not missing,
        "missing_inputs": missing,
        "input_paths": {name: str(path) for name, path in inputs.items()},
        "source_exhaustion": _source_exhaustion(loaded),
        "aggregate_signals": _aggregate_signals(loaded),
        "enforcement_deltas": _deltas(loaded),
        "pending_surfaces": _pending(loaded),
    }


def _source_exhaustion(loaded: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    pass5 = loaded.get("pass5_path_ledger") or {}
    pass6 = loaded.get("pass6_deep_extract") or {}
    pass7 = loaded.get("pass7_delta_synthesis") or {}
    return {
        "pass5_coverage": pass5.get("coverage"),
        "pass6_counts": pass6.get("counts"),
        "pass7_assessment": pass7.get("source_material_exhaustion_assessment"),
    }


def _aggregate_signals(loaded: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    categories: Counter[str] = Counter()
    terms: Counter[str] = Counter()
    for source in loaded.values():
        if not source:
            continue
        _merge_counter(categories, source, ("aggregates", "category_counts"))
        _merge_counter(categories, source, ("aggregate_signals", "category_counts"))
        _merge_counter(terms, source, ("aggregates", "term_counts"))
        _merge_counter(terms, source, ("aggregate_signals", "term_counts_top"))
    return {
        "category_counts": dict(categories.most_common()),
        "term_counts": dict(terms.most_common(80)),
    }


def _merge_counter(counter: Counter[str], source: dict[str, Any], path: tuple[str, str]) -> None:
    value: Any = source
    for part in path:
        if not isinstance(value, dict):
            return
        value = value.get(part)
    if isinstance(value, dict):
        counter.update(
            {str(key): int(count) for key, count in value.items() if isinstance(count, int)}
        )


def _deltas(loaded: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    pass7 = loaded.get("pass7_delta_synthesis") or {}
    deltas = pass7.get("final_enforcement_deltas")
    if not isinstance(deltas, list):
        return []
    return [item for item in deltas if isinstance(item, dict)]


def _pending(loaded: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    pass6 = loaded.get("pass6_deep_extract") or {}
    pass7 = loaded.get("pass7_delta_synthesis") or {}
    return {
        "pass6_pending_records": pass6.get("pending_records", [])[:120],
        "pass7_pending_extraction_surfaces": pass7.get("pending_extraction_surfaces"),
    }


def _output_paths(project_root: Path) -> dict[str, Path]:
    reports = project_root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    return {
        "json": reports / "UNIVERSAL_CSC_RESEARCH_SYNTHESIS.json",
        "md": reports / "UNIVERSAL_CSC_RESEARCH_SYNTHESIS.md",
    }


def _write_outputs(paths: dict[str, Path], payload: dict[str, Any]) -> None:
    write_json(paths["json"], payload)
    write_text(paths["md"], _markdown(payload))


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Universal CSC Research Synthesis",
        "",
        f"Created: {payload['created_at_utc']}",
        f"Clean: `{payload['clean']}`",
        "",
    ]
    lines.extend(_section("Missing inputs", payload.get("missing_inputs", [])))
    lines.extend(_dict_section("Source exhaustion", payload.get("source_exhaustion", {})))
    lines.extend(_delta_section(payload.get("enforcement_deltas", [])))
    return "\n".join(lines) + "\n"


def _section(title: str, values: list[Any]) -> list[str]:
    lines = [f"## {title}", ""]
    if not values:
        lines.append("- none")
    for value in values:
        lines.append(f"- `{value}`")
    lines.append("")
    return lines


def _dict_section(title: str, value: dict[str, Any]) -> list[str]:
    lines = [f"## {title}", "", "```json", json.dumps(value, indent=2)[:12000], "```", ""]
    return lines


def _delta_section(deltas: list[dict[str, Any]]) -> list[str]:
    lines = ["## Enforcement deltas", ""]
    if not deltas:
        lines.append("- none")
    for delta in deltas:
        lines.append(f"- `{delta.get('priority')}` `{delta.get('id')}`: {delta.get('status')}")
    lines.append("")
    return lines
