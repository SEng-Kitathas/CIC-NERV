"""CSC doctrine manifest helper for collecting governed doctrine and invariant surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from csc_runtime_bindings import get_bindings

BINDINGS = get_bindings()
PROJECT_ROOT = BINDINGS.target_project_root
DOCS_ROOT = BINDINGS.docs_root


@dataclass(frozen=True)
class RequiredDocument:
    path: Path
    required_phrases: tuple[str, ...]


@dataclass(frozen=True)
class DoctrineAuthority:
    authority_id: str
    title: str
    source_kind: str
    source_ref: str


@dataclass(frozen=True)
class DoctrineRequirement:
    requirement_id: str
    normalized_class: str
    title: str
    authorities: tuple[str, ...]
    expectation: str
    enforcement_kind: tuple[str, ...]
    promotion_blocking: bool


@dataclass(frozen=True)
class HolonSpec:
    subsystem_id: str
    file_path: Path
    purpose: str
    boundary: str
    interface: str
    invariants: tuple[str, ...]
    hazards: tuple[str, ...]
    required_signals: tuple[str, ...]


TRI_AUTHORITIES: tuple[DoctrineAuthority, ...] = (
    DoctrineAuthority(
        "receiver_project",
        "PCMMAD Receiver V27 project bindings",
        "local_doctrine",
        "docs/receiver_doctrine/00_RECEIVER_PROJECT_BINDINGS.md",
    ),
    DoctrineAuthority(
        "receiver_sop",
        "Receiver ingress and evaluation SOP",
        "local_sop",
        "docs/receiver_sop/01_RECEIVER_INGRESS_AND_EVALUATION_SOP.md",
    ),
    DoctrineAuthority(
        "omega_local",
        "CODEX OMEGA v2.0",
        "local_doctrine",
        "docs/ergo_foundations/CODEX_OMEGA_BIBLE.md",
    ),
    DoctrineAuthority(
        "unified_local",
        "UNIFIED CODE STANDARDS DOCTRINE v1.2",
        "local_doctrine",
        "docs/ergo_foundations/UNIFIED_CODE_STANDARDS_DOCTRINE_v1.2.md",
    ),
    DoctrineAuthority("csc_sop", "CSC SOP set", "local_sop", "docs/csc_sop/"),
)

REQUIRED_LOCAL_CSC_DOCS: tuple[RequiredDocument, ...] = (
    RequiredDocument(
        DOCS_ROOT / "00_CSC_START_AND_AUTHORITY.md",
        ("# 00 — CSC START AND AUTHORITY", "## Purpose"),
    ),
    RequiredDocument(
        DOCS_ROOT / "05_CSC_REQUIRED_SOP_SET.md",
        ("# 05 — CSC REQUIRED SOP SET", "## Required Local CSC SOP Documents"),
    ),
    RequiredDocument(
        DOCS_ROOT / "09_CSC_SOP_FRESHNESS_AND_MUTATION_LAG_SOP.md",
        ("# 09 — CSC SOP FRESHNESS AND MUTATION-LAG SOP", "## Required checks"),
    ),
    RequiredDocument(
        DOCS_ROOT / "10_CSC_GENERAL_GUIDE_AND_UNIVERSALIZATION.md",
        ("# 10 — CSC GENERAL GUIDE AND UNIVERSALIZATION", "## Universalization rule"),
    ),
    RequiredDocument(
        DOCS_ROOT / "11_CSC_SERVER_EXECUTION_METHODOLOGY_FOR_UNRELIABLE_PLANES.md",
        (
            "# 11 — CSC SERVER EXECUTION METHODOLOGY FOR UNRELIABLE PLANES",
            "## Purpose",
            "## Core rule",
        ),
    ),
    RequiredDocument(
        PROJECT_ROOT / "docs" / "receiver_doctrine" / "00_RECEIVER_PROJECT_BINDINGS.md",
        (
            "PCMMAD Receiver V27 Project Bindings",
            "Extracted package code is controlled evidence until promoted.",
        ),
    ),
    RequiredDocument(
        PROJECT_ROOT / "docs" / "receiver_sop" / "01_RECEIVER_INGRESS_AND_EVALUATION_SOP.md",
        ("Receiver Ingress and Evaluation SOP", "Promotion boundary"),
    ),
    RequiredDocument(
        PROJECT_ROOT / "spec" / "PCMMAD_RECEIVER_V27_PACKAGE_SPEC.md",
        ("PCMMAD Receiver V27 Package Spec", "Required evaluation gates"),
    ),
    RequiredDocument(
        PROJECT_ROOT / "reports" / "INITIAL_EXTRACTION_MANIFEST.json",
        ("entry_count", "PCMMAD_RECEIVER_V27_TOOL_PRIMITIVES_AND_EXECUTION_REDUCTION_PACKAGE"),
    ),
    RequiredDocument(
        PROJECT_ROOT / "reports" / "INITIAL_PACKAGE_EVALUATION.json",
        ("module_count", "compileall_returncode"),
    ),
)

REQUIRED_REPAIRED_ARCHIVE_FILES: tuple[str, ...] = ()
REPAIRED_ARCHIVE_ROOT = PROJECT_ROOT / "data" / "imports"

TRI_DOCTRINE_REQUIREMENTS: tuple[DoctrineRequirement, ...] = (
    DoctrineRequirement(
        "REQ_RECEIVER_INGRESS",
        "receiver_ingress_and_evidence_boundary",
        "Receiver ingress and evidence boundary",
        ("csc_sop",),
        (
            "Archive contents must be extracted, inventoried, and evaluated "
            "as controlled evidence before promotion."
        ),
        ("sop", "coverage", "pdver"),
        True,
    ),
    DoctrineRequirement(
        "REQ_RECEIVER_VERIFICATION",
        "receiver_compile_and_static_evaluation",
        "Receiver compile and static evaluation",
        ("csc_sop",),
        (
            "Extracted receiver package must pass static compile verification "
            "and produce an evaluation report."
        ),
        ("verification", "coverage"),
        True,
    ),
    DoctrineRequirement(
        "REQ_RECEIVER_FINALIZER",
        "receiver_finalizer_and_doctrine_gate",
        "Receiver finalizer and doctrine gate",
        ("csc_sop",),
        (
            "The receiver lab must end tasks through finalizer clean status "
            "or exact blocker reporting."
        ),
        ("verification", "coverage"),
        True,
    ),
)

HOLON_SPECS: tuple[HolonSpec, ...] = (
    HolonSpec(
        "receiver_extracted_package",
        PROJECT_ROOT
        / "extracted"
        / "PCMMAD_RECEIVER_V27_TOOL_PRIMITIVES_AND_EXECUTION_REDUCTION_PACKAGE"
        / "pcmmad_receiver"
        / "server.py",
        "Extracted PCMMAD receiver server entrypoint under forensic evaluation.",
        "Evidence boundary.",
        "Extracted Python package.",
        ("server entrypoint", "Flask app factory", "environment bind configuration"),
        ("unpromoted code treated as final", "schema drift"),
        ("create_app", "_bind_host", "_bind_port"),
    ),
    HolonSpec(
        "receiver_action_schema",
        PROJECT_ROOT
        / "extracted"
        / "PCMMAD_RECEIVER_V27_TOOL_PRIMITIVES_AND_EXECUTION_REDUCTION_PACKAGE"
        / "pcmmad_receiver"
        / "pcmmad_lab_action_schema_v10_1_compact_30_router.json",
        "Compact action schema/router for PCMMAD receiver tools.",
        "Schema boundary.",
        "OpenAPI JSON schema.",
        ("openapi", "paths", "components"),
        ("tool/schema mismatch",),
        ("openapi", "paths"),
    ),
    HolonSpec(
        "receiver_evaluation_report",
        PROJECT_ROOT / "reports" / "INITIAL_PACKAGE_EVALUATION.json",
        "Static package evaluation output.",
        "Evaluation boundary.",
        "JSON report.",
        ("module_count", "compileall_returncode"),
        ("evaluation drift",),
        ("module_count", "compileall_returncode"),
    ),
    HolonSpec(
        "task_finalizer",
        PROJECT_ROOT / "system" / "finalize_task.py",
        "Run CSC and finalize receiver lab tasks.",
        "Finalization boundary.",
        "CLI script.",
        ("csc output", "final_clean"),
        ("silent success",),
        ("csc_output_root", "final_clean"),
    ),
)


def required_document_status(document: RequiredDocument) -> tuple[bool, tuple[str, ...]]:
    if not document.path.exists():
        return False, document.required_phrases
    text = document.path.read_text(encoding="utf-8", errors="ignore")
    missing = tuple(phrase for phrase in document.required_phrases if phrase not in text)
    return len(missing) == 0, missing


def authority_status(authority: DoctrineAuthority) -> bool:
    if authority.source_ref.endswith("/"):
        return (PROJECT_ROOT / authority.source_ref).exists()
    return (PROJECT_ROOT / authority.source_ref).exists()
