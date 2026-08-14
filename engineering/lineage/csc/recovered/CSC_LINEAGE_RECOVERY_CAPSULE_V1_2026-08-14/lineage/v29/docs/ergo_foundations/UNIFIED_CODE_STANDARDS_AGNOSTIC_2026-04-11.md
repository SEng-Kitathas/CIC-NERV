# Unified Code Standards — Agnostic

**Date:** 2026-04-11  
**Status:** Normative working synthesis  
**Scope:** Any codebase, any language, any runtime  
**Purpose:** Define a universal, implementation-facing standard for style, logic, verification, embodiment, and recursive refinement without tying the standard to a single framework, model family, or project.

---

## 1. Core premise

Code quality is not one thing.
It is the integrated result of:
- correct logic
- clean boundaries
- strong invariants
- low-entropy expression
- explicit verification
- safe embodiment
- recursive refinement under reality pressure

Good code is not merely readable.
Good code is:
- structurally legible
- semantically stable
- operationally verifiable
- resistant to drift
- resistant to accidental misuse
- explicit about what it is allowed to do and what it refuses to do

---

## 2. Global engineering invariant

Every meaningful engineering action SHALL be evaluated through the same fractal cycle:

**PROBE → DERIVE → VERIFY → EMBODY → RECURSE**

This applies at all scales:
- **micro:** functions, classes, local decisions, primitives, interfaces
- **meso:** modules, subsystems, pipelines, data contracts, runtime boundaries
- **macro:** architecture, repositories, build systems, deployment surfaces, datasets, governance, operations

### 2.1 Meaning of each step

#### PROBE
Inspect reality before shaping it.
Identify:
- constraints
- inputs
- outputs
- hazards
- negative space
- existing invariants
- uncertainty
- forbidden paths

#### DERIVE
Infer the correct structure from the probed reality.
Prefer:
- explicit invariants
- typed boundaries
- small composable primitives
- orthogonal responsibilities
- declarative intent where possible

#### VERIFY
Confirm that the derived structure actually holds.
Use reality anchors where possible:
- compilers
- type checkers
- tests
- proofs
- static analysis
- benchmarks
- runtime assertions
- model checks
- schema validation
- executable exemplars

#### EMBODY
Commit the verified logic into concrete artifact form.
Embodiment includes:
- code
- docs
- tests
- schemas
- migrations
- APIs
- build rules
- dataset rows
- runtime traces

Embodiment SHALL preserve the invariant rather than degrading it into convenience.

#### RECURSE
Re-enter the cycle on the remaining seam.
Do not recurse forever.
Recurse only when:
- a residual defect remains
- a verification failure exposes a deeper issue
- a boundary is still too implicit
- a stronger primitive is discoverable

---

## 3. Primary quality laws

### 3.1 Truth before theater
The code SHALL not merely look disciplined.
It SHALL survive contact with reality.

### 3.2 Explicitness over implication
Semantics that matter SHALL be visible.
Important concepts SHOULD NOT be hidden in:
- naming tricks
- comments alone
- string tags
- magic constants
- duplicated conventions
- folklore knowledge

### 3.3 Invariants before convenience
When a concept is load-bearing, define it explicitly.
Do not let the system depend on memory, vibes, or accidental consistency.

### 3.4 Primitives before repetition
If multiple places express the same semantic idea, that idea wants a primitive.
Repeated local derivation is usually a code smell.

### 3.5 Boundaries before cleverness
The system SHOULD be hard to misuse.
Prefer clear interfaces over impressive implementation tricks.

### 3.6 Verification before promotion
No behavior becomes load-bearing because it feels right.
It becomes load-bearing because it is verified.

### 3.7 Sidecars before contamination
Governance, metadata, provenance, and audit information SHOULD remain distinct from the specimen/body that is meant to execute or train.

---

## 4. The anti-pattern ledger

The following patterns are presumptively suspect.
They require active justification or removal.

### 4.1 Stringly-typed semantics
Examples:
- logic encoded in free-form strings
- policy carried by message phrasing
- category selection by substring heuristics

Preferred replacement:
- enums
- structured records
- typed classifiers
- explicit policy tables

### 4.2 Primitive obsession
Examples:
- raw dicts passed across important boundaries
- tuples or arrays carrying domain meaning without names
- loose booleans whose meaning depends on external context

Preferred replacement:
- typed records
- named fields
- constrained value objects
- explicit schemas

### 4.3 Metadata entanglement
Examples:
- governance data mixed into executable or trainable bodies
- adjudication notes fused into business logic
- operator bookkeeping leaking into specimen data

Preferred replacement:
- sidecars
- linked governance surfaces
- explicit provenance layers

### 4.4 Prestige-theater abstraction
Examples:
- abstractions that increase indirection without increasing truth
- patterns added for style-credit rather than system benefit
- architecture that sounds advanced but hides the invariant

Preferred replacement:
- smaller primitives
- direct expression of constraints
- fewer layers, each with a sharper purpose

### 4.5 Verification theater
Examples:
- long reasoning without executable anchor
- green tests that do not test the real invariant
- static assertions disconnected from runtime behavior

Preferred replacement:
- test the actual contract
- verify the final embodiment
- force reality anchors into the loop

### 4.6 State theater
Examples:
- implied lifecycle stages
- mutation without trace
- cached assumptions treated as truth
- continuity existing only in operator memory

Preferred replacement:
- explicit lifecycle records
- typed state transitions
- durable trace surfaces
- append-preferred mutation discipline

### 4.7 Comment-justified code
Examples:
- comments explaining what the types/interfaces should have expressed
- prose compensating for bad boundaries

Preferred replacement:
- use comments to explain why, not to rescue what

---

## 5. Invariants and boundaries

Every serious module SHOULD be answerable in terms of:
- what invariant it owns
- what inputs it accepts
- what outputs it guarantees
- what failure modes it exposes
- what it refuses to do
- what it delegates elsewhere

A module is suspect when:
- its responsibilities cannot be named cleanly
- its outputs require tribal knowledge to interpret
- its invariants live only in tests or comments
- it smuggles multiple lifecycles through one opaque surface

---

## 6. Style rules that are actually semantic

### 6.1 Name the concept, not the implementation accident
Prefer names that reflect:
- domain meaning
- contract meaning
- invariant meaning

Avoid names that merely reflect:
- historical leftovers
- local implementation mechanics
- temporary derivation details

### 6.2 Write for the next proof, not the next glance
Readable code is not just visually tidy.
It is code that makes the next audit, repair, extension, or proof easier.

### 6.3 Prefer low-surprise expression
Idiomatic code SHOULD feel unsurprising to a competent reader of the language.
When deviating from idiom, the gain must be structural, not aesthetic.

### 6.4 Make illegal states hard to represent
Use:
- narrow types
- constructors
- explicit stage objects
- validation at boundaries
- sidecar separation
- immutable defaults where feasible

### 6.5 Keep bodies sharp
Functions and methods SHOULD do one semantic thing.
If a body repeatedly shifts interpretive mode, it likely needs decomposition.

---

## 7. Verification standards

Verification SHALL match the kind of claim being made.

### 7.1 For logic claims
Use:
- unit tests
- property tests
- symbolic checks
- proofs where feasible

### 7.2 For interface claims
Use:
- schema checks
- contract tests
- round-trip tests
- fuzzing where relevant

### 7.3 For embodiment claims
Verify the final artifact, not just the planning path.
Examples:
- compiled binary
- generated file
- transformed code
- emitted row
- deployed config

### 7.4 For recursion/refinement claims
Verify:
- why recursion was entered
- what seam it targeted
- what termination condition ended it
- whether the recursive pass improved the system measurably

---

## 8. Data, corpus, and synthetic artifact rules

These rules apply to any synthetic or semi-synthetic engineering artifact.

### 8.1 Separate specimen from governance
Keep the trainable/executable specimen separate from:
- provenance
- adjudication
- review chatter
- promotion state
- contamination notes
- bookkeeping

### 8.2 Keep lineages traceable
Every significant artifact SHOULD have:
- identity
- lineage
- verification path
- promotion status
- demotion trigger when relevant

### 8.3 Treat contamination as a first-class defect
Train/eval, source/derived, and specimen/governance leakage SHALL be treated as real structural failures.

---

## 9. Minimal engineering checklist

Before promoting any implementation pass, ask:

1. **PROBE** — What did we actually inspect, and what remains uncertain?
2. **DERIVE** — What invariant or primitive did we derive from that inspection?
3. **VERIFY** — What concrete anchor proves the derivation survives reality?
4. **EMBODY** — Is the embodiment typed, explicit, and inspectable?
5. **RECURSE** — What is the next seam, and does it justify another pass?

If these cannot be answered cleanly, the pass is probably not finished.

---

## 10. Promotion standard

A pass is promotable when it:
- reduces ambiguity
- reduces drift risk
- reduces hidden state
- strengthens invariants
- strengthens verification
- improves embodiment clarity
- preserves or improves runtime truth under regression pressure

A pass is not promotable merely because it:
- looks cleaner
- uses more abstractions
- sounds more principled
- shortens code at the cost of explicitness

---



---

## 12. Review rubric

Use this rubric during code review, architecture review, or refactor evaluation.

### 12.1 Scoring bands
- **0** = absent / actively violated
- **1** = weak / mostly implicit / not load-bearing
- **2** = present but inconsistent
- **3** = solid / operationally reliable
- **4** = strong / explicit / hard to misuse
- **5** = exemplary / elegant / load-bearing under pressure

### 12.2 Rubric dimensions

| Dimension | Question | Score (0–5) |
|---|---|---|
| Invariant clarity | Are the governing invariants explicit and localizable? |  |
| Boundary quality | Are inputs/outputs/ownership/failure modes explicit? |  |
| Primitive quality | Are repeated semantic ideas embodied as shared primitives? |  |
| Type integrity | Are important concepts represented structurally rather than stringly? |  |
| Anti-pattern resistance | Does the code resist the known failure patterns in this document? |  |
| Verification quality | Does the verification actually test the claim being made? |  |
| Embodiment clarity | Is the final artifact explicit, inspectable, and traceable? |  |
| Recursion discipline | Is recursion/refinement justified, bounded, and terminating? |  |
| Specimen/governance separation | Are executable/trainable bodies kept distinct from governance/metadata? |  |
| Idiomatic expression | Is the implementation low-surprise and natural for its language/runtime? |  |

### 12.3 Interpretation
- **45–50** → promotion-ready, unusually strong
- **35–44** → strong but still worth targeted hardening
- **25–34** → mixed quality, not yet load-bearing
- **15–24** → substantial structural debt
- **0–14** → unfit for promotion

---

## 13. Promotion gate checklist

A change SHOULD NOT be promoted unless the reviewer can answer these clearly.

### PROBE gate
- [ ] The actual seam/problem was inspected directly.
- [ ] Uncertainty and negative-space constraints were stated.
- [ ] The anti-pattern or failure mode was named explicitly.

### DERIVE gate
- [ ] The change introduced or clarified a real invariant, primitive, or boundary.
- [ ] The derived structure is better than the prior shape for a concrete reason.
- [ ] The change is not merely aesthetic or prestige-driven.

### VERIFY gate
- [ ] The relevant verification anchor was run.
- [ ] The verification matches the claim being made.
- [ ] Regressions on neighboring behavior were checked.
- [ ] The system still behaves correctly at the final embodiment boundary.

### EMBODY gate
- [ ] The final code/artifact clearly embodies the derived invariant.
- [ ] Important records are typed/structured rather than smeared into dict/string payloads.
- [ ] The change is inspectable by a future reviewer without folklore knowledge.

### RECURSE gate
- [ ] The next seam is known.
- [ ] The current pass is bounded rather than endlessly widening.
- [ ] A demotion trigger is visible if later evidence invalidates the change.

### Final promotion decision
- [ ] This pass reduced ambiguity.
- [ ] This pass reduced drift or contamination risk.
- [ ] This pass increased truthfulness, verification strength, or embodiment clarity.
- [ ] This pass is better in reality, not just in prose.


## 11. Bottom line

The universal engineering target is not “clean code.”
It is **truthful code with explicit invariants, verified behavior, disciplined embodiment, and recursive refinement under reality pressure**.

The operative cycle is always:

**PROBE → DERIVE → VERIFY → EMBODY → RECURSE**

---

## Addendum — anti-pattern-to-invariant pass requirement

When reevaluating any artifact from square one, the operator SHALL:
- inspect the current step directly
- compare the current step to its own anti-pattern
- derive the best invariant for that step
- derive the best primitive/boundary/classifier/trace for embodying that invariant
- choose the most idiomatic low-surprise expression available in the host language/runtime
- verify the replacement under real anchors

This is mandatory at:
- micro scale
- meso scale
- macro scale

This requirement is now explicitly standardized rather than merely implied.

Note: The framework could be improved by adopting a "Law of Proportionate Rigor" that scales compliance with risk and by changing the scoring model from a fixed sum to a normalized density percentage.

