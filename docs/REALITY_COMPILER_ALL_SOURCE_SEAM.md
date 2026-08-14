# Reality Compiler All-Source Semantic Seam

Status: **candidate substrate; no new world/runtime/promotion authority**

This seam adds provider-independent Source/Evidence/Query/Collection primitives before
additional source families are connected. It does not replace current traffic/weather
components, `WorldState`, or read-only semantic projection.

## Architectural firewall

Operator/research labels such as HUMAN-ORIGIN, FININT, SOCMINT, GEOINT, CYBINT, and
similar families are views over orthogonal semantics. They are not canonical
world-model classes.

The machine-facing dimensions are:

- source agent;
- information origin;
- acquisition regime;
- observation modality;
- publication medium;
- source lineage and lineage relation;
- handling policy;
- statement and evidence relation;
- information requirement and observation capability;
- coverage claim and collection gap;
- observation opportunity, acquisition task, and acquisition attempt.

## Existing CIC roles preserved

`core.observations.Observation` remains an adapter collection-result envelope. It is not
redefined as a universal Evidence-IR observation.

`ObservationState` remains collection/currentness qualification.

Existing traffic `source_family` and `TrafficSituationState.collection_gaps` remain
domain-specific compatibility surfaces. They are not silently reclassified as universal
source ontology or query-relative `CollectionGap`.

`SemanticAssertion` remains a read-only semantic projection surface. The new IR does not
write `WorldState` or replace the existing semantic spine.

## Acceptance proofs

The initial seam is qualified by six focused proofs:

1. human statement/report does not manufacture world state;
2. known syndication/common origin does not manufacture independence;
3. financial ceiling semantics cannot become paid-transfer semantics;
4. source count cannot fill missing required capabilities;
5. collection opportunity/task/attempt does not become target-world evidence;
6. protected reporter identity is not required as an ordinary WorldState entity.

## Pressure laws

These remain candidates until broader cross-modal integration proves them:

> SOURCE DIVERSITY DOES NOT EQUAL OBSERVATIONAL BREADTH. BREADTH IS THE
> QUALIFIED, INDEPENDENT CAPABILITY TO DISCRIMINATE DIMENSIONS OF AN
> INFORMATION REQUIREMENT.

> SOURCE-NATIVE SEMANTICS MAY BE PRESERVED, WEAKENED, OR QUALIFIED; THEY MAY
> NOT BE STRENGTHENED INTO A DIFFERENT WORLD RELATION WITHOUT ADDITIONAL WARRANT.

> OPPORTUNITY IS NOT OBSERVATION. TASK IS NOT SUCCESS. ATTEMPT IS NOT EVIDENCE
> OF THE TARGET PHENOMENON.
