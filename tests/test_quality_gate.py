from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "quality_gate.py"


def load_quality_gate():
    spec = importlib.util.spec_from_file_location("personal_cic_quality_gate", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QualityGateTests(unittest.TestCase):
    def test_static_quality_gate_finds_no_current_source_violations(self) -> None:
        gate = load_quality_gate()
        self.assertEqual(gate.static_violations(), [])
        self.assertEqual(gate.json_violations(), [])
        self.assertEqual(gate.shell_violations(), [])

    def test_quality_gate_is_explicitly_non_promotional(self) -> None:
        text = TOOL.read_text(encoding="utf-8")
        self.assertIn("Target behavior still requires", text)
        self.assertIn("promotion_authority=NONE", text)


if __name__ == "__main__":
    unittest.main()
