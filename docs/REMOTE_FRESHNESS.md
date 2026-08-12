# Remote Observation Freshness — 0.3.5

## Problem

A request timeout means CIC failed to obtain a newer sample. It does not by itself prove that the last valid observation has become unusable.

## First concrete policy: AviationWeather METAR

```text
fresh success in this runtime epoch
        ↓
current METAR state
        ↓
transient retrieval failure
        ↓
report age still <= configured max_age_minutes
        ↓
ObservationStatus.RETAINED
ObservationAvailability.DEGRADED
last_success_at preserved
current-weather estimate remains METAR-backed
```

When report age exceeds the configured source-age policy, the failed retrieval produces UNAVAILABLE and fusion may fall back to Open-Meteo.

## Re-entry

Retention is not allowed merely because a persisted METAR exists. A fresh METAR success must occur after process re-entry before retention can be earned.

## Non-goals

This slice does not create a generic ProviderManager, failure-count hysteresis, retry storm, or universal freshness score. Other remote providers keep their existing semantics until concrete evidence earns a provider-specific retention policy.
