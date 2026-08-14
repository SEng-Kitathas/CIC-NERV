# Slice 003 — Presentation Surface

## Scope

Slice 003 / 0.3.0 adds the first browser-visible Personal CIC surface.

It is intentionally **read-only**.

```text
native substrate
    ↓
adapters
    ↓
WorldState
    ↓
presentation projection
    ↓
loopback HTTP API
    ↓
local browser
```

The browser does not call:
- `lsusb`
- `iw`
- NetworkManager
- `psutil`
- systemd
- shell commands
- device/vendor APIs

It can only consume CIC's typed projection.

## Authority

Presentation owns no truth and no actuation authority.

`POST`, `PUT`, `PATCH`, and `DELETE` are rejected with HTTP 405.

The first release binds only to:

```text
127.0.0.1
```

A non-loopback bind is rejected by configuration validation.

## Original 0.3.0 Systems endpoint

```text
GET /api/v1/systems
```

The endpoint projects:
- host health and observation freshness;
- CPU/load, memory, storage, temperature, uptime;
- Tenda observation state and health;
- USB identity/mode;
- WLAN association, SSID, frequency/band, signal, RX/TX, IPv4;
- runtime PID/start metadata.

`WLAN connected` is intentionally not promoted to `Internet available`.
CIC does not yet possess an Internet capability proof.

## Concurrency

Slice 003 introduces a real concurrent reader of live WorldState.

`WorldState` therefore owns the lock protecting mutation and atomic snapshot
projection. The HTTP layer receives one immutable JSON-ready snapshot and
performs no direct entity mutation.

## Current scope beyond original Slice 003

The original 0.3.0 surface intentionally deferred world/traffic/weather. Those capabilities are now
embodied. Current loopback read-only surfaces include:

```text
/          Systems
/world     weather / forecast / radar / alerts
/traffic   multi-source traffic + geographic investigation map
```

House controls, privileged actuation, general RF interpretation, and AI/model control surfaces remain
future work and must not be inferred from the existence of the read-only presentation server.

## World-provider re-entry

Persisted remote provider values are last-known history, not inherited current authority.

On process restart:

```text
hydrate last-known weather/alerts
    ↓
mark remote ObservationState UNAVAILABLE
reason = awaiting fresh provider observation
    ↓
start presentation
    ↓
fresh provider fetch
    ↓
CURRENT is re-earned on success
```

The World page also carries explicit Open-Meteo / CC BY 4.0 attribution.

## 0.3.6 presentation sovereignty / execution assurance

The presentation chain is part of the verified system proposition:

```text
WorldState
    ↓
CIC projection
    ↓
loopback HTTP + security headers
    ↓
browser execution runtime
    ↓
local/remote reference resources
    ↓
rendered operator interface
```

The browser is deliberately denied world and mutation authority, but it retains execution authority:
it can admit/block requests, execute JavaScript/WebGL, propagate input, enforce CSP/referrer policy,
use storage, and determine whether the operator receives a functioning projection.

RC2D proved that a successful server/network probe is insufficient when the browser request contract
differs. RC2D-R1 therefore preserves `Referrer-Policy: strict-origin-when-cross-origin` for the OSM
reference-tile contract. Required MapLibre runtime assets are served locally from pinned bytes.

Current sovereignty level is mixed: CIC owns projection and locally serves the map runtime, while OSM
raster tiles remain a browser-direct reference dependency. They are reference cartography only;
they do not become observations or canonical WorldState. The long-term geographic target is a local
data substrate where remote providers refresh local assets rather than owning live-screen rendering.

Human-facing claims still require human-perception evidence. A static/API test can prove structure; it
cannot prove legibility, interaction quality, or that the rendered map is operationally usable.

## Semantic inspection API

The loopback presentation server exposes `GET`/`HEAD /api/v1/semantics` as a read-only
inspection surface over NERV semantic assertions. Optional query parameters are:

- `entity=<world-entity-id>`
- `kind=<semantic-kind>`
- `predicate=<exact-predicate>`
- `limit=<1..2000>` (default `500`)

The endpoint is intentionally bounded and non-persistent. It does not alter WorldState,
create semantic graph authority, or accept mutation verbs. Semantic projection uses a
stable typed WorldState read snapshot so collection threads cannot mutate the entity
universe during one request.

