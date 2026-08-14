# 003f Semantic Binding RC3

RC3 extends the target-verified RC2 semantic spine without changing its identity,
provenance, temporal, or read-only authority contracts.

```text
provider / adapter
    -> existing typed CIC components
    -> WorldState (world authority)
    -> read-only semantic projection
```

No `WorldState` component changes. No snapshot/journal schema changes. No ontology
runtime dependency is added.

## RC2 foundation preserved

- proposition identity remains distinct from assertion-instance identity;
- provenance remains typed by provider / adapter / source-record / derivation / world reference;
- phenomenon, source, observed/retrieved, and derived times remain role-bearing;
- unknown time roles remain unknown;
- qualifiers and semantic assertions remain read-only;
- provider-native TomTom confidence remains unresolved foreign semantics.

## RC3 promoted runtime bindings

### Authority / freshness

CIC intentionally retains last-known components after collection loss. RC3 therefore
projects semantic authority independently from component presence:

- `current`
- `degraded_or_mixed`
- `retained_by_policy`
- `last_known_noncurrent`
- `unscoped`
- `locally_derived`

**LAST-KNOWN STATE IS NOT CURRENT STATE.**

### Traffic reports and evidence

A `TrafficEventObservation` is projected as a source report, not as identity for a
world event. Event start time is phenomenon time; provider report/update time remains
source time; CIC collection check time remains observed-at time.

A CURRENT successfully empty event collection can provide scoped negative evidence
for that provider/source-family/scope only.

**EVENT RECORD IS NOT WORLD EVENT.**
**REPORT IS NOT CAUSATION.**
**CURRENT EMPTY COLLECTION IS NOT UNIVERSAL ABSENCE.**

### Measurement and data-product quality

TomTom successful/configured probe fraction is projected as collection-completeness
quality, separate from provider confidence, source reliability, and claim confidence.

Station observations and provider current weather values are measurements. The
current-weather fusion product is a CIC-derived estimate and is not re-labeled as a
direct observation.

**DATA-PRODUCT QUALITY IS NOT CLAIM CONFIDENCE OR SOURCE RELIABILITY.**
**DIRECT OBSERVATION IS NOT DERIVED ESTIMATE.**

### System state

- `HealthState` -> derived State condition.
- CPU / memory / storage / temperature -> Measurement assertion.
- USB presence -> State condition.
- Wi-Fi connectivity -> State condition.
- Wi-Fi signal / rates -> Measurement assertion.

**DERIVED HEALTH IS NOT RAW TELEMETRY.**
**CONNECTIVITY STATE IS NOT SIGNAL MEASUREMENT.**

## Explicit non-promotion

RC3 does not create topology edges from component co-location in an Entity.

**COMPONENT CO-LOCATION IS NOT A PROVED TOPOLOGY EDGE.**

It also does not introduce source-reliability scores, causal assertions, foreign
ontology IRIs, or graph persistence. Those require independent runtime pressure.

## RC4 — Forecast Modality + Information-Artifact Boundary

Daily and hourly forecasts are predictive epistemic assertions, not observations,
measurements, or present-world state. Forecast target time is `phenomenon_time`;
provider issue/update time remains `source_time`; CIC collection time remains
`observed_at`.

**FORECAST VALUE IS NOT OBSERVED VALUE.**
**PREDICTION IS NOT MEASUREMENT.**
**FUTURE PHENOMENON TIME IS NOT SOURCE ISSUE TIME.**

Radar mosaics/context, traffic-camera records, and dynamic-message-sign records are
preserved as information artifacts. They do not become weather-event identity,
interpreted visual evidence, or physical-event truth without an explicit interpretation
process.

**INFORMATION ARTIFACT REQUIRES INTERPRETATION BEFORE BECOMING A WORLD CLAIM.**
**CAMERA RECORD IS NOT CAMERA OBSERVATION RESULT.**
**MESSAGE TEXT IS NOT EVENT TRUTH.**

## RC5 — Spatial Roles + Geometry Authority

RC5 is the first runtime-earned promotion of a native `Spatial assertion` semantic
home. It does not import GeoSPARQL, run spatial inference, or create automatic
identity/correlation edges. It names spatial roles that CIC already materially
distinguishes.

Promoted roles include:

- collection scope center + radius;
- acquisition query/reference point;
- provider-matched road geometry;
- source-reported event geometry;
- provider-reported infrastructure point;
- radar product coverage envelope;
- reference-context coverage envelope;
- derived traffic-awareness scope.

Constitutional firewalls:

**COLLECTION SCOPE IS NOT OBJECT LOCATION.**

**QUERY POINT IS NOT MATCHED GEOMETRY.**

**REPORTED GEOMETRY IS NOT ENTITY IDENTITY.**

**SHARED OR INTERSECTING GEOMETRY DOES NOT ESTABLISH SAME EVENT.**

**RADAR PRODUCT EXTENT IS NOT STORM FOOTPRINT.**

**REFERENCE GEOMETRY DOES NOT ACQUIRE METEOROLOGICAL OR TRAFFIC AUTHORITY BY CO-RENDERING.**

**INFRASTRUCTURE LOCATION IS NOT SENSOR FIELD OF VIEW, OBSERVATION RESULT, MESSAGE CONTENT LOCATION, OR EVENT LOCATION.**

The runtime remains deliberately non-inferential: RC5 preserves and labels geometry
so later association engines can reason from explicit spatial roles without first
having to recover what each coordinate meant.

## RC6 — Source Classification, Reported Condition, and Metric Authority

RC6 does not add a new semantic home. It uses the homes already earned by runtime
pressure to prevent provider vocabularies and provider-reported conditions from
silently becoming NERV-native truth.

Provider categorical fields such as Open-Meteo weather codes, AviationWeather flight
category/present-weather expressions, NWS alert event/severity/urgency, and traffic
event category/severity/probability/time-validity/code fields are projected as
`FOREIGN_NATIVE` assertions with an explicit `FOREIGN_SEMANTIC_AUTHORITY` provenance
role. Their local mapping status remains unresolved.

**PROVIDER CLASSIFICATION IS NOT NERV CLASS MEMBERSHIP.**

**FOREIGN CODE IS NOT LOCAL CONDITION WITHOUT AN EXPLICIT CROSSWALK.**

Raw METAR text remains an information artifact. Parsed fields can support distinct
semantic assertions, but the raw report is not itself world state.

Provider closure booleans are projected as source reports rather than direct physical
verification. A provider-reported `false` does not prove unrestricted road access or
absence of lesser lane restrictions.

**PROVIDER REPORT IS NOT DIRECT PHYSICAL VERIFICATION.**

**REPORTED NOT-FULL-CLOSURE IS NOT PROOF OF NO RESTRICTION.**

Provider delay/length values are provider-estimated measurements. Community report
count is preserved as a count while explicitly refusing to treat plurality as
independent corroboration, claim confidence, or source reliability.

**SOURCE PLURALITY IS NOT INDEPENDENCE.**

**REPORT COUNT IS NOT CLAIM CONFIDENCE.**

The copied `flight_category` field in `CurrentWeatherEstimateState` remains deliberately
unprojected because its source-record lineage is not yet explicit enough to reassert it
without provenance loss.

## RC7 — Live Semantic Inspection + Atomic Projection Boundary

RC7 stops expanding semantic breadth and makes the semantic layer operationally
inspectable through the loopback presentation boundary.

`GET /api/v1/semantics` exposes a bounded JSON projection of semantic assertions with:

- assertion-instance and proposition identity;
- owning world-entity reference;
- semantic kind and native home;
- subject, predicate, and value;
- typed provenance sources and derivation reference;
- independent temporal roles;
- qualifiers/firewalls.

Exact filters are available for entity, semantic kind, and predicate. Responses are
bounded by a validated limit (default 500, maximum 2000) and declare projected,
filtered, returned, and truncation counts.

**THE SEMANTIC API IS AN INSPECTION SURFACE, NOT WORLD AUTHORITY.**

**SERIALIZATION DOES NOT CREATE PERSISTENCE OR A SECOND WRITER.**

### Atomic read boundary

Before RC7, `project_world_semantics()` walked `WorldState.entities` directly. That was
acceptable while the function was effectively library/test-only, but exposing it to a
live HTTP reader would allow projection to race collector updates.

RC7 adds `WorldState.read_entities_snapshot()`: a lock-bounded, detached typed entity
view used by semantic projection. Live semantic reads therefore project one stable
entity universe rather than iterating the mutable world mapping.

**READ-ONLY DOES NOT MEAN RACE-SAFE BY ITSELF.**

**A LIVE PROJECTION MUST HAVE A DEFINED READ CONSISTENCY BOUNDARY.**

No world snapshot schema, journal schema, semantic persistence, foreign ontology
runtime, inference engine, or write endpoint is added.

