# 10 — CSC GENERAL GUIDE AND UNIVERSALIZATION

# CSC general guide and universalization

## What CSC is

CSC means **Code-Slop Cleanup**.

That name undersells it.

In practice CSC is not a generic linter and not just a cleanup script. It is a **doctrine-aware audit and hardening loop** that checks whether a code surface still obeys the tri-doctrine stack:

- CODEX OMEGA
- Unified Code Standards Doctrine
- repaired PCMMAD archive doctrine

CSC exists to stop three failure modes:

1. code drifting into naive implementation shape
2. experiments outrunning their control surfaces and SOP updates
3. local convenience being mistaken for universal law

So CSC should be read as:

- a code-quality pressure engine
- a doctrine coverage engine
- a control-surface freshness engine
- a promotion/gating engine

It is a **lab governance subsystem**, not only a style pass.

## What CSC checks

CSC currently checks at least these surfaces:

- required SOP/control-surface presence
- required SOP freshness against meaningful mutation
- doctrine coverage
- holonic clarity
- anti-pattern residue
- typed surface and boundary integrity
- idiomatic expression / cognitive conservation
- promotion-readiness pressure
- self-audit of CSC itself

Typical findings include:

- `raw_json_boundary_bypass`
- `uses_any_type`
- `broad_asdict_projection`
- `silent_exception_handler`
- `too_long_function`
- `too_many_parameters`
- `too_deep_nesting`
- `stale_required_sop_document`
- `sop_mutation_lag`

## What CSC is not

CSC is not:

- a generic formatting tool
- a taste-based style engine
- an authority substitute for experiments
- a guarantee that a system is correct
- permission to promote artifacts without separate evidence

CSC should never be used to claim:

- “the system is solved”
- “the runtime is justified”
- “the doctrine is complete”

It only says whether the inspected surface is currently in or out of doctrine-clean condition under its active rules.

## The two forms of CSC

CSC now exists in two valid forms.

### Form 1: local host CSC

This is the original form.

It runs against the host project directly and writes reports into that host project’s audit/output root.

For this lab, the host form is:

- target project root = `pcmmad_lab`
- docs root = `pcmmad_lab/docs/csc_sop`
- output root = `pcmmad_lab/data/pdver_lab_hardening_2026-04-14`

This form is appropriate when:

- CSC is auditing its home project
- the control surfaces are meant to live inside that project
- the audit outputs are part of the host project’s own continuity and maintenance trail

Strengths:

- simple
- direct
- ideal for self-audit and host hardening

Risk:

- can accidentally look “universal” when it is really only locally embodied

### Form 2: universal-root shadow-target CSC

This is the generalized form.

The doctrine stays universal, but the bindings become runtime-supplied:

- target project root
- docs root
- output root
- repaired archive root
- holon profile

This form is appropriate when:

- the doctrine is universal
- the target project is not the CSC host project
- we want truthful audit results without mutating the target’s own output/control surfaces

For TQ2, the safe form is:

- target project root = `pcmmad_tq2_geometric_lab`
- output root = external shadow audit workspace
- docs root = materialized universal SOP copy in the external shadow workspace
- target project remains read-only from CSC’s perspective

Strengths:

- doctrine stays universal
- target project is audited truthfully
- local path coupling does not masquerade as doctrine
- no live-project-risk from the audit outputs

Risk:

- if profile/binding layers are incomplete, coupling noise can be mistaken for target failure

## Why the universal form mattered

The key doctrine point is:

> the SOP law is universal; only the embodiment was local

So the correct move was not:

- weaken CSC for TQ2
- invent a separate TQ2 doctrine
- pretend the universal SOP set changed

The correct move was:

- decouple project-root assumptions
- decouple output-root assumptions
- decouple docs-root assumptions
- decouple holonic profile assumptions

That allows one doctrine engine to inspect many projects truthfully.

## Server execution methodology under unreliable planes

CSC universalization is not only about path bindings and holon profiles.
It also requires a truthful execution method when some planes are flaky.

Under degraded conditions, CSC-aligned operation SHALL prefer:
- operator-side server-native project execution routes
- operator-side direct local subprocess / python execution
- durable runner scripts committed into the operator-side project and then executed there
- assistant/model-side execution only when it is materially better or faster and stronger operator-side routes are not the right choice for that step

The operational rule is:
**use the strongest surviving plane, not the prettiest plane — and prefer the operator-side plane when it is available and sufficient.**

This means:
- inspect target root, interpreter, dependencies, and output destination first
- materialize durable runner scripts for load-bearing work
- keep stdout/stderr and result artifacts server-side
- inspect artifacts directly before making claims
- stop retrying known-brittle bridge/queue routes once they have shown instability

This law is now formalized in:
- `11_CSC_SERVER_EXECUTION_METHODOLOGY_FOR_UNRELIABLE_PLANES.md`
- `docs/SERVER_EXECUTION_METHODOLOGY_FOR_UNRELIABLE_PLANES_2026-04-16.md`

## Core architecture of CSC

At a high level CSC has these layers:

1. **runtime bindings**
   - where the target root, docs root, output root, archive root, and holon profile come from
2. **core cycle**
   - scan, probe, verify, recurse, summarize
3. **doctrine passes**
   - SOP availability, SOP freshness, anti-pattern inversion, holonic audit, doctrine coverage
4. **event runner / entrypoint**
   - write top-level event report and make the audit externally readable
5. **gate usage**
   - use the report as a precondition for further mutation or promotion-sensitive work

This separation matters.

CSC should never collapse:

- bindings
- doctrine rules
- target profile
- report writing
- experiment logic

into one opaque script.

## Holonic profile law

One of the most important lessons from generalizing CSC was this:

> the holonic audit is universal in law but profile-specific in embodiment

That means:

- the law “subsystems must have explicit purpose, boundary, interface, invariants, and hazards” is universal
- the actual subsystem set under test depends on the target project

For `pcmmad_lab`, the relevant holons are CSC/lifecycle/shadow-evaluator centered.

For `pcmmad_tq2_geometric_lab`, the relevant holons are things like:

- bootstrap
- runtime kernel
- inference harness
- realized mainline lane
- holonic recipe search

If CSC reuses the wrong holon profile, the audit becomes false.

So universal CSC must always pair:

- **universal doctrine**
with
- **target-aware holon profile**

## When CSC is safe to run on another project

CSC is safe to run on another project when all of these are true:

- doctrine stays universal
- target root is explicit
- output root is external or otherwise controlled
- required control surfaces are explicit
- holon profile matches the target project
- report paths can represent external universal control surfaces honestly

CSC is not safe when:

- target root is implicit
- host-project paths are treated as universal doctrine
- the output root writes into the target project without that being intended
- holonic profile still points at unrelated subsystem files

## How CSC becomes a universal lab tool

CSC becomes a universal lab tool by keeping the doctrine fixed and lifting the embodiment.

That means:

### 1. universal doctrine engine

Keep one engine for:

- anti-pattern mapping
- doctrine coverage
- SOP freshness
- promotion/gating logic

Do not fork these per project unless doctrine itself changes.

### 2. runtime bindings

Make these explicit at invocation time:

- target project root
- docs root
- output root
- repaired archive root
- holon profile

### 3. target-aware holon profiles

Keep a profile registry for target families.

Examples:

- `pcmmad_lab`
- `pcmmad_tq2_geometric_lab`
- future lab projects

### 4. shadow-target execution by default

For non-host projects, prefer:

- external output root
- materialized universal SOP copy
- read-only target audit behavior

This preserves thread life and avoids accidental mutation.

### 5. explicit result classes

Universal CSC should distinguish:

- host-clean
- target-clean
- target-doctrine-fail
- target-profile-mismatch
- target-control-surface-incomplete
- target-audit-not-yet-trustworthy

That keeps engineering failures separate from target failures.

## What universal CSC still should not do

Even as a universal tool, CSC still should not:

- become a universal proof engine
- override experiment evidence
- auto-promote artifacts
- mutate target projects by default
- confuse raw runtime health with lawful alignment

It remains a governance/audit tool, not a universal judge of truth.

## Recommended operating pattern

### For the host project

Use local host CSC as a standing gate:

- before major mutation
- after major mutation
- before promotion-sensitive transitions

### For other projects

Use universal-root shadow-target CSC first:

- audit safely in an external workspace
- verify the holon profile is correct
- separate coupling noise from true target failures
- only later consider whether a native in-project output form is justified

## Current state after universalization

At the time of this guide:

- CSC is clean on `pcmmad_lab`
- CSC can run safely against `pcmmad_tq2_geometric_lab` in shadow-target mode
- TQ2 now passes universal SOP and holonic profile checks under the generalized runner
- TQ2 still has substantive code-doctrine failures that are now cleanly visible as target failures rather than adapter noise

That is the correct end state for this phase.

## Best concise summary

CSC is a doctrine-aware audit and hardening loop.

Its two valid forms are:

- **local host CSC** for the host project’s own maintenance and gating
- **universal-root shadow-target CSC** for auditing other projects truthfully under the same universal doctrine

CSC becomes a universal lab tool not by weakening doctrine, but by:

- universalizing bindings
- universalizing external control-surface handling
- making holonic profiles target-aware
- defaulting to shadow-target execution for non-host projects

That preserves one law while allowing many truthful embodiments.

## Current alignment note

- Refreshed at: `2026-04-16T18:08:21.194523+00:00`
- This guide now explicitly includes the stronger operator-side-first execution rule rather than only the weaker strongest-plane wording.
- Universal-root / shadow-target CSC now states plainly that operator-side save/store/edit/execute/mutate/readback is the default when available and sufficient.


## Universalization rule
CSC should pressure reusable invariants, boundaries, and control surfaces rather than project-name theater or one-off convenience logic.


## Pressure rule
When a project-local seam reveals a broader class of doctrine defect, CSC should preserve the local seam while also deriving the stronger reusable primitive where the evidence supports it.

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

