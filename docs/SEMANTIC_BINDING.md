# 003f Semantic Binding RC1

Read-only semantic projection over existing CIC WorldState. It does not mutate WorldState, change snapshot v2, alter materiality, write the event journal, add OWL/RDF runtime dependencies, or promote unresolved provider-native semantics.

First bindings:
- ObservationState -> Observation boundary.
- UNAVAILABLE -> Absence assertion, explicitly not a negative world-state claim.
- TrafficSituationState.collection_gaps -> Collection gap.
- TomTom flow speed/travel time -> Measurement assertion.
- same-lineage traffic kernels -> Identity assertion without corroboration/equivalence/causality transfer.
- TomTom `confidence` -> Foreign semantic preservation with unresolved local role.
