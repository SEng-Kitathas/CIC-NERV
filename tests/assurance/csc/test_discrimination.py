from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.assurance.csc.discrimination import (
    run_discrimination,
    write_discrimination_report,
)
from tools.assurance.csc.rule_registry import load_rule_registry


ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / 'engineering/assurance/csc/CSC_RULE_REGISTRY.json'


class CscDiscriminationTests(unittest.TestCase):
    def test_registry_is_audit_only_and_not_enforcement_eligible(self):
        rules = load_rule_registry(REGISTRY)
        self.assertEqual(len(rules), 5)
        for rule in rules:
            self.assertEqual(rule.authority_status, 'audit_only')
            self.assertFalse(rule.enforcement_eligible)

    def test_all_registered_rules_discriminate_required_case_classes(self):
        report = run_discrimination(REGISTRY)
        self.assertTrue(report.all_discriminated)
        self.assertEqual(report.authority_mode, 'audit_only')
        self.assertEqual(report.veto_authority, 'NONE')
        self.assertEqual(report.enforcement_authority, 'NONE')
        for rule in report.rules:
            self.assertTrue(rule.discriminated, rule)
            self.assertEqual(
                set(rule.case_classes),
                {'known_good', 'known_bad', 'near_miss', 'false_positive'},
            )
            self.assertEqual(rule.case_count, 4)

    def test_report_is_generated_outside_repository(self):
        report = run_discrimination(REGISTRY)
        with tempfile.TemporaryDirectory() as td:
            path = write_discrimination_report(report, Path(td))
            payload = json.loads(path.read_text(encoding='utf-8'))
            self.assertTrue(payload['all_discriminated'])
            self.assertEqual(payload['enforcement_authority'], 'NONE')
        self.assertFalse((ROOT / 'CIC_CSC_DISCRIMINATION_REPORT.json').exists())


if __name__ == '__main__':
    unittest.main()
