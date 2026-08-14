# CSC / PDVER Assurance Boundary

CSC is part of CIC's engineering authority and source lineage. It is not part of
CIC's operational phenotype.

## Artifact classes

### Repository / authored engineering source

The repository may contain:

- `engineering/lineage/csc/**` — historical executable/doctrinal lineage;
- `tools/assurance/csc/**` — active CIC-native CSC tooling after qualification;
- `tests/assurance/csc/**` — CSC self-audit and discrimination fixtures;
- a CIC-specific CSC project/profile definition when the active tool is earned.

### Runtime package / installable product

The installable `personal_cic` Python package must contain none of those paths.

The runtime package is discovered from `src/` only. Engineering lineage,
development tools, tests, donor evidence, reports, and CSC profiles are separate
authored artifact classes.

## Dependency direction

```text
assurance tooling -> inspect CIC                   ALLOWED
personal_cic      -> import assurance tooling      FORBIDDEN
```

A running CIC process must not require CSC to import, start, observe, persist,
recover, or serve operator projections.

## Authority

A clean CSC result can qualify source/governance claims within its proved scope.
It cannot manufacture:

- runtime qualification;
- provider reachability;
- current world authority;
- exact deployed-tree identity;
- restart/re-entry success;
- Git promotion or publication success.

Those remain claim-matched target proof obligations.

## Development checkout versus runtime install

The current development target executes from an editable repository checkout.
Therefore engineering files may be physically present on that development
machine. Physical co-location does not make them runtime dependencies or members
of the distributable runtime package.

A runtime-package boundary gate must therefore inspect the built wheel itself and
also reject runtime imports of engineering/assurance namespaces.
