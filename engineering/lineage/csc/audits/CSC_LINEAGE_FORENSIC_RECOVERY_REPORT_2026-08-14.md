# CSC / PDVER Forensic Recovery Report

**Date:** 2026-08-14  
**Status:** RECOVERED ENOUGH TO BEGIN CIC-NATIVE REINTEGRATION DESIGN  
**Mutation:** None to CIC source/repo/runtime.

## 1. What the supplied corpus recovered

The upload was substantially better than merely "what could be found."

It contains all three previously requested authority specimens, and each exact
hash matches the historical expectation:

- `PCMMAD_RECEIVER_V29_NATIVE_PROTOCOL_RC1.zip`
  - `5baf9b66a9137d950aeabac2ea76fbbb919e177f90788e5341ee6e15a80b89d8`
  - **MATCH**
- `PCMMAD_RECEIVER_V28_PDVER_REFACTOR.zip`
  - `0b024d46eadd96be43d609898874e3c051bb7a8941d33be5ac848b7271571f54`
  - **MATCH**
- `e drive csc alternate.zip`
  - `a0a907d4e1de95ff454fc3af8d1e66e5b3b361d0ce429742377264a265a4d8ec`
  - **MATCH**

The upload also contains the missing counterpart:

- `e drive csc.zip`
  - `4366bacf617f99c8a415dce37abc211bdaa504c6cd79fde252064e58079b6c22`

And it contains the surviving pre-refactor PCMMAD specimen itself:

- `PCMMAD_receiver.zip`
  - `b4d8a284a0acc9ef37aa115d2be4e4b67550730d80555e06771bc41c820564a3`
  - this exactly matches the `PCMMAD_receiver(2).zip` surviving-specimen SHA
    named by both V28 and V29.

**No additional CSC archive is required before the primary recovery can proceed.**

## 2. e-drive CSC main vs alternate

Raw archive comparison after stripping only the top-level container directory:

- main paths: **1705**
- alternate paths: **3781**
- common paths: **1705**
- byte-identical common paths: **1645**
- changed common paths: **60**
- main-only paths: **0**
- alternate-only paths: **2076**

Therefore the raw alternate archive is a **strict superset container** of the
main archive: every main relative path is present in alternate, with 60 changed
common members and 2076 additional members.

V29's refactor audit states that it compared **1705 paths in each CSC tree,
1645 identical and 60 different, with no unique paths**. The raw archives we
possess show 1705 vs 3781. The most likely explanation is that V29 compared a
bounded equivalent 1705-path CSC subtree/universe inside the larger alternate
container rather than every raw alternate member. That is a provenance
inference, not something the archive alone proves. Preserve the distinction.

## 3. Stable generalized implementation core

The standalone `universal_csc/` Python package contains **11**
source files and is byte-identical between `e drive csc.zip` and
`e drive csc alternate.zip`.

That is the strongest recovered generalized implementation donor.

Its architecture already provides:
- project-profile loading from `csc_project.json` / `csc_profile.json`
- active/doctrine/evidence root discovery
- structured `Finding` and `GateResult` models
- PDVER phase and nano/micro/meso/macro levels
- native gates plus configurable command/report/sidecar adapters
- claim governance
- recursive remediation planning
- report generation
- project-local finalizer integration

The standalone finalizer README explicitly describes it as a
**project-agnostic CSC/PDVER finalizer prototype** and says it was intentionally
kept separate from the receiver until stable enough to integrate.

## 4. It is not clean enough to copy blindly

The recovered `universal_csc` implementation still contains receiver/PCMMAD
residues, including:
- `PCMMAD_LOCAL_ENV.CMD` classification
- `GITHOME_API_KEY` / PCMMAD launcher assumptions
- receiver-specific route-report names
- receiver-specific required report discovery

Therefore:

> `universal_csc` is the canonical generalized donor, not automatically the
> canonical CIC implementation.

CIC must adapt and self-qualify it.

## 5. CSC-native lineage continuity

Several load-bearing `csc_native` files are byte-identical across the later
e-drive alternate, V28, and V29 packages, including:

- `csc_gate.py`
- `code_slop_cleanup_csc.py`
- `csc_universal_runner.py`
- `csc_doctrine_passes.py`
- `guide_quality_audit.py`
- `codex_unified_loc_compliance_audit.py`
- `strict_json_boundary.py`

This gives direct implementation continuity from the standalone CSC corpus into
the receiver's V28/V29 governed verification plane.

Other files intentionally diverge:
- `csc_doctrine_manifest.py`
- `csc_runtime_bindings.py`
- `pdver_lab_hardening_cycle.py`

Those divergences are exactly where project binding / receiver adaptation
pressure appears and should not be mistaken for universal CSC law.

## 6. Latest recovered operational doctrine

The V29 package carries a later 12-document `docs/csc_sop/` set than the April
e-drive copies. It also carries the agnostic Unified Standards document.

V29's own refactor audit says:
- PCMMAD remained the product
- Forge and CSC/CTO were doctrine/evidence sources
- project names/topology/target-specific machinery were not imported
- generalized gains were selectively translated
- repeated CSC reports, bytecode, caches, vendor material, and target-specific
  branch history were deliberately not promoted into the runtime body

Its release contract further states that a green process exit is insufficient
when the claimed sub-invariant is false, and keeps host-bound verification
separate from sandbox/source verification.

Those are directly compatible with CIC's existing authority hierarchy.

## 7. CIC repository vs install boundary

Recommended CIC repository classes:

```text
engineering/lineage/csc/       historical source snapshots, hashes, doctrine,
                               crosswalks, donor provenance

tools/assurance/csc/           qualified CIC-native active CSC implementation

tests/assurance/csc/           CSC self-audit and false-positive/known-bad fixtures

csc_project.json               CIC-specific profile / command/report adapters
```

Runtime/install artifact MUST exclude all four.

Strong dependency rule:

```text
CSC assurance tooling  --->  CIC source/runtime artifacts   allowed to inspect

CIC runtime            -X->  CSC assurance tooling           forbidden dependency
```

This is intentionally stronger than the old PCMMAD release packaging, which
still carried `tools/csc_native` in the receiver release body.

## 8. Immediate reintegration plan

1. Keep the recovered donor material as **lineage**, not active authority.
2. Recon current CIC packaging/install/source-distribution boundaries.
3. Build a minimal CIC-native CSC profile around the standalone generalized
   engine.
4. Remove/parameterize PCMMAD/receiver assumptions.
5. Add CSC self-qualification fixtures before allowing CSC to veto CIC.
6. Wire current `quality_gate.py` and source-distribution verification in as
   command/report adapters rather than replacing them.
7. Keep target restart, exact-tree, provider reachability, Git promotion, and
   publication as separate target-bound authority gates.
8. Resume A0.3.2 only after the assurance substrate is qualified.

## 9. Recovery result

**Primary CSC/PDVER executable lineage is recovered.**

We are no longer blocked on missing donor archives.
