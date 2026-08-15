from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class StatementBasis(str, Enum):
    DIRECT_OBSERVATION = "direct_observation"
    SECONDHAND_REPORT = "secondhand_report"
    THIRD_PARTY_ATTRIBUTION = "third_party_attribution"
    INFERENCE = "inference"
    BELIEF = "belief"
    EXPECTATION = "expectation"
    INTENTION = "intention"


class EvidenceRelationKind(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXTUALIZES = "contextualizes"
    REPORTS = "reports"
    OBSERVES = "observes"
    DERIVED_FROM = "derived_from"


@dataclass(frozen=True, slots=True)
class Statement:
    statement_id: str
    proposition: str
    basis: StatementBasis
    source_record_ref: str
    subject_ref: str | None = None
    phenomenon_time: str | None = None
    claimed_location_ref: str | None = None
    source_claimed_confidence: str | float | int | None = None
    attribution_chain: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.statement_id, "statement_id")
        _require_text(self.proposition, "proposition")
        _require_text(self.source_record_ref, "source_record_ref")


@dataclass(frozen=True, slots=True)
class EvidenceRelation:
    relation_id: str
    evidence_ref: str
    proposition_ref: str
    kind: EvidenceRelationKind
    basis: str
    warrant_class: str = "unqualified"

    def __post_init__(self) -> None:
        _require_text(self.relation_id, "relation_id")
        _require_text(self.evidence_ref, "evidence_ref")
        _require_text(self.proposition_ref, "proposition_ref")
        _require_text(self.basis, "basis")
        _require_text(self.warrant_class, "warrant_class")

    @property
    def world_mutation_authority(self) -> str:
        return "NONE"


@dataclass(frozen=True, slots=True)
class RequalificationImpact:
    """Read-only requalification work item for one dependent proposition.

    The index identifies what must be reconsidered and which support/contradiction
    edges are stable, unavailable, or themselves pending requalification. It does
    not decide the resulting warrant, truth, independence, or world state.
    """

    proposition_ref: str
    depth: int
    trigger_refs: tuple[str, ...]
    stable_relation_ids: tuple[str, ...]
    unavailable_relation_ids: tuple[str, ...]
    pending_relation_ids: tuple[str, ...]
    stable_support_refs: tuple[str, ...]
    unavailable_support_refs: tuple[str, ...]
    pending_support_refs: tuple[str, ...]
    stable_contradiction_refs: tuple[str, ...]
    unavailable_contradiction_refs: tuple[str, ...]
    pending_contradiction_refs: tuple[str, ...]

    @property
    def requires_re_evaluation(self) -> bool:
        return True

    @property
    def warrant_authority(self) -> str:
        return "NONE"

    @property
    def independence_authority(self) -> str:
        return "NONE"

    @property
    def world_mutation_authority(self) -> str:
        return "NONE"


class EvidenceDependencyIndex:
    """Deterministic read-only reverse index over existing EvidenceRelation edges.

    This is intentionally not a graph database, persistence layer, inference engine,
    or warrant calculator. Relation semantics remain owned by EvidenceRelationKind.
    The index only makes forward and reverse dependency questions explicit and can
    produce a bounded requalification frontier after premise changes.
    """

    def __init__(self, relations: Iterable[EvidenceRelation]) -> None:
        ordered = tuple(sorted(relations, key=lambda relation: relation.relation_id))
        seen_ids: set[str] = set()
        by_proposition: dict[str, list[EvidenceRelation]] = defaultdict(list)
        by_evidence: dict[str, list[EvidenceRelation]] = defaultdict(list)

        for relation in ordered:
            if relation.relation_id in seen_ids:
                raise ValueError(
                    f"duplicate evidence relation id: {relation.relation_id}"
                )
            seen_ids.add(relation.relation_id)
            by_proposition[relation.proposition_ref].append(relation)
            by_evidence[relation.evidence_ref].append(relation)

        self._relations = ordered
        self._by_proposition = {
            key: tuple(value) for key, value in by_proposition.items()
        }
        self._by_evidence = {
            key: tuple(value) for key, value in by_evidence.items()
        }

    @property
    def world_mutation_authority(self) -> str:
        return "NONE"

    @property
    def warrant_authority(self) -> str:
        return "NONE"

    @property
    def independence_authority(self) -> str:
        return "NONE"

    @property
    def relations(self) -> tuple[EvidenceRelation, ...]:
        return self._relations

    def relations_for(
        self,
        proposition_ref: str,
        *,
        kinds: frozenset[EvidenceRelationKind] | None = None,
    ) -> tuple[EvidenceRelation, ...]:
        _require_text(proposition_ref, "proposition_ref")
        relations = self._by_proposition.get(proposition_ref, ())
        if kinds is None:
            return relations
        return tuple(relation for relation in relations if relation.kind in kinds)

    def supporting_relations(
        self,
        proposition_ref: str,
    ) -> tuple[EvidenceRelation, ...]:
        return self.relations_for(
            proposition_ref,
            kinds=frozenset({EvidenceRelationKind.SUPPORTS}),
        )

    def contradicting_relations(
        self,
        proposition_ref: str,
    ) -> tuple[EvidenceRelation, ...]:
        return self.relations_for(
            proposition_ref,
            kinds=frozenset({EvidenceRelationKind.CONTRADICTS}),
        )

    def direct_dependents(
        self,
        evidence_ref: str,
        *,
        kinds: frozenset[EvidenceRelationKind] | None = None,
    ) -> tuple[str, ...]:
        _require_text(evidence_ref, "evidence_ref")
        relations = self._by_evidence.get(evidence_ref, ())
        if kinds is not None:
            relations = tuple(
                relation for relation in relations if relation.kind in kinds
            )
        return tuple(sorted({relation.proposition_ref for relation in relations}))

    def transitive_dependents(
        self,
        evidence_ref: str,
        *,
        kinds: frozenset[EvidenceRelationKind] | None = None,
    ) -> tuple[str, ...]:
        _require_text(evidence_ref, "evidence_ref")
        queue = deque([evidence_ref])
        visited_refs = {evidence_ref}
        dependents: list[str] = []

        while queue:
            current = queue.popleft()
            for dependent in self.direct_dependents(current, kinds=kinds):
                if dependent in visited_refs:
                    continue
                visited_refs.add(dependent)
                dependents.append(dependent)
                queue.append(dependent)

        return tuple(dependents)

    def plan_requalification(
        self,
        *,
        changed_refs: Iterable[str],
        unavailable_refs: Iterable[str] = (),
        kinds: frozenset[EvidenceRelationKind] | None = None,
    ) -> tuple[RequalificationImpact, ...]:
        """Return dependent propositions in deterministic causal-depth order.

        Explicitly unavailable roots are separated from changed-but-still-present
        roots. A dependent proposition becomes a pending input to deeper dependents
        until a caller re-evaluates it. No support count, confidence, independence,
        or warrant is manufactured here.
        """

        changed = tuple(dict.fromkeys(changed_refs))
        if not changed:
            return ()
        for ref in changed:
            _require_text(ref, "changed_ref")

        unavailable = frozenset(unavailable_refs)
        for ref in unavailable:
            _require_text(ref, "unavailable_ref")
        unknown_unavailable = unavailable.difference(changed)
        if unknown_unavailable:
            raise ValueError(
                "unavailable refs must also be declared changed: "
                + ", ".join(sorted(unknown_unavailable))
            )

        depth_by_proposition: dict[str, int] = {}
        triggers_by_proposition: dict[str, set[str]] = defaultdict(set)
        queue = deque((ref, 0) for ref in changed)
        expanded_refs = set(changed)

        while queue:
            current_ref, current_depth = queue.popleft()
            next_depth = current_depth + 1
            for dependent in self.direct_dependents(current_ref, kinds=kinds):
                if dependent in changed:
                    # A changed root may participate in a cycle. It remains a root,
                    # not a dependent work item.
                    continue
                previous_depth = depth_by_proposition.get(dependent)
                if previous_depth is None or next_depth < previous_depth:
                    depth_by_proposition[dependent] = next_depth
                triggers_by_proposition[dependent].add(current_ref)
                if dependent not in expanded_refs:
                    expanded_refs.add(dependent)
                    queue.append((dependent, next_depth))

        impacted_refs = frozenset(depth_by_proposition)
        pending_refs = impacted_refs.union(changed).difference(unavailable)
        impacts: list[RequalificationImpact] = []

        for proposition_ref in sorted(
            depth_by_proposition,
            key=lambda ref: (depth_by_proposition[ref], ref),
        ):
            relations = self.relations_for(proposition_ref, kinds=kinds)
            stable: list[EvidenceRelation] = []
            lost: list[EvidenceRelation] = []
            pending: list[EvidenceRelation] = []

            for relation in relations:
                if relation.evidence_ref in unavailable:
                    lost.append(relation)
                elif relation.evidence_ref in pending_refs:
                    pending.append(relation)
                else:
                    stable.append(relation)

            def refs(
                selected: Iterable[EvidenceRelation],
                kind: EvidenceRelationKind,
            ) -> tuple[str, ...]:
                return tuple(
                    sorted(
                        {
                            relation.evidence_ref
                            for relation in selected
                            if relation.kind is kind
                        }
                    )
                )

            impacts.append(
                RequalificationImpact(
                    proposition_ref=proposition_ref,
                    depth=depth_by_proposition[proposition_ref],
                    trigger_refs=tuple(
                        sorted(triggers_by_proposition[proposition_ref])
                    ),
                    stable_relation_ids=tuple(r.relation_id for r in stable),
                    unavailable_relation_ids=tuple(r.relation_id for r in lost),
                    pending_relation_ids=tuple(r.relation_id for r in pending),
                    stable_support_refs=refs(stable, EvidenceRelationKind.SUPPORTS),
                    unavailable_support_refs=refs(
                        lost,
                        EvidenceRelationKind.SUPPORTS,
                    ),
                    pending_support_refs=refs(
                        pending,
                        EvidenceRelationKind.SUPPORTS,
                    ),
                    stable_contradiction_refs=refs(
                        stable,
                        EvidenceRelationKind.CONTRADICTS,
                    ),
                    unavailable_contradiction_refs=refs(
                        lost,
                        EvidenceRelationKind.CONTRADICTS,
                    ),
                    pending_contradiction_refs=refs(
                        pending,
                        EvidenceRelationKind.CONTRADICTS,
                    ),
                )
            )

        return tuple(impacts)


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
