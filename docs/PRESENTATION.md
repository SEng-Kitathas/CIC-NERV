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

## Current endpoint

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

## Deferred

This slice does not implement:
- House controls;
- world/traffic/weather/news;
- RF sensing;
- AI/model controls;
- actuator registry;
- alerts;
- capability proof DAGs;
- kiosk boot behavior.

Those remain later slices.
