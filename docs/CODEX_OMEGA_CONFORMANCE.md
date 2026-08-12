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
5. World-state serialization deliberately mirrors registered component dataclasses and is versioned, but does not yet have explicit per-version migrations.
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
