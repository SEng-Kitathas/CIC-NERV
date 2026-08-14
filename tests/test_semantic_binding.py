import unittest
from personal_cic.core.events import EventBus
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import ObservationState, TrafficEventKernel, TrafficFlowCollectionState, TrafficFlowProbeObservation, TrafficSituationState
from personal_cic.semantics import SemanticKind, project_world_semantics

class SemanticBindingTests(unittest.TestCase):
    def _world(self):
        w=WorldState(EventBus()); w.ensure_entity("traffic-flow","Traffic Flow")
        w.upsert_component("traffic-flow",ObservationState("tomtom.flow",ObservationAvailability.CURRENT,"t2","t2"))
        w.upsert_component("traffic-flow",TrafficFlowCollectionState("Test","TomTom","tomtom","commercial_modeled_telemetry",35,-80,10,1,1,
            (TrafficFlowProbeObservation("p1","query ref","tomtom","TomTom","commercial_modeled_telemetry",35,-80,
             "nearest_road_fragment_to_query_point","FRC2",42.0,60.0,90,60,0.91,False,"abc",()),)))
        return w
    def test_projection_is_read_only_and_schema_stays_v2(self):
        w=self._world(); before=w.snapshot(); self.assertTrue(project_world_semantics(w)); self.assertEqual(w.snapshot(),before); self.assertEqual(before["schema_version"],2)
    def test_provider_confidence_is_unresolved_foreign_native(self):
        a=next(x for x in project_world_semantics(self._world()) if x.predicate=="tomtom_flow_confidence")
        self.assertEqual(a.kind,SemanticKind.FOREIGN_NATIVE); self.assertEqual(a.home,"Foreign semantic preservation")
        self.assertEqual(a.qualifiers["local_semantic_role"],"unresolved"); self.assertTrue(a.qualifiers["not_claim_confidence"])
    def test_flow_speed_is_measurement(self):
        a=next(x for x in project_world_semantics(self._world()) if x.predicate=="current_speed")
        self.assertEqual(a.kind,SemanticKind.MEASUREMENT); self.assertEqual(a.qualifiers["quantity_kind"],"velocity"); self.assertEqual(a.qualifiers["unit"],"mile_per_hour")
    def test_unavailable_is_absence_not_negative_world_state(self):
        w=WorldState(EventBus()); w.ensure_entity("s","Source"); w.upsert_component("s",ObservationState("x",ObservationAvailability.UNAVAILABLE,"t2","t1",("failed",)))
        a=next(x for x in project_world_semantics(w) if x.kind is SemanticKind.ABSENCE); self.assertTrue(a.qualifiers["does_not_assert_negative_world_state"])
    def test_same_lineage_is_not_corroboration(self):
        w=WorldState(EventBus()); w.ensure_entity("ts","Traffic")
        w.upsert_component("ts",TrafficSituationState("Test","t",35,-80,10,2,1,0,0,0,("drivenc","wzdx"),(),"exact only",False,12,0,
            (TrafficEventKernel("k","Road","event",None,None,("drivenc","wzdx"),("DriveNC|1","WZDx|1"),"same-lineage upstream identifier"),)))
        a=next(x for x in project_world_semantics(w) if x.kind is SemanticKind.IDENTITY_ASSOCIATION)
        self.assertTrue(a.qualifiers["not_independent_corroboration"]); self.assertTrue(a.qualifiers["not_cross_lineage_equivalence"])
if __name__=="__main__": unittest.main()

class SemanticBindingRC2Tests(unittest.TestCase):
    def _world(self, checked_at="t2", speed=42.0):
        w=WorldState(EventBus()); w.ensure_entity("traffic-flow","Traffic Flow")
        w.upsert_component("traffic-flow",ObservationState("tomtom.flow",ObservationAvailability.CURRENT,checked_at,checked_at))
        w.upsert_component("traffic-flow",TrafficFlowCollectionState("Test","TomTom","tomtom","commercial_modeled_telemetry",35,-80,10,1,1,
            (TrafficFlowProbeObservation("p1","query ref","tomtom","TomTom","commercial_modeled_telemetry",35,-80,
             "nearest_road_fragment_to_query_point","FRC2",speed,60.0,90,60,0.91,False,"abc",()),)))
        return w

    def _current_speed(self, world):
        return next(x for x in project_world_semantics(world) if x.predicate == "current_speed")

    def test_equal_measurement_value_at_distinct_times_has_distinct_assertion_identity(self):
        a=self._current_speed(self._world("t2",42.0)); b=self._current_speed(self._world("t3",42.0))
        self.assertEqual(a.proposition_key,b.proposition_key); self.assertNotEqual(a.assertion_id,b.assertion_id)

    def test_equal_source_event_reprojection_is_deterministic(self):
        w=self._world("t2",42.0); a=self._current_speed(w); b=self._current_speed(w)
        self.assertEqual(a.assertion_id,b.assertion_id); self.assertEqual(a.proposition_key,b.proposition_key)

    def test_proposition_key_stable_across_measurement_samples(self):
        a=self._current_speed(self._world("t2",42.0)); b=self._current_speed(self._world("t3",41.0))
        self.assertEqual(a.proposition_key,b.proposition_key); self.assertNotEqual(a.assertion_id,b.assertion_id)

    def test_source_roles_do_not_collapse_provider_adapter_and_record(self):
        from personal_cic.semantics import SemanticSourceRole
        a=self._current_speed(self._world())
        roles={x.role for x in a.provenance.sources}
        self.assertIn(SemanticSourceRole.PROVIDER,roles); self.assertIn(SemanticSourceRole.ADAPTER,roles)
        self.assertIn(SemanticSourceRole.SOURCE_RECORD,roles); self.assertIn(SemanticSourceRole.WORLD_ENTITY_REFERENCE,roles)

    def test_observation_and_unknown_source_times_remain_distinct(self):
        a=self._current_speed(self._world("t2"))
        self.assertEqual(a.temporal.observed_at,"t2")
        self.assertIsNone(a.temporal.phenomenon_time); self.assertIsNone(a.temporal.source_time)
        self.assertIsNone(a.temporal.retrieved_at); self.assertIsNone(a.temporal.derived_at)

    def test_rc1_source_refs_remains_compatible_projection(self):
        a=self._current_speed(self._world())
        self.assertIn("provider:TomTom",a.source_refs); self.assertIn("adapter:tomtom.flow",a.source_refs)

    def test_provider_confidence_remains_foreign_native_after_provenance_upgrade(self):
        a=next(x for x in project_world_semantics(self._world()) if x.predicate=="tomtom_flow_confidence")
        self.assertEqual(a.kind,SemanticKind.FOREIGN_NATIVE); self.assertEqual(a.qualifiers["local_semantic_role"],"unresolved")
        self.assertTrue(a.qualifiers["not_measurement_uncertainty_without_provider_contract"])

    def test_semantic_qualifiers_are_read_only(self):
        a=self._current_speed(self._world())
        with self.assertRaises(TypeError): a.qualifiers["unit"]="kilometer_per_hour"
