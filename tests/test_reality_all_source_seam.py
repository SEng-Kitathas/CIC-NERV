from __future__ import annotations

from decimal import Decimal
import unittest

from personal_cic.core.events import EventBus
from personal_cic.core.world.store import WorldState
from personal_cic.reality import (
    AcquisitionAttempt,
    AcquisitionAttemptStatus,
    AcquisitionRegime,
    AcquisitionTask,
    CollectionGap,
    CoverageClaim,
    CoverageIndependence,
    CoverageStatus,
    EconomicAmount,
    EconomicAmountRole,
    EconomicRelation,
    EconomicRelationKind,
    EvidenceRelation,
    EvidenceRelationKind,
    HumanReport,
    InformationOrigin,
    InformationRequirement,
    LineageRelation,
    LineageRelationKind,
    ObservationModality,
    ObservationOpportunity,
    ProtectedSourceRef,
    PublicationMedium,
    SourceRecord,
    Statement,
    StatementBasis,
    assess_requirement_coverage,
    known_common_origin_components,
)


class AllSourceSemanticSeamTests(unittest.TestCase):
    def test_as_p1_human_statement_does_not_mutate_world_state(self):
        world = WorldState(EventBus())
        before = world.snapshot()

        source_record = SourceRecord(
            record_id="record-human-1",
            source_agent_ref="protected:alpha",
            information_origin=InformationOrigin.HUMAN_AUTHORED,
            acquisition_regime=AcquisitionRegime.DIRECT_OPERATOR,
            observation_modality=ObservationModality.REPORTED_VISUAL_OBSERVATION,
            publication_medium=PublicationMedium.DIRECT_REPORT,
            lineage_id="human-lineage-alpha",
        )
        statement = Statement(
            statement_id="statement-1",
            proposition="workers entered facility-x at 22:00",
            basis=StatementBasis.DIRECT_OBSERVATION,
            source_record_ref=source_record.record_id,
            subject_ref="facility-x",
        )
        report = HumanReport(
            report_id="human-report-1",
            protected_source=ProtectedSourceRef("protected:alpha"),
            source_record_ref=source_record.record_id,
            statements=(statement,),
        )
        relation = EvidenceRelation(
            relation_id="evidence-1",
            evidence_ref=statement.statement_id,
            proposition_ref="facility-x:resumed-production",
            kind=EvidenceRelationKind.SUPPORTS,
            basis="claimed direct visual observation",
        )

        self.assertEqual(report.world_mutation_authority, "NONE")
        self.assertEqual(relation.world_mutation_authority, "NONE")
        self.assertEqual(world.snapshot(), before)
        self.assertEqual(statement.basis, StatementBasis.DIRECT_OBSERVATION)

    def test_as_p2_known_syndication_is_one_known_common_origin_component(self):
        records = tuple(
            SourceRecord(
                record_id=f"record-{index}",
                source_agent_ref=f"publisher-{index}",
                information_origin=InformationOrigin.HUMAN_AUTHORED,
                acquisition_regime=AcquisitionRegime.PUBLICLY_ACCESSIBLE,
                observation_modality=ObservationModality.PUBLIC_STATEMENT,
                publication_medium=PublicationMedium.PUBLIC_WEB,
                lineage_id=f"lineage-{index}",
            )
            for index in range(6)
        )
        relations = tuple(
            LineageRelation(
                left_lineage_id="lineage-0",
                right_lineage_id=f"lineage-{index}",
                relation=LineageRelationKind.KNOWN_COMMON_ORIGIN,
                basis="explicit repost/source attribution",
            )
            for index in range(1, 6)
        )

        groups = known_common_origin_components(
            tuple(record.lineage_id for record in records),
            relations,
        )

        self.assertEqual(len(records), 6)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 6)
        self.assertFalse(
            any(
                relation.relation is LineageRelationKind.QUALIFIED_INDEPENDENT
                for relation in relations
            )
        )

    def test_as_p2_unknown_lineage_does_not_become_independence_claim(self):
        relation = LineageRelation(
            left_lineage_id="lineage-a",
            right_lineage_id="lineage-b",
            relation=LineageRelationKind.INDEPENDENCE_UNPROVEN,
            basis="no common-origin determination available",
        )

        self.assertEqual(
            relation.relation,
            LineageRelationKind.INDEPENDENCE_UNPROVEN,
        )
        self.assertNotEqual(
            relation.relation,
            LineageRelationKind.QUALIFIED_INDEPENDENT,
        )

    def test_as_p3_contract_ceiling_cannot_construct_paid_transfer(self):
        ceiling = EconomicAmount(
            value=Decimal("20000000"),
            currency="USD",
            role=EconomicAmountRole.CEILING,
            basis="maximum contract value",
        )
        contract = EconomicRelation(
            relation_id="contract-1",
            kind=EconomicRelationKind.CONTRACT,
            subject_ref="agency-a",
            object_ref="company-b",
            amount=ceiling,
            basis_record_refs=("award-record-1",),
        )

        self.assertEqual(contract.amount.role, EconomicAmountRole.CEILING)
        with self.assertRaises(ValueError):
            EconomicRelation(
                relation_id="transfer-invalid",
                kind=EconomicRelationKind.TRANSFER,
                subject_ref="agency-a",
                object_ref="company-b",
                amount=ceiling,
            )

    def test_as_p4_source_count_does_not_fill_missing_capabilities(self):
        requirement = InformationRequirement(
            requirement_id="facility-resumed-production",
            proposition="facility-x materially resumed production",
            target_ref="facility-x",
            required_capability_ids=(
                "mobility",
                "financial",
                "physical_change",
                "human_origin",
            ),
        )
        traffic_refs = tuple(f"traffic-{index}" for index in range(12))
        claims = (
            CoverageClaim(
                requirement_id=requirement.requirement_id,
                capability_id="mobility",
                status=CoverageStatus.STRONG,
                record_refs=traffic_refs,
                qualified_independent_lineage_ids=(
                    "traffic-lineage-a",
                    "traffic-lineage-b",
                ),
                independence=CoverageIndependence.QUALIFIED,
                currentness="current",
                warrant_class="qualified",
            ),
            CoverageClaim(
                requirement_id=requirement.requirement_id,
                capability_id="financial",
                status=CoverageStatus.PARTIAL,
                record_refs=("filing-1",),
                independence=CoverageIndependence.UNPROVEN,
                currentness="current",
                warrant_class="limited",
            ),
        )

        gaps = assess_requirement_coverage(requirement, claims)

        self.assertEqual(sum(claim.record_count for claim in claims), 13)
        self.assertEqual(claims[0].status, CoverageStatus.STRONG)
        self.assertEqual(claims[1].status, CoverageStatus.PARTIAL)
        self.assertEqual(
            {gap.capability_id for gap in gaps},
            {"financial", "physical_change", "human_origin"},
        )

    def test_as_p5_failed_collection_attempt_has_no_target_evidence_authority(self):
        world = WorldState(EventBus())
        before = world.snapshot()

        gap = CollectionGap(
            gap_id="gap-human",
            requirement_id="facility-resumed-production",
            capability_id="human_origin",
            reason="no qualified human-origin observation available",
        )
        opportunity = ObservationOpportunity(
            opportunity_id="opp-human",
            gap_ref=gap.gap_id,
            required_capability_id=gap.capability_id,
            candidate_source_ref="public-complaint-feed",
            expected_information_gain=0.5,
        )
        task = AcquisitionTask(
            task_id="task-human",
            opportunity_ref=opportunity.opportunity_id,
            authorized_by="test-operator",
            created_at="2026-08-14T23:00:00Z",
        )
        attempt = AcquisitionAttempt(
            attempt_id="attempt-human",
            task_ref=task.task_id,
            status=AcquisitionAttemptStatus.FAILED,
            attempted_at="2026-08-14T23:01:00Z",
            completed_at="2026-08-14T23:01:01Z",
            failure_reason="source unavailable",
        )

        self.assertEqual(
            opportunity.target_phenomenon_evidence_authority,
            "NONE",
        )
        self.assertEqual(task.target_phenomenon_evidence_authority, "NONE")
        self.assertEqual(attempt.target_phenomenon_evidence_authority, "NONE")
        self.assertEqual(attempt.result_source_record_refs, ())
        self.assertEqual(world.snapshot(), before)

    def test_as_p6_protected_reporter_identity_is_not_world_entity_requirement(self):
        world = WorldState(EventBus())
        before = world.snapshot()

        protected = ProtectedSourceRef(
            "protected:opaque-alpha",
            compartment="human-source",
        )
        source_record = SourceRecord(
            record_id="protected-record",
            source_agent_ref=protected.protected_ref,
            information_origin=InformationOrigin.HUMAN_AUTHORED,
            acquisition_regime=AcquisitionRegime.PARTNER_PROVIDED,
            observation_modality=ObservationModality.REPORTED_VISUAL_OBSERVATION,
            publication_medium=PublicationMedium.DIRECT_REPORT,
            lineage_id="protected-lineage",
        )
        statement = Statement(
            statement_id="protected-statement",
            proposition="vehicle entered facility gate",
            basis=StatementBasis.DIRECT_OBSERVATION,
            source_record_ref=source_record.record_id,
            subject_ref="facility-x",
        )
        report = HumanReport(
            report_id="protected-report",
            protected_source=protected,
            source_record_ref=source_record.record_id,
            statements=(statement,),
        )

        self.assertEqual(world.snapshot(), before)
        self.assertEqual(
            report.protected_source.protected_ref,
            "protected:opaque-alpha",
        )
        self.assertFalse(hasattr(report.protected_source, "person_entity_id"))
        self.assertEqual(report.world_mutation_authority, "NONE")


if __name__ == "__main__":
    unittest.main()
