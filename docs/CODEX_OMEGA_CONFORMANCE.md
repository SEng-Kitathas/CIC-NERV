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
## 0.3.6 / 003f current candidate conformance — RC2D-R2-QA1

This section is an internal assurance assessment, not an external certification claim. The running
target and claim-matched gates retain veto authority.

- **G0 Build/existence:** authored source compiles/imports under the audit interpreter; full unit regression passes. A fresh map-capable deployment additionally requires materialized pinned MapLibre runtime bytes.
- **G1 Type/boundary:** configuration now parses strict booleans, finite numbers, structured arrays/maps, environment names, and source-provenanced site anchors at ingress. Broad dynamic carrier types remain explicit debt at ECS/event seams.
- **G2 State/protocol:** collection center, fixed site anchor, and live operator position are distinct; unavailable/current/degraded states and same-lineage traffic association remain explicit.
- **G3 Resource/effect:** vendor/remote acquisition remains in adapters. Presentation is read-only. Service install refuses an incomplete required presentation runtime.
- **G4 Temporal/concurrency:** worker stop returns actual quiescence; timeout is not success. Concurrent journal append is serialized. Runtime does not force a final snapshot while a state-mutating worker remains live.
- **G5 Serialization/persistence:** snapshot writer remains v2; known historical v1/v2/v3 are explicitly readable; unknown future versions fail closed. Explicit migrations remain debt.
- **G6 Security/authority:** loopback-only bind and GET/HEAD presentation authority remain; secrets stay environment-based; service adds no-new-privileges and restrictive umask. Inline script/style CSP remains accepted presentation debt at the current sovereignty level.
- **G7 Architecture/holonic:** no new generic provider manager or semantic god-object was introduced. Existing large functions are recorded as refactor pressure, not mechanically split without an invariant.
- **G8 Verification:** regression, concurrency, configuration, persistence, source-distribution, coverage, syntax, JSON, shell, and artifact-integrity evidence are retained by the QA audit. Human HMI acceptance remains separate.
- **G9 Continuity/governance:** promoted RC1B floor, open 003f slice, candidate chronology, donor/non-lineage distinction, and unearned RC2D-R2/QA1 status are explicit.
- **G10 Supply chain:** MapLibre source/version/archive digest and target Python direct dependency are configuration-controlled separately from authored source. Build-toolchain locking is not yet target-qualified.
- **G11 Performance:** no new quantitative performance claim is promoted by QA1. Operator reports of smoothness are useful target evidence but are not a benchmark.

### Additional residual seams accepted by QA1

- browser CSP still requires `unsafe-inline` for the current inline presentation implementation; S3/S4 presentation-sovereignty work should remove this when the frontend substrate earns that refactor;
- remote provider response-size/content-type bounds are inconsistent across adapters and should be hardened when that acquisition surface becomes the active pressure;
- the static `SITE 15 MI` label has a dormant generic-profile fallback to collection center when site anchoring is disabled; the configured target has an enabled site anchor, so the path is inactive but recorded;
- several domain/projector functions are large; splitting them solely to satisfy a line-count heuristic would violate abstraction-before-invariant discipline;
- Python build-backend reproducibility is not yet an exact target lock; do not call the source package hermetic.

