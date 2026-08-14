# 11 — CSC SERVER EXECUTION METHODOLOGY FOR UNRELIABLE PLANES

## Purpose
This SOP makes the server-execution methodology for unreliable planes a first-class CSC control surface.

It exists so the lab does not silently drift into brittle bridge/queue habits when a stronger surviving server-native plane is available.

## Authority linkage
This SOP operationalizes the already-stated local-first / strongest-plane discipline under degraded execution conditions.

It SHALL be read together with:
- `00_CSC_START_AND_AUTHORITY.md`
- `05_CSC_REQUIRED_SOP_SET.md`
- `09_CSC_SOP_FRESHNESS_AND_MUTATION_LAG_SOP.md`
- `10_CSC_GENERAL_GUIDE_AND_UNIVERSALIZATION.md`
- `docs/SERVER_EXECUTION_METHODOLOGY_FOR_UNRELIABLE_PLANES_2026-04-16.md`

## Core rule
**Use the strongest surviving plane, not the prettiest plane.**

## Operator-side-first rule
CSC SHALL default to the operator's side for as much as possible.

If the operator's side can:
- save it
- store it
- edit it
- execute it
- mutate it
- materialize it
- read it back

then that path SHOULD be the default.

Assistant/model-side execution SHOULD only take the lead when it is **materially better or faster** for the specific step.
This exception SHALL be explicit rather than silent.

If a bridge, queue, or interactive orchestration path fails repeatedly, CSC-aligned operation SHALL stop politely retrying the fragile route and SHALL move work onto the server-native path that actually lands.

## Required plane order under instability
When execution surfaces are degraded, prefer this order:
1. operator-side server-native project execution routes
2. operator-side direct local subprocess / python execution
3. durable script files committed into the operator-side project and then executed there
4. assistant/model-side execution only when it is materially better or faster and the stronger operator-side route is not the right choice for that step

## Required operating method
### 1. Inspect first
Before mutation or execution, verify:
- target root
- runtime/interpreter path
- dependent artifacts
- output destination

### 2. Materialize durable runners for load-bearing work
If the run matters, write a durable project-local script.
The operator-side/server-side environment SHOULD execute that script and the script SHOULD own output/log writing.

### 3. Prefer direct local execution when queue/bridge paths are unstable
When queue or bridge paths are failing, CSC SHALL prefer the stable operator-side server-native execution plane instead of repeatedly retrying the brittle path or drifting to assistant-side execution out of convenience.

### 4. Make writes incremental and resumable
Long runs SHOULD:
- write progress incrementally
- flush after each item or step
- support resume
- capture per-item failures without aborting the entire run

### 5. Separate machine truth from conversational truth
A run is only execution-truthful when the machine can prove it through one or more of:
- job id
- pid
- stdout/stderr path
- output artifact
- durable summary JSON

CSC SHALL treat readback artifacts as higher authority than chat memory.

## Required anti-pattern rejections
CSC SHALL treat the following as execution anti-patterns:
- leaving an available operator-side path without a material speed/capability reason
- repeatedly retrying a known-failing bridge route
- relying on a known-unstable queue for long-running work
- using one giant inline command where a durable runner script is safer
- claiming success before artifact readback
- confusing started with completed

## Universalization implication
For shadow-target / non-host audits, this methodology strengthens the existing universal-root CSC form:
- prefer server-side runner scripts
- keep outputs on disk
- inspect artifacts directly
- widen only after the smoke run proves stability

## Enforcement implication
Where relevant, CSC SHOULD pressure target workflows toward:
- durable script materialization
- server-side execution
- resumable writes
- artifact-first readback
- explicit rejection of repeated brittle-plane retries

## Failure rule
If a workflow shows repeated plane fragility and the project continues to depend on the brittle route instead of escalating to the stronger surviving plane, CSC SHOULD surface this as doctrine failure / operational anti-pattern rather than treating it as harmless convenience.

## Current alignment note

- Refreshed at: `2026-04-16T18:08:21.194523+00:00`
- This SOP now explicitly encodes the stronger operator-side-first rule: save/store/edit/execute/mutate/readback/materialize on the operator's side by default when that path is available and sufficient.
- Assistant/model-side execution is now explicitly treated as an exception that requires material speed or capability advantage.


## Preferred plane order
1. operator-side server-native project execution
2. operator-side direct local Python or subprocess execution
3. durable scripts committed into the project and then executed there
4. bridge or convenience paths only when materially stronger for that step


## Required outputs
Server-side execution on unreliable planes should leave inspectable outputs such as paths, reports, machine-readable artifacts, and readback confirming what actually happened.

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

