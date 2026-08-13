# Personal CIC

A local-first, holonic, ECS-inspired operator CIC over a provenance-bearing world-state runtime.

## Current configuration-controlled status — 2026-08-13

- **Version:** `0.3.6`
- **Slice:** `003f` — **OPEN**
- **Promoted floor:** `99eb5e1d8fad82a0603825282218e3d98aa7d039` (`slice-003f-rc1b-target-verified`)
- **Current authored-source candidate:** `RC2D-R2 + QA1-R2`
- **Promotion state:** candidate only; RC2D-R2 and QA1-R2 have **not** been target-promoted.
- **Authority rule:** target behavior and exact-byte gates outrank this document.

The current candidate preserves the verified host/weather/radar/traffic lineage while adding the
MapLibre geographic camera, the RC2D-R1 browser-resource contract repair, and an explicitly
separate fixed CIC site anchor. The traffic collection-scope center, fixed site anchor, and future
live operator position are distinct concepts.

The QA1 reconciliation hardens configuration parsing, snapshot-version governance, concurrent
shutdown honesty, event-journal concurrency, dependency/source-distribution provenance, and
current documentation. It intentionally does **not** add new traffic-fusion claims.

## Architecture in one line

```text
entity → components → WorldState → typed events → systems/derivation → read-only CIC projection
```

Remote and local sources terminate at typed acquisition boundaries. Presentation consumes
normalized state; it does not own world truth. See `docs/ARCHITECTURE.md`,
`docs/PRESENTATION.md`, `docs/TRAFFIC.md`, and `docs/QUALITY_AUDIT_2026-08-13.md`.

## Install / validate authored source

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/verify-source-distribution.py
python tools/quality_gate.py
```

`tools/quality_gate.py` is a source-local assurance convenience only. A PASS does not promote a
candidate or replace target/runtime/operator proof.

The traffic map uses a pinned, locally served MapLibre runtime. Authored source preserves the
dependency lock even when the third-party runtime bytes are not embedded. Before installing the
map-capable service on a fresh tree, materialize and verify the pinned runtime:

```bash
python tools/install-maplibre-vendor.py
python tools/verify-source-distribution.py --require-runtime-vendor
```

See `docs/SOURCE_DISTRIBUTION.md`.

## Runtime shutdown guarantee

SIGINT/SIGTERM requests bounded shutdown of state-mutating remote workers before the final
snapshot. A forced final snapshot is written only after those workers actually quiesce. If a
worker exceeds its bounded stop/join budget, the runtime records an explicit incomplete-shutdown
reason and skips the forced final snapshot rather than pretending the world was race-free.

---

## Historical slice notes

## Slice 002 — Persistent Runtime

Verified Slice 001 established real self-awareness:

physical host / radio
→ adapters
→ typed components
→ shared world state
→ typed component-change events
→ systems health evaluation
→ presentation
→ durable state artifact

Slice 002 promotes that one-shot cycle into a persistent organism heartbeat.

### New in Slice 002

- `cic-runtime` long-running process
- config-driven collection and snapshot intervals
- append-only typed JSONL event journal
- graceful SIGINT/SIGTERM shutdown
- final world-state snapshot after confirmed worker quiescence (strengthened after later concurrency pressure)
- config-driven health thresholds
- systemd user-service installer
- `cic-self` retained as a one-shot diagnostic

## Install/update

Inside the repository virtual environment:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## One-shot diagnostic

```bash
cic-self
```

## Foreground runtime test

```bash
cic-runtime
```

In another terminal:

```bash
tail -f logs/events.jsonl
cat state/world.json
```

Stop the foreground runtime with `Ctrl+C`. It should emit `RuntimeStopping`; it writes the
final state snapshot only after state-mutating workers have confirmed quiescence.

## systemd user service

The installer verifies an embodied working tree (generated caches/build metadata are
non-source) while still requiring the exact pinned MapLibre runtime.

```bash
./tools/install-user-service.sh
systemctl --user status personal-cic.service
```

For startup before graphical login, enable user lingering once:

```bash
sudo loginctl enable-linger "$USER"
```

Then verify after reboot:

```bash
systemctl --user status personal-cic.service
tail -n 20 logs/events.jsonl
```

## Test

```bash
python -m unittest discover -s tests -v
```


## 0.2.1 event hygiene

The runtime samples current state frequently, but the durable event journal records only
operationally meaningful changes. Current world state remains fresh without turning
`logs/events.jsonl` into a five-second telemetry dump.


## 0.2.2 restart continuity

The runtime now rehydrates `state/world.json` before starting a new process lifetime. On restart,
unchanged topology and ordinary telemetry do not masquerade as newly discovered facts.
`RuntimeStarted` reports how many entities were restored, and the event journal records causes
before derived health effects.

## 0.2.3 observation integrity

Slice 002c hardens the telemetry boundary under Codex Omega's **resolve or represent
uncertainty** rule. Adapter command failure is no longer allowed to masquerade as a
device being absent or disconnected.

Adapters now emit typed observations with `observed`, `partial`, or `unavailable`
status. The world keeps the last known domain value when observation is unavailable,
and separately records an `ObservationState` that tells systems whether the current
telemetry is current, degraded, or unavailable. Health derivation runs only after an
adapter observation batch is complete, avoiding transient health conclusions from
half-updated state.

## 0.2.4 temperature source stability

Host temperature remains the maximum currently exposed sensor value, but the
semantic source is stable across Package/Core hand-offs. Normal sensor-order
changes therefore remain live telemetry instead of durable operational history.

## 0.3.0 — Systems presentation

The persistent runtime now exposes a loopback-only, read-only Systems surface:

```text
http://127.0.0.1:8765/
```

Browser-visible state is projected from CIC `WorldState`; the browser performs no
direct hardware, kernel, NetworkManager, systemd, or vendor queries.

JSON projection:

```text
GET http://127.0.0.1:8765/api/v1/systems
```

## 0.3.1 — World Awareness

The World page is available at `http://127.0.0.1:8765/world`. Remote weather/alert providers are observed by CIC adapters and projected from WorldState; the browser never calls them directly.
## 0.3.2 — WX Fusion Foundation

The World surface now distinguishes observed surface weather (AviationWeather METAR), model-derived
Open-Meteo context, official NWS hourly forecasts, and NWS alerts. It derives a source-aware current
estimate and exposes source disagreement rather than hiding it.

The World API remains read-only:

```text
GET http://127.0.0.1:8765/api/v1/world
```

- 0.3.3 adds local NOAA/NWS MRMS radar imagery with warning overlay, source-stream/frame provenance, and loopback-only cached image delivery.

### 0.3.4 Radar Context + Loop

The World surface adds a subdued locally cached TIGERweb reference overlay and a bounded real-frame MRMS playback loop. Each frame remains hash-addressed and timestamped; no interpolation is synthesized, and normal loop turnover is sample telemetry.


### 0.3.5 Surface Freshness Resilience

Transient AviationWeather transport failure no longer forces an immediate switch away from still-fresh METAR evidence. The surface observation becomes explicitly DEGRADED while the last-known report remains inside its configured age window; fusion stays METAR-backed. Re-entry still requires fresh post-restart success, and genuine report staleness still withdraws authority.

### 0.3.6 RC1 — Multi-source traffic substrate

The read-only Traffic surface is available at `http://127.0.0.1:8765/traffic` with JSON at `GET /api/v1/traffic`. RC1 collects source-preserving official/local roadway evidence from DriveNC events, WZDx, CMPD traffic CAD, Charlotte street closures, DriveNC cameras, and message signs. It performs only exact same-lineage/upstream-ID event association and exposes collection gaps rather than manufacturing confidence or silently merging sources. The optional Waze Live Map is operator-triggered external visual evidence and is not canonical WorldState. See `docs/TRAFFIC.md`.

### 0.3.6 RC2 candidate — Commercial incidents + sparse flow

RC2 extends the still-open 003f slice with TomTom Incident Details as a separately labeled commercial-reporting lineage and TomTom Flow Segment Data as sparse commercial/modeled telemetry. Provider community-report metadata remains attached to the TomTom record rather than being promoted into a current crowd lineage. Flow query labels remain reference points; matched OpenLR/geometry owns segment identity. The browser continues to consume only CIC's loopback projection, while Waze stays separately labeled operator-opt-in external crowd visual evidence.
