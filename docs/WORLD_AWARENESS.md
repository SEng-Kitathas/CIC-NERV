# 0.3.1 — World Awareness

## Purpose

0.3.1 proves the first external-world observation pattern without letting the browser call remote
providers directly.

```text
remote provider
    ↓
typed adapter
    ↓
Observation[T]
    ↓
CIC WorldState
    ↓
read-only projection
    ↓
World page
```

## Concrete providers

### Open-Meteo

Used for model-derived current weather and one-day local forecast. CIC records both provider/model
observation time and local retrieval freshness.

### National Weather Service

Used for official active alert products at the configured point. The adapter sends an explicit
User-Agent and the runtime enforces an alert refresh interval of at least 30 seconds.

## Epistemic boundary

HTTP success is not itself the weather claim. Provider payload parsing must succeed before typed
state is admitted.

Provider failure behaves as:

```text
remote request unavailable
    ↓
no new Weather*/Alert domain value
    ↓
prior last-known domain value preserved
    ↓
ObservationState → UNAVAILABLE
```

The World projection must therefore distinguish current provider evidence from last-known values.
For alerts in particular, stale `active_count` is not rendered as an authoritative current-alert
claim when the NWS observation is unavailable.

## Scheduling

Remote providers run on a dedicated slow observation thread so network latency cannot block the
5-second local host/Tenda observation loop.

Current defaults:

```text
Open-Meteo current/forecast: 300 seconds
NWS active alerts:            60 seconds
```

These are provider-specific cadences, not a universal world-data tick.

## Scope

0.3.1 intentionally does not add:
- traffic;
- general news;
- Internet capability proof;
- browser-held API keys;
- remote actuation;
- generic external-provider framework;
- capability-proof DAG machinery.

Two concrete remote sources are enough to earn the first pattern.
