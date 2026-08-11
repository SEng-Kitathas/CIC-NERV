# Changelog

## 0.2.1 — Event Hygiene

- Separated current-state sampling from durable operational event significance.
- Added Systems-holon materiality policy.
- Uptime, tiny memory/storage fluctuations, and link-rate churn remain live world state without flooding the journal.
- Health threshold crossings, connectivity changes, USB state changes, large telemetry shifts, and structural Wi-Fi changes remain durable events.
- Added tests for event significance and journal filtering.

## 0.2.0 — Slice 002: Persistent Runtime

- Added long-running `cic-runtime`.
- Added graceful SIGINT/SIGTERM lifecycle.
- Added typed append-only JSONL event journal.
- Added config-driven collection/snapshot cadence.
- Moved health thresholds into configuration data.
- Added shared bootstrap path for one-shot and persistent modes.
- Added systemd user-service install/uninstall helpers.
- Expanded tests for journaling and runtime configuration.

## 0.1.0 — Slice 001: Self Awareness

- Added Engage and Tenda entities.
- Added Linux and Tenda adapters.
- Added typed components, WorldState, EventBus, HealthSystem, and console projection.
- Added atomic world-state snapshot.
