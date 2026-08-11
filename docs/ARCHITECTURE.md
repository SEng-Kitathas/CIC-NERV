# Architecture Baseline

## North star

**Sense → Understand → Act**

## Composition model

Entities are stable identities. Components carry capabilities, properties, and observed state.
Systems operate on matching components. Adapters terminate vendor / OS-specific ugliness at
the boundary. Presentation consumes normalized world state. Future controls emit intents rather
than directly manipulating devices.

## Holonic rule

A holon is simultaneously a coherent whole and a valid part of a larger whole. A holon earns
a boundary when it has a clear purpose, ownership boundary, interface, invariants, and hazards.

## Slice 001 — Self Awareness

The Systems holon observes the Engage and Tenda, normalizes telemetry into components,
derives health, emits typed events, and embodies a world snapshot.

## Slice 002 — Persistent Runtime

The one-shot cognition cycle becomes a persistent process:

1. Runtime starts and emits `RuntimeStarted`.
2. LinuxHostAdapter and TendaU11ProAdapter collect on a configured interval.
3. WorldState accepts only changed components.
4. `ComponentUpdated` events flow synchronously through systems.
5. HealthSystem derives normalized `HealthState`.
6. Every typed event is appended to `logs/events.jsonl`.
7. WorldState is atomically embodied to `state/world.json`.
8. SIGINT/SIGTERM cause a final snapshot and `RuntimeStopping`.
9. systemd owns process resurrection; runtime code does not reinvent supervision.

## Runtime ownership

The runtime owns scheduling and lifecycle only. It does **not** own:

- hardware semantics,
- health semantics,
- UI state,
- device control logic,
- RF interpretation.

Those remain in adapters, systems, presentation, and future control holons.

## Anti-grimoire invariants

- Vendor/OS details stop at adapters.
- Shared world state is canonical.
- Systems own behavior.
- UI does not own operational truth.
- UI will emit intents rather than direct side effects.
- Configuration is data.
- Research code stays out of runtime.
- Odd hardware gets adapters, not exceptions in core.
- Process supervision is delegated to systemd rather than reimplemented.
