import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RuntimePackageBoundaryTests(unittest.TestCase):
    def test_python_package_discovery_is_src_only(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('where = ["src"]', text)

    def test_runtime_does_not_import_engineering_or_csc_namespaces(self):
        forbidden = {"engineering", "tools", "tests", "csc", "universal_csc"}
        violations = []
        for path in sorted((ROOT / "src/personal_cic").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names.extend(item.name for item in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names.append(node.module)
                for name in names:
                    if name.split(".", 1)[0] in forbidden:
                        violations.append(
                            f"{path.relative_to(ROOT)}:{getattr(node, 'lineno', '?')}:{name}"
                        )
        self.assertEqual(violations, [])

    def test_csc_lineage_is_outside_runtime_source_root(self):
        lineage = ROOT / "engineering/lineage/csc"
        self.assertTrue(lineage.is_dir())
        self.assertFalse(str(lineage).startswith(str(ROOT / "src/personal_cic")))

    def test_runtime_package_boundary_verifier_is_present(self):
        self.assertTrue((ROOT / "tools/verify_runtime_package_boundary.py").is_file())


if __name__ == "__main__":
    unittest.main()
