# Personal CIC Authority and Lineage

## Current target-verified authority

As of 2026-08-14, the authoritative Personal CIC semantic-foundation checkpoint is:

```text
TAG        slice-003f-semantic-binding-rc7-target-verified
COMMIT     424c8ade02fa4ad4c9f944c82e56a6c715615b18
TREE       d8ba2a50651d42c14524299b14d6672c76de8cdd
PARENT     7a71fe605809325de7bda8fb8a78d019c734ba6f
TAG OBJECT 779af03cd5cca0077112c7c0b23639b87259652d
```

The RC7 target qualification established:

- 48/48 focused semantic tests PASS;
- 17/17 focused presentation tests PASS;
- 258/258 full regression PASS;
- source-distribution hygiene PASS;
- runtime ontology dependency firewall PASS;
- live `/world` PASS;
- live `/api/v1/semantics` PASS;
- POST mutation rejection (405) PASS;
- exact committed tree preserved through restart;
- exactly four MapLibre runtime members remain intentionally derived/untracked.

`WorldState` remains the sole world authority. Semantic projection is bounded read-only inspection and
has no semantic persistence or write authority.

## Active source candidate

The active post-RC7 development line is **003g Runtime Authority Integrity**. The current authored-source
candidate is RC4 of that slice. It derives from RC7 and remains **unpromoted until exact target proof**.

RC3 preserves the Runtime Authority mechanisms and the RC2 configuration-control/HMI truth alignment,
then reconciles the FIE documentation against the closed OIG/EDG first-pass results and adds the
non-canonical CIC reasoning/provenance handoff. No new runtime authority mechanism is introduced by the
RC3 document reconciliation. Source-local verification can qualify the candidate; only target promotion
discipline can create a new authority checkpoint.

## Configuration-control rule

Current-facing documentation must distinguish:

1. target-verified authority;
2. active source candidate;
3. historical candidate/audit records;
4. derived runtime state.

Historical audit artifacts retain the authority statements they had when created. They are evidence of
that time, not present-tense authority.

Hard-coded UI lineage labels are avoided unless generated from a verified deployment-identity mechanism.
A UI label must not silently fossilize an obsolete release name.

## Development direction

Semantic Binding RC7 closes the ontology-foundation expansion workstream for now. New semantic homes are
pressure-triggered only. Mainline development resumes with Runtime Authority Integrity and then evidence
association/correlation work that consumes the semantic substrate without making semantics a second world
writer.
