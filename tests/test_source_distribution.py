from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def _load_tool(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load tool {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceDistributionTests(unittest.TestCase):
    def test_working_tree_distribution_verifier_passes_without_runtime_requirement(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/verify-source-distribution.py"), "--working-tree"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("source-distribution hygiene", result.stdout)
        self.assertIn("scope=working-tree", result.stdout)

    def test_strict_source_capture_rejects_generated_product_under_authored_root(self):
        tool = _load_tool("source_distribution_strict", "verify-source-distribution.py")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        cache = root / "tests" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "x.pyc").write_bytes(b"cache")
        failures = tool.hygiene_failures(root, working_tree=False)
        self.assertTrue(any("tests/__pycache__" in item for item in failures), failures)

    def test_working_tree_scope_tolerates_generated_product_without_reclassifying_it_as_source(self):
        tool = _load_tool("source_distribution_working", "verify-source-distribution.py")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        cache = root / "src" / "pkg" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "x.pyc").write_bytes(b"cache")
        self.assertEqual(tool.hygiene_failures(root, working_tree=True), [])
        strict = tool.hygiene_failures(root, working_tree=False)
        self.assertTrue(strict)

    def test_virtual_environment_is_outside_source_capture_authority(self):
        tool = _load_tool("source_distribution_venv", "verify-source-distribution.py")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        cache = root / ".venv" / "lib" / "python3.10" / "site-packages" / "x" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "x.pyc").write_bytes(b"cache")
        self.assertEqual(tool.hygiene_failures(root, working_tree=False), [])

    def test_service_installer_uses_working_tree_scope_with_runtime_requirement(self):
        script = (ROOT / "tools/install-user-service.sh").read_text(encoding="utf-8")
        invocation = (
            '"${PROJECT_ROOT}/.venv/bin/python" "${VERIFY_SOURCE}" '
            '--working-tree --require-runtime-vendor'
        )
        self.assertIn(invocation, script)
        self.assertNotIn(
            '"${PROJECT_ROOT}/.venv/bin/python" "${VERIFY_SOURCE}" --require-runtime-vendor;',
            script,
        )

    def test_maplibre_lock_has_expected_bounded_identity_contract(self):
        tool = _load_tool("maplibre_materializer", "install-maplibre-vendor.py")
        lock = tool.load_lock()
        self.assertEqual(lock["dependency"], "maplibre-gl-js")
        self.assertEqual(lock["version"], "5.24.0")
        self.assertEqual(len(lock["release_archive_sha256"]), 64)
        self.assertEqual(lock["release_archive_size_bytes"], 8_016_600)
        self.assertEqual(len(lock["required_files"]), len(set(lock["required_files"])))
        self.assertLessEqual(lock["release_archive_size_bytes"], tool.MAX_ARCHIVE_BYTES)

    def test_exact_extraction_rejects_oversized_required_member(self):
        tool = _load_tool("maplibre_materializer_oversize", "install-maplibre-vendor.py")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        archive = base / "fake.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("maplibre-gl.js", b"x" * (tool.MAX_MEMBER_BYTES + 1))
            zf.writestr("maplibre-gl.css", b"x")
            zf.writestr("LICENSE.txt", b"Redistribution and use in source and binary forms")
        destination = base / "stage"
        destination.mkdir()
        with self.assertRaises(SystemExit):
            tool.extract_exact(
                archive,
                ["maplibre-gl.js", "maplibre-gl.css", "LICENSE.txt"],
                destination,
            )

    def test_source_lock_required_files_are_path_safe(self):
        lock = json.loads(
            (ROOT / "src/personal_cic/presentation/vendor/maplibre/LOCK.json").read_text(encoding="utf-8")
        )
        for name in lock["required_files"]:
            self.assertEqual(Path(name).name, name)


if __name__ == "__main__":
    unittest.main()
