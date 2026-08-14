# Runtime Authority Integrity

Status: 003g Runtime Authority RC4 source candidate. RC7 remains target-verified authority. This document defines runtime authority mechanics; it does not claim target promotion.

## Constitutional boundary

Personal CIC distinguishes the process being alive from the mechanisms that earn collection authority being alive.

> COLLECTION AUTHORITY MUST NOT OUTLIVE THE MECHANISM CURRENTLY EARNING IT.

It also distinguishes in-process `WorldState` authority from ownership of its durable embodiment.

> DURABLE WORLD EMBODIMENT MUST HAVE EXACTLY ONE WRITER OWNER.

## Fractal-isomorphic relationship

Runtime Authority remains a useful FIE/OIG-EDG quarry specimen, but RC3 does not claim a universal
recurring grammar. Its local design can be examined through bounded relations such as GC-01
(guarantee-support concordance), GP-01 (propagation shaping), CS-01 (consequence-scope alignment), and
GR-01 (function restoration != guarantee restoration). Aerospace FDIR, circuit breakers, ECS, and semantic
firewalls remain non-identical donors/analogues whose transfer requires frame/intervention/breakpoint proof.
See `FRACTAL_ISOMORPHISM_ENGINEERING.md`.

## Enabled worker liveness

`WorldAwarenessWorker` and `TrafficAwarenessWorker` expose a typed `WorkerRuntimeStatus` with a closed lifecycle:

- `initialized`
- `starting`
- `running`
- `stopping`
- `stopped`
- `failed`

The status records worker start, scheduler-cycle timing, terminal stop time, and a bounded terminal-failure classification. It is runtime-mechanism evidence only and does not confer `WorldState` authority.

Unexpected worker exceptions are captured at the worker boundary. Arbitrary exception text is not persisted or projected because provider/request failures may contain credentials or source-native sensitive details. An enabled worker entering `failed` wakes the main runtime, causes `WorkerAuthorityFailure`, and therefore exits the process nonzero. The installed user service already uses `Restart=on-failure`.

A terminal worker failure is not converted into a graceful stop merely because the worker callback uses the runtime stop event as its wake-up primitive.

## Failure shutdown

When an enabled collection worker fails:

1. the failure becomes a typed runtime fact;
2. the main loop is woken immediately;
3. the runtime exits through a failure path;
4. presentation is stopped;
5. a forced final world snapshot is deliberately skipped;
6. the next runtime epoch must pass the existing remote re-entry gate before presentation can expose remote `CURRENT` authority again.

This preserves the existing rule that persisted remote state cannot silently regain current authority after restart.

## Durable-state single writer

`DurableStateLease` takes a non-blocking exclusive OS `flock` on a lock file beside the configured world snapshot. The lock, not file existence, is the authority.

The persistent runtime acquires the lease before:

- journal publication;
- world-state hydration;
- re-entry mutation;
- periodic/final snapshot writing.

The one-shot `cic-self` command uses the same lease before hydration and writeback. A second writer therefore fails before it can touch the durable world proposition.

The lock file is runtime state and is excluded from authored Git identity by `state/*.lock`.

## Read-only presentation

`/api/v1/systems` may project worker-liveness facts supplied by the runtime metadata seam. Presentation remains read-only and owns no worker or world truth.

Example shape:

```json
{
  "runtime": {
    "workers": {
      "world-awareness": {
        "lifecycle": "running",
        "started_at": "...",
        "last_cycle_started_at": "...",
        "last_cycle_completed_at": "...",
        "stopped_at": null,
        "terminal_failure": null
      }
    }
  }
}
```

## Non-goals

This slice does not introduce:

- semantic persistence;
- a second world-state writer;
- snapshot schema changes;
- provider retry policy changes;
- event-journal rotation;
- persistence cadence optimization;
- cross-lineage evidence association.

Those remain separate operational questions.
