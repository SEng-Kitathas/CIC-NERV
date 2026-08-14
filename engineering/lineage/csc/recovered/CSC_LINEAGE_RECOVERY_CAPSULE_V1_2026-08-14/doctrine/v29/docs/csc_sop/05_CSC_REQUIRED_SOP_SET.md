# 05 — CSC REQUIRED SOP SET

## Purpose
This document defines the minimum SOP/document set CSC SHALL require before declaring doctrine-aligned operation.

## Required Local CSC SOP Documents
- `docs/csc_sop/00_CSC_START_AND_AUTHORITY.md`
- `docs/csc_sop/01_CSC_DOCTRINE_LINKAGE.md`
- `docs/csc_sop/02_CSC_HOLONIC_AUDIT_SOP.md`
- `docs/csc_sop/03_CSC_ANTI_PATTERN_INVERSION_SOP.md`
- `docs/csc_sop/04_CSC_PROMOTION_AND_RECURSION_SOP.md`
- `docs/csc_sop/05_CSC_REQUIRED_SOP_SET.md`
- `docs/csc_sop/06_CSC_TRI_DOCTRINE_AUTHORITY.md`
- `docs/csc_sop/07_CSC_TRI_DOCTRINE_COVERAGE_POLICY.md`
- `docs/csc_sop/08_CSC_IDIOMATIC_EXPRESSION_SOP.md`
- `docs/csc_sop/09_CSC_SOP_FRESHNESS_AND_MUTATION_LAG_SOP.md`
- `docs/csc_sop/10_CSC_GENERAL_GUIDE_AND_UNIVERSALIZATION.md`
- `docs/csc_sop/11_CSC_SERVER_EXECUTION_METHODOLOGY_FOR_UNRELIABLE_PLANES.md`

## Required Upstream Archive Documents
CSC SHALL also require availability of the repaired PCMMAD starter archive control files and at minimum treat these as always-on:
- `README__SHALL_START_AT_00.md`
- `00 SHALL_READ_BOOTSTRAP_INIT_PROTOCOL_FIRST.md`
- `01 SHALL_READ_BOOTSTRAP_PROMPT_SHIM_NEXT.md`
- `02 SHALL_READ_REHYDRATION_NOTE_NEXT.md`
- `03 SHALL_READ_MASTER_SOP_NEXT.md`
- `10A SHALL_INIT_LIVE_SHADOW_NEXT.md`
- `10B SHALL_INIT_DESIGN_THREAD_STREAM_NEXT.md`
- `10C SHALL_MAINTAIN_SHADOW_PAIR_EACH_TURN_NEXT.md`
- `90 SHALL_READ_APPEND_ONLY_PROTOCOL_BEFORE_MUTATING_CORPUS.md`
- `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`

## Required Structural Elements In Local CSC SOP Docs
Each local CSC SOP doc SHOULD include, where relevant:
- purpose
- authority or linkage statement
- required behavior or procedure
- hazards or blockers
- interlink or next-doc references

## Failure Rule
If the local CSC SOP set is missing or materially incomplete, CSC SHALL report:
- `missing_required_sop_document` and/or
- `incomplete_required_sop_document`

and SHALL block claims of canonical cleanup readiness.

## Reason
A doctrine-enforcing cleanup system without its own project-local SOP set and repaired-archive control surface is performing authority theater.

## Current alignment note

- Refreshed at: `2026-04-16T17:55:01.867431+00:00`
- This SOP now treats `10_CSC_GENERAL_GUIDE_AND_UNIVERSALIZATION.md` and `11_CSC_SERVER_EXECUTION_METHODOLOGY_FOR_UNRELIABLE_PLANES.md` as required local CSC SOP documents.
- This refresh closes the gap where server execution methodology for unreliable planes existed as a standalone doc but not as an explicit required SOP surface.

## CTO required local extension of the SOP set — 2026-04-16
For CTO, the required local SOP set now includes the imported CSC documents plus the localized doctrine and SOP surfaces under `docs/cto_doctrine/` and `docs/cto_sop/`. A project-local doctrine instantiation is now part of the required control surface, not optional commentary.

## CTO remediation/evaluation/recurse sync — 2026-04-16
This control surface is synchronized after the latest PDVER remediation pass that localized CSC typing discipline, removed mutable global-state findings from CSC core surfaces, flattened scanner/helper seams to stay within cognitive limits, and reduced dict-smear inside the DB helper boundary layer. Freshness here reflects real post-remediation alignment, not timestamp theater.

## CTO artifact-core synchronization — 2026-04-17
This control surface is synchronized after the local artifact-core build pass that added `tools/cto_core`, the SQLite-backed artifact registry, typed ingest, and context pack construction. Freshness here reflects the new non-extension core plane and its holonic bindings, not timestamp theater.

## CTO extension projection synchronization — 2026-04-17
This control surface is synchronized after the local-core-to-extension projection bridge build that added published extension bundles, a pure extension bundle parser, and explicit bundle import into extension scoped-pack cache. Freshness here reflects the projection bridge mutation and its operator/import path, not timestamp theater.

## CTO bundle promotion synchronization — 2026-04-17
This control surface is synchronized after the bundle-promotion and default-resolution build that separated active bundle from preferred bundle, added explicit promotion states, and tied injection/export defaults to promotion ordering rather than active editor focus. Freshness here reflects the promotion-resolution mutation and not timestamp theater.

## CTO signed promotion gate synchronization — 2026-04-17
This control surface is synchronized after the signed-promotion-gate build that added operator signature requirements, promotion classes, class-specific gate evidence, and adjudication entries that preserve the exact gate evidence authorizing promoted transitions. Freshness here reflects the signed-gate mutation and not timestamp theater.

## CTO local verifier plug synchronization — 2026-04-17
This control surface is synchronized after the local-verifier-plug build that projects machine-derived verifier evidence from local-core and CSC surfaces into extension bundle imports, persists that snapshot per workstream, and merges machine evidence with operator evidence during promotion authorization. Freshness here reflects the verifier-plug mutation and not timestamp theater.

## CTO verifier-class adapter synchronization — 2026-04-17
This control surface is synchronized after the verifier-class-adapter build that introduced explicit machine authority adapters, class-declared required adapter sets, adapter-aware promotion blocking, and adjudication output that preserves required adapter IDs plus machine adapter results. Freshness here reflects the verifier-adapter mutation and not timestamp theater.

## CTO promotion certificate chain synchronization — 2026-04-20
This control surface is synchronized after the promotion-certificate-chain build that introduced prior-certificate references, chain depth, append-only promotion certificate ledgers, and operator surfaces that expose latest certificate plus ledger traversal per workstream. Freshness here reflects the certificate-chain mutation and not timestamp theater.

## CTO branch fork and merge topology synchronization — 2026-04-21
This control surface is synchronized after the branch-fork-and-merge topology build that introduced parent-certificate sets, explicit topology kinds, thread-wide certificate topology ledgers, and operator surfaces for explicit merge-parent declaration and cross-branch certificate traversal. Freshness here reflects the topology mutation and not timestamp theater.

## CTO topology edge adjudication synchronization — 2026-04-22
This control surface is synchronized after the topology-edge-adjudication build that introduced explicit parent-edge classes, edge rationale, parent-edge readback in certificate and decision surfaces, and a compact thread topology graph for operator inspection. Freshness here reflects the topology-edge mutation and not timestamp theater.

