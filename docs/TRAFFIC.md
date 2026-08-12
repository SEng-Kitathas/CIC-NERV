# Traffic Situational Awareness — Slice 003f RC1

## Purpose

Traffic is CIC's first deliberately multi-lineage operational collection domain.
The objective is not a traffic widget. It is a source-preserving local mobility
picture that can eventually correlate official, observational, commercial, and
crowdsourced evidence without laundering one source into another.

RC1 establishes the official/local collection substrate and the active read-only
map surface. It is not the completed 003f traffic capability.

## Collection doctrine

Within lawful civilian-accessible data, CIC should collect as many useful
independent observation/reporting lineages as practical while preserving:

- provider and source family,
- source-record identity,
- collection class,
- source/retrieval time,
- geographic scope,
- observation authority,
- disagreement and collection gaps.

A derived event kernel never replaces its source observations.

## RC1 sources

### NCDOT DriveNC Events

Credentialed official roadway-event collection. The API key is read from the
environment variable configured by `world_awareness.traffic.drivenc.api_key_env`
(default `DRIVENC_API_KEY`). The key is not configuration data and must never be
persisted in WorldState, journal payloads, presentation JSON, or source control.

A successful HTTP response is not sufficient evidence. The adapter requires the
expected array contract. A 200 response with a message/error object is
`UNAVAILABLE`, not a valid empty traffic state.

### DriveNC WZDx

Public GeoJSON Work Zone Data Exchange feed. WZDx records retain their source data
identifier and `road_event_id`. When WZDx and DriveNC Events identify the same
`NCDOT/ATMSERS` upstream event, CIC may associate the records into one event
kernel while retaining both source records.

### CMPD Traffic CAD

Official Charlotte-Mecklenburg Police Department live roadway-crash/obstruction
reporting. The current public table provides time, division, address, and
description but no geometry. RC1 therefore preserves CMPD as an independent
address-only lineage and does not fabricate coordinates.

### City of Charlotte street closures

Public city-operated CDOT ArcGIS MapServer closure layer queried as GeoJSON. Only
records explicitly marked active by the source are requested. The adapter preserves
CDOT closure identity, roadway, reason/type, full-closure state, direction, source
times, and source geometry; geometry determines traffic scope and textual place
names do not. ArcGIS epoch-millisecond date fields are normalized explicitly.

The City states that this closure map populates closures in Waze. A Charlotte closure
that later appears in Waze therefore must not automatically be counted as an
independent crowd confirmation merely because it is visible through a second product.

### DriveNC cameras

Official camera inventory with source identity, position, status, DriveNC page,
and HLS URL when exposed by the provider. Camera availability is observational
infrastructure, not automatically an incident report.

### DriveNC message signs

Official dynamic-message-sign state. `NO_MESSAGE` after a successful collection is
valid negative infrastructure evidence. A displayed message transition is a
material event.

## Spatial scope

RC1 uses physical coordinates against a configured radius. County matching is only
a fallback for DriveNC event records that lack usable geometry. Terms such as
"Union", "Matthews", or "US-74" never establish locality by themselves.

## Observation integrity

Traffic currently has no provider-specific retained-authority policy.

```text
fresh successful collection
    -> CURRENT (or DEGRADED if partially parsed)

retrieval/schema failure
    -> UNAVAILABLE
    -> preserve last-known domain value historically
    -> do not present it as current evidence

process re-entry
    -> withdraw persisted traffic authority
    -> require fresh post-restart collection
```

A successful empty collection is CURRENT negative evidence. An unavailable
collection is not an empty collection.

## Event association

RC1 intentionally performs only an association it can presently prove:

```text
same source family
+ same upstream event identifier
= one event kernel
```

This primarily prevents DriveNC Events and WZDx views of the same ATMSERS event
from becoming fake independent confirmations or duplicate closure counts.

RC1 does **not** merge CMPD, NCDOT, crowd, flow, or camera observations merely
because their descriptions look similar. Cross-lineage association must be earned
from spatial, temporal, roadway/direction, and event-class evidence in a later
003f iteration.

## Presentation boundary

The local traffic surface is:

```text
http://127.0.0.1:8765/traffic
```

with JSON projection:

```text
GET http://127.0.0.1:8765/api/v1/traffic
```

The browser reads CIC projections and locally cached TIGERweb reference geometry.
It does not call DriveNC, CMPD, Charlotte, or WZDx directly.

The optional Waze Live Map is deliberately different. It is operator-triggered,
browser-direct external visual evidence, explicitly outside canonical WorldState.
Its crowd observations are not counted as normalized CIC corroboration in RC1.

## Materiality

Durable traffic history records semantic changes, including event appearance /
clearance, lane/closure/severity/description/geometry changes, camera operational
changes, message-sign transitions, source-family/gap changes, and event-kernel
membership changes.

Provider retrieval timestamps, unchanged periodic refreshes, and camera stream URL
rotation without an operational state change remain sample telemetry.

## Known collection gaps / remaining 003f work

RC1 intentionally leaves these visible rather than pretending completeness:

- no supported normalized Waze crowd incident/police/hazard feed has yet been
  established on the target;
- independent commercial flow/travel-time/route lineages (for example Google,
  TomTom, Mapbox) are not yet configured;
- CMPD address records are not geocoded yet;
- camera imagery is mapped but not yet fused into computer-vision observations;
- cross-lineage event association is deliberately not implemented yet;
- reference-route ETA/delay intelligence is not implemented yet.

003f must continue until the broader traffic collection and operator-use case is
satisfied; RC1 is the truthful official/local substrate, not the finish line.
