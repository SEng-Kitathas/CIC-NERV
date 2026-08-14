"""Manifest/profile loading for the universal CSC finalizer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .json_io import read_json

DEFAULT_ACTIVE = ("baseline", "src", "system", "tools", "tests")
DEFAULT_DOCTRINE = ("docs", "spec")
DEFAULT_EVIDENCE = (
    "reports",
    "data",
    "logs",
    "browser_screenshots",
    "browser_bridge_logs",
    "extracted",
)


@dataclass(frozen=True)
class CommandGateSpec:
    id: str
    command: tuple[str, ...]
    required: bool = True
    cwd: str = "."
    clean_exit_codes: tuple[int, ...] = (0,)


@dataclass(frozen=True)
class ReportGateSpec:
    id: str
    path: str
    clean_field: str = "clean"
    required: bool = True
    expected: bool = True
    inputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SidecarSpec:
    id: str
    health_url: str
    required: bool = False
    manual_start: bool = True


@dataclass(frozen=True)
class ProjectProfile:
    project_name: str
    active_roots: tuple[str, ...] = DEFAULT_ACTIVE
    doctrine_roots: tuple[str, ...] = DEFAULT_DOCTRINE
    evidence_roots: tuple[str, ...] = DEFAULT_EVIDENCE
    command_gates: tuple[CommandGateSpec, ...] = ()
    report_gates: tuple[ReportGateSpec, ...] = ()
    sidecars: tuple[SidecarSpec, ...] = ()


def load_profile(project_root: Path) -> ProjectProfile:
    manifest = _manifest(project_root)
    return ProjectProfile(
        project_name=str(manifest.get("project_name") or project_root.name),
        active_roots=_string_tuple(manifest.get("active_roots"), DEFAULT_ACTIVE),
        doctrine_roots=_string_tuple(manifest.get("doctrine_roots"), DEFAULT_DOCTRINE),
        evidence_roots=_string_tuple(manifest.get("evidence_roots"), DEFAULT_EVIDENCE),
        command_gates=tuple(_command_gate(item) for item in _list(manifest.get("command_gates"))),
        report_gates=tuple(_report_gate(item) for item in _list(manifest.get("report_gates"))),
        sidecars=tuple(_sidecar(item) for item in _list(manifest.get("sidecars"))),
    )


def _manifest(project_root: Path) -> dict[str, Any]:
    for name in ("csc_project.json", "csc_profile.json"):
        value = read_json(project_root / name)
        if isinstance(value, dict):
            return value
    return {}


def _list(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_tuple(value: object, default: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, list):
        return default
    items = tuple(str(item) for item in value if isinstance(item, str) and item)
    return items or default


def _command_gate(item: dict[str, Any]) -> CommandGateSpec:
    command = item.get("command")
    argv = tuple(str(arg) for arg in command) if isinstance(command, list) else ()
    return CommandGateSpec(
        str(item.get("id") or "command_gate"),
        argv,
        bool(item.get("required", True)),
        str(item.get("cwd") or "."),
        _exit_codes(item.get("clean_exit_codes")),
    )


def _exit_codes(value: object) -> tuple[int, ...]:
    if not isinstance(value, list):
        return (0,)
    codes = tuple(int(item) for item in value if isinstance(item, int))
    return codes or (0,)


def _report_gate(item: dict[str, Any]) -> ReportGateSpec:
    return ReportGateSpec(
        str(item.get("id") or "report_gate"),
        str(item.get("path") or ""),
        str(item.get("clean_field") or "clean"),
        bool(item.get("required", True)),
        bool(item.get("expected", True)),
        _string_tuple(item.get("inputs"), ()),
    )


def _sidecar(item: dict[str, Any]) -> SidecarSpec:
    return SidecarSpec(
        str(item.get("id") or "sidecar"),
        str(item.get("health_url") or ""),
        bool(item.get("required", False)),
        bool(item.get("manual_start", True)),
    )
