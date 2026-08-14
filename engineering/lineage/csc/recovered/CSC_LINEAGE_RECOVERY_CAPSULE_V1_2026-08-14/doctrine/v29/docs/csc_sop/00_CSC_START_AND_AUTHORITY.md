# 00 — CSC START AND AUTHORITY

## Purpose
This document defines the authority stack and operating start point for **Code-Slop Cleanup (CSC)** inside `pcmmad_lab`.

CSC is not a generic linter.
CSC is a doctrine-enforcing cleanup and hardening subsystem for the lab.

## Authority Stack
When CSC runs, authority resolves in this order:
1. PCMMAD archive bootstrap and master SOP chain
2. UNIFIED CODE STANDARDS DOCTRINE v1.2
3. CODEX OMEGA v2.0
4. project-local CSC SOP set
5. local implementation convenience

Local convenience SHALL NOT override the archive or code doctrine.

## Required Upstream Archive Documents
CSC SHALL assume the following archive documents are required and available to the operator/model pair:
- `00 SHALL_READ_BOOTSTRAP_INIT_PROTOCOL_FIRST.md`
- `01_LIVE_SHADOW_PROTOCOL.md`
- `02_DESIGN_THREAD_STREAM_PROTOCOL.md`
- `03 SHALL_READ_MASTER_SOP_NEXT.md`

These documents define ingress, continuity, PDVER, promotion, rescue, and anti-drift behavior.

## Local CSC Obligations
CSC SHALL:
- distinguish discussion from implementation pressure
- treat all inbound code/artifacts as controlled evidence
- run `PROBE → DERIVE → VERIFY → EMBODY → RECURSE`
- enforce typed and inspectable boundaries where feasible
- preserve granular probes needed for macro synthesis without silently promoting them
- produce artifacts that are operator-legible and machine-usable

## Hard Failure Cases
CSC is in violation if it:
- reports cleanliness while using naive or self-contradictory checks
- treats named probes as canonical merely because they exist
- deletes granular probes that are still needed to solve macro seams
- emits cleanup theater without embodiment or verification
- ignores missing local SOP surfaces or missing required upstream archive references

## Interlink Requirements
This file SHALL be read with:
- `01_CSC_DOCTRINE_LINKAGE.md`
- `02_CSC_HOLONIC_AUDIT_SOP.md`
- `03_CSC_ANTI_PATTERN_INVERSION_SOP.md`
- `04_CSC_PROMOTION_AND_RECURSION_SOP.md`
- `10_CSC_GENERAL_GUIDE_AND_UNIVERSALIZATION.md`
- `11_CSC_SERVER_EXECUTION_METHODOLOGY_FOR_UNRELIABLE_PLANES.md`

## Immediate Use Rule
Before expanding CSC behavior, check:
1. required upstream archive docs are available
2. this local CSC SOP set is available
3. the intended CSC mutation is traceable to doctrine or SOP pressure

## Current alignment note

- Refreshed at: `2026-04-16T17:55:01.867431+00:00`
- This authority/start doc now interlinks the CSC general guide and the explicit unstable-plane server execution methodology SOP.
- This refresh makes reliable server execution under degraded planes part of the stated local CSC authority/start surface.

## CTO local authority synchronization — 2026-04-16
The imported CSC authority stack is now synchronized to CTO-local doctrine surfaces. For CTO, authority is exercised through both the imported CSC control set and the local doctrine bindings under `docs/cto_doctrine/` and `docs/cto_sop/`, rather than through imported CSC docs alone.

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

