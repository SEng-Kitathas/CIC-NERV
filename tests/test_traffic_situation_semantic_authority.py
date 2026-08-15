from __future__ import annotations

import unittest

from personal_cic.core.events import EventBus
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    ObservationState,
    TrafficEventKernel,
    TrafficSituationState,
)
from personal_cic.semantics import project_world_semantics


class TrafficSituationSemanticAuthorityTests(unittest.TestCase):
    def _traffic_derived_assertions(
        self,
        availability: ObservationAvailability,
        *,
        reasons: tuple[str, ...] = (),
    ):
        world = WorldState(EventBus())
        world.ensure_entity("traffic-situation", "Traffic Situation")
        world.upsert_component(
            "traffic-situation",
            ObservationState(
                "traffic.fusion",
                availability,
                "checked-t2",
                "success-t1",
                reasons,
            ),
        )
        world.upsert_component(
            "traffic-situation",
            TrafficSituationState(
                "Charlotte",
                "derived-t2",
                35.2271,
                -80.8431,
                75.0,
                6,
                1,
                0,
                0,
                0,
                ("drivenc",),
                ("configured source unavailable: example",),
                "exact same-lineage only",
                False,
                11,
                0,
                (
                    TrafficEventKernel(
                        "kernel-1",
                        "I-77",
                        "Test event",
                        35.23,
                        -80.84,
                        ("drivenc",),
                        ("drivenc|record-1",),
                        "same-lineage upstream identifier",
                    ),
                ),
            ),
        )

        predicates = {
            "collection_scope",
            "known_collection_gap",
            "same_upstream_event_representation",
        }
        selected = tuple(
            assertion
            for assertion in project_world_semantics(world)
            if assertion.predicate in predicates
        )
        self.assertEqual({a.predicate for a in selected}, predicates)
        return selected

    def test_current_traffic_situation_inherits_current_collection_authority(self):
        assertions = self._traffic_derived_assertions(
            ObservationAvailability.CURRENT
        )
        for assertion in assertions:
            self.assertEqual(
                assertion.qualifiers["semantic_authority_state"],
                "current",
            )
            self.assertTrue(assertion.qualifiers["current_authority"])
            self.assertEqual(
                assertion.qualifiers["observation_checked_at"],
                "checked-t2",
            )
            self.assertEqual(
                assertion.qualifiers["observation_last_success_at"],
                "success-t1",
            )

    def test_degraded_traffic_situation_is_only_qualified_current(self):
        assertions = self._traffic_derived_assertions(
            ObservationAvailability.DEGRADED,
            reasons=("one configured source unavailable",),
        )
        for assertion in assertions:
            self.assertEqual(
                assertion.qualifiers["semantic_authority_state"],
                "degraded_or_mixed",
            )
            self.assertEqual(
                assertion.qualifiers["current_authority"],
                "qualified",
            )
            self.assertEqual(
                assertion.qualifiers["observation_reasons"],
                ("one configured source unavailable",),
            )

    def test_unavailable_traffic_situation_withdraws_current_authority(self):
        assertions = self._traffic_derived_assertions(
            ObservationAvailability.UNAVAILABLE,
            reasons=("traffic fusion unavailable",),
        )
        for assertion in assertions:
            self.assertEqual(
                assertion.qualifiers["semantic_authority_state"],
                "last_known_noncurrent",
            )
            self.assertFalse(assertion.qualifiers["current_authority"])
            self.assertEqual(
                assertion.qualifiers["observation_reasons"],
                ("traffic fusion unavailable",),
            )

    def test_retained_traffic_situation_is_policy_qualified(self):
        assertions = self._traffic_derived_assertions(
            ObservationAvailability.RETAINED,
            reasons=("retained by freshness policy",),
        )
        for assertion in assertions:
            self.assertEqual(
                assertion.qualifiers["semantic_authority_state"],
                "retained_by_policy",
            )
            self.assertEqual(
                assertion.qualifiers["current_authority"],
                "policy_qualified",
            )


if __name__ == "__main__":
    unittest.main()
