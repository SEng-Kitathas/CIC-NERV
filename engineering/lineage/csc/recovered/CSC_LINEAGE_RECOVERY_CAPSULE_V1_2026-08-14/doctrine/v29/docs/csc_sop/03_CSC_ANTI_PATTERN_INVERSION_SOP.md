# 03 — CSC ANTI-PATTERN INVERSION SOP

## Purpose
This SOP defines how CSC performs anti-pattern inversion instead of only issue listing.

CSC SHALL NOT stop at:
- “bad pattern detected”
- “style issue exists”
- “file is noisy”

It SHALL derive the target invariant or primitive that should replace the anti-pattern.

## Inversion Procedure
For each finding class:
1. identify the anti-pattern
2. identify the structural harm
3. derive the target invariant
4. derive the target primitive or boundary shape
5. identify demotion trigger if the fix is not embodied

## Required Output Fields
Each anti-pattern inversion entry SHOULD contain:
- file
- anti-pattern
- why it is naive / mixed / misleading
- target invariant
- target primitive or idiomatic expression
- doctrine class
- promotion blocker
- next embodiment action

## Example Inversion Classes
- `uses_any_type` → target invariant: invalid shape should not survive type surface
- `raw_json_boundary_bypass` → target invariant: serialization belongs at explicit boundary utility only
- `machine_absolute_path` → target invariant: runtime location must be derived from explicit root or config, not machine-local literals
- `dataclass_raw_projection` → target invariant: artifact projection must remain boundary-explicit and inspectable
- `dict_smear_in_types` → target invariant: operational boundaries must be typed, not anonymous payloads

## Non-Negotiable
CSC SHALL distinguish:
- a local convenience hack
- a transitional exception
- a doctrine violation

It SHALL NOT label all three as the same thing.

## Hazard
Anti-pattern inversion becomes fake if it only rewrites findings into nicer prose without yielding a stronger primitive or cleaner boundary.

## Current alignment note

- Refreshed at: `2026-04-16T14:01:29.875370+00:00`
- This SOP has been re-reviewed against the always-on tri-doctrine stack: Omega, Unified Code Doctrine, and the repaired PCMMAD archive.
- This refresh acknowledges the CSC general guide, universal-root CSC, target-aware holon profiles, shadow-only runtime class-marker emission, the three-way runtime judgment split, relation/temporal/phase-aware law, recovery recognition, hysteresis bridge layers, the cross-plane lifecycle ladder, the runtime trace-matrix bridge, the coverage audit, and the now-integrated auto-drift sentinel gate in the lifecycle build path as current load-bearing control surfaces.
- Required control surfaces have been refreshed so CSC freshness and mutation-lag enforcement remain truthful after the latest integrated lifecycle-gate pass.

## CTO anti-pattern inversion sync — 2026-04-16
Current CTO-specific anti-pattern classes include provider-specific logic smeared into core continuity logic, snapshot fan-out masquerading as storage truth, mutable titles used as primary thread identity, silent injection failure, and imported governance surfaces left unlocalized after doctrine binding.

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

