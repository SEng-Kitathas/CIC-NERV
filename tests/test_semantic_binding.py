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



class SemanticBindingRC3Tests(unittest.TestCase):
    def _flow_world(self, availability=ObservationAvailability.CURRENT, checked_at="t2"):
        w=WorldState(EventBus()); w.ensure_entity("traffic-flow","Traffic Flow")
        w.upsert_component("traffic-flow",ObservationState("tomtom.flow",availability,checked_at,"t2",(() if availability is ObservationAvailability.CURRENT else ("collector state changed",))))
        w.upsert_component("traffic-flow",TrafficFlowCollectionState("Test","TomTom","tomtom","commercial_modeled_telemetry",35,-80,10,2,1,
            (TrafficFlowProbeObservation("p1","query ref","tomtom","TomTom","commercial_modeled_telemetry",35,-80,
             "nearest_road_fragment_to_query_point","FRC2",42.0,60.0,90,60,0.91,False,"abc",()),)))
        return w

    def test_retained_flow_state_loses_current_authority_when_collector_unavailable(self):
        a=next(x for x in project_world_semantics(self._flow_world(ObservationAvailability.UNAVAILABLE,"t3")) if x.predicate=="current_speed")
        self.assertEqual(a.qualifiers["semantic_authority_state"],"last_known_noncurrent")
        self.assertFalse(a.qualifiers["current_authority"])
        self.assertEqual(a.temporal.observed_at,"t3")

    def test_degraded_flow_state_is_qualified_not_clean_current(self):
        a=next(x for x in project_world_semantics(self._flow_world(ObservationAvailability.DEGRADED,"t3")) if x.predicate=="current_speed")
        self.assertEqual(a.qualifiers["semantic_authority_state"],"degraded_or_mixed")
        self.assertEqual(a.qualifiers["current_authority"],"qualified")

    def test_probe_success_fraction_is_data_quality_not_confidence(self):
        a=next(x for x in project_world_semantics(self._flow_world()) if x.predicate=="probe_collection_completeness")
        self.assertEqual(a.kind,SemanticKind.DATA_QUALITY)
        self.assertEqual(a.value,0.5)
        self.assertTrue(a.qualifiers["not_claim_confidence"])
        self.assertTrue(a.qualifiers["not_source_reliability"])

    def test_event_record_is_report_not_world_event_identity_with_role_times(self):
        from personal_cic.core.world.components import TrafficEventCollectionState, TrafficEventObservation
        w=WorldState(EventBus()); w.ensure_entity("events","Events")
        w.upsert_component("events",ObservationState("wzdx",ObservationAvailability.CURRENT,"retrieval-t2","retrieval-t2"))
        w.upsert_component("events",TrafficEventCollectionState("Test","WZDx","wzdx","official_exchange",35,-80,10,1,1,"source-t1",
            (TrafficEventObservation("r1","wzdx","WZDx","official_exchange","incident",None,"Crash","I-485","N","Mecklenburg",(),
             "reported-t0","updated-t1","start-t0","end-t3","major",True),)))
        a=next(x for x in project_world_semantics(w) if x.predicate=="provider_reports_event_record")
        self.assertEqual(a.kind,SemanticKind.SOURCE_REPORT)
        self.assertTrue(a.qualifiers["record_is_not_world_event_identity"])
        self.assertTrue(a.qualifiers["report_does_not_establish_causality"])
        self.assertEqual(a.temporal.phenomenon_time,"start-t0")
        self.assertEqual(a.temporal.source_time,"updated-t1")
        self.assertEqual(a.temporal.observed_at,"retrieval-t2")

    def test_current_empty_collection_is_scoped_negative_evidence(self):
        from personal_cic.core.world.components import TrafficEventCollectionState
        w=WorldState(EventBus()); w.ensure_entity("events","Events")
        w.upsert_component("events",ObservationState("drivenc",ObservationAvailability.CURRENT,"t2","t2"))
        w.upsert_component("events",TrafficEventCollectionState("Test","NCDOT","drivenc","official",35,-80,10,0,0,"t2",()))
        a=next(x for x in project_world_semantics(w) if x.kind is SemanticKind.EVIDENCE)
        self.assertTrue(a.value)
        self.assertTrue(a.qualifiers["not_universal_event_absence"])

    def test_surface_station_is_direct_but_current_estimate_is_derived(self):
        from personal_cic.core.world.components import CurrentWeatherEstimateState, SurfaceObservationNetworkState, SurfaceStationObservation
        w=WorldState(EventBus()); w.ensure_entity("surface","Surface")
        w.upsert_component("surface",ObservationState("aviation.surface",ObservationAvailability.CURRENT,"retrieval-t2","retrieval-t2"))
        w.upsert_component("surface",SurfaceObservationNetworkState("Test","AviationWeather","station-t1","KCLT",1,70.0,60.0,55.0,0.0,
            (SurfaceStationObservation("KCLT","Charlotte","station-t1",35.2,-80.9,5.0,70.0,60.0,55.0,180.0,10.0,None,10.0,30.01,1016.0,5000,"VFR",None,None),)))
        w.ensure_entity("estimate","Estimate")
        w.upsert_component("estimate",CurrentWeatherEstimateState("Test","derived-t3","surface_primary","aviation_surface",1,70.0,60.0,55.0,180.0,10.0,None,10.0,30.01,5000,"VFR",0.0,None,None,None,None,None))
        assertions=project_world_semantics(w)
        station=next(x for x in assertions if x.subject_ref.endswith("surface-station:KCLT") and x.predicate=="temperature")
        estimate=next(x for x in assertions if x.subject_ref.endswith("current-weather-estimate") and x.predicate=="temperature")
        self.assertEqual(station.qualifiers["measurement_kind"],"direct_station_observation")
        self.assertEqual(station.temporal.phenomenon_time,"station-t1")
        self.assertEqual(station.temporal.observed_at,"retrieval-t2")
        self.assertEqual(estimate.qualifiers["measurement_kind"],"derived_estimate")
        self.assertEqual(estimate.temporal.derived_at,"derived-t3")
        self.assertTrue(estimate.qualifiers["not_direct_observation"])

    def test_weather_alert_is_provider_report_not_hazard_identity(self):
        from personal_cic.core.world.components import WeatherAlertState, WeatherAlertSummary
        w=WorldState(EventBus()); w.ensure_entity("alerts","Alerts")
        w.upsert_component("alerts",ObservationState("nws.alerts",ObservationAvailability.CURRENT,"retrieval-t3","retrieval-t3"))
        w.upsert_component("alerts",WeatherAlertState("Test","NWS",1,"Severe","provider-updated",
            (WeatherAlertSummary("a1","Severe Thunderstorm Warning","Severe","Immediate","headline","sent-t0","effective-t1","expires-t4"),)))
        a=next(x for x in project_world_semantics(w) if x.predicate=="provider_reports_alert")
        self.assertEqual(a.kind,SemanticKind.SOURCE_REPORT)
        self.assertTrue(a.qualifiers["record_is_not_hazard_identity"])
        self.assertEqual(a.temporal.source_time,"sent-t0")
        self.assertEqual(a.temporal.phenomenon_time,"effective-t1")
        self.assertEqual(a.temporal.observed_at,"retrieval-t3")

    def test_health_is_derived_condition_while_cpu_is_measurement(self):
        from personal_cic.core.world.components import ComputeState, HealthState, HealthStatus
        from personal_cic.semantics import SemanticAssertionOrigin
        w=WorldState(EventBus()); w.ensure_entity("host","Host")
        w.upsert_component("host",ObservationState("linux.host",ObservationAvailability.CURRENT,"t2","t2"))
        w.upsert_component("host",ComputeState(10.0,4,0.5,0.125))
        w.upsert_component("host",HealthState(HealthStatus.NOMINAL,()))
        assertions=project_world_semantics(w)
        health=next(x for x in assertions if x.predicate=="health_status")
        cpu=next(x for x in assertions if x.predicate=="cpu_utilization")
        self.assertEqual(health.kind,SemanticKind.STATE_CONDITION)
        self.assertEqual(health.provenance.origin,SemanticAssertionOrigin.CIC_DERIVED)
        self.assertTrue(health.qualifiers["health_is_not_raw_telemetry"])
        self.assertEqual(cpu.kind,SemanticKind.MEASUREMENT)

    def test_usb_absence_inherits_collection_authority(self):
        from personal_cic.core.world.components import UsbDeviceState
        w=WorldState(EventBus()); w.ensure_entity("radio","Radio")
        w.upsert_component("radio",ObservationState("tenda.u11_pro",ObservationAvailability.CURRENT,"t2","t2"))
        w.upsert_component("radio",UsbDeviceState(False,None,None,"absent"))
        a=next(x for x in project_world_semantics(w) if x.predicate=="usb_device_present")
        self.assertFalse(a.value); self.assertTrue(a.qualifiers["current_authority"])
        w.upsert_component("radio",ObservationState("tenda.u11_pro",ObservationAvailability.UNAVAILABLE,"t3","t2",("lsusb failed",)))
        a=next(x for x in project_world_semantics(w) if x.predicate=="usb_device_present")
        self.assertFalse(a.qualifiers["current_authority"])

    def test_wifi_connectivity_state_and_signal_measurement_do_not_collapse(self):
        from personal_cic.core.world.components import WifiLinkState
        w=WorldState(EventBus()); w.ensure_entity("radio","Radio")
        w.upsert_component("radio",ObservationState("tenda.u11_pro",ObservationAvailability.CURRENT,"t2","t2"))
        w.upsert_component("radio",WifiLinkState("wlan0",True,"ssid",5180,-48,100.0,80.0,"10.0.0.2/24"))
        assertions=project_world_semantics(w)
        state=next(x for x in assertions if x.predicate=="wifi_connected")
        signal=next(x for x in assertions if x.predicate=="wifi_signal")
        self.assertEqual(state.kind,SemanticKind.STATE_CONDITION)
        self.assertEqual(signal.kind,SemanticKind.MEASUREMENT)
        self.assertEqual(signal.qualifiers["unit"],"dBm")

