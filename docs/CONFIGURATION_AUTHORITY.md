# Configuration Authority

Configuration is **declarative intent**, not operational proof.

```text
AUTHORED SOURCE
    reusable mechanisms + neutral configuration example

DEPLOYMENT CONFIGURATION
    mutable node/site/provider/operator setup for one installation

SECRET STATE
    credentials granting external access

WORLD STATE
    evidence-bearing model of what CIC currently knows

RUNTIME AUTHORITY
    mechanisms and collections currently qualified on this target
```

These artifact classes may interact but are not interchangeable.

## Runtime configuration

The default live runtime configuration is:

```text
${XDG_CONFIG_HOME:-~/.config}/personal-cic/runtime.json
```

It is deployment-local mutable state and is ignored by Git.
`config/runtime.example.json` is the authored reusable example.

The installer may initialize a **missing** deployment config from that neutral
example, with owner-only permissions, but must never overwrite an existing
configuration.

## Secrets

Provider credentials remain separate from ordinary configuration. Naming a
credential environment variable does not establish that the credential exists,
works, or currently earns collection authority.

## Location semantics

Collection-scope center, fixed site anchor, node location, operator default
area, live operator position, query location, target location, and collection
coverage geometry are independently variable roles. Coincidence in one
installation does not make them identical.

## Promotion law

```text
configuration present
    != configuration valid for a task
    != mechanism reachable
    != mechanism qualified
    != collection successful
    != observation current
    != claim warranted
```

A0.1 moved the live target to deployment-local configuration while preserving
003g Git/source authority. A0.2 separates reusable source distribution from the
private deployment specimen and changes runtime/install defaults accordingly.

Remaining deployment-specific production defaults and stable deployment/node/site
identity are subsequent pressure-driven work. Historical provenance, provider-native
regional scope, and regression fixtures are not erased merely because they name the
current region.
