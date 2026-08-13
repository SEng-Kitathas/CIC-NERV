#!/usr/bin/env python3
"""Run the authored-source quality gate without mutating runtime state.

This is an assurance convenience, not promotion authority. It qualifies the source
candidate against source-local claims (syntax, static invariants, tests, distribution
hygiene, JSON structure, and shell syntax). Target behavior still requires a
claim-matched target gate and operator proof where applicable.
"""

from __future__ import annotations

from argparse import ArgumentParser
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOTS = (ROOT / "src", ROOT / "tests", ROOT / "tools")
WORK_MARKERS = ("TODO", "FIXME", "XXX", "HACK", "NotImplemented")
MUTABLE_DEFAULT_TYPES = (ast.List, ast.Dict, ast.Set)


def python_files() -> list[Path]:
    files: list[Path] = []
    for root in PYTHON_ROOTS:
        if not root.exists():
            continue
        files.extend(
            path
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts
        )
    return sorted(set(files))


def static_violations() -> list[str]:
    failures: list[str] = []
    for path in python_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        try:
            compile(text, str(rel), "exec")
            tree = ast.parse(text, filename=str(rel))
        except (SyntaxError, ValueError) as exc:
            failures.append(f"syntax failure {rel}: {exc}")
            continue

        if rel.parts and rel.parts[0] in {"src", "tools"} and path.resolve() != Path(__file__).resolve():
            for marker in WORK_MARKERS:
                if marker in text:
                    failures.append(f"unfinished-work marker {marker!r} in {rel}")

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                failures.append(f"bare except in {rel}:{node.lineno}")
            if rel.parts and rel.parts[0] == "src" and isinstance(node, ast.Assert):
                failures.append(f"runtime assert in {rel}:{node.lineno}")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defaults = [*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]]
                for default in defaults:
                    if isinstance(default, MUTABLE_DEFAULT_TYPES):
                        failures.append(
                            f"mutable default argument in {rel}:{node.lineno} function {node.name}"
                        )
    return failures


def json_violations() -> list[str]:
    failures: list[str] = []
    for path in sorted(ROOT.rglob("*.json")):
        if "__pycache__" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    return failures


def run(command: list[str], *, env: dict[str, str] | None = None) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def shell_violations() -> list[str]:
    failures: list[str] = []
    for path in sorted((ROOT / "tools").glob("*.sh")):
        code, output = run(["bash", "-n", str(path)])
        if code:
            failures.append(
                f"shell syntax failure {path.relative_to(ROOT)}: {output.strip()}"
            )
    return failures


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="run static/distribution checks only; does not qualify behavioral regression",
    )
    args = parser.parse_args()

    failures = [*static_violations(), *json_violations(), *shell_violations()]

    code, output = run([sys.executable, "tools/verify-source-distribution.py", "--working-tree"])
    if code:
        failures.append("source-distribution verifier failed:\n" + output.rstrip())

    test_output = ""
    if not args.skip_tests:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(ROOT / "src")
        code, test_output = run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            env=env,
        )
        if code:
            failures.append("unit/regression suite failed:\n" + test_output.rstrip())

    if failures:
        print("FAIL: Personal CIC authored-source quality gate")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    mode = "static-only" if args.skip_tests else "static+regression"
    print(f"PASS: Personal CIC authored-source quality gate ({mode})")
    print(f"python_files={len(python_files())}")
    print("promotion_authority=NONE // target gate still required")
    if test_output:
        for line in test_output.splitlines():
            if line.startswith("Ran ") or line == "OK":
                print(line)


if __name__ == "__main__":
    main()
