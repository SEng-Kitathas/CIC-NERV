# Changelog

### 0.3.4 RC2 — Radar loop playback stability

- Repairs browser loop-state synchronization so the 5-second World API refresh no longer resets an active radar loop to the newest frame.
- Requires three distinct observed radar frames before autoplay begins; two-frame collections remain inspectable with step controls but are not presented as useful motion.
- Adds accessible previous/next/play control labels and corrects the target HMI gate to verify control identity rather than literal PREV/NEXT text.
- No radar collection, provenance, context, re-entry, or materiality semantics change from RC1.


## 0.3.4 — Slice 003d Radar Context + Loop

- Adds a restrained Census TIGERweb vector context layer over the local MRMS radar view: county boundaries, generalized primary roads, Interstate/US-highway context, and sparse place labels.
- Keeps geographic context as separately sourced reference data rather than meteorological evidence; the browser consumes only hash-bound loopback-cached context JSON.
- Separates context artifact identity (`context_sha256`) from retrieval-invariant semantic content identity (`content_sha256`) so a routine six-hour refresh cannot fabricate durable history.
- Adds a bounded immutable recent-frame cache and frame manifest for real observed WMS radar playback; no frame interpolation or synthetic tweening is performed.
- Retains the NWS warning overlay captured in the same collection cycle as each cached radar frame so historical loop frames do not receive the current warning overlay.
- Auto-runs the loop after two distinct observed frames exist; play/pause and frame-step controls remain operator-accessible.
- Adds explicit range-ring labels and collision-suppressed place labels for professional spatial context without consumer map tiles.
- Keeps ordinary frame-list growth, frame hashes, retrieval times, and stream-witness turnover as sample telemetry rather than durable journal history.

## 0.3.3 — Slice 003c Radar Spatial Awareness

- Adds verified NOAA/NWS MRMS BREF.QCD local radar imagery with NWS short-fuse warning overlay.
- Separates MRMS distribution-stream freshness from independent WMS frame retrieval/hash provenance.
- Preserves equal-distance radar geometry across the 900x600 raster and 75-mile centered range rings.
- Hash-binds locally served radar imagery and rejects mismatched frame identities.
- Withdraws/re-earns radar observation authority across process re-entry.
- Treats routine radar frame/hash/timestamp churn as sample telemetry and structural radar changes as durable material events.
- Keeps `state/radar/` runtime cache outside Git history.

## 0.3.2 — Slice 003b WX Fusion Foundation

- Adds NOAA/NWS AviationWeather.gov METAR surface-observation network support for KEQY/KCLT/KJQF.
- Adds official NWS hourly forecast discovery through `/points` and six-hour forecast projection.
- Adds a source-aware current-weather estimate that privileges observed surface data and exposes model/forecast disagreement instead of averaging unlike sources.
- Adds professional surface instrumentation: T/Td/RH, wind/gust, visibility, ceiling, altimeter, flight category, station distance, source age, and station temperature spread.
- Adds a bounded WX operational feed projected from durable material weather events.
- Extends remote-provider re-entry withdrawal to METAR, NWS forecast, and current-estimate authority.
- Keeps radar/MRMS explicitly deferred to the next coherent slice.
- Rejects METAR rows without a parseable observation timestamp and uses the current `hoursBeforeNow` API window parameter.
- Treats fused current weather as current-derived state rather than external authority.
- Renders remote-provider strings with DOM `textContent` rather than `innerHTML`.

### 0.3.1 RC3 — verification-gate cleanup

- No runtime semantic changes from RC2.
- Moves the RC2 re-entry regression functions into their `unittest.TestCase` classes so discovery actually executes them.
- Removes candidate-wide trailing blank-line/whitespace defects required by the static gate.
- RC2 is rejected as a verification artifact because its new regressions were present but undiscovered.

### 0.3.1 RC2 — re-entry and provider-attribution hardening

- Withdraws restored remote-provider `CURRENT` authority before presentation starts; fresh Open-Meteo/NWS observation must re-earn current status after every process restart.
- Preserves last-known remote domain values during that re-entry gate.
- Ensures NWS alert `authoritative_now` cannot be inherited solely from a persisted snapshot.
- Adds explicit Open-Meteo / CC BY 4.0 attribution to the World presentation.
- Adds regression coverage for re-entry ordering and freshness withdrawal.
- No expansion of 0.3.1 scope.

## 0.3.1 — World Awareness

- Adds typed Open-Meteo current-weather and daily-forecast observations for the configured local area.
- Adds typed National Weather Service active-alert observations with explicit User-Agent and provider-safe refresh cadence.
- Runs remote-provider observation on a slow dedicated thread so network latency does not block local 5-second sensing.
- Preserves last-known remote domain state when a provider becomes unavailable while marking the observation unavailable.
- Adds `/api/v1/world` and a read-only `/world` page; the browser still owns no provider calls or keys.
- Adds WorldState synchronized component reads for the newly concurrent remote writer and removes direct entity reads from health/ingest paths.
- Corrects two 0.3.0 RuntimeConfig tests that were accidentally defined at module scope and therefore not discovered by `unittest`.

## 0.3.0 — Slice 003 Presentation Surface

- Adds the first read-only browser presentation directly projected from live CIC `WorldState`.
- Adds a loopback-only HTTP endpoint at `GET /api/v1/systems` and a local Systems dashboard.
- Explicitly rejects HTTP mutation verbs; presentation has no actuation authority.
- Adds WorldState locking because presentation introduces a real concurrent reader.
- Surfaces observation freshness, health, host telemetry, Tenda USB state, and WLAN state without direct browser hardware queries.
- Deliberately labels WLAN association as WLAN state rather than claiming Internet capability.
- Adds presentation/configuration/server regression tests.

## 0.2.4 — Temperature Source Stability

- Defines `TemperatureState` as the maximum currently exposed host temperature under a stable logical source identity.
- Prevents Package/Core hottest-sensor hand-offs from fabricating durable `TemperatureState` source transitions.
- Preserves conservative max-temperature health semantics while separating measurement policy from transient physical-sensor identity.
- Synchronizes `personal_cic.__version__` with project metadata.
- Adds target-derived regression coverage for temperature-source stability.

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
