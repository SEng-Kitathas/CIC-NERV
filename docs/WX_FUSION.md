# 0.3.2 — WX Fusion Foundation

## Purpose

0.3.2 separates weather source roles instead of flattening unlike data into one provider value.

```text
AviationWeather METAR  -> observed surface reality
Open-Meteo             -> model-derived current/daily context
NWS hourly forecast    -> official forecast
NWS CAP alerts         -> official hazard authority
                         ↓
                 source-aware estimate
                         ↓
                    World projection
```

## Current estimate

The current local estimate privileges current surface observation over model output.

With current METAR reports, temperature and dewpoint are robust medians across the configured
station set. Wind, visibility, ceiling, altimeter, and flight category come from the nearest
current station because averaging those unlike/vector/categorical quantities would fabricate
meaning.

If no current METAR source exists, Open-Meteo is an explicit fallback. It is never silently
averaged with METAR observations.

The projection exposes model/forecast deltas rather than hiding disagreement.

## Surface network

Initial configured stations:

```text
KEQY
KCLT
KJQF
```

The adapter requests them in one AviationWeather.gov METAR query, rejects reports older than the
configured age ceiling, deduplicates each station to its newest report, computes station distance,
and retains the full source set.

Polling is configured at 60 seconds, matching the provider's documented per-thread floor.

## NWS hourly forecast

The adapter discovers the point's current `forecastHourly` URL through `/points/{lat},{lon}`.
That mapping is cached for six hours, then re-resolved because NWS documents that office/grid
mapping can occasionally change.

Only the next six hourly periods are retained in this first slice.

## WX Feed

The World page includes a bounded RSS-like operational feed. It is a projection of CIC's durable
material event journal, not another source of truth and not another history database.

Sample/retrieval heartbeat events are therefore absent by construction.

## Deferred

Radar/MRMS remains the next slice. 0.3.2 creates the source-role and professional-instrumentation
surface it will plug into without mixing raster transport/rendering into this verification unit.
## External-data rendering boundary

Remote provider strings are untrusted input even on a loopback-only HMI. The World browser renders
METAR, NWS forecast, alert, and feed text through DOM `textContent`; provider strings are not
interpolated through `innerHTML`.

## Surface-current qualification

A METAR row without a parseable observation timestamp is not admitted as a current surface report.
The current AviationWeather query uses the provider's `hoursBeforeNow` window parameter and the
runtime enforces its own age ceiling as a second boundary.

The current source-aware estimate is a derived current projection, not an authoritative external
source. `authoritative_now` remains reserved for claims such as current NWS alert state.


## RC2 live-data corrections

The first Engage run exposed semantic/HMI issues that fixtures could not reveal:

- The NWS comparison was mislabeled "next hour" even when the returned period was the active current forecast period. It is now a reference period selected by start time relative to now.
- Nearest-station wind/visibility/ceiling context is explicitly labeled. Separate area summaries expose median sustained wind, maximum reported gust, minimum visibility, and minimum ceiling without pretending these spatially heterogeneous measurements are one point value.
- Expected restart re-entry provider transitions remain durable provenance but are suppressed from the default WX feed; real provider failures and recoveries remain eligible.
- Forecast materiality no longer fires merely because the hourly window rolled forward with unchanged condition and PoP band.
