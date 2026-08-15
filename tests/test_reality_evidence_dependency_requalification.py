from __future__ import annotations

import unittest

from personal_cic.reality import (
    EvidenceDependencyIndex,
    EvidenceRelation,
    EvidenceRelationKind,
)


def _relation(
    relation_id: str,
    evidence_ref: str,
    proposition_ref: str,
    kind: EvidenceRelationKind = EvidenceRelationKind.SUPPORTS,
) -> EvidenceRelation:
    return EvidenceRelation(
        relation_id=relation_id,
        evidence_ref=evidence_ref,
        proposition_ref=proposition_ref,
        kind=kind,
        basis=f"{evidence_ref} -> {proposition_ref}",
        warrant_class="qualified",
    )


class EvidenceDependencyRequalificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = EvidenceDependencyIndex(
            (
                _relation("r-a", "A", "D"),
                _relation("r-b", "B", "D"),
                _relation("r-c", "C", "D"),
                _relation(
                    "r-q",
                    "Q",
                    "D",
                    EvidenceRelationKind.CONTRADICTS,
                ),
                _relation("r-d", "D", "E"),
                _relation("r-x", "X", "Y"),
            )
        )

    def test_support_and_reverse_dependency_use_existing_evidence_edges(self) -> None:
        self.assertEqual(
            tuple(
                relation.evidence_ref
                for relation in self.index.supporting_relations("D")
            ),
            ("A", "B", "C"),
        )
        self.assertEqual(self.index.direct_dependents("B"), ("D",))
        self.assertEqual(self.index.transitive_dependents("B"), ("D", "E"))

    def test_unavailable_premise_preserves_surviving_support(self) -> None:
        plan = self.index.plan_requalification(
            changed_refs=("B",),
            unavailable_refs=("B",),
        )

        self.assertEqual(
            tuple(impact.proposition_ref for impact in plan),
            ("D", "E"),
        )
        direct, transitive = plan
        self.assertEqual(direct.depth, 1)
        self.assertEqual(direct.trigger_refs, ("B",))
        self.assertEqual(direct.stable_support_refs, ("A", "C"))
        self.assertEqual(direct.unavailable_support_refs, ("B",))
        self.assertEqual(direct.stable_contradiction_refs, ("Q",))
        self.assertEqual(transitive.depth, 2)
        self.assertEqual(transitive.trigger_refs, ("D",))
        self.assertEqual(transitive.pending_support_refs, ("D",))

    def test_changed_but_present_premise_is_pending_not_stable(self) -> None:
        plan = self.index.plan_requalification(changed_refs=("B",))
        direct = plan[0]

        self.assertEqual(direct.stable_support_refs, ("A", "C"))
        self.assertEqual(direct.pending_support_refs, ("B",))
        self.assertEqual(direct.unavailable_support_refs, ())

    def test_unaffected_branch_is_not_requalified(self) -> None:
        plan = self.index.plan_requalification(
            changed_refs=("B",),
            unavailable_refs=("B",),
        )

        self.assertNotIn("Y", tuple(item.proposition_ref for item in plan))

    def test_contradiction_is_not_collapsed_into_support(self) -> None:
        self.assertEqual(
            tuple(
                relation.evidence_ref
                for relation in self.index.contradicting_relations("D")
            ),
            ("Q",),
        )
        support_only = frozenset({EvidenceRelationKind.SUPPORTS})
        self.assertEqual(
            self.index.direct_dependents("Q", kinds=support_only),
            (),
        )

    def test_cycle_is_bounded_and_does_not_return_changed_root(self) -> None:
        index = EvidenceDependencyIndex(
            (
                _relation("r-1", "A", "D"),
                _relation("r-2", "D", "E"),
                _relation("r-3", "E", "D"),
            )
        )

        self.assertEqual(index.transitive_dependents("A"), ("D", "E"))
        self.assertEqual(
            tuple(
                impact.proposition_ref
                for impact in index.plan_requalification(changed_refs=("A",))
            ),
            ("D", "E"),
        )

    def test_duplicate_relation_identity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceDependencyIndex(
                (
                    _relation("duplicate", "A", "D"),
                    _relation("duplicate", "B", "E"),
                )
            )

    def test_unavailable_ref_must_be_declared_changed(self) -> None:
        with self.assertRaises(ValueError):
            self.index.plan_requalification(
                changed_refs=("A",),
                unavailable_refs=("B",),
            )

    def test_index_and_plan_do_not_manufacture_authority(self) -> None:
        plan = self.index.plan_requalification(changed_refs=("B",))

        self.assertEqual(self.index.world_mutation_authority, "NONE")
        self.assertEqual(self.index.warrant_authority, "NONE")
        self.assertEqual(self.index.independence_authority, "NONE")
        self.assertEqual(plan[0].world_mutation_authority, "NONE")
        self.assertEqual(plan[0].warrant_authority, "NONE")
        self.assertEqual(plan[0].independence_authority, "NONE")
        self.assertTrue(plan[0].requires_re_evaluation)


if __name__ == "__main__":
    unittest.main()
