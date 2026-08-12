# Radar / Spatial Precipitation Awareness — 0.3.4

## Scope

Personal CIC consumes NOAA/NWS operational MRMS CONUS QCd base-reflectivity as a rendered WMS mosaic and separately overlays current NWS short-fuse warning geometry.

```text
MRMS RIDGEII product index
        -> latest BREF.QCD stream timestamp
        -> source-stream freshness witness
NWS GeoServer WMS
        -> independently retrieved latest bounded base-reflectivity PNG
NWS warning WMS
        -> transparent warning overlay PNG
        -> atomic local cache
        -> RadarMosaicState metadata
        -> loopback read-only /radar/*.png
        -> World HMI
```

Image bytes are adapter-owned cache artifacts, not WorldState facts. WorldState stores product identity, bounds, the independently observed MRMS stream-latest timestamp, WMS frame retrieval time, image hashes, and observation authority. The stream-latest GeoTIFF is a freshness witness; CIC does not claim the unversioned WMS render is that exact file.

## Truth rules

- latest MRMS stream time is derived from the official RIDGEII directory filename timestamps and is used only as a source-stream freshness witness;
- the WMS frame has its own retrieval timestamp/hash and is not falsely bound to the indexed GeoTIFF;
- stale or malformed source indexes do not fabricate a current radar frame;
- radar-image retrieval failure preserves last-known state/cache but withdraws CURRENT authority;
- warning-overlay failure yields DEGRADED radar observation and removes the cached warning overlay rather than presenting stale warning geometry as current;
- two-minute frame/image/hash churn is sample telemetry and not durable history;
- product/layer/bounds/overlay availability changes are material;
- browser receives only locally cached imagery through the loopback presentation server.

## Product

Initial product: `BREF.QCD` / `conus_bref_qcd`, quality-controlled base reflectivity in dBZ.

Initial local range: 75 miles around the configured World location.

Raw Level-II volume decoding is intentionally outside this slice.
## Geometry and stale-state rules

`range_miles` is the radius of the largest centered range ring. The vertical map half-extent is
that range; the horizontal geographic extent expands with the requested image aspect ratio so the
render preserves approximately equal miles-per-pixel rather than stretching a square physical area
into a wide raster. Range rings are sized from the rendered stage height for the same reason.

A last-known radar frame may remain visible while radar observation authority is UNAVAILABLE, but
the frame is explicitly labeled `LAST KNOWN`. Warning geometry is stricter: cached warning polygons
are never rendered as current after radar authority is withdrawn. A warning overlay is shown only
when the current radar observation is CURRENT/DEGRADED and the overlay succeeded in that observation
cycle.
## Cache identity invariant

The browser never receives a cached radar image merely because a fixed file exists. The projection
places the expected SHA-256 in the loopback image URL, and the presentation server hashes the cached
PNG before serving it. If a process dies between atomic cache replacement and WorldState/snapshot
update, an old metadata hash cannot silently authorize newer image bytes; the server returns a frame
identity mismatch until a fresh observation reconciles state and cache.

The radar collector is scheduled after the smaller alert/surface/weather/forecast calls when several
remote sources are simultaneously due, so multi-request image retrieval does not take priority over
the more time-sensitive structured weather feeds. The static reflectivity legend is reused from a
validated local cache instead of being downloaded every two-minute radar cycle.


## Runtime cache hygiene

`state/radar/` is runtime-owned cache state and is ignored by Git. The repository retains only
`state/.gitkeep`; collected radar, warning, and legend PNGs must never dirty the source tree or enter
a checkpoint.

## 0.3.4 context and loop

The 0.3.4 continuation adds two presentation capabilities without changing radar truth semantics.

### Geographic context

Census TIGERweb reference geometry is collected server-side and cached under the radar runtime cache. The initial context set uses county boundaries, the generalized `Primary Roads 2_1M scale` layer, the Interstate/US-highway secondary-road layer, and incorporated/CDP internal points for sparse place labels. The browser never calls TIGERweb directly.

`RadarContextState.context_sha256` identifies the exact cached JSON artifact served to the browser. `content_sha256` identifies the same normalized context with retrieval time removed; materiality compares the latter, so a routine refresh of unchanged geography remains sample telemetry.

The vector context is deliberately subdued and rendered over the opaque radar raster. It is reference geometry, not meteorological evidence.

### Recent-frame loop

Each distinct observed WMS frame is stored under its SHA-256 in a bounded runtime cache together with the warning-overlay image captured during the same collection cycle. The typed frame reference carries WMS retrieval time, image hash, optional warning hash, and the contemporaneous MRMS stream-freshness witness.

The loop contains only actually retrieved frames. Adjacent visually identical radar+warning pairs are de-duplicated rather than padded with fake repeated animation frames. Playback performs no interpolation or frame blending. Autoplay waits for three distinct observed frames so a two-frame cache cannot masquerade as meaningful motion. The browser preserves the currently displayed frame across its 5-second API refreshes instead of snapping playback back to newest. Once three distinct frames exist, the operator surface auto-runs the loop; play/pause and previous/next controls allow inspection.

Frame-list growth and normal turnover remain sample telemetry. Radar availability, warning-overlay authority, product/bounds changes, and radar-context semantic-content changes retain material significance.


### Context canonicalization and cache-serving grace

TIGERweb feature order is normalized before semantic hashing. A provider response that contains the same county/road geometry in a different feature order therefore does not fabricate a context-content transition.

The loop manifest remains bounded to the configured frame capacity. Immutable PNG files from the immediately previous manifest receive one collection-generation serving grace before pruning. This prevents a concurrent browser reading the previous WorldState from losing a still-published oldest-frame URL during the collector-to-ingest handoff, while keeping the runtime frame cache bounded to approximately the loop capacity plus one distinct frame.
