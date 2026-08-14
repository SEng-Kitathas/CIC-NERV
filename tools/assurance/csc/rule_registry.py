from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    family: str
    description: str
    authority_status: str
    enforcement_eligible: bool
    required_case_classes: tuple[str, ...]


def load_rule_registry(path: Path) -> tuple[RuleSpec, ...]:
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        raise ValueError('CSC rule registry must be a JSON object')
    if raw.get('format') != 'personal-cic.csc-rule-registry.v1':
        raise ValueError('unexpected CSC rule registry format')
    rules = raw.get('rules')
    if not isinstance(rules, list) or not rules:
        raise ValueError('CSC rule registry must contain rules')

    seen: set[str] = set()
    parsed: list[RuleSpec] = []
    for item in rules:
        if not isinstance(item, dict):
            raise ValueError('CSC rule entries must be objects')
        rule_id = _text(item, 'rule_id')
        if rule_id in seen:
            raise ValueError(f'duplicate CSC rule_id: {rule_id}')
        seen.add(rule_id)

        authority_status = _text(item, 'authority_status')
        if authority_status != 'audit_only':
            raise ValueError(f'{rule_id}: authority_status must remain audit_only')

        enforcement_eligible = item.get('enforcement_eligible')
        if enforcement_eligible is not False:
            raise ValueError(f'{rule_id}: enforcement_eligible must remain false')

        classes = item.get('required_case_classes')
        if not isinstance(classes, list) or not all(isinstance(v, str) and v for v in classes):
            raise ValueError(f'{rule_id}: required_case_classes must be a non-empty string array')
        class_tuple = tuple(classes)
        required = {'known_good', 'known_bad', 'near_miss', 'false_positive'}
        if set(class_tuple) != required:
            raise ValueError(
                f'{rule_id}: required_case_classes must be exactly {sorted(required)}'
            )

        parsed.append(RuleSpec(
            rule_id=rule_id,
            family=_text(item, 'family'),
            description=_text(item, 'description'),
            authority_status=authority_status,
            enforcement_eligible=False,
            required_case_classes=class_tuple,
        ))
    return tuple(parsed)


def _text(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{key} must be a non-empty string')
    return value.strip()
