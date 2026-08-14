# 09 — CSC SOP FRESHNESS AND MUTATION-LAG SOP

## Purpose
This SOP defines how CSC verifies that required control-surface documents are not only present, but also fresh enough for the current experimental heat.

Presence alone is not enough.
A required SOP set can exist and still be lagging behind active lab mutation.

## Required checks
CSC SHALL check:
- latest modification time of each required local CSC SOP document
- latest modification time across the required local CSC SOP set
- latest meaningful lab mutation time
- delta between latest meaningful lab mutation and latest required SOP update
- delta between current time and latest required SOP update

## Meaningful lab mutation
CSC SHALL prefer meaningful mutation surfaces over self-generated cleanup outputs.
At minimum, meaningful mutation SHOULD include:
- code changes in `code/*.py`
- active lab output artifacts outside CSC's own report directory
- experiment, runtime, routing, sidecar, contract, and queue outputs

CSC SHALL avoid treating CSC’s own report emission as sufficient evidence that SOP freshness is current.

## Failure classes
CSC SHOULD be able to report:
- `stale_required_sop_document`
- `stale_required_sop_set`
- `sop_mutation_lag`

## Default policy pressure
During active experiment heat, CSC SHOULD block canon-clean claims when:
- required SOP docs are materially older than the latest meaningful lab mutation by more than the configured lag window
- the overall required SOP set has not been refreshed within the configured active-heat freshness window

## Hazard
Naive timestamp enforcement is also bad.
CSC SHALL distinguish:
- static archive doctrine that is not expected to change every hour
- local active control surfaces that should track current experiment reality

## Output expectation
CSC SHOULD emit a freshness report showing:
- document path
- modified_at
- age_seconds
- stale flag
- mutation_lag_seconds where relevant
- policy thresholds used

## Current alignment note

- Refreshed at: `2026-04-16T14:01:29.875370+00:00`
- This SOP has been re-reviewed against the always-on tri-doctrine stack: Omega, Unified Code Doctrine, and the repaired PCMMAD archive.
- This refresh acknowledges the CSC general guide, universal-root CSC, target-aware holon profiles, shadow-only runtime class-marker emission, the three-way runtime judgment split, relation/temporal/phase-aware law, recovery recognition, hysteresis bridge layers, the cross-plane lifecycle ladder, the runtime trace-matrix bridge, the coverage audit, and the now-integrated auto-drift sentinel gate in the lifecycle build path as current load-bearing control surfaces.
- Required control surfaces have been refreshed so CSC freshness and mutation-lag enforcement remain truthful after the latest integrated lifecycle-gate pass.

## CTO freshness scope sync — 2026-04-16
For CTO, freshness pressure now explicitly includes the localized doctrine and SOP surfaces under `docs/cto_doctrine/` and `docs/cto_sop/`, not only the imported CSC set. Mutation-lag evaluation should therefore consider both imported and localized governance surfaces when judging project freshness.

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

