# UNIFIED CODE STANDARDS DOCTRINE v1.2

## The Canonical Standard for Rahl-Authored Code

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║   "A defect is not merely a bug; it is a violation of mathematical truth.       ║
║    Inefficiency is not merely a performance issue; it is an indefensible        ║
║    contribution to thermodynamic entropy."                                       ║
║                                                                                  ║
║                              — The Omega Thesis                                  ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

**Version:** 1.2 (Wild Hunt Integration — Chimera/Corpus/Forge/Meta-Control)  
**Status:** Normative Specification  
**Domain:** Universal (Language-Agnostic, Platform-Agnostic)  
**Date:** 2026-04-13  
**Synthesis Base:** 3.5GB PCMMAD Knowledge Graph (202K files, 531 doctrine rules, 12 project families)

---

## PART I: GOVERNANCE FRAME

### The Immutable Laws

These laws govern all work. They are not guidelines.

| Law | Name | Mandate |
|-----|------|---------|
| **0** | Discourse ≠ Implementation | Iterate freely in conversation. Challenge assumptions. Explore. This is "measure twice." |
| **1** | 0-Day Not Someday | When building: no stubs, no TODOs, no MVPs, no phases. Full production-grade only. |
| **2** | Explicit Mode Mapping | Law 1 is GLOBAL for implementation. Law 0 governs discourse. Triggers: "build/implement/code" = Law 1. "explore/what if" = Law 0. |
| **3** | Ambiguity Resolution | All laws SHALL be obeyed. If ambiguous whether discourse or implementation: ASK. |
| **4** | Pedantic Verification | ALL documents read in-full. EVERY element researched to current SOTA. VERIFY, don't infer. |
| **5** | Multi-Disciplinary Grounding | Features cite foundations (cog-sci, psychology, info theory). Cross-pollinate fields. |
| **Ω** | Theoretical Maximum | Every artifact at THEORETICAL MAXIMUM quality. Not "good enough" — Platonic ideal in bytes. |
| **Σ** | Divergent Search | Voice speculative ideas, explore "wrong" paths, generate alternatives, map isomorphisms. |

### The Epistemic Constraint

```
β ≥ α + ε
```

Where:
- **β** = Evidence strength
- **α** = Confidence level
- **ε** = Safety margin

Evidence MUST dominate confidence. No claim without support.

---

## PART II: THE PHYSICS OF COMPUTATION

Software is not abstract. Computation is a physical process governed by thermodynamics and information theory.

### The Thermodynamic Floor: Landauer's Limit

The absolute minimum energy for computation:

```
E_min = k_B × T × ln(2)

At room temperature (300K):
E_min ≈ 2.87 × 10⁻²¹ Joules per bit erased
```

**Omega Implication:** Imperative programming (mutable state) is inherently dissipative — it erases information. Functional/immutable paradigms approach thermodynamic optimality.

| Paradigm | Thermodynamic Character | Omega Compliance |
|----------|------------------------|------------------|
| Imperative (mutation) | Dissipative | Non-compliant |
| Functional (immutable) | Reversible | Compliant |
| Append-only structures | Minimal erasure | Compliant |
| Event sourcing | History-preserving | Compliant |

### The Informational Ceiling: Kolmogorov Complexity

```
K(x) = min{|p| : U(p) = x}
```

The "perfect" implementation of specification S is code P where |P| approaches K(S). **Any line exceeding this minimum is accidental complexity.**

**Practical Metric:**
```
Compressibility Ratio = Original Size / Compressed Size

High ratio = High redundancy = Low Omega compliance
Low ratio  = High entropy density = High Omega compliance
```

**Refactoring Redefined:** Refactoring is a **data compression activity**. A module is clean when it cannot be compressed further without losing correctness.

---

## PART III: THE FIVE FUNDAMENTAL LAWS OF SOFTWARE DESIGN

Software exhibits thermodynamic properties. These laws derive from cognitive neuroscience, systems biology, formal mathematics, computational physics, and cross-domain synthesis.

### Law I: Cognitive Conservation

**Working memory holds 4±1 items.**

- Directory depth ≤ 4 levels
- Function parameters ≤ 4 (prefer ≤ 3)
- Cyclomatic complexity ≤ 10 per function
- A single developer MUST be able to hold the entire module in working memory

**Metric:** Viscosity Index = Files Changed / Conceptual Changes → target < 1.5

### Law II: Entropy Resistance

**Complexity increases monotonically without active reduction.**

- Every commit either reduces entropy or explicitly justifies the increase
- Refactoring is not optional maintenance; it is thermodynamic survival
- Dead code, unused imports, commented blocks: excise immediately
- Technical debt is not a ledger; it is an uncontrolled reaction

### Law III: Coupling Distance

**Modification work = Coupling × Distance**

- Minimize coupling between modules
- Minimize conceptual distance between related code
- Changes should be local; global effects indicate architectural failure
- If changing A requires changing B, they should be adjacent or merged

### Law IV: Failure Locality

**Defects cascade through opaque dependencies.**

- Every boundary must be typed and explicit
- Every failure mode must be enumerable
- No silent failures; no swallowed exceptions
- Error propagation must be traceable

### Law V: Substrate Sovereignty

**The substrate is primary. Imports are material, not truth.**

- External libraries are consumables, not architecture
- Vendored code does not grant wisdom; it grants liability
- Every dependency must justify its presence against the full attack surface it introduces
- The system's truth lives in your code, not in abstractions you didn't write

---

## PART IV: THE HOLONIC ARCHITECTURE

A **Holon** is an entity that is simultaneously a whole unto itself and a part of a larger system.

### Every Holon MUST Define:

| Attribute | Question |
|-----------|----------|
| **Purpose** | Why does this exist? |
| **Boundary** | What does it own? What does it assume? Where does it end? |
| **Interface** | How does it communicate? |
| **Invariants** | What must always be true? |
| **Hazards** | How can it fail? |

### The Primordial Holon

> "No unit is allowed to be mysterious."

Every component must be explainable, observable, bounded.

### Holonic Layers

| Layer | Scale | Examples |
|-------|-------|----------|
| **Nano** | Expression | Type-safe, referentially transparent, composable |
| **Micro** | Function | Pure logic, explicit I/O, single responsibility |
| **Meso** | Module/Service | Bounded context, autopoietic, stigmergic communication |
| **Macro** | System | Global invariants, allostatic control, emergent behavior |

---

## PART V: THE PDVER LIFECYCLE

All code evolution follows this cycle at every scale.

```
PROBE → DERIVE → VERIFY → EMBODY → RECURSE
```

### PROBE
- What seam are we inspecting?
- What evidence proves the seam is real?
- What failure mode or anti-pattern exists here?

### DERIVE
- What invariant, primitive, classifier, or boundary emerges?
- Why is this shape better than the previous?
- What rule does this enforce?

### VERIFY
- What battery, regression, or runtime check validates this?
- What boundary cases were tested?
- Did we avoid softening true-danger paths?

### EMBODY
- Where is the new structure actually manifest in code?
- Is it typed, traceable, and inspectable?
- Is governance separated from specimen?

### RECURSE
- What seam remains after this pass?
- Does it justify another refinement step?
- What would demote the current change?

---

## PART VI: CODE-LEVEL MANDATES

### Naming

- Names encode domain truth, not implementation detail
- Abbreviations require project-wide glossary entry
- Units MUST be explicit: `timeout_ms`, `distance_meters`, `price_usd`
- Boolean names: `is_`, `has_`, `can_`, `should_` prefixes

### Functions

- Single responsibility: one function, one job
- Pure where possible; explicit effects where not
- No function exceeds what can be reasoned about in working memory
- Return early; avoid deep nesting
- Parameters: prefer immutable; mutate only when semantically necessary

### Types

- Encode invariants in the type system
- Invalid states should be unrepresentable
- Use sum types (enums/unions) for mutually exclusive states
- Use product types (structs/records) for composite data
- Avoid stringly-typed APIs

### Error Handling

- Errors are values, not exceptions (where language permits)
- Every error path must be explicitly handled
- No silent swallowing; no `catch (Exception e) {}`
- Distinguish recoverable errors from fatal conditions
- Error messages must be actionable

### State Management

- Minimize mutable state
- State transitions must be explicit and auditable
- Prefer append-only over mutate-in-place where feasible
- Global state requires justification and explicit lifecycle management

### Boundaries

- Typed at every module boundary
- Serialization formats explicit and versioned
- API contracts documented and enforced
- No dict-smearing across interfaces

---

## PART VII: VERIFICATION ARCHITECTURE

### The Verification Ladder

| Level | What | Tools |
|-------|------|-------|
| **0: Existence** | Artifact exists, parses, integrity verified | File system, hash verification |
| **1: Syntax** | Code compiles/parses correctly | Compiler, linter, parser |
| **2: Type** | Type constraints satisfied | Type checker, static analysis |
| **3: Semantic** | Logic predicates hold | Unit tests, property tests |
| **4: Integration** | Components interact correctly | Integration tests, contract tests |
| **5: System** | End-to-end behavior correct | System tests, smoke tests |
| **6: Proof** | Formal correctness guarantee | Formal methods, proof assistants |

### The Traceability Law

```
REQUIREMENT → IMPLEMENTATION → TEST → VERIFICATION
```

- Every functional component traces to a requirement
- If a function exists but traces to no requirement, it is **unauthorized**
- Dead code is not "legacy"; it is liability

### Non-LLM Anchors are Mandatory

Where possible, verification MUST use:
- Compilers
- Test suites
- Runtime execution
- Schema validation
- Static analysis
- Type checking

LLM verification is advisory, not authoritative.

---

## PART VIII: SPECIMEN/GOVERNANCE SEPARATION

This is non-negotiable.

### Specimen / Body
What executes, trains, or reasons:
- Runtime code
- Transformation outputs
- Executable artifacts
- Model weights

### Governance / Sidecar
What tracks, judges, or explains:
- Lineage
- Adjudication records
- Promotion state
- Maintenance notes
- Trace matrices

**The system SHALL NOT train governance theater as if it were the specimen.**

---

## PART IX: ANTI-PATTERNS

### Explicit Violations

| Anti-Pattern | Violation | Fix |
|--------------|-----------|-----|
| **Verdict Bridge Theater** | Deep analysis collapses to blunt final judgment | Explicit verdict classes with inspectable bridge semantics |
| **Analyzer Drift** | Same primitive re-derived in multiple places | Shared primitive substrate |
| **Lifecycle Implication** | PDVER exists only in comments | Explicit lifecycle traces with stage-visible transitions |
| **Embodiment Collapse** | Typed plans degrade to anonymous dicts | Typed embodiment records with explicit identity |
| **Governance Contamination** | Admin chatter leaks into trainable specimens | Clean row body; governance in sidecars only |
| **Beautiful Trace Addiction** | Long reasoning decoupled from verification | Traces must strengthen verification or embodiment |
| **Prestige Theater** | Code sounds principled but teaches bad habits | Meaning over decorative sophistication |

### The Three Tens Alignment

Any code must align:

| Dimension | Question |
|-----------|----------|
| **Intent (Why)** | Is the artifact's reason legible from structure? |
| **Structure (What)** | Does the architecture serve the intent honestly? |
| **Implementation (How)** | Does the code express the structure without distortion? |

Misalignment between any pair is a defect.

---

## PART X: PROMOTION DISCIPLINE

### Promotion Gate Checklist

Before any code becomes load-bearing:

**PROBE Gate**
- [ ] Actual runtime/corpus seam was directly inspected
- [ ] Failure mode identified in concrete terms
- [ ] Change responds to evidence, not aesthetic discomfort

**DERIVE Gate**
- [ ] Pass introduces clearer invariant/primitive/boundary
- [ ] Heuristic drift reduced
- [ ] Dict/string policy leakage reduced
- [ ] Change is smaller and truer, not just more abstract

**VERIFY Gate**
- [ ] Build passes
- [ ] Self-verification clean or improved
- [ ] Known boundary cases replayed
- [ ] True-danger paths not softened
- [ ] False-positive contamination not reintroduced

**EMBODY Gate**
- [ ] New behavior present in runtime artifact, not only prose
- [ ] Lifecycle/embodiment records inspectable
- [ ] If governance moved, it moved to sidecar

**RECURSE Gate**
- [ ] Next seam explicitly named
- [ ] Pass does not pretend to solve wider class than solved
- [ ] Demotion triggers visible

### Scoring Rubric

| Score | Meaning |
|-------|---------|
| **45-50** | Canonical promotion candidate |
| **35-44** | Strong, likely promotable after narrow replay |
| **25-34** | Useful but structurally mixed |
| **15-24** | Local improvement with doctrine debt |
| **0-14** | Not fit for load-bearing use |

---

## PART XI: QUICK REFERENCE CARD

### The Five Laws
1. **Cognitive Conservation** — 4±1 chunks, viscosity < 1.5
2. **Entropy Resistance** — Active reduction or explicit justification
3. **Coupling Distance** — Work = Coupling × Distance
4. **Failure Locality** — Typed boundaries, enumerable failures
5. **Substrate Sovereignty** — Your code is truth; imports are material

### The Immutable Laws
- **0**: Discourse ≠ Implementation
- **1**: 0-Day Not Someday
- **2**: Explicit mode mapping
- **3**: Resolve ambiguity
- **4**: Pedantic verification
- **5**: Multi-disciplinary grounding
- **Ω**: Theoretical maximum
- **Σ**: Divergent search

### The Lifecycle
```
PROBE → DERIVE → VERIFY → EMBODY → RECURSE
```

### The Holonic Questions
- Purpose: Why?
- Boundary: What's mine?
- Interface: How communicate?
- Invariants: What's always true?
- Hazards: How can it fail?

### The Epistemic Constraint
```
β ≥ α + ε
```
Evidence dominates confidence.

---

## APPENDIX A: CROSS-FAMILY APPLICABILITY

This doctrine applies across all project families:

| Family | Primary Application |
|--------|---------------------|
| **PCMMAD** | Orchestration, receiver runtime, lab infrastructure |
| **Monster** | Inference substrate, tensor operations, weight handling |
| **NEAL** | Cognitive architecture, reasoning pipelines |
| **Forge** | SAST engine, analyzer surfaces, LBE |
| **Geometric** | TQ2 kernel, dialectical search, Rosetta pipeline |
| **Singularity** | Security analysis, genome detection |
| **Nexus** | Browser environment, cognitive substrate |
| **KarnOS** | Bare-metal OS, AVX-512 kernels |
| **TacSim** | Tactical simulation, combat doctrine |
| **Law Omega** | Standards themselves, doctrine evolution |
| **Receiver** | API surfaces, schema enforcement |
| **Research** | Experimental code, exploratory work |

---

## APPENDIX B: FRAMEWORK GENEALOGY

```
RPF (Reflective Protocol Framework) — FAILED
│   Lesson: Observable semantic states required, not software metrics
│
▼
AUOF (Accuracy, Understanding, Objectivity, Falsifiability)
│   Constitutional layer: why we reason this way
│
▼
NEAL-CORE v1.0 → v36+
│   Starmap Geometry, K/I/S classification, 7-Gate pipeline
│   Epistemic constraint: β ≥ α + ε
│
▼
IW-CO (Integrated Weighted Cognitive Overlay)
│   Generative component, multi-path reasoning
│
▼
CIL (Cognitive Intersymbolic Ledger) v4.0 → v5.0
│   Memory substrate, 6-layer architecture
│
▼
CODEX PRIME v4.0 (Five Pillars)
│   Executive framework: what to achieve
│
▼
LEGENDARY CODE (Seven Pillars)
│   Operational framework: how to achieve
│
▼
CODEX OMEGA v2.0 (Unified)
│   Immutable Laws + Physics foundations
│
▼
THIS DOCUMENT (Unified Code Standards Doctrine v1.0)
    Synthesis from 3.5GB knowledge graph
    12 project families integrated
```

### Source Documents
- **Codex Omega Bible v2.0** — Theoretical maximum framework, physics foundations
- **Codex Prime v4.0** — Five fundamental laws of software design
- **Forge Unified Code Standards 2026-04-11** — PDVER lifecycle, anti-patterns
- **Unified Code and CILNX Doctrine 2026-04-09** — Corpus standards, verification
- **Omega Quality Audit Standards v5.0** — Verification layers
- **531 extracted doctrine rules** — From 3.5GB knowledge graph
- **12 project families** — Cross-project pattern synthesis
- **168 cross-family impact mappings** — Inter-project relationships
- **1,551 contradiction records** — Conflict resolution basis

---

## APPENDIX C: THE OMEGA THESIS

> "A defect is not merely a bug; it is a violation of mathematical truth.
> Inefficiency is not merely a performance issue; it is an indefensible
> contribution to thermodynamic entropy."

The standard is not "production-grade."
The standard is not "good enough."
The standard is not "ships on time."

The standard is: **Would this survive scrutiny by a future version of yourself who has forgotten the context but must maintain the system?**

If not, iterate.

---

## APPENDIX D: CHIMERA CORPUS & DATASET DOCTRINE

### The Packetized Paradigm

Training data is treated as discrete signal packets, not homogenized mixture. This parallels TCP/IP layer separation — independent innovation and error handling within each domain.

**Ten-Bucket System:**

| Bucket | Domain | Objective |
|--------|--------|-----------|
| B1 | Stabilization | Noise reduction, corporate sludge removal |
| B2 | Long-horizon | Continuity, thread-memory persistence |
| B3 | Fast Reasoning | Compressed, decisive-step solving |
| B4 | Slow Reasoning | Long deliberate traces, step-wise logic |
| B5 | Isomorphism | Structural mapping across domains |
| B6 | Code Consensus | Test-backed repair, executable verification |
| B7 | Interpersonal | Directness and warmth without pandering |
| B8 | Speakability | Transcript-confidence, verbal fluency |
| B9 | Negative-Space | Forbidden paths, law-break detection |
| B10 | Governance | Lineage, provenance, adjudication (SIDECAR ONLY) |

### Specimen/Governance Split (NON-NEGOTIABLE)

**Layer A — Trainable Specimen Body:**
- task/problem surface
- reasoning voices (when behaviorally relevant)
- reasoning trace / compressed rationale
- render contract
- dual-output topology
- final answer / embodiment
- verifier
- boundary policy / out_of_scope
- continuity state surfaces

**Layer B — Governance Sidecar (NEVER IN TRAINING):**
- lineage
- review provenance
- adjudication log
- promotion state
- blocking findings
- scores and rubric notes
- contamination notes
- external review readiness

**Law:** If a field exists only for project tracking, it does not belong in the trainable body.

### Next Family Build Order

1. **Negative-Space Family** — teach impossible/underdetermined/forbidden/repairable distinctions
2. **Long-Horizon Capybara Family** — thread memory, recap, state carry, interruption/resume
3. **Isomorphic Rigor Family** — invariant mapping without fake analogy
4. **Governance Sidecar Family** — move row-management out of specimen

### Hard Acceptance Laws for Corpus

| Law | Mandate |
|-----|---------|
| **A** | No more specimen/governance soup |
| **B** | Negative-space must be first-class |
| **C** | Verification remains load-bearing |
| **D** | Long-horizon must be exercised, not praised |
| **E** | Isomorphism requires invariant + breakpoint |
| **F** | PDVER must remain behavioral |

### Anti-Failure Modes (from Gemini Deep Research)

- **Trace Addiction** — beautiful reasoning uncoupled from final embodiment → require Executable Verification Gate
- **Identity Drift** — model responds with training markers ("This response is rated 5/5") → strict B10 sidecar separation
- **Merge Noise** — conflicting instructional signals degrade performance → packetized bucket isolation
- **Robotic Identity Bias** — mechanical persona from overly formal datasets → emphasize realistic prose

---

## APPENDIX E: META CONTROL LAYER (LOOP+)

### Evidence Handling Stack

```
OIE + ELT + Systematic Extraction + DEFNLP-style Post-Processing
```

**OIE (Open Information Extraction):**
- Capture entities, relations, claims, dependencies, contradictions
- Normalize to: subject / predicate / object / confidence / source

**ELT (Extract → Load → Transform):**
- Preserve raw material FIRST
- Manifest it, hash it
- ONLY THEN transform or summarize

**Systematic Extraction Matrix:**
- Predefine extraction variables
- Distinguish: new signal / reinforcement / contradiction / correction / unresolved
- Track: source / seam / claim / evidence strength / doctrine effect / status / next action

**DEFNLP-style Rescue Pass:**
- Find orphan signals
- Catch missed acronyms/aliases
- Identify repeated claims under different wording
- Recover contradictions
- Find facts stranded in appendices

### Minimal Operating Questions

For any corpus pass:
1. What is genuinely new signal?
2. What only reinforces existing knowledge?
3. What contradicts or weakens current doctrine?
4. What was a baseline or interpretation mistake?
5. What is still unresolved?
6. What should be promoted into the control layer?
7. What should become experiment pressure?
8. What older conclusion must be replayed recursively?

### Anti-Failure Rules

- Do not summarize before preserving raw structure
- Do not treat one source family as sufficient
- Do not let fast-signal outlets masquerade as primary mechanism proof
- Do not let extraction stop at the first clean summary
- Do not leave doctrine-changing facts trapped in prose
- Do not fail to distinguish evidence from interpretation
- Do not fail to record what remains unresolved

---

## APPENDIX F: FORGE-SPECIFIC DOCTRINE

### Authority Stacking (in order)

1. PCMMAD runtime control constitution
2. Forge unified code standards and anti-pattern-to-invariant refactor protocol
3. Forge one-page scoring sheet
4. CODEX OMEGA as major code-doctrine source

### Current Correction Priorities

1. Remove split truth between workshop ledger and CILNX continuity
2. Singularize naming from vessel to Cockpit internally
3. Deconcentrate runtime/orchestration god-nodes
4. Reduce hardcoded/dynamic external CILNX brittleness
5. Singularize LBE lineage
6. Kill orphan substrate remnants when safe
7. Harden soft dict/string/event boundaries

### Forge Reading Order

**First pass — foundations:**
1. `CODEX_OMEGA_BIBLE.md`
2. `PCMMAD_Canonical_Runtime_Specification.md`

**Second pass — standards:**
3. `UNIFIED_CODE_STANDARDS_AGNOSTIC_2026-04-11.md`
4. `FORGE_UNIFIED_CODE_STANDARDS_AND_DOCTRINE_2026-04-11.md`

**Third pass — corpus:**
5. Dataset card / engineering manifest
6. Split hygiene / contamination control

### Conflict Resolution

1. Foundational law wins over local convenience
2. Runtime/process law wins over ad hoc workflow
3. Forge-specific wins over agnostic when topic is Forge-internal
4. Corpus doctrine governs data but SHALL NOT override foundational law
5. When ambiguous: explicit invariant > implied convention; typed boundary > dict payload

---

*This doctrine is a living document. It evolves through the same PDVER discipline it mandates.*
