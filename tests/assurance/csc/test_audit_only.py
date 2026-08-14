from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.assurance.csc.audit import run_audit


ROOT = Path(__file__).resolve().parents[3]


class CscAuditOnlyAuthorityTests(unittest.TestCase):
    def test_cli_self_audit_passes_without_granting_veto_authority(self):
        proc = subprocess.run(
            [sys.executable, '-m', 'tools.assurance.csc.cli', 'self-audit'],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn('veto_authority=NONE', proc.stdout)

    def test_audit_report_can_be_written_outside_fixture_project(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'project'
            output = Path(td) / 'output'
            (root / 'src').mkdir(parents=True)
            (root / 'docs').mkdir()
            (root / 'engineering/lineage/csc').mkdir(parents=True)
            (root / 'src/sample.py').write_text('VALUE = 1\n', encoding='utf-8')
            (root / 'docs/LAW.md').write_text(
                'Verification must remain claim-matched.\n', encoding='utf-8'
            )
            (root / 'engineering/lineage/csc/MANIFEST.json').write_text(
                '{}\n', encoding='utf-8'
            )
            profile = root / 'profile.json'
            profile.write_text(json.dumps({
                'project_name': 'fixture',
                'authority_mode': 'audit_only',
                'source_roots': ['src'],
                'doctrine_roots': ['docs'],
                'lineage_anchor': 'engineering/lineage/csc/MANIFEST.json',
                'command_gates': [],
            }), encoding='utf-8')

            report, clean = run_audit(root, profile, output)

            self.assertTrue(clean)
            self.assertEqual(report, output / 'CIC_CSC_AUDIT_REPORT.json')
            self.assertTrue(report.is_file())
            self.assertFalse((root / 'CIC_CSC_AUDIT_REPORT.json').exists())


if __name__ == '__main__':
    unittest.main()
