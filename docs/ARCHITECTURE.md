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

## Slice 001

The Systems holon owns local compute/network operational state and health evaluation. It does
not own presentation, RF interpretation, or vendor device control.

Runtime path:

1. LinuxHostAdapter observes the Engage.
2. TendaU11ProAdapter observes the Tenda radio.
3. WorldState stores typed components by entity.
4. ComponentUpdated events are emitted on material state changes.
5. HealthSystem consumes those events and derives HealthState.
6. ConsoleView projects the shared state.
7. WorldState is atomically embodied to `state/world.json`.

## Anti-grimoire invariants

- Vendor/OS details stop at adapters.
- Shared world state is canonical.
- Systems own behavior.
- UI does not own operational truth.
- Configuration is data.
- Research code stays out of runtime.
- Odd hardware gets adapters, not exceptions in core.
