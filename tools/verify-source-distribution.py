#!/usr/bin/env python3
"""Verify authored source-capture hygiene and presentation dependency materialization.

Two scopes are deliberately distinct:

* source-capture (default): reject generated products inside authored/project roots;
* working-tree: tolerate generated runtime/build products that may exist beside an
  editable target checkout, while still validating authored dependency contracts.

A virtual environment is never authored source and is excluded in both modes.
"""

from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "src/personal_cic/presentation/vendor/maplibre"
LOCK_PATH = VENDOR / "LOCK.json"
FORBIDDEN_DIRS = {"__pycache__", "build", "dist", "htmlcov"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".whl"}
EXTERNAL_RUNTIME_ROOTS = {
    ".git",
    ".venv",
    ".tox",
    ".nox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _outside_authored_distribution(rel: Path) -> bool:
    """Return True for local runtime/tooling roots that are never source payload."""

    return bool(rel.parts) and rel.parts[0] in EXTERNAL_RUNTIME_ROOTS


def _generated_product(rel: Path, path: Path) -> str | None:
    if any(part.endswith(".egg-info") for part in rel.parts):
        return f"generated egg-info present: {rel}"
    if path.is_dir() and path.name in FORBIDDEN_DIRS:
        return f"generated directory present: {rel}"
    if path.is_file() and (
        path.suffix in FORBIDDEN_SUFFIXES or path.name.startswith(".coverage")
    ):
        return f"generated file present: {rel}"
    return None


def hygiene_failures(root: Path, *, working_tree: bool) -> list[str]:
    """Return source-hygiene violations for the selected verification scope.

    `working_tree=True` does not bless generated products as source. It merely
    recognizes that an embodied editable checkout can contain caches/build metadata
    that are outside the sealed authored-source proposition. Archive/source-capture
    verification must use the default strict scope.
    """

    failures: list[str] = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if _outside_authored_distribution(rel):
            continue
        generated = _generated_product(rel, path)
        if generated is not None and not working_tree:
            failures.append(generated)
    return failures


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-runtime-vendor",
        action="store_true",
        help="fail unless exact pinned MapLibre runtime files are materialized",
    )
    parser.add_argument(
        "--working-tree",
        action="store_true",
        help=(
            "verify an embodied editable checkout: tolerate generated caches/build metadata "
            "that are not part of the sealed authored-source distribution"
        ),
    )
    args = parser.parse_args()
    failures: list[str] = hygiene_failures(ROOT, working_tree=args.working_tree)

    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"invalid MapLibre LOCK.json: {exc}")
        lock = {}

    expected_size = lock.get("release_archive_size_bytes")
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size <= 0:
        failures.append("MapLibre LOCK.json has invalid release_archive_size_bytes")
    expected_archive = lock.get("release_archive_sha256")
    if not isinstance(expected_archive, str) or len(expected_archive) != 64 or any(
        c not in "0123456789abcdef" for c in expected_archive.lower()
    ):
        failures.append("MapLibre LOCK.json has invalid release_archive_sha256")
    required = lock.get("required_files", [])
    if not isinstance(required, list) or not required or not all(isinstance(name, str) for name in required):
        failures.append("MapLibre LOCK.json required_files must be a non-empty string array")
        required = []
    elif len(required) != len(set(required)) or any(Path(name).name != name for name in required):
        failures.append("MapLibre LOCK.json required_files must be unique basenames")
        required = []
    materialized_path = VENDOR / "MATERIALIZED.json"
    runtime_present = bool(required) and all((VENDOR / name).is_file() for name in required)
    if args.require_runtime_vendor and not runtime_present:
        failures.append(
            "pinned MapLibre runtime is not materialized; run tools/install-maplibre-vendor.py"
        )
    if runtime_present:
        try:
            materialized = json.loads(materialized_path.read_text(encoding="utf-8"))
            if materialized.get("dependency") != lock.get("dependency"):
                failures.append("MapLibre materialization dependency differs from LOCK.json")
            if materialized.get("version") != lock.get("version"):
                failures.append("MapLibre materialization version differs from LOCK.json")
            if materialized.get("release_archive_sha256") != lock.get("release_archive_sha256"):
                failures.append("MapLibre materialization archive identity differs from LOCK.json")
            recorded = materialized.get("files", {})
            if not isinstance(recorded, dict):
                failures.append("MapLibre MATERIALIZED.json files must be an object")
                recorded = {}
            for filename in required:
                actual = file_sha(VENDOR / filename)
                if recorded.get(filename) != actual:
                    failures.append(f"MapLibre materialized file hash mismatch: {filename}")
        except Exception as exc:
            failures.append(f"invalid MapLibre MATERIALIZED.json: {exc}")

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for pattern in (
        "vendor/maplibre/*.js",
        "vendor/maplibre/*.css",
        "vendor/maplibre/*.txt",
        "vendor/maplibre/*.json",
        "vendor/maplibre/*.md",
    ):
        if pattern not in pyproject:
            failures.append(f"pyproject package-data is missing {pattern}")

    if failures:
        print("FAIL: source-distribution verification")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    status = "materialized" if runtime_present else "locked-but-not-materialized"
    scope = "working-tree" if args.working_tree else "source-capture"
    print(f"PASS: source-distribution hygiene; scope={scope}; maplibre={status}")


if __name__ == "__main__":
    main()
