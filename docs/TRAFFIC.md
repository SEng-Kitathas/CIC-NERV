# Traffic Situational Awareness — 003f Foundation / 003g Continuation


## Current status — 2026-08-13

- Current target-verified authority: `slice-003f-semantic-binding-rc7-target-verified` / `424c8ade02fa4ad4c9f944c82e56a6c715615b18`.
- RC7 preserves the multi-lineage traffic substrate and its read-only presentation while adding the now-sealed semantic inspection foundation.
- 003g Runtime Authority Integrity is the active source-candidate slice; it does not add cross-lineage traffic equivalence or corroboration claims.
- Historical RC2/RC2D/QA1 labels below describe the construction lineage that was later promoted through QA1 and Semantic Binding RC1–RC7.

Target behavior remains final authority. Historical status statements are preserved as evidence of their
own phase and must not be read as present-tense configuration control.

## Purpose

Traffic is CIC's first deliberately multi-lineage operational collection domain.
The objective is not a traffic widget. It is a source-preserving local mobility
picture that can eventually correlate official, observational, commercial, and
crowdsourced evidence without laundering one source into another.

RC1 established the target-verified official/local collection substrate and active read-only map surface. RC2 adds a commercial incident lineage and sparse live-flow telemetry from TomTom while preserving their distinct evidence semantics. It is still not the completed 003f traffic capability.

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

### TomTom Incident Details — RC2

TomTom incidents are normalized as `commercial_report`, not as direct observation
or automatic independent corroboration. CIC preserves provider incident identity,
source geometry, category, event detail/code, start/end time, road numbers,
delay/length fields, probability, and `timeValidity`.

TomTom may also expose `numberOfReports` and `lastReportTime`. Those fields remain
provider-supplied community attribution attached to the commercial incident record.
They do **not** change the source family to Waze/crowd, and an old `lastReportTime`
does not become a current crowd report merely because the surrounding TomTom
incident is current. Target reconnaissance observed exactly that case: one current
incident carried a community-report timestamp from more than a year earlier.

TomTom `roadClosed` is retained as the provider's event category. RC2 deliberately
does not translate that category into CIC's stronger generic `full_closure=True`
field, because doing so would erase the distinction between source category and a
normalized closure proposition.

### TomTom Flow Segment Data — RC2

TomTom flow is normalized separately as `commercial_modeled_telemetry`. RC2 uses a
small set of configured geographic **query references** and preserves the road
fragment TomTom actually matched: functional road class, current/free-flow speed,
current/free-flow travel time, confidence, closure state, OpenLR identity, and
matched segment geometry.

A query label such as `I-277 Uptown reference` is not asserted roadway identity.
The provider contract returns the nearest road fragment to the query coordinate;
therefore the matched geometry/OpenLR is evidence and the human-friendly query
label is only a reference. The HMI exposes that distinction explicitly.

RC2 flow is sparse probe telemetry, not continuous network coverage and not yet a
route ETA system. The default collection cadence is an operational request-budget
choice, not a constitutional source-freshness rule.

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

The browser reads CIC projections and locally served presentation/runtime assets. It does not call
DriveNC, CMPD, Charlotte, WZDx, or TomTom directly. TIGERweb context remains a separately sourced
local reference artifact. RC2C/RC2D additionally use browser-direct OpenStreetMap raster tiles as
noncanonical reference cartography; those tiles have rendering/resource authority only and do not
become traffic observations or WorldState.

The optional Waze Live Map is deliberately different. It is operator-triggered,
browser-direct external visual evidence, explicitly outside canonical WorldState.
Its crowd observations are not counted as normalized CIC corroboration in RC2. TomTom is shown separately as commercial incident reporting and modeled flow telemetry, never relabeled as Waze.

### Geographic investigation viewport

The traffic surface must behave as an investigation map, not as a magnified static
SVG. RC2A replaces fixed-canvas `viewBox` magnification with a geographic viewport.
The SVG remains only a rendering surface; viewport truth is longitude/latitude bounds.

Operator controls include:

- `75 MI SCOPE` to return to the currently collected traffic domain;
- historical RC2A `LOCAL 15 MI` centered on the collection/awareness center; RC2D-R2 replaces this with `SITE 15 MI` against the separately sourced fixed site anchor;
- `FIT ACTIVE` to fit currently enabled evidence layers;
- cursor-anchored wheel zoom and double-click zoom;
- geographic drag/pan clamped to the collected source scope;
- event-list focus that centers/zooms onto the selected event;
- a viewport-scoped event list by default; and
- a live viewport readout showing center, approximate dimensions, zoom factor, and
  visible event/camera/sign/flow counts.

Semantic zoom also reduces clutter: secondary roads and place labels are withheld at
the broadest view and become visible as the operator narrows the viewport. Data
collection scope is not silently expanded by panning; expanding collection beyond
the configured 75-mile domain is a separate future capability.

## Materiality

Durable traffic history records semantic changes, including event appearance /
clearance, lane/closure/severity/description/geometry changes, camera operational
changes, message-sign transitions, source-family/gap changes, and event-kernel
membership changes.

Provider retrieval timestamps, unchanged periodic refreshes, camera stream URL
rotation without an operational state change, and ordinary TomTom speed churn that
remains inside the same operational congestion band remain sample telemetry. A
matched-segment/OpenLR change, closure transition, or congestion-band transition is
material.

## Known collection gaps / remaining 003f work

RC1 intentionally leaves these visible rather than pretending completeness:

- no supported normalized Waze crowd incident/police/hazard feed has yet been
  established on the target;
- TomTom now provides one commercial incident lineage and sparse flow probes, but
  independent corroborating commercial flow/ETA and route intelligence are still open;
- CMPD address records are not geocoded yet;
- camera imagery is mapped but not yet fused into computer-vision observations;
- cross-lineage event association is deliberately not implemented yet;
- reference-route ETA/delay intelligence is not implemented yet.

003f must continue until the broader traffic collection and operator-use case is
satisfied; RC1 is the target-verified official/local substrate and RC2 is the first
commercial incident/flow extension, not the finish line.

### RC2B investigation presentation corrections

RC2A target use exposed two presentation defects that are now treated as concrete
engineering evidence rather than operator preference:

1. The geographic viewport was reset by ordinary API refresh because the refresh
   path compared raw source bounds against aspect-fitted scope bounds. Those values
   necessarily differ, so every refresh was falsely classified as a scope change.
   The resulting behavior looked like a several-second "return to default zoom" and
   could also interrupt a deep pan.
2. The map still presented heterogeneous source records more like colored pins than
   an operational picture. TomTom often carried delay/flow detail that was only
   visible after selection, while the map and event list did not expose enough of
   that operational meaning.

RC2B therefore keeps collection semantics unchanged while improving the projection:

- operator viewport persists across periodic API refresh and within the browser
  session;
- source-scope changes clamp the current operator view instead of resetting it;
- drag updates the geographic view without rebuilding the event list on every
  pointermove;
- a viewport-scoped operational panel summarizes evidence, explicit closures,
  delayed events, crash/hazard classes, and slow flow probes;
- the attention ordering is explicitly a deterministic presentation rule, not a
  confidence score or corroboration claim;
- event shape conveys event effect while color continues to convey source lineage;
- TomTom flow segments expose current/free-flow speed on-map at investigative zoom;
- road names from the existing separately sourced TIGERweb context appear at deeper
  zoom where available; and
- event rows expose operational badges and delay before source/provenance metadata.

This does not implement cross-lineage event fusion. The HMI may make multiple
observations easier to compare, but source independence and event equivalence remain
unearned until the backend correlation layer can support those propositions.

### RC2C detailed reference-map substrate

RC2B-R1 operator soak established that the geographic viewport itself no longer
resets during ordinary refresh, but target use exposed two remaining presentation
failures: wheel gestures at the map boundary could chain into document scrolling,
and the fixed TIGERweb reference geometry was too coarse for street-level
investigation.

RC2C remains a presentation-only proposition. It does not alter collection,
authority, event association, or cross-lineage semantics.

- wheel input is captured by the entire map viewport rather than only the SVG;
- the map viewport uses CSS overscroll containment and explicitly consumes wheel
  events so zooming the map does not simultaneously scroll the document;
- an operator-toggleable OpenStreetMap standard raster layer supplies detailed
  street/landuse/POI cartography beneath the CIC evidence overlay;
- the OSM layer is explicitly browser-direct **reference context only** and is not
  canonical WorldState, observation, claim, evidence, or corroboration;
- visible OpenStreetMap attribution is retained;
- only tiles intersecting the current human-viewed viewport are requested; CIC does
  not prefetch or bulk-download the OSM tile service; and
- CIC overlay projection uses Web Mercator latitude mapping so evidence aligns with
  the reference tiles rather than relying on an equirectangular approximation.

The separately sourced TIGERweb context remains available as a local reference/fallback
layer and is still useful for scope, county, and cached geographic context.

This is an interim detailed 2D substrate, not the terminal mapping architecture. The
next map-substrate lane should evaluate a locally controlled MapLibre/vector-tile
stack. That path can support richer semantic styling, Overture/OSM place layers,
terrain, and building extrusion while keeping evidence overlays source-preserving.
Satellite/aerial imagery should enter as a separately attributed reference layer,
never as silently canonical evidence. 3D building representations should likewise
preserve whether height is observed, source-provided, level-derived, or estimated.

### RC2D geographic camera substrate

RC2C target use established that the sticky operator viewport survived a multi-minute
soak, but it also exposed two presentation faults that invalidate the hand-built map
as the long-term substrate:

1. Wheel input still produced simultaneous map zoom and document scroll under the
   target Firefox/browser interaction path even though the wrapper called
   `preventDefault()`. Map gesture ownership therefore remained unearned.
2. The evidence/reference scene was visibly distorted. The RC2C SVG retained a
   fixed 1200x760 logical camera and `preserveAspectRatio="none"` while the rendered
   map container used a substantially different live aspect ratio. The raster tile
   fitter also independently scaled X and Y. That could make correct geographic data
   look oblique, stretched, or otherwise subtly wrong.

RC2D treats those as architectural pressure rather than adding another layer of SVG
camera math. It moves geographic-camera ownership to a pinned MapLibre GL JS engine
while preserving CIC evidence as a separate read-only overlay.

- MapLibre GL JS 5.24.0 is locally served from a release artifact acquired and
  SHA-256 verified by the target gate. It is a rendering mechanism, not a semantic
  authority or data lineage.
- OpenStreetMap standard raster tiles remain browser-direct noncanonical reference
  cartography beneath the CIC evidence overlay.
- Camera aspect, Web Mercator projection, panning, cursor-centric scroll zoom,
  resize behavior, bearing, pitch, and fullscreen behavior are owned by the map
  engine rather than hand-written SVG viewport math.
- CIC evidence continues to be drawn from local WorldState into an independent SVG
  overlay using `map.project()`, so projection machinery cannot silently become the
  owner of traffic truth.
- The overlay viewBox is derived from the actual rendered viewport dimensions; no
  fixed 1200x760 aspect is imposed.
- The map canvas and enclosing map boundary both consume wheel events after the map
  engine handles zoom, preventing scroll chaining into the document.
- Operator camera state now includes center, zoom, bearing, and pitch and survives
  ordinary 15-second traffic refreshes in browser-session storage.
- Explicit controls provide rotate-left/right, pitch-up/down, and `2D NORTH`; native
  MapLibre navigation/compass/fullscreen controls remain available as well.
- Pitch and rotation are explicitly projection controls only. RC2D does not claim
  terrain elevation, building height, 3D structure, or new evidence.
- The 75-mile collection boundary remains the governing pan/zoom envelope. Changing
  the camera does not change what CIC has actually collected.

RC2D is still an HMI candidate, not a promotion. Operator proof must demonstrate
that map zoom no longer scrolls the page, geographic proportions look normal across
window/aspect changes, rotation/pitch remain usable, evidence stays aligned during
camera movement, and the viewport remains stable across periodic refresh.

### RC2D-R1 — browser reference-identification repair

Target operator proof of RC2D exposed a basemap failure: OpenStreetMap returned
403 placeholder tiles because the local presentation server emitted
`Referrer-Policy: no-referrer`, suppressing the browser `Referer` required by the
standard tile service for web clients. RC2D-R1 changes the presentation policy to
`strict-origin-when-cross-origin`, preserving only origin-level cross-origin
referrer information while allowing browser-direct OSM reference requests to
identify their calling web origin. This is a presentation-egress repair only; it
does not alter CIC WorldState, collection authority, event semantics, or the
MapLibre geographic-camera model.

Constitutional scar: a locally hardened browser policy can invalidate an external
provider contract even when the provider URL, CSP allow-list, and rendering engine
are otherwise correct. Verification must exercise the actual browser request
contract, not endpoint reachability alone.

## RC2D-R2 fixed CIC site anchor

Target reconnaissance on 2026-08-13 proved that the white map marker had been derived from the regional traffic collection-scope center (`35.1115, -80.6099`), not from a live or exact operator position. Union County NC GIS Address_Point record `65294` resolved the configured CIC site at `35.12042277, -80.62950725`; the county parcel product agreed within 1.1 m but is treated only as same-lineage consistency evidence, not independent corroboration.

RC2D-R2 therefore separates three concepts:

- `location`: the traffic collection-scope center; it remains unchanged and continues to define the 75-mile collection domain.
- `operator_context.site_anchor`: a fixed, provenance-bearing CIC site anchor from configuration.
- `operator_context.live_operator_position`: unimplemented / `null`; the fixed site must never be silently presented as a live/mobile operator observation.

The HMI marker is now `CIC SITE`, and `SITE 15 MI` centers investigative viewing on that fixed anchor without changing collection scope.
### Collection center versus fixed site anchor

The regional traffic collection center remains the configured awareness center. The default TomTom
probe ID `cic-center` is retained for continuity, but its human label is now `collection-scope center
reference`; the identifier must not be reinterpreted as the physical CIC site.

RC2D-R2 exposes the fixed site separately as `operator_context.site_anchor`, backed by the recorded
Union County address-point evidence. `live_operator_position` remains null. The map therefore has no
license to imply that the fixed site is a live/mobile person location.



## 003g RC4 — explainable degradation and secure-reference quarry

The aggregate traffic situation remains intentionally `DEGRADED` whenever an enabled/configured source path is unavailable or partial and no stronger policy says that path is optional. RC4 does **not** paint that state green. Instead `/api/v1/traffic` now exposes `summary.degrading_sources` with each observed adapter path, availability, last-success timing, and bounded reason strings. The HMI surfaces those paths directly above the broader collection-gap list. Target evidence must determine which source is keeping the current system degraded before policy is changed.

### DeFlock / public surveillance-infrastructure reference candidate

DeFlock is being tracked as a **reference-source candidate**, not as live traffic truth. The project maps publicly reported ALPR/surveillance infrastructure using OpenStreetMap-compatible data. If embodied, CIC should ingest the underlying public map records with explicit OSM/DeFlock-profile provenance, slow-changing freshness semantics, and no plate/vehicle capture data. Camera-location presence would be infrastructure context, not evidence of a traffic event, police action, or observed vehicle.

### Direct camera feeds

DriveNC camera records can expose provider page/video references, but those references do not automatically grant CIC playback authority. Direct in-CIC viewing should use the provider-specific Secure Reference Gateway contract in `docs/SECURE_OPERATING_SURFACE.md` once the target recon establishes which camera hosts are public, which return credential challenges, and whether a supported stream contract exists.
