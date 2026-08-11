# Personal CIC

A holonic, ECS-inspired personal command environment.

## Slice 002 — Persistent Runtime

Verified Slice 001 established real self-awareness:

physical host / radio
→ adapters
→ typed components
→ shared world state
→ typed component-change events
→ systems health evaluation
→ presentation
→ durable state artifact

Slice 002 promotes that one-shot cycle into a persistent organism heartbeat.

### New in Slice 002

- `cic-runtime` long-running process
- config-driven collection and snapshot intervals
- append-only typed JSONL event journal
- graceful SIGINT/SIGTERM shutdown
- atomic final world-state snapshot on shutdown
- config-driven health thresholds
- systemd user-service installer
- `cic-self` retained as a one-shot diagnostic

## Install/update

Inside the repository virtual environment:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## One-shot diagnostic

```bash
cic-self
```

## Foreground runtime test

```bash
cic-runtime
```

In another terminal:

```bash
tail -f logs/events.jsonl
cat state/world.json
```

Stop the foreground runtime with `Ctrl+C`. It should write a final state snapshot and a
`RuntimeStopping` journal event.

## systemd user service

```bash
./tools/install-user-service.sh
systemctl --user status personal-cic.service
```

For startup before graphical login, enable user lingering once:

```bash
sudo loginctl enable-linger "$USER"
```

Then verify after reboot:

```bash
systemctl --user status personal-cic.service
tail -n 20 logs/events.jsonl
```

## Test

```bash
python -m unittest discover -s tests -v
```


## 0.2.1 event hygiene

The runtime samples current state frequently, but the durable event journal records only
operationally meaningful changes. Current world state remains fresh without turning
`logs/events.jsonl` into a five-second telemetry dump.


## 0.2.2 restart continuity

The runtime now rehydrates `state/world.json` before starting a new process lifetime. On restart,
unchanged topology and ordinary telemetry do not masquerade as newly discovered facts.
`RuntimeStarted` reports how many entities were restored, and the event journal records causes
before derived health effects.

## 0.2.3 observation integrity

Slice 002c hardens the telemetry boundary under Codex Omega's **resolve or represent
uncertainty** rule. Adapter command failure is no longer allowed to masquerade as a
device being absent or disconnected.

Adapters now emit typed observations with `observed`, `partial`, or `unavailable`
status. The world keeps the last known domain value when observation is unavailable,
and separately records an `ObservationState` that tells systems whether the current
telemetry is current, degraded, or unavailable. Health derivation runs only after an
adapter observation batch is complete, avoiding transient health conclusions from
half-updated state.

## 0.2.4 temperature source stability

Host temperature remains the maximum currently exposed sensor value, but the
semantic source is stable across Package/Core hand-offs. Normal sensor-order
changes therefore remain live telemetry instead of durable operational history.
