"""CSC doctrine pass definitions for universalized code and doctrine quality checks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from pathlib import Path

from csc_doctrine_manifest import (
    HOLON_SPECS,
    REQUIRED_LOCAL_CSC_DOCS,
    REQUIRED_REPAIRED_ARCHIVE_FILES,
    REPAIRED_ARCHIVE_ROOT,
    TRI_AUTHORITIES,
    TRI_DOCTRINE_REQUIREMENTS,
)
from csc_runtime_bindings import get_bindings
from pdver_lab_hardening_cycle import (
    ACTIVE_HEAT_WINDOW_SECONDS,
    MAX_MUTATION_LAG_SECONDS,
    MAX_REQUIRED_SOP_SET_AGE_SECONDS,
)
from strict_json_boundary import read_json_boundary, write_json_boundary

BINDINGS = get_bindings()
PROJECT_ROOT = BINDINGS.target_project_root
DATA_ROOT = BINDINGS.output_root
PDVER_REPORT_PATH = DATA_ROOT / "PDVER_HARDENING_REPORT.json"


def _display_path(path: Path) -> str:
    if PROJECT_ROOT == path or PROJECT_ROOT in path.parents:
        return path.relative_to(PROJECT_ROOT).as_posix()
    if BINDINGS.docs_root == path or BINDINGS.docs_root in path.parents:
        return f"<csc_docs>/{path.relative_to(BINDINGS.docs_root).as_posix()}"
    if REPAIRED_ARCHIVE_ROOT == path or REPAIRED_ARCHIVE_ROOT in path.parents:
        return f"<repaired_archive>/{path.relative_to(REPAIRED_ARCHIVE_ROOT).as_posix()}"
    return path.as_posix() if path.drive == "" else str(path).replace("\\", "/")


@dataclass(frozen=True)
class SopAvailabilityItem:
    path: str
    present: bool
    missing_phrases: tuple[str, ...]


@dataclass(frozen=True)
class ArchiveAvailabilityItem:
    file_name: str
    present: bool


@dataclass(frozen=True)
class SopAvailabilityReport:
    report_id: str
    local_docs: tuple[SopAvailabilityItem, ...]
    repaired_archive_root: str
    repaired_archive_files: tuple[ArchiveAvailabilityItem, ...]
    clean: bool
    note: str


@dataclass(frozen=True)
class SopFreshnessItem:
    path: str
    modified_at_epoch: float
    age_seconds: int
    lag_from_latest_mutation_seconds: int
    stale: bool


@dataclass(frozen=True)
class SopFreshnessReport:
    report_id: str
    latest_meaningful_lab_mutation_path: str
    latest_meaningful_lab_mutation_epoch: float
    latest_required_sop_path: str
    latest_required_sop_epoch: float
    items: tuple[SopFreshnessItem, ...]
    active_heat_window_seconds: int
    max_mutation_lag_seconds: int
    max_required_sop_set_age_seconds: int
    clean: bool
    note: str


@dataclass(frozen=True)
class AntiPatternInversionEntry:
    file: str
    anti_pattern: str
    target_invariant: str
    target_primitive: str
    doctrine_class: str
    authorities: tuple[str, ...]
    next_action: str


@dataclass(frozen=True)
class AntiPatternInversionReport:
    report_id: str
    entries: tuple[AntiPatternInversionEntry, ...]
    note: str


@dataclass(frozen=True)
class HolonicAuditEntry:
    subsystem_id: str
    file_path: str
    purpose: str
    boundary: str
    interface: str
    invariants: tuple[str, ...]
    hazards: tuple[str, ...]
    status: str
    missing_signals: tuple[str, ...]


@dataclass(frozen=True)
class HolonicAuditReport:
    report_id: str
    entries: tuple[HolonicAuditEntry, ...]
    clean: bool
    note: str


@dataclass(frozen=True)
class DoctrineCoverageEntry:
    requirement_id: str
    normalized_class: str
    title: str
    authorities: tuple[str, ...]
    status: str
    enforcement_surfaces: tuple[str, ...]
    active_findings: tuple[str, ...]
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class DoctrineCoverageReport:
    report_id: str
    authorities: tuple[str, ...]
    entries: tuple[DoctrineCoverageEntry, ...]
    clean: bool
    note: str


@dataclass(frozen=True)
class DoctrineAuthorityView:
    authority_id: str
    title: str
    source_kind: str
    source_ref: str


@dataclass(frozen=True)
class TriDoctrineAuthorityReport:
    report_id: str
    authorities: tuple[DoctrineAuthorityView, ...]
    note: str


_ANTI_PATTERN_MAP = MappingProxyType(
    {
        "uses_any_type": (
            "Invalid shape should not survive the type surface.",
            (
                "Replace Any with explicit dataclasses, enums, tagged unions, "
                "or precise mapping/product types."
            ),
            "typed_surface_and_boundary_integrity",
            ("omega", "unified"),
            "narrow the type surface until invalid states become harder to represent",
        ),
        "raw_json_boundary_bypass": (
            "Serialization belongs at an explicit boundary utility only.",
            "Route reads/writes through strict_json_boundary and typed boundary records.",
            "typed_surface_and_boundary_integrity",
            ("omega", "unified", "pcmmad_repaired"),
            "move raw json usage into the boundary helper or remove it",
        ),
        "machine_absolute_path": (
            "Runtime location should derive from explicit root/config, not machine-local literals.",
            "Use project root derivation or typed config roots instead of hardcoded machine paths.",
            "substrate_sovereignty_and_dependency_pressure",
            ("omega", "unified"),
            "replace absolute path with root-relative derivation",
        ),
        "dataclass_raw_projection": (
            "Artifact projection must remain explicit, typed, and boundary-owned.",
            (
                "Pass dataclass objects directly to boundary writers or use "
                "explicit record conversion."
            ),
            "typed_surface_and_boundary_integrity",
            ("unified", "pcmmad_repaired"),
            "remove __dict__ projection and keep boundary conversion inspectable",
        ),
        "broad_asdict_projection": (
            "Embodiment records should not smear into anonymous dicts.",
            "Keep dataclass artifacts intact until the boundary utility renders them.",
            "specimen_governance_separation",
            ("unified", "pcmmad_repaired"),
            "replace broad asdict projection with explicit typed emission",
        ),
        "legacy_typing_aliases": (
            "Modern typed surfaces should use current builtin generics.",
            (
                "Replace legacy typing aliases with builtin generic forms "
                "where language supports them."
            ),
            "cognitive_conservation_and_idiom",
            ("omega", "unified"),
            "modernize typing surface and reduce transitional alias drift",
        ),
        "loose_dict_typing": (
            "Module boundaries should carry typed product/sum records, not anonymous dict smear.",
            (
                "Replace builtin dict annotations with dataclasses, TypedDict "
                "at unavoidable boundaries, or explicit typed records."
            ),
            "typed_surface_and_boundary_integrity",
            ("omega", "unified"),
            "replace dict-shaped interfaces with explicit typed records",
        ),
        "mutable_default_argument": (
            "Function defaults must not carry hidden mutable state across calls.",
            (
                "Replace mutable defaults with None sentinels or explicit product "
                "construction inside the function body."
            ),
            "state_transition_and_append_only_integrity",
            ("omega", "unified"),
            "remove mutable default arguments and make state construction explicit",
        ),
        "broad_exception_handler": (
            (
                "Failure locality requires explicit, bounded error classes "
                "rather than broad catch-all suppression."
            ),
            (
                "Catch narrower exception classes or convert the error into "
                "an explicit typed result path."
            ),
            "failure_locality_and_error_visibility",
            ("omega", "unified"),
            "replace broad exception handling with explicit bounded failure paths",
        ),
        "module_mutable_global_state": (
            (
                "Global mutable state hides lifecycle and violates explicit "
                "state-transition discipline."
            ),
            (
                "Move mutable state behind explicit constructors, append-only ledgers, "
                "or lifecycle-owned instances."
            ),
            "state_transition_and_append_only_integrity",
            ("omega", "unified"),
            "remove module-level mutable state or make its lifecycle explicit and owned",
        ),
        "boolean_name_discipline": (
            "Boolean surfaces should advertise predicate semantics directly in their names.",
            "Rename boolean variables and fields to is_/has_/can_/should_ forms.",
            "cognitive_conservation_and_idiom",
            ("omega", "unified"),
            "rename boolean surfaces to explicit predicate forms",
        ),
        "excessive_path_depth": (
            "Path depth should remain within local working-memory limits.",
            (
                "Flatten directory structure or extract a clearer local holon "
                "so the path depth falls within the doctrine budget."
            ),
            "cognitive_conservation_and_idiom",
            ("omega", "unified"),
            "reduce path depth to keep module location cognitively local",
        ),
        "missing_required_sop_document": (
            "Doctrine-enforcing cleanup requires its own project-local SOP substrate.",
            (
                "Create the missing local CSC SOP document with purpose, "
                "procedure, hazards, and interlinks."
            ),
            "authority_and_mode_control",
            ("unified", "pcmmad_repaired"),
            "materialize the missing SOP document before promotion pressure",
        ),
        "incomplete_required_sop_document": (
            (
                "Required SOP docs must be structurally complete enough to operate "
                "as control surfaces."
            ),
            "Add the missing required sections/phrases to the local CSC SOP document.",
            "authority_and_mode_control",
            ("unified", "pcmmad_repaired"),
            "complete the SOP document rather than treating its existence as sufficient",
        ),
        "too_many_parameters": (
            "Local reasoning should stay within the cognitive parameter budget.",
            "Split or bundle arguments so the function surface fits within working-memory limits.",
            "cognitive_conservation_and_idiom",
            ("omega", "unified"),
            "reduce parameter count or introduce typed product inputs",
        ),
        "too_deep_nesting": (
            "Control flow should remain legible without excessive local stack burden.",
            (
                "Flatten control flow with early returns, helper extraction, "
                "or clearer state partitioning."
            ),
            "cognitive_conservation_and_idiom",
            ("omega", "unified"),
            "reduce nesting depth until the seam is locally legible",
        ),
        "too_long_function": (
            "One function should express one coherent job within local working memory.",
            "Split the function into clearer primitives or local holons.",
            "cognitive_conservation_and_idiom",
            ("omega", "unified"),
            "compress the function into cleaner local primitives",
        ),
        "silent_exception_handler": (
            "Failure paths should remain explicit and traceable.",
            (
                "Replace swallowed failures with typed handling, escalation, "
                "or explicit commentary on why suppression is safe."
            ),
            "anti_pattern_residue",
            ("unified", "pcmmad_repaired"),
            "make exception handling explicit and inspectable",
        ),
        "missing_required_archive_file": (
            "Archive-backed control claims require the archive surface to actually exist.",
            "Restore the required repaired archive file or stop claiming archive-backed coverage.",
            "archive_integrity_and_chain_trust",
            ("pcmmad_repaired",),
            "restore the repaired archive surface before promotion",
        ),
        "missing_repaired_archive_root": (
            "Archive-backed control claims require the repaired archive root to exist.",
            "Restore or relocate the repaired archive root and update the manifest.",
            "archive_integrity_and_chain_trust",
            ("pcmmad_repaired",),
            "restore the repaired archive root before promotion",
        ),
    }
)


def _load_pdver_report() -> Mapping[str, Any]:
    raw = read_json_boundary(PDVER_REPORT_PATH)
    if not isinstance(raw, dict):
        raise TypeError(f"expected object at {PDVER_REPORT_PATH}")
    return raw


def _excluded_generated_or_backup_path(path: Path) -> bool:
    excluded_parts = {
        ".pcmmad_sync_runs",
        "data",
        "reports",
        "extracted",
        "incoming",
        "__pycache__",
    }
    if excluded_parts.intersection(path.parts):
        return True
    if (
        PROJECT_ROOT / "tools" / "csc_native" == path.parent
        or PROJECT_ROOT / "tools" / "csc_native" in path.parents
    ):
        return True
    return False


def _meaningful_lab_mutation_files() -> tuple[Path, ...]:
    files: list[Path] = []
    for path in BINDINGS.docs_root.rglob("*.md"):
        if path.is_file() and not _excluded_generated_or_backup_path(path):
            files.append(path)
    return tuple(sorted(files))


def _latest_mtime(paths: tuple[Path, ...]) -> tuple[float, str]:
    latest_time = 0.0
    latest_path = ""
    for path in paths:
        mtime = path.stat().st_mtime
        if mtime > latest_time:
            latest_time = mtime
            latest_path = _display_path(path)
    return latest_time, latest_path


def _now_epoch() -> float:
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).timestamp()


def _sop_freshness_item(
    doc: Path, now_epoch: float, latest_mutation_epoch: float
) -> SopFreshnessItem:
    age_seconds = int(max(0.0, now_epoch - doc.stat().st_mtime))
    lag_seconds = int(max(0.0, latest_mutation_epoch - doc.stat().st_mtime))
    stale = _sop_item_stale(age_seconds, lag_seconds, now_epoch, latest_mutation_epoch)
    return SopFreshnessItem(
        path=_display_path(doc),
        modified_at_epoch=doc.stat().st_mtime,
        age_seconds=age_seconds,
        lag_from_latest_mutation_seconds=lag_seconds,
        stale=stale,
    )


def _sop_item_stale(
    age_seconds: int, lag_seconds: int, now_epoch: float, latest_mutation_epoch: float
) -> bool:
    active_heat = latest_mutation_epoch >= now_epoch - ACTIVE_HEAT_WINDOW_SECONDS
    return (
        active_heat and age_seconds > MAX_REQUIRED_SOP_SET_AGE_SECONDS
    ) or lag_seconds > MAX_MUTATION_LAG_SECONDS


def build_sop_freshness_report() -> SopFreshnessReport:
    docs = tuple(required.path for required in REQUIRED_LOCAL_CSC_DOCS if required.path.exists())
    latest_mutation_epoch, latest_mutation_path = _latest_mtime(_meaningful_lab_mutation_files())
    latest_sop_epoch, latest_sop_path = _latest_mtime(docs) if docs else (0.0, "")
    now_epoch = _now_epoch()
    items = tuple(_sop_freshness_item(doc, now_epoch, latest_mutation_epoch) for doc in docs)
    return SopFreshnessReport(
        report_id="CSC_SOP_FRESHNESS_REPORT_2026-04-15",
        latest_meaningful_lab_mutation_path=latest_mutation_path,
        latest_meaningful_lab_mutation_epoch=latest_mutation_epoch,
        latest_required_sop_path=latest_sop_path,
        latest_required_sop_epoch=latest_sop_epoch,
        items=items,
        active_heat_window_seconds=ACTIVE_HEAT_WINDOW_SECONDS,
        max_mutation_lag_seconds=MAX_MUTATION_LAG_SECONDS,
        max_required_sop_set_age_seconds=MAX_REQUIRED_SOP_SET_AGE_SECONDS,
        clean=all(not item.stale for item in items),
        note=(
            "Freshness compares required local SOP updates against current time and "
            "the latest meaningful lab mutation surface, excluding CSC's own report directory."
        ),
    )


def build_tri_doctrine_authority_report() -> TriDoctrineAuthorityReport:
    return TriDoctrineAuthorityReport(
        report_id="CSC_TRI_DOCTRINE_AUTHORITY_REPORT_2026-04-15",
        authorities=tuple(
            DoctrineAuthorityView(
                authority_id=item.authority_id,
                title=item.title,
                source_kind=item.source_kind,
                source_ref=item.source_ref,
            )
            for item in TRI_AUTHORITIES
        ),
        note=(
            "CSC adopts Omega, Unified Code Doctrine, and the repaired PCMMAD archive "
            "as simultaneous authority layers."
        ),
    )


def _read_required_doc_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _sop_availability_item(required: Any) -> SopAvailabilityItem:
    present = required.path.exists()
    if present:
        required_text = _read_required_doc_text(required.path)
        missing_phrases = tuple(
            phrase for phrase in required.required_phrases if phrase not in required_text
        )
    else:
        missing_phrases = tuple(required.required_phrases)
    return SopAvailabilityItem(
        path=_display_path(required.path), present=present, missing_phrases=missing_phrases
    )


def _archive_availability_items() -> tuple[ArchiveAvailabilityItem, ...]:
    return tuple(
        ArchiveAvailabilityItem(
            file_name=file_name, present=(REPAIRED_ARCHIVE_ROOT / file_name).exists()
        )
        for file_name in REQUIRED_REPAIRED_ARCHIVE_FILES
    )


def build_sop_availability_report() -> SopAvailabilityReport:
    local_items = tuple(_sop_availability_item(required) for required in REQUIRED_LOCAL_CSC_DOCS)
    archive_items = _archive_availability_items()
    clean = all(item.present and not item.missing_phrases for item in local_items) and all(
        item.present for item in archive_items
    )
    return SopAvailabilityReport(
        report_id="CSC_SOP_AVAILABILITY_REPORT_2026-04-15",
        local_docs=local_items,
        repaired_archive_root=str(REPAIRED_ARCHIVE_ROOT),
        repaired_archive_files=archive_items,
        clean=clean,
        note=(
            "Local CSC SOP set and repaired PCMMAD archive control files must be "
            "present before CSC can claim tri-doctrine readiness."
        ),
    )


def _antipattern_entry(finding: Mapping[str, Any]) -> AntiPatternInversionEntry | None:
    issue = str(finding["issue"])
    if issue not in _ANTI_PATTERN_MAP:
        return None
    target_invariant, target_primitive, doctrine_class, authorities, next_action = (
        _ANTI_PATTERN_MAP[issue]
    )
    return AntiPatternInversionEntry(
        file=str(finding["file"]),
        anti_pattern=issue,
        target_invariant=target_invariant,
        target_primitive=target_primitive,
        doctrine_class=doctrine_class,
        authorities=authorities,
        next_action=next_action,
    )


def build_antipattern_inversion_report() -> AntiPatternInversionReport:
    report = _load_pdver_report()
    cycle = report["cycles"][0]
    entries = tuple(
        entry
        for finding in cycle["probe_findings"]
        if (entry := _antipattern_entry(finding)) is not None
    )
    return AntiPatternInversionReport(
        report_id="CSC_ANTI_PATTERN_INVERSION_REPORT_2026-04-15",
        entries=entries,
        note=(
            "CSC should invert anti-patterns into stronger invariants and primitives, "
            "not only list defects."
        ),
    )


def _read_holon_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _holon_missing_signals(spec: Any, text: str) -> tuple[str, ...]:
    missing: list[str] = []
    if not spec.file_path.exists():
        missing.append("file_missing")
    missing.extend(
        f"missing_signal::{signal}" for signal in spec.required_signals if signal not in text
    )
    return tuple(missing)


def _holonic_entry(spec: Any) -> HolonicAuditEntry:
    text = _read_holon_text(spec.file_path)
    missing = _holon_missing_signals(spec, text)
    return HolonicAuditEntry(
        subsystem_id=spec.subsystem_id,
        file_path=_display_path(spec.file_path),
        purpose=spec.purpose,
        boundary=spec.boundary,
        interface=spec.interface,
        invariants=spec.invariants,
        hazards=spec.hazards,
        status="clean" if not missing else "mixed",
        missing_signals=missing,
    )


def build_holonic_audit_report() -> HolonicAuditReport:
    entries = tuple(_holonic_entry(spec) for spec in HOLON_SPECS)
    clean = all(item.status == "clean" for item in entries)
    return HolonicAuditReport(
        report_id="CSC_HOLONIC_AUDIT_REPORT_2026-04-15",
        entries=entries,
        clean=clean,
        note=(
            "CSC holonic audit checks whether the active holonic profile "
            f"'{BINDINGS.holon_profile}' remains explicit enough to survive "
            "maintenance pressure."
        ),
    )


@dataclass(frozen=True)
class SurfaceBlockerSpec:
    requirement: Any
    sop: SopAvailabilityReport
    holon: HolonicAuditReport
    verification_names: tuple[str, ...]
    self_audit_clean: bool


def _active_findings_by_class(issue_names: tuple[str, ...]) -> Mapping[str, tuple[str, ...]]:
    grouped = {}
    for issue in issue_names:
        if issue in _ANTI_PATTERN_MAP:
            doctrine_class = _ANTI_PATTERN_MAP[issue][2]
            grouped.setdefault(doctrine_class, []).append(issue)
    return {key: tuple(values) for key, values in grouped.items()}


def _sop_surfaces(spec: SurfaceBlockerSpec, surfaces: list[str], blockers: list[str]) -> None:
    if "sop" not in spec.requirement.enforcement_kind:
        return
    (
        surfaces.append("sop_availability")
        if spec.sop.clean
        else blockers.append("required_sop_or_archive_surface_incomplete")
    )


def _holon_surfaces(spec: SurfaceBlockerSpec, surfaces: list[str], blockers: list[str]) -> None:
    if "holonic_audit" not in spec.requirement.enforcement_kind:
        return
    (
        surfaces.append("holonic_audit")
        if spec.holon.clean
        else blockers.append("holonic_audit_not_clean")
    )


def _self_audit_surfaces(
    spec: SurfaceBlockerSpec, surfaces: list[str], blockers: list[str]
) -> None:
    if "self_audit" not in spec.requirement.enforcement_kind:
        return
    (
        surfaces.append("csc_self_audit")
        if spec.self_audit_clean
        else blockers.append("csc_self_audit_not_clean")
    )


def _archive_surfaces(spec: SurfaceBlockerSpec, surfaces: list[str], blockers: list[str]) -> None:
    if "archive_presence" not in spec.requirement.enforcement_kind:
        return
    ok = all(item.present for item in spec.sop.repaired_archive_files)
    (
        surfaces.append("repaired_archive_presence")
        if ok
        else blockers.append("repaired_archive_surface_incomplete")
    )


def _surfaces_and_blockers(spec: SurfaceBlockerSpec) -> tuple[list[str], list[str]]:
    surfaces: list[str] = []
    blockers: list[str] = []
    _sop_surfaces(spec, surfaces, blockers)
    _holon_surfaces(spec, surfaces, blockers)
    if "verification" in spec.requirement.enforcement_kind and spec.verification_names:
        surfaces.append("verification_battery")
    _self_audit_surfaces(spec, surfaces, blockers)
    _archive_surfaces(spec, surfaces, blockers)
    for key, label in (
        ("style_scan", "style_scan"),
        ("scan", "core_scan"),
        ("anti_pattern", "anti_pattern_inversion"),
        ("coverage", "doctrine_coverage"),
    ):
        if key in spec.requirement.enforcement_kind:
            surfaces.append(label)
    return surfaces, blockers


def _status_for_requirement(requirement, surfaces: list[str], blockers: list[str]) -> str:
    if surfaces:
        return "enforced" if not blockers else "partial"
    if requirement.normalized_class in {
        "continuity_shadow_pair",
        "rehydration_and_restart_discipline",
        "experiment_pressure_and_reporting",
    }:
        return "partial"
    return "missing"


def _finalize_partial_support(
    requirement, surfaces: list[str], blockers: list[str], status: str
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    if (
        requirement.normalized_class
        in {
            "continuity_shadow_pair",
            "rehydration_and_restart_discipline",
            "experiment_pressure_and_reporting",
        }
        and status == "partial"
    ):
        surfaces.extend(["tri_doctrine_registry", "archive_surface_presence"])
        blockers.append("coverage_not_yet_file-specific")
    return tuple(dict.fromkeys(surfaces)), tuple(dict.fromkeys(blockers)), status


def _coverage_clean(entries: tuple[DoctrineCoverageEntry, ...]) -> bool:
    requirement_by_id = {item.requirement_id: item for item in TRI_DOCTRINE_REQUIREMENTS}
    return all(
        (entry.status == "enforced")
        or (
            not requirement_by_id[entry.requirement_id].promotion_blocking
            and entry.status == "partial"
        )
        for entry in entries
    )


@dataclass(frozen=True)
class CoverageEntrySpec:
    requirement: Any
    sop: SopAvailabilityReport
    holon: HolonicAuditReport
    verification_names: tuple[str, ...]
    self_audit_clean: bool
    active_by_class: Mapping[str, tuple[str, ...]]


def _coverage_context() -> (
    tuple[JsonValue, JsonValue, tuple[str, ...], bool, Mapping[str, tuple[str, ...]]]
):
    report = _load_pdver_report()
    cycle = report["cycles"][0]
    issue_names = tuple(str(item["issue"]) for item in cycle["probe_findings"])
    verification_names = tuple(
        str(item["name"]) for item in cycle["verification"] if bool(item["ok"])
    )
    self_audit_clean = bool(cycle["csc_self_audit"]["clean"])
    return (
        cycle,
        verification_names,
        issue_names,
        self_audit_clean,
        _active_findings_by_class(issue_names),
    )


def _coverage_entry(spec: CoverageEntrySpec) -> DoctrineCoverageEntry:
    surfaces, blockers = _surfaces_and_blockers(
        SurfaceBlockerSpec(
            spec.requirement,
            spec.sop,
            spec.holon,
            spec.verification_names,
            spec.self_audit_clean,
        )
    )
    active_findings = spec.active_by_class.get(spec.requirement.normalized_class, ())
    blockers.extend(f"active:{item}" for item in active_findings)
    status = _status_for_requirement(spec.requirement, surfaces, blockers)
    enforcement_surfaces, blockers_out, final_status = _finalize_partial_support(
        spec.requirement, surfaces, blockers, status
    )
    return DoctrineCoverageEntry(
        requirement_id=spec.requirement.requirement_id,
        normalized_class=spec.requirement.normalized_class,
        title=spec.requirement.title,
        authorities=spec.requirement.authorities,
        status=final_status,
        enforcement_surfaces=enforcement_surfaces,
        active_findings=active_findings,
        blockers=blockers_out,
    )


def build_doctrine_coverage_report(
    sop: SopAvailabilityReport, holon: HolonicAuditReport, freshness: SopFreshnessReport
) -> DoctrineCoverageReport:
    _cycle, verification_names, _issue_names, self_audit_clean, active_by_class = (
        _coverage_context()
    )
    entries_out = tuple(
        _coverage_entry(
            CoverageEntrySpec(
                req, sop, holon, verification_names, self_audit_clean, active_by_class
            )
        )
        for req in TRI_DOCTRINE_REQUIREMENTS
    )
    return DoctrineCoverageReport(
        report_id="CSC_TRI_DOCTRINE_COVERAGE_REPORT_2026-04-15",
        authorities=tuple(item.authority_id for item in TRI_AUTHORITIES),
        entries=entries_out,
        clean=_coverage_clean(entries_out),
        note=(
            "Coverage means each load-bearing tri-doctrine class has an inspectable "
            "enforcement surface or an explicit partial/missing marker."
        ),
    )


def write_all_outputs(output_dir: Path) -> Mapping[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    authority = build_tri_doctrine_authority_report()
    sop = build_sop_availability_report()
    freshness = build_sop_freshness_report()
    anti = build_antipattern_inversion_report()
    holon = build_holonic_audit_report()
    coverage = build_doctrine_coverage_report(sop=sop, holon=holon, freshness=freshness)
    write_json_boundary(output_dir / "CSC_TRI_DOCTRINE_AUTHORITY_REPORT.json", authority)
    write_json_boundary(output_dir / "CSC_SOP_AVAILABILITY_REPORT.json", sop)
    write_json_boundary(output_dir / "CSC_SOP_FRESHNESS_REPORT.json", freshness)
    write_json_boundary(output_dir / "CSC_ANTI_PATTERN_INVERSION_REPORT.json", anti)
    write_json_boundary(output_dir / "CSC_HOLONIC_AUDIT_REPORT.json", holon)
    write_json_boundary(output_dir / "CSC_TRI_DOCTRINE_COVERAGE_REPORT.json", coverage)
    return {
        "tri_doctrine_authority": authority,
        "sop_availability": sop,
        "sop_freshness": freshness,
        "antipattern_inversion": anti,
        "holonic_audit": holon,
        "doctrine_coverage": coverage,
    }
