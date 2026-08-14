"""CLI for the universal CSC/PDVER finalizer."""

from __future__ import annotations

import argparse
from pathlib import Path

from .discovery import discover
from .gates import run_all
from .json_io import write_json
from .reporting import write_reports
from .research import write_research_synthesis


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="csc-finalize")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_project_command(sub, "discover")
    _add_project_command(sub, "run")
    _add_research_command(sub)
    return parser


def _add_project_command(
    sub: argparse._SubParsersAction[argparse.ArgumentParser], name: str
) -> None:
    cmd = sub.add_parser(name)
    cmd.add_argument("--project", required=True)
    cmd.add_argument("--fail-closed", action="store_true")


def _add_research_command(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    cmd = sub.add_parser("research-synthesis")
    cmd.add_argument("--project", required=True)
    cmd.add_argument("--pass5")
    cmd.add_argument("--pass6")
    cmd.add_argument("--pass7")
    cmd.add_argument("--fail-closed", action="store_true")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    project_root = Path(args.project).resolve()
    if args.command == "research-synthesis":
        return _research(args, project_root)
    discovery = discover(project_root)
    if args.command == "discover":
        return _discover(project_root, discovery)
    return _run(args, project_root, discovery)


def _discover(project_root: Path, discovery: dict) -> int:
    out = project_root / "reports" / "UNIVERSAL_CSC_DISCOVERY_REPORT.json"
    write_json(out, discovery)
    print(out)
    return 0


def _run(args: argparse.Namespace, project_root: Path, discovery: dict) -> int:
    gates = run_all(project_root, discovery)
    payload = write_reports(project_root, discovery, gates)
    print(project_root / "reports" / "UNIVERSAL_CSC_FINALIZER_REPORT.json")
    return 1 if args.fail_closed and not payload["final_clean"] else 0


def _research(args: argparse.Namespace, project_root: Path) -> int:
    payload = write_research_synthesis(
        project_root, _path(args.pass5), _path(args.pass6), _path(args.pass7)
    )
    print(project_root / "reports" / "UNIVERSAL_CSC_RESEARCH_SYNTHESIS.json")
    return 1 if args.fail_closed and not payload["clean"] else 0


def _path(value: str | None) -> Path | None:
    return Path(value).resolve() if value else None


if __name__ == "__main__":
    raise SystemExit(main())
