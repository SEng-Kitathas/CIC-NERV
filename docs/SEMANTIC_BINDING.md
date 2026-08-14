# 003f Semantic Binding RC2 Candidate

Read-only semantic projection over existing CIC WorldState. RC2 retains RC1 authority boundaries and adds assertion-instance identity, stable proposition identity, typed provenance roles, and explicit temporal roles.

It does not mutate WorldState, change snapshot v2, alter materiality, write the event journal, add OWL/RDF runtime dependencies, perform entity resolution, infer confidence/causality, or promote unresolved provider-native semantics.

RC2 additions:
- `proposition_key` identifies the stable proposition family independently from an assertion instance.
- `assertion_id` includes observation/derivation instance context where available, so equal-valued observations at different collection times remain distinct assertions.
- provenance distinguishes provider, adapter, source record, derivation process, world-entity reference, and future foreign-semantic authority roles.
- temporal context distinguishes phenomenon/source/observed/retrieved/derived time; unknown roles remain unknown.
- traffic-flow measurement assertions use the sibling `ObservationState.checked_at` as CIC observation time without pretending it is provider phenomenon/source time.
- RC1 `source_refs` remains available as a compatibility projection over typed provenance.
- qualifier mappings are read-only.

First bindings remain:
- ObservationState -> Observation boundary.
- UNAVAILABLE -> Absence assertion, explicitly not a negative world-state claim.
- TrafficSituationState.collection_gaps -> Collection gap.
- TomTom flow speed/travel time -> Measurement assertion.
- same-lineage traffic kernels -> Identity association without corroboration/equivalence/causality transfer.
- TomTom `confidence` -> Foreign semantic preservation with unresolved local role.

External ontology relationship:
PROV-O, SOSA/SSN, OWL-Time, QUDT/OM, and other quarry donors remain external crosswalk authorities. RC2 adds no runtime ontology dependency and does not make foreign ontology resources sovereign over WorldState.
