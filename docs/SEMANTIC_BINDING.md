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

