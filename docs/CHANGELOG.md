# 0.3.6 / 003g Runtime Authority RC4 — explainable traffic degradation + local presentation-origin hardening

**Status:** source candidate; RC7 remains target-verified authority.

- Preserves RC3 runtime-authority and OIG/EDG/FIE reconciliation behavior.
- Adds explicit `summary.degrading_sources` diagnostics to the read-only traffic projection; no source authority or traffic fusion policy is weakened merely to obtain a green status.
- Makes the Traffic HMI identify the source paths responsible for an aggregate DEGRADED state.
- Rejects non-local HTTP `Host` values at the loopback presentation boundary to reduce DNS-rebinding exposure.
- Preserves the target-proved `strict-origin-when-cross-origin` OSM referrer contract; the candidate explicitly rejects the tempting `no-referrer` regression because RC2D-R1 already proved it breaks tiles.
- Adds the Secure Operating Surface / provider-specific Secure Reference Gateway contract for future camera/reference integration; no generic arbitrary URL proxy is introduced.
- Records DeFlock as a slow-changing public surveillance-infrastructure reference candidate, not a live traffic/corroboration source.

# 0.3.6 / 003g Runtime Authority RC3 — OIG/EDG + FIE reconciliation

**Status:** source candidate; RC7 remains target-verified authority.

- Preserves Runtime Authority RC2 code/runtime behavior without semantic or snapshot mutation.
- Reconciles FIE against the completed OIG/EDG first evaluation pass: 0/10 original candidate invariants survived unchanged as universal primitives.
- Replaces fixed-grammar language with bounded GC-01 / GP-01 / CS-01 / AB-01, GR-01, WT-01 / RC-01 / ED-01 quarry relations and explicit meta-hypothesis status.
- Records **INTERVENTION-PRESERVING STRUCTURAL RECURRENCE ACROSS SCALE** and **FRACTAL LAUNDERING** as the pressure-qualified recurrence formulation/failure signature.
- Adds `docs/REASONING_PROVENANCE_HANDOFF.md` as NON-CANONICAL SOP/quarry input; it has no runtime or promotion authority.
- Mainline direction remains 003g target proof followed by 003h Evidence Association; this reconciliation does not reopen ontology breadth expansion or the OIG/EDG side experiment.

# 0.3.6 / 003g Runtime Authority RC2 — FIE + configuration-control alignment

**Status:** authored-source candidate; not target-promoted. Parent authority remains Semantic Binding RC7
(`424c8ade02fa4ad4c9f944c82e56a6c715615b18` / `d8ba2a50651d42c14524299b14d6672c76de8cdd`).

- Preserves the Runtime Authority RC1 worker-liveness, fail-fast authority withdrawal, and single durable-writer lease mechanisms.
- Adds `docs/FRACTAL_ISOMORPHISM_ENGINEERING.md`, defining FIE as a PDVER-governed heuristic for mining conserved structure across domains/scales while requiring breakpoint audits.
- Adds `docs/AUTHORITY_LINEAGE.md` so current target authority, active candidate, historical evidence, and derived runtime state have separate configuration-control homes.
- Updates current-facing README/architecture/traffic/conformance/semantic/runtime-authority documents from stale pre-RC7 status without rewriting historical QA audit claims.
- Removes the stale hard-coded `003f RC2D-R2` Traffic HMI chip; the UI no longer claims a release lineage that it cannot dynamically verify.
- No new semantic home, traffic association claim, snapshot/journal schema, ontology runtime dependency, or world-state writer is introduced.

# 0.3.6 / 003f RC2D-R2-QA1-R2 — Service-installer verifier-scope propagation

- Corrects `tools/install-user-service.sh` to verify the embodied checkout with
  `--working-tree --require-runtime-vendor` rather than accidentally re-entering strict
  source-capture mode after QA1-R1 had already established the distinction.
- Corrects the service-install refusal diagnostic so any working-tree/dependency
  verification failure is not falsely reported as missing MapLibre materialization.
- Adds regression coverage proving the service installer propagates the required
  working-tree scope and pinned-runtime requirement together.
- No `src/personal_cic/` runtime, world-state, traffic, weather/radar, map-camera,
  site-anchor, source-authority, persistence, or HMI behavior changes from QA1-R1.

# 0.3.6 / 003f RC2D-R2-QA1-R1 — Verification-scope correction

- Separates sealed source-capture hygiene from embodied working-tree cleanliness.
- Excludes local runtime/tool roots such as `.venv/` from source-distribution authority.
- Adds explicit `--working-tree` verification for target checkouts containing expected caches/build metadata.
- Keeps strict source-capture verification for sealed artifacts and adds regression coverage proving the distinction.
- No world-state, traffic, map-camera, site-anchor, source-authority, persistence, or operator-HMI semantic change from QA1.

## 0.3.6 / 003f RC2D-R2-QA1 — quality-reconciled source candidate

**Status:** offline candidate; not target-promoted. The promoted floor remains RC1B and Slice 003f remains open.

- Preserves the RC2 traffic collection semantics, RC2A/RC2B-R1 operator-owned viewport work, RC2D MapLibre camera, RC2D-R1 browser referrer repair, and RC2D-R2 fixed-site-anchor separation.
- Hardens configuration parsing: strict booleans, finite numeric values, positive core cadences, typed nested shapes, health threshold ordering/ranges, environment-variable names, and required source provenance for an enabled fixed site anchor.
- Makes snapshot compatibility explicit: writer stays schema v2; reader admits the evidenced historical v1/v2/v3 lineage and rejects unknown future versions.
- Makes worker shutdown honest: bounded stop reports actual quiescence; runtime skips a forced final snapshot if a state-mutating worker remains live.
- Serializes concurrent event-journal appends and protects EventBus subscriber/count state without holding the bus lock across callbacks.
- Adds a machine-readable MapLibre dependency lock, exact-hash materializer, source-distribution verifier, package-data declaration, target Python dependency lock, and service-install refusal when required map runtime bytes are absent.
- Adds modest user-service hardening (`NoNewPrivileges=true`, `UMask=0077`) without introducing filesystem restrictions that have not been target-proved.
- Corrects the legacy TomTom `cic-center` probe display label to `collection-scope center reference` while retaining the stable probe ID for continuity.
- Reconciles current architecture/presentation/traffic/conformance documentation and records remaining debt rather than refactoring unrelated code for style.
- Adds a reproducible source-local quality gate for syntax/static invariants, JSON/shell integrity, source-distribution checks, and the full regression suite; it explicitly carries no promotion authority.
- Expands regression coverage; no inherited test is intentionally removed.

### Candidate chronology retained

- RC2: TomTom commercial incidents + sparse flow.
- RC2A: geographic viewport.
- RC2B/R1: sticky operator-owned viewport and operational presentation; R1 corrected an artifact whitespace failure.
- RC2C: detailed OSM reference map; target use exposed wheel chaining/aspect distortion and forced camera-substrate replacement.
- RC2D: MapLibre geographic camera; target use exposed browser referrer/resource-contract failure.
- RC2D-R1: referrer contract repair and successful operator map interaction.
- RC2D-R2: fixed CIC site anchor separated from collection center and future live operator location.

## 0.3.6 RC2 candidate — TomTom commercial incidents + sparse flow

- Adds TomTom Orbis Incident Details as a source-preserving `commercial_report` lineage with provider event identity, geometry, category/detail, delay, length, probability, time-validity, and lifecycle fields.
- Preserves TomTom end-user report count/time as provider community attribution without relabeling the event as a crowd report or assuming the attribution is current.
- Keeps TomTom `roadClosed` as source category evidence rather than silently promoting it into CIC's stronger normalized `full_closure` proposition.
- Adds TomTom Flow Segment Data as separately typed `commercial_modeled_telemetry` with query-reference identity, matched geometry/OpenLR, functional road class, current/free-flow speed and travel time, confidence, and closure state.
- Makes nearest-road-fragment semantics explicit: configured query labels do not assert roadway identity.
- Adds flow materiality bands so ordinary speed churn stays sample telemetry while matched-segment, closure, and operational congestion-band changes are material.
- Extends traffic snapshot hydration, re-entry authority withdrawal, source health, collection gaps, API projection, and map controls for TomTom incidents/flow.
- Bumps the traffic projection schema to API version 2 while retaining the `/api/v1/traffic` endpoint path.
- Keeps Waze normalized crowd telemetry, independent commercial corroboration/route ETA, CMPD geocoding, and cross-lineage event equivalence explicitly open; Slice 003f remains unfinished.

## 0.3.6 RC1 — Slice 003f Multi-Source Traffic Substrate

- Adds source-preserving traffic collection for DriveNC events, DriveNC WZDx work zones, CMPD live traffic CAD, Charlotte street closures, DriveNC cameras, and DriveNC message signs.
- Uses the current city-operated CDOT StreetClosuresAndDetours MapServer for Charlotte closures and normalizes ArcGIS epoch-millisecond dates; the stale ArcGIS Online FeatureServer pointer is not treated as current authority.
- Uses physical geometry/radius for locality instead of keyword matching; county scope is only a fallback when a DriveNC event has no usable geometry.
- Treats HTTP success with an invalid provider schema as unavailable observation rather than valid empty traffic state.
- Preserves fresh empty collections as explicit negative evidence.
- Withdraws persisted traffic authority on re-entry and requires fresh post-restart collection.
- Associates only proven same-lineage/same-upstream-ID records; DriveNC + WZDx representations of one ATMSERS event cannot become duplicate corroboration or duplicate closure counts.
- Preserves separate camera and message-sign source families and valid `NO_MESSAGE` infrastructure state.
- Adds source-aware materiality for traffic events, cameras, message signs, and derived event-kernel state.
- Adds read-only `/traffic` and `/api/v1/traffic` with an interactive CIC-owned local map, source health, gaps, event detail, cameras, signs, and last-known toggling.
- Adds an explicit operator-opt-in Waze Live Map visual seam that remains browser-direct external evidence and is not normalized into CIC WorldState.
- Adds optional systemd secret-environment loading; DriveNC API credentials remain outside committed configuration and are redacted from provider failure detail.
- RC1 does not claim completed Slice 003f: normalized Waze crowd telemetry, independent flow/ETA sources, CMPD geocoding, cross-lineage event association, and reference-route intelligence remain open.

## 0.3.5 — Slice 003e Surface Freshness Resilience

- Add explicit retained-observation status for policy-bounded last-known data.
- A transient AviationWeather retrieval failure degrades surface authority without discarding still-fresh METAR state.
- Current-weather fusion continues to use retained METAR while the configured report-age policy remains satisfied.
- Retention is forbidden until at least one fresh METAR success has occurred in the current runtime epoch, preserving the re-entry law.
- Surface/alert HMI freshness now reports age since last successful retrieval rather than age since the latest attempt.
- If retained METAR ages beyond its configured freshness limit, surface authority becomes unavailable and normal fallback applies.

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
