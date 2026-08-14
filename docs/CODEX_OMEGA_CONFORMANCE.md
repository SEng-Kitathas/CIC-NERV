# Codex Omega Conformance — Personal CIC

**Scope:** current software baseline, not a claim of universal correctness.

## Active constitutional constraints

- **Promotion honesty:** each slice is bounded and versioned; experimental RF work remains under `lab/`.
- **Resolve or represent uncertainty:** adapter/probe failure must not become fabricated device state.
- **Evidence-proportionate verification:** each promoted slice requires targeted tests plus full regression.
- **Semantic home:** adapters own OS/vendor observation mechanics; world components own normalized facts; systems own derivation; presentation owns projection only.
- **Strongest practical enforcement:** closed health/observation states are represented as enums; unavailable observations cannot carry a new domain value.
- **Causal/provenance integrity:** durable component causes precede derived health effects; high-rate samples stay out of semantic history.
- **Stable semantic identity:** derived telemetry sources identify the measurement policy, not transient winning sensor labels.
- **Complexity budget:** systemd remains process supervisor; the runtime does not grow a second supervisor.

## Current residual seams

These are explicit backlog, not hidden compliance claims:

1. `Entity.components`, the event bus, and journal codec still contain broad dynamic carrier types at core seams.
2. `Intent` is still stringly and uses `dict[str, Any]`; control authority is not yet embodied.
3. `UsbDeviceState.mode` is still an open string despite a currently small known state family.
4. A single `ObservationState` currently assumes one primary adapter per entity. Multi-source entities will need keyed source-observation state before promotion.
5. World-state serialization deliberately mirrors registered component dataclasses. The writer remains schema v2 and the reader explicitly admits evidenced v1/v2/v3 historical lineage, but explicit per-version migration functions are still not embodied.
6. Tenda interface attribution still assumes the CIC's relevant WLAN surface and has not yet been proven against a host with multiple unrelated Wi-Fi adapters.

## Promotion rule

A residual becomes P0 only when it creates a demonstrated correctness, authority, continuity, or change-safety defect in the next vertical slice. The existence of a static-code smell alone does not outrank useful CIC capability.

## Slice 003 conformance

- **Semantic home:** live domain truth remains `WorldState`; presentation is a projection.
- **Boundary integrity:** browser code cannot query hardware/native services directly.
- **Authority integrity:** the presentation server exposes GET/HEAD only; mutation verbs are rejected.
- **Scoped authority:** WLAN association is rendered as WLAN state, not promoted to Internet capability.
- **Concurrency ownership:** `WorldState` owns synchronization introduced by the concurrent presentation reader.

## 0.3.1 conformance

- **Remote observation ≠ reality:** provider payloads retain provider timestamps and local retrieval freshness.
- **Failure honesty:** provider failure preserves last-known domain value and degrades ObservationState instead of inventing weather/alert state.
- **Semantic home:** remote polling lives in typed adapters/runtime, never in browser code.
- **Timescale integrity:** slow remote I/O is isolated from the local 5-second observation loop.
- **Negative evidence:** a successful NWS response containing zero active alerts is legitimate current negative evidence; an unavailable NWS request is not.
## 0.3.2 conformance

- **Semantic homes:** surface observation, model current, official forecast, official alerts, derived estimate, and event-feed projection remain distinct.
- **Evidence honesty:** unlike weather sources are compared by role, not blindly averaged.
- **Re-entry:** restored remote freshness is withdrawn for every new provider/derived estimate before presentation.
- **Materiality:** provider polling does not itself create feed/history; the WX feed reads material journal facts.
- **Native substrate:** AviationWeather and NWS linked-data endpoints are consumed through narrow typed adapters.

### Radar semantic home

Radar metadata authority lives in `RadarMosaicState`; raw image bytes remain adapter cache artifacts and do not become competing WorldState truth. Provider failure withdraws observation authority without inventing a new radar domain value.

## 0.3.4 radar context / loop conformance

- **Semantic home:** WorldState owns typed radar/context metadata; cache bytes/manifests remain adapter-owned artifacts.
- **Provenance:** each loop frame is hash-addressed with explicit WMS retrieval time; MRMS stream time remains only a stream-freshness witness.
- **Authority separation:** Census map context is reference geometry, not weather evidence; warning overlays retain radar-observation authority rules.
- **Materiality:** ordinary frame-set turnover and context retrieval-time refresh are sample telemetry; semantic context content and structural radar authority changes remain material.
- **Presentation boundary:** browser access is loopback-only and hash-checked; it does not contact NOAA/NWS/Census providers directly.


## 0.3.5 retained-observation conformance

- Retrieval failure is not silently equated with domain invalidity.
- Retained state is explicitly DEGRADED and reasoned, never presented as newly observed.
- Last-success time is preserved during retention.
- Re-entry requires fresh success before retention is eligible.
- Source-specific freshness policy, not an arbitrary failure counter, decides when retained authority expires.
## 0.3.6 / 003g current candidate conformance — Runtime Authority RC4

This section is an internal assurance assessment, not an external certification claim. RC7 remains the
target-verified authority until exact target gates promote a successor. Historical QA1 evidence remains
in `QUALITY_AUDIT_2026-08-13.md` and is not rewritten into present-tense authority.

- **G0 Build/existence:** the 003g source candidate imports and passes its source-local quality/regression gates; target promotion remains unearned.
- **G1 Type/boundary:** worker lifecycle is closed typed state; collection authority and process liveness are distinct propositions.
- **G2 State/protocol:** terminal worker failure cannot be normalized into graceful stop; durable writer ownership is an explicit lease state rather than an ambient assumption.
- **G3 Resource/effect:** provider/OS effects remain in adapters; presentation remains read-only; a failed enabled collection plane withdraws dependent read authority rather than serving an apparently healthy world surface.
- **G4 Temporal/concurrency:** worker start/stop/cycle/failure timing is explicit; failure wakes the runtime; single-writer `flock` prevents concurrent durable embodiment.
- **G5 Serialization/persistence:** no snapshot-schema mutation is introduced; RC7 semantic persistence remains absent. Runtime failure deliberately skips a forced final snapshot when authority cannot be established.
- **G6 Security/authority:** arbitrary terminal exception text is not projected/persisted; only bounded failure classification crosses the runtime metadata seam.
- **G7 Architecture/holonic:** runtime supervision, durable embodiment, WorldState, semantics, and presentation retain separate ownership. FIE is a bounded recurrence/search heuristic reconciled against OIG/EDG falsification; no universal grammar or new runtime god-object is introduced.
- **G8 Verification:** source-local tests/quality gates qualify only the candidate. Target worker-kill and competing-writer tests are required before promotion.
- **G9 Continuity/governance:** current authority is RC7 (`424c8ade...` / `d8ba2a50...`); 003g is explicitly candidate lineage; historical QA1/RC2D records remain historical.
- **G10 Supply chain:** MapLibre authored lock versus derived runtime materialization remains unchanged.
- **G11 Performance:** 003g makes no new performance claim. Semantic endpoint and persistence scaling remain measurement-triggered future work.

### Fractal-Isomorphism Engineering / OIG-EDG conformance

FIE is classified as **HEURISTIC / mechanism-search discipline**. The OIG/EDG EVAL First Pass is
**CLOSED AS EVALUATION — NON-CANONICAL** and explicitly found that 0/10 original candidate invariants
survived unchanged as universal primitives. Cross-domain/cross-scale reuse therefore requires explicit
query/frame, guarantee, intervention, acquisition limits, non-isomorphism breakpoints, target-native
embodiment, and claim-matched verification. The CIC-facing handoff is quarry/SOP input only.

### Additional residual seams accepted by QA1

- browser CSP still requires `unsafe-inline` for the current inline presentation implementation; S3/S4 presentation-sovereignty work should remove this when the frontend substrate earns that refactor;
- remote provider response-size/content-type bounds are inconsistent across adapters and should be hardened when that acquisition surface becomes the active pressure;
- the static `SITE 15 MI` label has a dormant generic-profile fallback to collection center when site anchoring is disabled; the configured target has an enabled site anchor, so the path is inactive but recorded;
- several domain/projector functions are large; splitting them solely to satisfy a line-count heuristic would violate abstraction-before-invariant discipline;
- Python build-backend reproducibility is not yet an exact target lock; do not call the source package hermetic.

