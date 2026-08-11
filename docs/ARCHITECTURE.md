# Architecture Baseline

## North star

**Sense → Understand → Act**

## Composition model

Entities are stable identities. Components carry capabilities, properties, and observed state.
Systems operate on matching components. Adapters terminate vendor / OS-specific ugliness at
the boundary. Presentation consumes normalized world state. Future controls emit intents rather
than directly manipulating devices.

## Holonic rule

A holon is simultaneously a coherent whole and a valid part of a larger whole. A holon earns
a boundary when it has a clear purpose, ownership boundary, interface, invariants, and hazards.

## Slice 001 — Self Awareness

The Systems holon observes the Engage and Tenda, normalizes telemetry into components,
derives health, emits typed events, and embodies a world snapshot.

## Slice 002 — Persistent Runtime

The one-shot cognition cycle becomes a persistent process:

1. Runtime starts and emits `RuntimeStarted`.
2. LinuxHostAdapter and TendaU11ProAdapter collect on a configured interval.
3. WorldState accepts only changed components.
4. `ComponentUpdated` events flow synchronously through systems.
5. HealthSystem derives normalized `HealthState`.
6. Every typed event is appended to `logs/events.jsonl`.
7. WorldState is atomically embodied to `state/world.json`.
8. SIGINT/SIGTERM cause a final snapshot and `RuntimeStopping`.
9. systemd owns process resurrection; runtime code does not reinvent supervision.

## Runtime ownership

The runtime owns scheduling and lifecycle only. It does **not** own:

- hardware semantics,
- health semantics,
- UI state,
- device control logic,
- RF interpretation.

Those remain in adapters, systems, presentation, and future control holons.

## Anti-grimoire invariants

- Vendor/OS details stop at adapters.
- Shared world state is canonical.
- Systems own behavior.
- UI does not own operational truth.
- UI will emit intents rather than direct side effects.
- Configuration is data.
- Research code stays out of runtime.
- Odd hardware gets adapters, not exceptions in core.
- Process supervision is delegated to systemd rather than reimplemented.


## 0.2.2 continuity invariant

Embodiment must survive process death. `state/world.json` is therefore read as well as written.
A restarted runtime silently restores the previous typed world before sampling current reality.
Only differences between embodied prior state and new observations can become new events.

The durable journal is causal, not merely chronological by call stack accident: observers record
an event before typed systems may derive and publish consequences from it.

High-frequency telemetry and durable history are intentionally separate concerns. WorldState is
current truth; the event journal is semantic operational memory. A future metrics/time-series
store may preserve high-resolution telemetry without corrupting event meaning.

## 0.2.3 observation integrity boundary

Codex Omega Law 3 is now executable at the adapter seam:

```text
OS / vendor probe
    ↓
typed Observation
    ├── OBSERVED    -> update domain state
    ├── PARTIAL     -> update known state + mark degraded
    └── UNAVAILABLE -> preserve last known domain state; do not infer absence
    ↓
ObservationState
    ↓
ObservationCycleCompleted
    ↓
HealthSystem
```

`ObservationState` is the semantic home for adapter observability. `UsbDeviceState`
and `WifiLinkState` remain the semantic homes for device/link facts. This prevents
"could not inspect" from becoming a competing spelling of "device absent."

Health derivation now uses an explicit observation-cycle barrier. Component updates
are journaled before the derived health effect, but the system evaluates only after
the adapter has finished publishing the coherent batch.

## 0.2.4 temperature source stability

`TemperatureState` represents one logical host-temperature measurement: the
maximum currently exposed temperature returned by `psutil.sensors_temperatures`.
Its `source` therefore identifies the stable measurement policy
(`psutil:sensors_temperatures:max`), not whichever Package/Core sensor happens
to win a particular sample.

This keeps conservative thermal-health behavior while preventing transient
hottest-sensor hand-offs from becoming false durable provenance changes.

## Slice 003 presentation boundary

```text
WorldState
    ↓ atomic snapshot
presentation projector
    ↓
loopback read-only HTTP server
    ↓
local browser
```

Presentation is a projection boundary, not a truth owner.

Slice 003 adds `WorldState` synchronization because the runtime writer and HTTP
reader now coexist. The semantic home for synchronization is `WorldState`; the
HTTP layer is not allowed to coordinate domain mutation itself.

Mutation methods are structurally absent from the presentation API.

## 0.3.1 external-awareness boundary

Remote weather and alert providers are observed on a slower dedicated runtime thread. Their typed state is admitted into WorldState using the same Observation Integrity rules as local hardware: request failure changes observation availability but does not fabricate a replacement domain value. Remote provider latency therefore cannot stall the local host/Tenda observation cadence.
