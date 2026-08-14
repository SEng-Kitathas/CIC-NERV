from __future__ import annotations

import json
from pathlib import Path
import tempfile

from .adapters import run_command_gate
from .config import CommandGateSpec, load_profile
from .discovery import discover
from .discrimination import run_discrimination
from .rule_registry import load_rule_registry


def run_self_audit() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix='cic-csc-self-audit-') as td:
        root = Path(td)
        (root / 'src').mkdir()
        (root / 'docs').mkdir()
        (root / 'engineering/lineage/csc').mkdir(parents=True)
        (root / 'src/good.py').write_text('VALUE = 1\n', encoding='utf-8')
        (root / 'docs/LAW.md').write_text('A verifier must qualify its own claims.\n', encoding='utf-8')
        anchor = root / 'engineering/lineage/csc/MANIFEST.json'
        anchor.write_text('{}\n', encoding='utf-8')
        profile_path = root / 'profile.json'
        profile_path.write_text(json.dumps({
            'project_name': 'fixture',
            'authority_mode': 'audit_only',
            'source_roots': ['src'],
            'doctrine_roots': ['docs'],
            'lineage_anchor': 'engineering/lineage/csc/MANIFEST.json',
            'command_gates': [],
        }), encoding='utf-8')
        profile = load_profile(profile_path)
        found = discover(root, profile)
        if not any(item['rel'] == 'src/good.py' for item in found['files']):
            failures.append('known-good discovery fixture was not discovered')

        good = run_command_gate(root, CommandGateSpec('known_good', ('{python}', '-c', 'raise SystemExit(0)')))
        if not good.clean:
            failures.append('known-good command fixture false-vetoed')

        bad = run_command_gate(root, CommandGateSpec('known_bad', ('{python}', '-c', 'raise SystemExit(7)')))
        if bad.clean or not bad.findings:
            failures.append('known-bad command fixture was not detected')

        invalid = root / 'invalid-profile.json'
        invalid.write_text(json.dumps({
            'project_name': 'fixture',
            'authority_mode': 'enforce',
            'source_roots': ['src'],
            'doctrine_roots': ['docs'],
            'lineage_anchor': 'engineering/lineage/csc/MANIFEST.json',
        }), encoding='utf-8')
        try:
            load_profile(invalid)
        except ValueError:
            pass
        else:
            failures.append('unqualified enforce authority mode was accepted')

        # CSC v2 self-pressure: registered rules must demonstrate discrimination
        # before they can even be considered for later enforcement qualification.
        registry = Path(__file__).resolve().parents[3] / 'engineering/assurance/csc/CSC_RULE_REGISTRY.json'
        try:
            rules = load_rule_registry(registry)
            report = run_discrimination(registry)
        except Exception as exc:
            failures.append(f'discrimination self-audit could not execute: {type(exc).__name__}: {exc}')
        else:
            if not rules:
                failures.append('CSC rule registry is empty')
            if not report.all_discriminated:
                failures.append('one or more registered CSC rules failed discrimination')
            if report.enforcement_authority != 'NONE':
                failures.append('discrimination machinery claimed enforcement authority')
    return failures
