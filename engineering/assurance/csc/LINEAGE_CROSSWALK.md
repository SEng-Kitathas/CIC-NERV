# CSC donor -> CIC-native active assurance crosswalk

The active CIC CSC implementation is derived from the recovered standalone
`universal_csc` donor, but it is not a verbatim copy.

## Preserved generalized primitives

- explicit project profile;
- structured gate/finding model;
- severity plus blocking semantics;
- PDVER phase and nano/micro/meso/macro levels;
- declared command adapters;
- discovery and evidence hashing;
- claim/governance separation;
- recursive remediation output;
- generated structured report;
- self-audit pressure against known-good and known-bad fixtures.

## Changed for CIC

- authority is hard-limited to `audit_only`;
- reports default outside the repository under XDG state;
- project discovery walks only declared source/doctrine roots plus the sealed
  lineage anchor rather than indiscriminately hashing mutable runtime state;
- PCMMAD/receiver launcher and credential names are removed;
- receiver route-report assumptions are removed;
- project-local finalizer assumptions are removed;
- existing CIC verification tools are consumed as explicit command adapters;
- runtime/package qualification remains external evidence and is not inferred
  from generic CSC cleanliness.

## Not yet imported as blocking rules

The donor's fixed function-length, argument-count, broad style/footgun scans,
doctrine keyword coverage, route heuristics, launcher heuristics, and other
native rules are not granted blocking authority merely because they existed in
the donor. They require CIC-specific discrimination fixtures and false-positive
pressure first.

This is deliberate CSC lineage compliance: import the earned invariant, not the
historical syntax or target-specific ceremony.

## Discrimination hardening translation

The recovered CSC v2 doctrine required the checker to prove that its own rules
can distinguish known-good, known-bad, adversarial near-miss, and false-positive
specimens. CIC now embodies that invariant directly through an explicit rule
registry and generated discrimination report.

This is intentionally not a restoration of every historical slop rule. The
first registered rules cover only already-earned structural/authority seams:

- audit-only authority mode;
- command exit-contract semantics;
- exact lineage-anchor presence;
- declared doctrine-surface presence;
- exact project source-root contract.

All remain `enforcement_eligible=false`. Historical complexity, LOC, argument,
style, keyword, launcher, and route heuristics remain lineage evidence until
they independently earn useful discrimination against CIC-specific fixtures.
