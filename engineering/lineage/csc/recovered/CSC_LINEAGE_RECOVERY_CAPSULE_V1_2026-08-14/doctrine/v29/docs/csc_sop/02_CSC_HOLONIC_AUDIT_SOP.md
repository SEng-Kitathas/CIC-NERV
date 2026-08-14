# 02 — CSC HOLONIC AUDIT SOP

## Purpose
This SOP defines how CSC audits active lab subsystems as holons.

A subsystem is not clean merely because it compiles.
It is clean only when its purpose, boundary, interface, invariants, and hazards are explicit enough to survive maintenance and mutation pressure.

## Required Holonic Questions
For each CSC-relevant subsystem, record:
1. **Purpose** — why it exists
2. **Boundary** — what it owns, what it assumes, where it ends
3. **Interface** — how it communicates with other surfaces
4. **Invariants** — what must remain true
5. **Hazards** — how it can fail or become misleading

## Current Required Subsystems
CSC SHALL be able to audit at least:
- `code_slop_cleanup_csc.py`
- `pdver_lab_hardening_cycle.py`
- `repeatable_shadow_runtime_queue_runner.py`
- `shadow_runtime_quipu_evaluator.py`
- `lifecycle_batch_router.py`
- `quipu_outcome_sidecar_expansion.py`
- `full_model_experiment_contract_builder.py`

## Audit Rule
A subsystem fails holonic clarity if any of the following are true:
- purpose is broader than what the code actually does
- boundary is unclear or mixed
- interface depends on hidden global assumptions
- invariants are implicit only
- hazards are not named even though they are load-bearing

## Output Expectation
Holonic audit output SHOULD include:
- subsystem id
- purpose
- boundary
- interface
- invariants
- hazards
- doctrine tension if present
- next seam

## Promotion Rule
A subsystem SHALL NOT be promoted by CSC merely because it has style cleanliness.
Holonic opacity blocks promotion even when syntax/tests pass.

## Hazard Focus
CSC SHALL specifically watch for:
- wrapper theater pretending to be a subsystem
- god-node accumulation
- specimen/governance contamination
- boundary smear through dict/json payloads
- hidden machine-local assumptions

## Current alignment note

- Refreshed at: `2026-04-16T14:01:29.875370+00:00`
- This SOP has been re-reviewed against the always-on tri-doctrine stack: Omega, Unified Code Doctrine, and the repaired PCMMAD archive.
- This refresh acknowledges the CSC general guide, universal-root CSC, target-aware holon profiles, shadow-only runtime class-marker emission, the three-way runtime judgment split, relation/temporal/phase-aware law, recovery recognition, hysteresis bridge layers, the cross-plane lifecycle ladder, the runtime trace-matrix bridge, the coverage audit, and the now-integrated auto-drift sentinel gate in the lifecycle build path as current load-bearing control surfaces.
- Required control surfaces have been refreshed so CSC freshness and mutation-lag enforcement remain truthful after the latest integrated lifecycle-gate pass.

## CTO current required subsystems — 2026-04-16
For CTO, current required subsystems include at minimum the content controller (`code/cto_extension/content.js`), popup surface (`code/cto_extension/popup.js`), options/archive surface (`code/cto_extension/options.js`), CSC entrypoint, and CSC universal runner. These are now the active local holonic audit surfaces.

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

