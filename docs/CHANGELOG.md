# Changelog

## 0.2.3 — Observation Integrity

- Added typed adapter `Observation` values: observed / partial / unavailable.
- Added `ObservationState` with current / degraded / unavailable availability.
- Adapter failure no longer fabricates USB absence or Wi-Fi disconnection.
- Preserves last known domain state when the observation source is unavailable.
- Health becomes `unknown` when telemetry is unavailable and `warning` when degraded.
- Health derivation now occurs after a typed observation-cycle barrier.
- Snapshot schema bumped to v2 and restores enum-backed observation/health state.
- Event journal explicitly serializes enums and omits internal observation-heartbeat events.
- Added regression tests for false-absence prevention, partial telemetry, continuity, and journal hygiene.

## 0.2.2 — Continuity and Causal Journal

- Runtime now hydrates `state/world.json` before beginning a new process lifetime.
- State hydration is silent: restoring embodiment does not fabricate events.
- `RuntimeStarted` is the first new durable event after hydration and reports restored entity count.
- Event observers now record a cause before typed systems may publish derived effects.
- Health-derived events therefore follow their triggering component event in the journal.
- Normal CPU, temperature, storage, memory, signal, and bitrate churn remains live world state but is not durable history.
- Added temperature warning/critical health thresholds.
- Added schema version to world snapshots and typed component decoding for restart continuity.

## 0.2.1 — Event Hygiene

- Separated current-state sampling from durable operational event significance.
- Added Systems-holon materiality policy.
- Uptime, tiny memory/storage fluctuations, and link-rate churn remain live world state without flooding the journal.
- Health threshold crossings, connectivity changes, USB state changes, large telemetry shifts, and structural Wi-Fi changes remain durable events.
- Added tests for event significance and journal filtering.

## 0.2.0 — Slice 002: Persistent Runtime

- Added long-running `cic-runtime`.
- Added graceful SIGINT/SIGTERM lifecycle.
- Added typed append-only JSONL event journal.
- Added config-driven collection/snapshot cadence.
- Moved health thresholds into configuration data.
- Added shared bootstrap path for one-shot and persistent modes.
- Added systemd user-service install/uninstall helpers.
- Expanded tests for journaling and runtime configuration.

## 0.1.0 — Slice 001: Self Awareness

- Added Engage and Tenda entities.
- Added Linux and Tenda adapters.
- Added typed components, WorldState, EventBus, HealthSystem, and console projection.
- Added atomic world-state snapshot.

### 0.2.3 RC3 static-gate cleanup

- No semantic/runtime changes from RC2; this candidate only closes the static `git diff --check` whitespace gate.
- Treat incomplete connected `iw link` snapshots as PARTIAL observation quality.
- Stop journaling transient missing signal fields as durable Wi-Fi domain changes.
- Treat normal frequency/channel roaming as live radio telemetry rather than durable operational history.
- Preserve link/disconnect, SSID, interface, and IP structural transitions as material.
