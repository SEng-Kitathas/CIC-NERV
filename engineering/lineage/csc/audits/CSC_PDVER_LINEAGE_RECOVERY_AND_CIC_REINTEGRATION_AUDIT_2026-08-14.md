# CSC / PDVER Lineage Recovery and CIC Reintegration Audit

**Date:** 2026-08-14  
**Status:** RECOVERY IN PROGRESS — NO CIC SOURCE MUTATION AUTHORIZED BY THIS AUDIT  
**Scope:** Recover the mature CSC → PDVER → PCMMAD assurance lineage and reintroduce its generalized guarantees into Personal CIC / CIC-NERV without importing target-specific project identity or topology.

---

## 1. Executive finding

The engineering doctrine did **not** lose CSC.

The operational Personal CIC implementation did.

The current Rahl Engineering Doctrine Pass5R4 still contains a substantial CSC v2 specification, a verification/assurance/promotion standard, a rule catalog, and a candidate probe. The CSC v2 specification explicitly defines CSC as a governed defect-pressure system, not a formatting linter, and gives G0–G11 gate families, contextual finding semantics, risk profiles, waiver discipline, recursive repair, CSC self-audit, and a risk-scoped success condition.

However, the currently known Personal CIC `tools/quality_gate.py` is intentionally much narrower: static syntax/anti-pattern checks, source-distribution hygiene, and the regression suite, with explicit `promotion_authority=NONE`. It is a useful verification battery component, but it is not the mature CSC/PDVER control system.

The recent increase in A0 operation blockers is therefore not evidence that CSC doctrine failed. It is evidence that CIC work drifted into bespoke shell-gate orchestration **around a thin quality gate instead of consuming the mature CSC lineage as a governed assurance subsystem**.

---

## 2. Recovered lineage

### Stage A — Unified engineering invariant

Normative agnostic standard:

`PROBE → DERIVE → VERIFY → EMBODY → RECURSE`

Key laws recovered:
- truth before theater
- primitives before repetition
- boundaries before cleverness
- verification before promotion
- sidecars before contamination
- claim-matched verification
- verify final embodiment, not merely intent
- explicit lineage and promotion state
- recursion must be justified, bounded, and terminating

### Stage B — Mature CSC / PDVER lab

Recovered operational behavior from the historical CSC lab:

Authoritative flow:
```text
python code/code_slop_cleanup_csc.py --max-cycles 2
python code/csc_gate.py
```

CSC could complete its verification runners successfully while still blocking promotion/governance.

A historical blocked state had:
- compileall: green
- shadow_queue_runner: green
- lifecycle_batch_router: green
- outcome_sidecar_expansion: green
- full_model_contract_builder: green
- routing_quality_scorecard: green
- overnight_pdver_smoke: green

Yet the CSC gate remained blocked because:
- core cycle not clean
- SOP freshness not clean
- doctrine coverage not clean

Findings included:
- stale required SOP dependencies
- `Any` leakage
- raw JSON boundary bypass
- broad `asdict` projection
- parameter bundling
- nesting
- SOP mutation lag

The system then recursively repaired findings by defect family, reran CSC, and reached:
- `final_cycle_clean = true`
- no remaining probe findings
- gate pass

This is the critical lineage property: **green tests were necessary but not sufficient, and governance findings were not confused with product regressions.**

### Stage C — CSC v2 doctrine consolidation

Recovered from Rahl Engineering Doctrine Pass5R4:

CSC v2 gate families:
- **G0** Build / existence
- **G1** Type and boundary integrity
- **G2** State and protocol integrity
- **G3** Resource and effect integrity
- **G4** Temporal and concurrency integrity
- **G5** Serialization and persistence
- **G6** Security and authority
- **G7** Architecture / holonic integrity
- **G8** Verification adequacy
- **G9** Continuity and governance
- **G10** Dependency / supply-chain integrity
- **G11** Performance / mechanical sympathy when a performance claim exists

CSC v2 explicitly requires:
1. authoritative scan
2. group findings by shared defect class
3. semantic confirmation of highest-impact finding
4. derive a primitive/boundary fix
5. smallest coherent repair
6. targeted verification
7. neighbor regression
8. rerun CSC
9. record residuals and stop condition

CSC must also self-audit against:
- known-good specimens
- known-bad specimens
- adversarial near misses
- false-positive fixtures
- generated code
- language/version changes
- historical corpus examples

A rule that cannot discriminate usefully is demoted from gate to heuristic.

### Stage D — PCMMAD native assimilation

PCMMAD V29 did not become “a CSC product.” It translated generalized CSC/PDVER guarantees into PCMMAD-native form.

Recovered generalized gains:
- append-only mutation honesty
- explicit mode/policy gate
- proportionate rigor
- evidence freshness and verifier authority
- scoped/owned/expiring waiver discipline
- append-only promotion/demotion lineage
- derived-state rebuildability
- CSC doctrine/freshness/holonic/coverage included in aggregate verification

Deliberate non-imports:
- CSC/CTO target-specific branch/certificate topology where not earned
- Forge branding/project identity
- dataset split mechanics irrelevant to receiver runtime
- repeated historical run outputs
- caches/bytecode/vendor residue
- wholesale aesthetic rewrites without a verified seam

PCMMAD V29 aggregate verification explicitly ran `tools/csc_native/csc_universal_runner.py` and required all CSC surfaces clean:
- core_cycle
- sop_availability
- sop_freshness
- holonic_audit
- doctrine_coverage

---

## 3. Current CIC gap

### What CIC has

Personal CIC currently has strong target-specific assurance work:
- exact-tree identity
- target restart/re-entry proof
- artifact/readback proof
- source-distribution hygiene
- MapLibre authored/derived separation
- private GitHub exact fast-forward publication
- Host allowlist proof
- worker/runtime qualification
- deployment/source/secret/runtime authority separation
- crash recovery and committed-but-unsealed requalification
- full regression suite
- numerous durable failure scars

These are valuable and should remain.

### What CIC lacks operationally

CIC does not currently have the recovered mature CSC control plane as a first-class reusable subsystem.

The thin quality gate does not itself provide:
- G0–G11 governed finding taxonomy
- contextual severity/confidence
- defect-class grouping
- doctrine dependency freshness
- holonic audit as a standard surface
- waiver records
- risk profiles / proportionate rigor
- finding lineage / first-seen / last-seen
- CSC self-audit
- false-positive fixtures
- aggregate CSC event report
- PDVER cycle report
- explicit distinction between “verification battery green” and “governance clean”
- reusable adjudication of assurance-plane defects versus product-plane defects

Instead, much of that reasoning has been reimplemented ad hoc inside increasingly large per-operation shell gates.

That is the architectural regression.

---

## 4. Reinterpretation of recent CIC blockers

Recent failures should be classified through CSC/PDVER rather than counted as undifferentiated “operation failures.”

### A0.2 rename-detection veto
**Class:** assurance representation/adjudication defect  
**Not:** source-tree failure  
**Invariant:** heuristic diff presentation cannot outrank exact tree identity.

### A0.2 hard freeze
**Class:** environment/recovery event  
**Not:** source or Git object failure  
**Recovered state:** exact commit/tree survived; cold boot requalified it.

### stale PRE-state after surviving commit
**Class:** transition-state classifier defect  
**Invariant:** PRE / POST / OTHER must be explicit and retry-aware.

### A0.3.2 R1 missing `unittest` import
**Class:** verifier/test-harness self-qualification defect  
**Not:** product-source failure.

### A0.3.2 R2 fourteen regression errors
**Class:** genuine semantic pressure against the proposed embodiment  
**Interpretation:** the new fail-closed invariant was placed too high in the configuration hierarchy.

The R2 candidate made:
- `world_awareness.enabled` imply an explicit location is always required
- `traffic.enabled` imply county scope is always required

Neighbor regressions demonstrate those parent-level implications are too strong. The fail-closed requirement belongs at the **specific capability that consumes the missing geographic scope**, not automatically at the parent subsystem enable flag.

This is a valid PDVER recursion trigger, not an assurance false veto.

---

## 5. Reintegration law

The repair is **not**:

```text
copy old CSC project wholesale into CIC
```

The repair is:

```text
recover mature CSC implementation specimens
        ↓
establish lineage / exact hashes / differences
        ↓
extract generalized guarantees and reusable primitives
        ↓
translate them into CIC-native assurance surfaces
        ↓
self-qualify the imported/adapted CSC machinery
        ↓
make CIC's existing quality_gate one verification input
        ↓
make target/restart/exact-tree/publication proof separate target-bound gates
        ↓
resume product work under the recovered assurance plane
```

Core law:

> **Import guarantees, not syntax. Preserve invariants, not ceremony. Verify claims, not vibes.**

And a new operational corollary:

> **Do not reinvent CSC inside each promotion script.**

---

## 6. Missing implementation specimens

The current accessible corpus contains strong documentary and report evidence, but not all original archive payloads needed for byte-level implementation recovery.

### Priority 1 — required

`PCMMAD_RECEIVER_V29_NATIVE_PROTOCOL_RC1.zip`

Expected SHA-256:

`5baf9b66a9137d950aeabac2ea76fbbb919e177f90788e5341ee6e15a80b89d8`

Why:
- contains the later `tools/csc_native/` implementation used by a clean aggregate release
- expected to contain the current 12-document CSC SOP set
- contains aggregate verifier integration and strict boundary utilities
- best known mature generalized implementation donor

### Priority 2 — required for lineage cross-check

`e drive csc alternate.zip`

Expected SHA-256:

`a0a907d4e1de95ff454fc3af8d1e66e5b3b361d0ce429742377264a265a4d8ec`

Why:
- explicitly cross-evaluated as CSC evidence in the V29 audit
- one of two 1705-path CSC trees compared there
- provides historical implementation pressure and helps distinguish generalized CSC from one later PCMMAD adaptation

### Priority 3 — useful parity anchor

`PCMMAD_RECEIVER_V28_PDVER_REFACTOR.zip`

Expected SHA-256:

`0b024d46eadd96be43d609898874e3c051bb7a8941d33be5ac848b7271571f54`

Why:
- verified V28 PDVER recovery/refactor anchor
- lets us identify which CSC-native machinery predates V29 protocol additions
- useful to avoid attributing a V29 product-specific addition to CSC itself

V29 + e-drive alternate are enough to begin the primary recovery. V28 materially strengthens lineage discrimination.

If another “main CSC tree” archive exists beside the e-drive alternate, retain it; its exact archive name is not yet recovered from the accessible evidence.

---

## 7. Reintegration phases after specimen recovery

### C0 — Forensic corpus recovery
- hash every donor
- inventory trees
- compare V28, V29, e-drive CSC, and current doctrine candidate
- identify generalized implementation primitives
- classify each donor surface:
  - generalized CSC
  - PDVER orchestration
  - PCMMAD-specific
  - experimental/historical
  - generated/report-only
  - deprecated

### C1 — CIC-native CSC substrate candidate
Candidate should likely include, subject to recovered source:
- structured finding model
- rule catalog
- adapters/scanners
- risk profile
- waiver sidecar model
- doctrine dependency model
- holonic audit
- aggregate event report
- self-audit fixtures
- authoritative runner

Do **not** give it promotion authority merely by importing it.

### C2 — CSC self-qualification
Prove:
- known-good does not false-veto
- known-bad is found
- near misses are discriminated
- heuristics remain heuristics
- generated/vendor material is classified correctly
- current CIC source can be scanned without semantic laundering
- findings remain evidence, not automatic truth

### C3 — Integrate existing CIC verification
CIC `quality_gate.py` becomes a verification-battery component, not the entire control plane.

Other inputs can include:
- source-distribution hygiene
- full regressions
- selected concurrency/security/config tests
- exact artifact checks where appropriate

### C4 — Keep target-bound authority separate
CSC source/governance cleanliness must **not** be allowed to imply:
- deployed runtime qualification
- service restart/re-entry success
- remote publication success
- Git tree identity
- credential/provider reachability
- current world authority

Those remain target-bound proof obligations.

### C5 — Resume A0.3.2 under recovered CSC
Re-probe the fourteen regressions.
Derive capability-level geographic requirements rather than parent-level blanket requirements.
Use CSC/PDVER to distinguish:
- real semantic regression
- fixture pressure
- boundary design issue
- test deficiency
- assurance defect

Only then embody the next fail-closed candidate.

---

## 8. Immediate stop condition

Until the donor implementation specimens are recovered:

- do not generate A0.3.2 R3
- do not create another large bespoke source-mutation gate
- do not import the Pass5R4 `csc_probe.py` as if it were the mature CSC runtime; it explicitly identifies itself as a candidate finding generator, not a proof engine
- do not mutate current A0.2 Git authority
- do not alter the qualified A0.3.1 private deployment topology state

The correct next step is **lineage recovery, not another repair script**.

---

## 9. Current durable source anchors

Rahl Engineering Doctrine Pass5R4:
- archive: `RAHL_ENGINEERING_DOCTRINE_vNEXT_PASS5R4_ANALYTIC_SATURATION_RECONCILED_CANDIDATE_2026-08-14.zip`
- SHA-256: `a4e5494cd6d78e64700faba32875680fdb1fd6244f01816b09f678da128adeeb`
- contains:
  - `04_CSC_v2_SPEC.md`
  - `05_VERIFICATION_ASSURANCE_AND_PROMOTION.md`
  - `quality/CSC_RULE_CATALOG.json`
  - `tools/csc_probe.py`
  - `tools/test_csc_probe.py`

ProtoAGI / Rahl Engineering / CIC master archive:
- `PROTOAGI_RAHL_ENGINEERING_CIC_MASTER_ARCHIVE_v1.2_2026-08-14(1)(1).zip`
- SHA-256: `c52351f58b42cd7ee90ab2a8885cd2f0cc2c8caf3750c7792045fa7658853282`

These are doctrinal/strategic anchors, not substitutes for the missing mature executable CSC donor packages.

---

## 10. Decision

**RECOVER FIRST. ADAPT SECOND. SELF-QUALIFY THIRD. REINTEGRATE FOURTH. RESUME A0.3 FIFTH.**

The recent blocker cluster has now produced a useful higher-order finding:

> CIC preserved CSC's laws but stopped embodying CSC as a reusable governed subsystem.

That is the seam to repair.
