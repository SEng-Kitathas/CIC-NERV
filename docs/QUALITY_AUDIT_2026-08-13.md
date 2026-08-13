# Personal CIC 0.3.6 / Slice 003f — Full Source Quality Reconciliation

**Audit date:** 2026-08-13  
**Audited candidate input:** exact reconstructed RC2D-R2 authored source  
**Output:** RC2D-R2-QA1 quality-reconciled authored-source candidate  
**Promotion state:** **NOT TARGET-PROMOTED**  
**Promoted floor remains:** `99eb5e1d8fad82a0603825282218e3d98aa7d039` / `slice-003f-rc1b-target-verified`

This audit applies the current CIC engineering SOP, project constitution, CSC gate families,
verification/promotion discipline, security/trust-boundary standard, temporal/concurrency standard,
AI-generated-code standard, and high-assurance adaptation guidance to the full current source tree.
Doctrine is a review instrument, not authority over target reality.

## Method

The audit used the project metabolism:

```text
PROBE → DERIVE → EMBODY → VERIFY → RECURSE
```

It compared:

1. the verified historical source lineage through 0.3.5 / RC1B evidence;
2. every 003f traffic/map candidate artifact available in the project workspace;
3. the complete reconstructed RC2D-R2 source tree;
4. current Rahl Pass5R1 candidate standards and Semantic Harvest assurance distinctions;
5. durable CIC-NERV R3 project state;
6. executable tests, coverage, syntax, source-distribution and artifact-integrity checks.

Historical gates/artifacts were preserved as evidence. Known-bad historical verifier iterations were
not rewritten to look clean after the fact.

## CSC result

| Gate | Result | Audit conclusion |
|---|---|---|
| G0 Build/existence | PASS / corrected | Full authored tree compiles and tests. MapLibre source-distribution packaging defect was corrected with explicit lock/materialization tooling. |
| G1 Type/boundary | PASS with debt | Strict config boundary parsing added. Dynamic ECS/event/projection carriers remain explicit bounded debt. |
| G2 State/protocol | PASS | Observation/freshness, collection-center/site/live-position, traffic source state and materiality remain explicit. |
| G3 Resource/effect | PASS with debt | Effect ownership remains in adapters/runtime. Provider response-size/content-type limits are not yet uniform. |
| G4 Temporal/concurrency | PASS / corrected | Worker shutdown, concurrent EventBus registry/count access and concurrent journal append were hardened. |
| G5 Serialization/persistence | PASS with debt | Writer v2; evidenced historical v1/v2/v3 readable; unknown future versions rejected. Explicit migrations remain open. |
| G6 Security/authority | PASS with debt | Loopback/read-only boundary retained; source secrets remain environment-only; user service hardening added. Inline CSP remains presentation debt. |
| G7 Architecture/holonic | PASS with debt | No god-object/generalized provider manager introduced. Large functions remain evidence-backed refactor pressure rather than style-driven surgery. |
| G8 Verification adequacy | PASS | Regression suite expanded 176 → 203 tests with no inherited tests intentionally removed; branch coverage retained; new supply-chain/concurrency/config defects have targeted tests. |
| G9 Continuity/governance | PASS | Promoted floor, open slice, candidate chronology, target veto and unearned QA1 state are explicit. |
| G10 Dependency/supply chain | PASS with debt | MapLibre source/version/archive digest and package materialization are controlled; target direct Python dependency is pinned separately. Build backend is not yet a target-qualified hermetic lock. |
| G11 Performance | NO NEW CLAIM | QA1 makes no new quantitative performance claim; operator smoothness remains target observation, not benchmark proof. |

## Corrections embodied

### Configuration boundary integrity

- replaced permissive Python truthiness with JSON-boolean enforcement;
- rejects non-finite numeric values rather than permitting NaN/Inf to bypass range checks;
- requires positive core collection/snapshot cadences;
- validates provider cadences/timeouts and nested JSON collection shapes;
- validates health threshold range/order and Wi-Fi dBm bounds;
- validates environment-variable identifiers;
- rejects non-string identity/provenance fields instead of coercing `null` or numeric values through `str(...)`;
- enabled fixed site anchor now requires address, lineage, source record, timezone-aware verification time and source-artifact SHA-256;
- root `null` runtime/health documents fail as configuration errors rather than relying on assertions;
- NWS forecast discovery no longer relies on an optimization-removable `assert` for a runtime contract.

### Location semantic integrity

The fixed site anchor remains separate from regional collection scope and future live operator
position. The legacy TomTom probe ID `cic-center` is retained for continuity, but its display label is
now `collection-scope center reference` so a stable identifier does not silently acquire new meaning.

### Snapshot schema governance

`WorldState` continues to write schema v2 because that is the current verified target lineage.
Hydration explicitly admits only evidenced historical v1/v2/v3 snapshots and rejects unknown future
versions. Root/entity/component shapes are validated. Unknown/unreconstructable component payloads
retain the historical skip behavior rather than blocking startup.

### Concurrency / shutdown integrity

- remote state-mutating workers report whether bounded stop actually achieved thread termination;
- a join timeout is not recorded as success and the live thread reference is retained;
- runtime skips the forced final snapshot if a state-mutating worker remains live;
- shutdown reason explicitly records incomplete worker quiescence;
- EventBus registry/count access is lock-protected while callback execution remains outside the lock;
- EventJournal serializes durable append so concurrent publishers cannot interleave JSONL records.

### Presentation / dependency supply chain

RC2D target pressure showed the source tree was not independently sufficient to reconstruct the map
runtime because MapLibre bytes had been injected by the gate. QA1 separates authored source and
third-party runtime authority explicitly:

- `presentation/vendor/maplibre/LOCK.json` pins dependency/version/release archive SHA and admitted files;
- `tools/install-maplibre-vendor.py` verifies the exact archive before bounded extraction and atomic materialization;
- acquisition and ZIP member sizes are bounded;
- `MATERIALIZED.json` records per-file hashes when runtime bytes are installed;
- `tools/verify-source-distribution.py` validates lock/materialization/source hygiene;
- package-data rules include JS/CSS/license/lock/materialization/README files;
- a synthetic wheel proof confirms a materialized runtime is actually included in built wheels;
- a negative test confirms a wrong archive is rejected before vendor mutation;
- systemd install refuses to start a map-capable service when required pinned presentation bytes are absent.

### Service authority

The user service adds `NoNewPrivileges=true` and `UMask=0077`. More aggressive filesystem/network
sandboxing was deliberately not introduced without target proof that it preserves current hardware,
state, cache and acquisition requirements.

### Source / documentation hygiene

Generated caches/build products/wheels/coverage files are excluded from authored source. README,
architecture, presentation, traffic, changelog and conformance documentation now describe current
003f candidate reality rather than stopping at earlier slice assumptions.

`tools/quality_gate.py` now provides a reproducible, source-local assurance gate for syntax, static
invariants, JSON structure, shell syntax, source-distribution hygiene and the full regression suite.
It prints `promotion_authority=NONE` by design: source-local PASS is evidence, not target promotion.

## Verification evidence

Current QA1 result:

```text
unit tests                         203 / 203 PASS
Python compileall                  PASS
JSON parse                         PASS
shell syntax (source tools)        PASS
source distribution hygiene        PASS
wrong-vendor-archive negative       PASS
sentinel wheel package-data proof   PASS
unfinished-code marker scan         PASS
historical CIC shell gate syntax    PASS
historical tar/zip integrity         PASS
```

Branch coverage is retained as an audit measurement rather than a proof target. Current report is
stored alongside the release audit artifacts; aggregate branch-aware coverage remains approximately
85%, with lower-covered effectful provider/server/runtime paths explicitly visible rather than hidden.

## Accepted residual debt

The audit deliberately does **not** refactor these solely to improve aesthetics or a static score:

- broad dynamic carrier types at ECS/event/projection seams;
- stringly future `Intent` model and open `UsbDeviceState.mode`;
- one primary `ObservationState` per entity;
- large but coherent materiality/projector/server functions;
- inconsistent provider response-size/content-type limits;
- current inline presentation JS/CSS requiring an `unsafe-inline` CSP allowance;
- static `SITE 15 MI` generic fallback label if a future profile disables site anchoring;
- explicit snapshot migrations beyond the evidenced compatibility reader;
- exact target-qualified build-backend lock;
- continuous/route-complete traffic flow and cross-lineage event fusion (domain capability gaps, not QA defects).

These remain visible because `static smell != P0`. They should be promoted when actual pressure or a
stronger invariant makes the repair safer than leaving the seam alone.

## Assurance conclusion

No evidence was found that the foundational ECS/holonic/world-state/observation/persistence/weather/
radar/traffic architecture requires replacement. The material issues found were primarily boundary,
concurrency, dependency-governance, source-distribution and documentation-governance defects.

QA1 improves the authored candidate without granting it promotion authority. The next running-target
embodiment must still prove that the corrected source preserves all previously earned behavior and
that RC2D-R2's site-anchor proposition is correct on the Engage One.

## QA1-R1 target-verifier correction

Target embodiment exposed an assurance-scope defect in the new source-distribution verifier.
The isolated sealed QA1 source passed correctly, but the same verifier was then run against
the long-lived target checkout and recursively classified the target-local `.venv/`,
`__pycache__/`, and editable-install `*.egg-info` products as if they were members of the
source distribution.

The failure was detected before service reinstallation and triggered the gate fail-safe.
It did not establish a code/runtime semantic defect.

QA1-R1 separates the claims explicitly:

- strict source-capture verification continues to reject generated products in captured source;
- `.venv/` is never source-distribution authority;
- embodied working-tree verification tolerates generated runtime/build residue while still
  proving dependency locks/materialization and authored-source identity;
- the target gate continues to prove the sealed source artifact independently before mutation.

Derived rule:

> **A verifier must evaluate the artifact class named by its claim. A source-distribution
> verifier may not reject a runtime checkout because non-source runtime residue exists beside it.**

## QA1-R2 service-installer scope propagation

The QA1-R1 target gate passed isolated source capture, 206 regressions, immutable-parent
comparison, target-local working-tree verification, and target-local regressions, then
failed at service installation. The installer called the corrected verifier without the
new `--working-tree` selector, silently reverting to strict source-capture semantics.

This was a composed-tool contract defect, not a runtime semantic failure. The target gate
fail-safe restored the pre-candidate repository-owned files and restarted the service.

QA1-R2 corrects the caller:

```text
install-user-service.sh
    -> verify-source-distribution.py
       --working-tree
       --require-runtime-vendor
```

The runtime-vendor requirement remains strict. Only the artifact-class selector changes.
The previous diagnostic also falsely implied MapLibre was absent even though materialization
had just passed; QA1-R2 replaces it with an accurate working-tree/dependency failure message.

Derived assurance rule:

> **A newly introduced verification distinction is not embodied until every composed caller
> selects the correct side of that distinction. Caller propagation is part of the contract.**

