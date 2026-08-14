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

## Rule discrimination before enforcement

The active assurance substrate now carries an explicit rule registry at
`engineering/assurance/csc/CSC_RULE_REGISTRY.json`.

A registered rule remains `audit_only` and `enforcement_eligible=false` even
after it passes discrimination. Discrimination is necessary evidence, not an
automatic authority promotion.

Each registered rule must distinguish all four fixture classes:

- `known_good` — a specimen that must not be vetoed;
- `known_bad` — a specimen the rule must detect;
- `near_miss` — a superficially similar case that probes the exact boundary;
- `false_positive` — harmless material that must not be treated as a defect.

The command adapter is deliberately judged by its declared exit-code contract,
not by words such as `FAIL` appearing in output. Likewise, doctrine presence is
about declared doctrine artifacts, not keyword sentiment.

Current rule discrimination can be run with:

```bash
python -m tools.assurance.csc.cli discriminate
```

Generated discrimination reports remain outside authored source under the CSC
XDG state root unless an explicit external output directory is supplied.

Passing discrimination does **not** grant veto, promotion, runtime, Git, or
world authority. Any future enforcement eligibility requires a separate,
rule-specific promotion with additional evidence.
