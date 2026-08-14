from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.assurance.csc.config import CommandGateSpec, load_profile
from tools.assurance.csc.adapters import run_command_gate
from tools.assurance.csc.self_audit import run_self_audit


class CscEngineSelfQualificationTests(unittest.TestCase):
    def test_builtin_self_audit_discriminates_good_bad_and_authority_mode(self):
        self.assertEqual(run_self_audit(), [])

    def test_command_adapter_preserves_failure_as_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            result = run_command_gate(
                Path(td),
                CommandGateSpec('fixture', ('{python}', '-c', 'raise SystemExit(9)')),
            )
        self.assertFalse(result.clean)
        self.assertEqual(result.status, 'fail')
        self.assertTrue(result.findings)

    def test_profile_rejects_unqualified_enforcement(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'profile.json'
            path.write_text(json.dumps({
                'project_name': 'fixture',
                'authority_mode': 'enforce',
                'source_roots': ['src'],
                'doctrine_roots': ['docs'],
                'lineage_anchor': 'engineering/lineage/csc/MANIFEST.json',
                'command_gates': [],
            }), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'audit_only'):
                load_profile(path)


if __name__ == '__main__':
    unittest.main()
