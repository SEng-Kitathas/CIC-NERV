# CIC-native CSC active assurance

The recovered CSC/PDVER lineage is preserved under `engineering/lineage/csc/`.
That lineage is donor evidence, not directly executable CIC authority.

The CIC-native active assurance implementation lives under
`tools/assurance/csc/` and begins in **audit-only** mode.

Audit-only means:

- it may discover CIC source and doctrine;
- it may execute already-qualified source-local verification commands;
- it may structure findings, remediation, and PDVER phase/level metadata;
- it may write generated reports outside the repository;
- it may not veto promotion, rewrite Git, restart services, mutate deployment
  configuration, or manufacture runtime/world authority.

The profile parser rejects any authority mode other than `audit_only` until a
later source change separately earns enforcement authority.

Before enforcement can exist, CSC itself must demonstrate useful discrimination
against known-good, known-bad, adversarial near-miss, and false-positive fixtures.
Rules that cannot discriminate are heuristics, not gates.

Dependency remains one-way:

`CSC assurance -> CIC inspection` is allowed.

`CIC runtime -> CSC assurance` is forbidden.
