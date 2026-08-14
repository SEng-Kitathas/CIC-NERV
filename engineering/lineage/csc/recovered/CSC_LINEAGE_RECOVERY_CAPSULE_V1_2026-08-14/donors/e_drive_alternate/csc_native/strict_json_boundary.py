"""Strict JSON boundary helper for deterministic serialization and safe persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


def _to_boundary(obj: Any) -> Any:
    if is_dataclass(obj):
        return {key: _to_boundary(value) for key, value in asdict(obj).items()}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj).replace("\\", "/")
    if isinstance(obj, tuple):
        return [_to_boundary(item) for item in obj]
    if isinstance(obj, list):
        return [_to_boundary(item) for item in obj]
    if isinstance(obj, dict):
        return {str(key): _to_boundary(value) for key, value in obj.items()}
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    raise TypeError(f"unsupported boundary type: {type(obj)!r}")


def render_json_boundary(obj: Any) -> str:
    payload = _to_boundary(obj)
    return json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False, allow_nan=False)


def write_json_boundary(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = render_json_boundary(obj)
    path.write_text(text + "\n", encoding="utf-8")


def read_json_boundary(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_json_boundary_text(text: str) -> Any:
    return json.loads(text)
