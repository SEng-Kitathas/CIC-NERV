\
#!/usr/bin/env python3
"""Prove that engineering/CSC source does not enter the CIC runtime package.

This is a source/package assurance gate, not runtime or promotion authority.
"""

from __future__ import annotations

import ast
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "src" / "personal_cic"

FORBIDDEN_IMPORT_ROOTS = {
    "engineering",
    "tools",
    "tests",
    "csc",
    "universal_csc",
}

FORBIDDEN_WHEEL_PREFIXES = (
    "engineering/",
    "tools/",
    "tests/",
    "universal_csc/",
)
FORBIDDEN_WHEEL_BASENAMES = {
    "csc_project.json",
    "csc_profile.json",
}


def runtime_import_violations() -> list[str]:
    failures: list[str] = []
    for path in sorted(RUNTIME_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[tuple[str, int]] = []
            if isinstance(node, ast.Import):
                names.extend((item.name, node.lineno) for item in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append((node.module, node.lineno))
            for name, lineno in names:
                root = name.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    failures.append(
                        f"runtime import crosses assurance boundary: "
                        f"{path.relative_to(ROOT)}:{lineno}: {name}"
                    )
    return failures


def _copy_project_for_build(target: Path) -> None:
    ignore = shutil.ignore_patterns(
        ".git",
        ".venv",
        ".tox",
        ".nox",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "build",
        "dist",
        "*.egg-info",
        "state",
    )
    for path in ROOT.iterdir():
        if path.name in {".git", ".venv"}:
            continue
        dst = target / path.name
        if path.is_dir():
            shutil.copytree(path, dst, ignore=ignore)
        elif path.is_file():
            shutil.copy2(path, dst)


def wheel_violations() -> tuple[list[str], str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="cic-runtime-package-") as td:
        temp = Path(td)
        project = temp / "project"
        wheelhouse = temp / "wheelhouse"
        project.mkdir()
        wheelhouse.mkdir()
        _copy_project_for_build(project)

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                ".",
                "--no-deps",
                "--no-build-isolation",
                "--disable-pip-version-check",
                "-w",
                str(wheelhouse),
            ],
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if proc.returncode:
            return [f"runtime wheel build failed:\n{proc.stdout.rstrip()}"], ""

        wheels = sorted(wheelhouse.glob("personal_cic-*.whl"))
        if len(wheels) != 1:
            return [f"expected exactly one personal_cic wheel, found {len(wheels)}"], ""

        wheel = wheels[0]
        with zipfile.ZipFile(wheel) as zf:
            names = sorted(name for name in zf.namelist() if not name.endswith("/"))

        for name in names:
            if name.startswith(FORBIDDEN_WHEEL_PREFIXES):
                failures.append(f"forbidden engineering path in runtime wheel: {name}")
            if Path(name).name in FORBIDDEN_WHEEL_BASENAMES:
                failures.append(f"forbidden CSC profile in runtime wheel: {name}")
            if "/engineering/" in name or "/tests/" in name or "/tools/" in name:
                failures.append(f"forbidden non-runtime segment in runtime wheel: {name}")

        # Runtime code must be present, and only package/dist-info roots are admitted.
        if not any(name.startswith("personal_cic/") for name in names):
            failures.append("runtime wheel contains no personal_cic package")
        unexpected_roots = sorted(
            {
                name.split("/", 1)[0]
                for name in names
                if not (
                    name.startswith("personal_cic/")
                    or ".dist-info/" in name
                )
            }
        )
        if unexpected_roots:
            failures.append(
                "unexpected top-level runtime wheel roots: "
                + ", ".join(unexpected_roots)
            )

        return failures, wheel.name


def main() -> None:
    failures = runtime_import_violations()
    wheel_failures, wheel_name = wheel_violations()
    failures.extend(wheel_failures)

    if failures:
        print("FAIL: CIC runtime-package / CSC exclusion boundary")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("PASS: CIC runtime-package / CSC exclusion boundary")
    print("runtime_imports_assurance=NONE")
    print(f"wheel={wheel_name}")
    print("engineering_lineage_in_runtime=NONE")
    print("assurance_tools_in_runtime=NONE")
    print("promotion_authority=NONE // package/source boundary only")


if __name__ == "__main__":
    main()
