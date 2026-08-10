# Personal CIC

A holonic, ECS-inspired personal command environment.

## Slice 001 — Self Awareness

This first vertical slice proves:

physical host / radio
→ adapters
→ typed components
→ shared world state
→ typed component-change events
→ systems health evaluation
→ presentation
→ durable state artifact

It intentionally does **not** introduce a web framework, MQTT broker, database, or device-control framework yet.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cic-self
```

The current world snapshot is written to `state/world.json`.

## Test

```bash
python -m unittest discover -s tests -v
```
