# Universal CSC Finalizer

Standalone project-agnostic CSC/PDVER finalizer prototype.

Canonical algorithm:

```text
PROBE -> DERIVE -> VERIFY -> EMBODY -> RECURSE
```

Primary command:

```cmd
python tools\csc_native\universal_csc_finalize.py run --project C:\Users\ancal\Desktop\PCMMAD_receiver --fail-closed
```

This project is intentionally separate from the receiver until the universal tool is stable enough to integrate.

## Manifest/profile layer

The tool reads `csc_project.json` or `csc_profile.json` from the target project. A manifest can declare active roots, doctrine roots, evidence roots, command gates, report gates, and sidecars. Generic adapters run after native universal gates and before claim governance.


## Research synthesis command

`research-synthesis` consumes Pass 5 / Pass 6 / Pass 7 evidence ledgers and writes `reports/UNIVERSAL_CSC_RESEARCH_SYNTHESIS.json` plus markdown. Research outputs remain evidence-plane artifacts, not active-source gates.
