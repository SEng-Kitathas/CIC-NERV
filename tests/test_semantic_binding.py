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
