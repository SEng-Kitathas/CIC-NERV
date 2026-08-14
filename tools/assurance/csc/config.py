from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .model import AuthorityMode


@dataclass(frozen=True)
class CommandGateSpec:
    gate_id: str
    command: tuple[str, ...]
    required: bool = True
    cwd: str = '.'
    clean_exit_codes: tuple[int, ...] = (0,)


@dataclass(frozen=True)
class ProjectProfile:
    project_name: str
    authority_mode: AuthorityMode
    source_roots: tuple[str, ...]
    doctrine_roots: tuple[str, ...]
    lineage_anchor: str
    command_gates: tuple[CommandGateSpec, ...]


def load_profile(path: Path) -> ProjectProfile:
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        raise ValueError('CSC profile must be a JSON object')
    mode = raw.get('authority_mode')
    if mode != 'audit_only':
        raise ValueError('CIC CSC authority_mode must remain audit_only until separately qualified')
    return ProjectProfile(
        project_name=_required_text(raw, 'project_name'),
        authority_mode='audit_only',
        source_roots=_string_tuple(raw.get('source_roots')),
        doctrine_roots=_string_tuple(raw.get('doctrine_roots')),
        lineage_anchor=_required_text(raw, 'lineage_anchor'),
        command_gates=tuple(_command_gate(item) for item in _object_list(raw.get('command_gates'))),
    )


def _required_text(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{key} must be a non-empty string')
    return value.strip()


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError('profile root lists must be arrays')
    items = tuple(item for item in value if isinstance(item, str) and item)
    if not items:
        raise ValueError('profile root lists must not be empty')
    return items


def _object_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _command_gate(raw: dict[str, Any]) -> CommandGateSpec:
    command = raw.get('command')
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise ValueError('command gate command must be a string array')
    clean_codes = raw.get('clean_exit_codes', [0])
    if not isinstance(clean_codes, list) or not all(isinstance(item, int) for item in clean_codes):
        raise ValueError('clean_exit_codes must be an integer array')
    return CommandGateSpec(
        gate_id=_required_text(raw, 'gate_id'),
        command=tuple(command),
        required=bool(raw.get('required', True)),
        cwd=str(raw.get('cwd') or '.'),
        clean_exit_codes=tuple(clean_codes) or (0,),
    )
