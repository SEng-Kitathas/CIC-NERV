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
8. SIGINT/SIGTERM request bounded worker shutdown; a final snapshot is written only after state-mutating workers actually quiesce, then `RuntimeStopping` records the outcome.
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
## 0.3.2 source-role weather architecture

Weather sources are not interchangeable votes. METAR owns observed surface reports, NWS owns official forecast/alerts, and Open-Meteo remains model-derived context/fallback. Current-weather fusion preserves those roles and exposes disagreement. The WX feed is a read-only projection of material durable events, not a competing history store.

## Radar image cache boundary

Radar image bytes are adapter-owned cache artifacts under `state/radar/`; only typed radar metadata and observation authority enter WorldState. The presentation server serves current and immutable hash-addressed cache artifacts read-only over loopback.

## 0.3.4 radar context / temporal presentation boundary

Radar remains a typed current-world observation while recent image frames and map geometry remain adapter-owned presentation artifacts. `RadarMosaicState` may project a bounded sequence of hash-addressed frame references; normal sequence turnover is not durable history. `RadarContextState` separately carries exact-artifact and semantic-content hashes for Census TIGERweb reference geometry. The browser fetches both images and context only from hash-checked loopback routes. Geographic context does not acquire meteorological authority merely because it is co-rendered with radar.


## 0.3.5 remote surface freshness resilience

A failed retrieval attempt and invalid domain evidence are distinct facts. For AviationWeather METAR, a failed request may produce a DEGRADED retained observation only after this runtime epoch has already earned a fresh METAR success and only while the report timestamp remains inside the configured source-age policy. Re-entry still withdraws authority and retention cannot re-authorize persisted state before fresh post-restart observation. Once report age exceeds policy, the surface observation becomes UNAVAILABLE and fusion may fall back to a model source.

## 0.3.6 RC1 traffic collection / correlation boundary

Traffic is the first external domain intentionally composed from several collection lineages rather than several providers answering the same scalar question. Each source retains its own observation authority and record identity. A `TrafficSituationState` may derive event kernels, coverage families, and collection gaps, but those derived records never replace the source collections.

RC1 permits only one event-equivalence rule: same source family plus the same upstream event identifier. This allows DriveNC Events and WZDx representations of one ATMSERS road event to share a kernel without being counted as independent confirmation. Cross-lineage event correlation remains deferred until spatial/temporal/road/direction/event-class evidence earns it.

Traffic reuses the established Observation Integrity and re-entry laws. A successful empty source is current negative evidence; retrieval or schema failure is unavailable observation; persisted traffic values remain historical through restart until fresh source success re-earns authority. Traffic has no inherited METAR-style retained-authority policy.

The `/traffic` browser remains a read-only WorldState projection. TIGERweb radar-context geometry may be reused as separately sourced reference context, but it acquires no traffic authority. Waze Live Map is an explicit exception only as operator-triggered external visual evidence: browser direct, noncanonical, and never counted as normalized corroboration in RC1.

## 0.3.6 / Slice 003f — current architectural state

Slice 003f remains open. The promoted floor is RC1B; later RC2/RC2A/RC2B-R1/RC2C/RC2D/RC2D-R1/RC2D-R2 work remains candidate lineage until an exact target promotion gate earns a new floor.

The current architecture is intentionally hybrid rather than a single universal store:

```text
ECS-like typed current state
+ holonic ownership/boundaries
+ typed event history
+ source-preserving domain collections
+ derived situation state
+ specialized raster/vector/cache artifacts
        ↓
semantic contracts over one modeled world
        ↓
read-only Personal CIC projection
```

This preserves the original `entity → components → world state → typed event → system → intent`
shape while allowing richer evidence, provenance, and future semantic-graph relationships without
turning `WorldState` into a semantic god-object.

### Recursive heterogeneous fusion rule

Traffic is the first multi-lineage domain to make the general fusion requirement concrete.
Normalization makes records mutually intelligible but does not erase source lineage. Fusion may
produce agreement, disagreement, association, an unresolved hypothesis, or refusal to fuse. A
derived product remains derived and must retain enough provenance to unwind back to contributing
source records.

### Location semantics

Three location concepts are now separate:

```text
collection_scope_center
    regional acquisition geometry / awareness center

fixed_site_anchor
    source-provenanced location of the fixed CIC node/site

live_operator_position
    future mobile/live estimate; currently unimplemented / null
```

The traffic collection domain remains centered on the configured awareness location. RC2D-R2
adds the fixed site anchor without reinterpreting it as a live operator position.

### Presentation sovereignty / execution boundary

The browser has no world authority, but it participates in execution. Current presentation has
four separable authorities:

```text
WORLD AUTHORITY       WorldState / domain semantics
PROJECTION AUTHORITY  CIC read-only projection
EXECUTION AUTHORITY   browser + JS + WebGL / MapLibre runtime
RESOURCE AUTHORITY    assets/providers required for rendering
```

Therefore server reachability is not browser-integration proof, projection correctness is not
rendering proof, and rendering success is not operator acceptance. MapLibre is served locally and
pinned as a presentation dependency; OSM raster tiles remain browser-direct reference context in
this candidate and possess no WorldState authority. The long-term map direction is a more sovereign
local geo substrate, not a dependency that owns whether CIC can render.

### Concurrency and shutdown integrity

Local collection, world-awareness collection, traffic collection, and presentation are concurrent.
The event bus snapshots subscriber registries under a lock but invokes callbacks outside that lock;
this preserves recursive publish behavior without imposing a bus/world lock-order deadlock. Durable
JSONL appends are serialized so concurrent publishers cannot interleave records.

Remote worker `stop()` is a proposition, not a command receipt: it returns whether the thread
actually terminated. A timeout leaves the live thread represented. Runtime shutdown does not force
a final snapshot if a state-mutating worker has failed to quiesce.

### Snapshot schema governance

The current writer remains schema version 2 because that is the verified target lineage. The reader
explicitly admits historical versions 1, 2, and the radar-era version 3 fixture required by the
verified lineage; unknown future versions are rejected rather than guessed. This is a compatibility
policy, not a claim that explicit migration functions are complete.

### Dependency / source-distribution boundary

Critical presentation-runtime dependency identity lives in a machine-readable lock. Authored source
and third-party runtime bytes are separate configuration-controlled artifacts. A fresh map-capable
service install must verify that the pinned MapLibre runtime is materialized before starting.
Compatibility ranges in `pyproject.toml` and exact observed target dependency pins are separate
claims; see `requirements-target.lock` and `docs/SOURCE_DISTRIBUTION.md`.

