from dataclasses import replace
import unittest

from personal_cic.bootstrap import create_context, ingest_observation_batch
from personal_cic.core.config import TrafficConfig
from personal_cic.core.observations import Observation, ObservationAvailability
from personal_cic.core.world.components import (
    GeoPoint,
    ObservationState,
    TrafficCameraCollectionState,
    TrafficEventCollectionState,
    TrafficEventObservation,
    TrafficFlowCollectionState,
    TrafficFlowProbeObservation,
    TrafficMessageSignCollectionState,
    TrafficSituationState,
)
from personal_cic.traffic_awareness import (
    CAMERAS_ENTITY_ID,
    CHARLOTTE_CLOSURES_ENTITY_ID,
    CMPD_ENTITY_ID,
    DRIVENC_EVENTS_ENTITY_ID,
    SIGNS_ENTITY_ID,
    SITUATION_ENTITY_ID,
    WZDX_ENTITY_ID,
    TrafficAwarenessWorker,
    derive_traffic_situation,
)


def event(
    *,
    record_id: str,
    family: str,
    provider: str,
    upstream_id: str | None,
    description: str,
    roadway: str = "I-485",
    lat: float | None = 35.11,
    lon: float | None = -80.61,
    full_closure: bool | None = None,
):
    geometry = () if lat is None or lon is None else (GeoPoint(lat, lon),)
    return TrafficEventObservation(
        source_record_id=record_id,
        source_family=family,
        provider=provider,
        collection_class="official_report",
        event_type="incident",
        event_subtype="crash",
        description=description,
        roadway=roadway,
        direction="eastbound",
        county="Mecklenburg",
        geometry=geometry,
        full_closure=full_closure,
        upstream_event_id=upstream_id,
    )


def collection(provider: str, family: str, events):
    return TrafficEventCollectionState(
        location_label="Indian Trail / 28079",
        provider=provider,
        source_family=family,
        collection_class="official_report",
        scope_center_latitude=35.1115,
        scope_center_longitude=-80.6099,
        scope_radius_miles=75.0,
        source_record_count=len(events),
        local_record_count=len(events),
        freshest_source_at=None,
        events=tuple(events),
    )


def current(adapter_id="test"):
    return ObservationState(
        adapter_id=adapter_id,
        availability=ObservationAvailability.CURRENT,
        checked_at="2026-08-12T04:00:00+00:00",
        last_success_at="2026-08-12T04:00:00+00:00",
    )


class TrafficFusionTests(unittest.TestCase):
    def test_same_atmsers_upstream_id_is_one_kernel_not_two_confirmations(self):
        drive = collection(
            "NCDOT DriveNC",
            "NCDOT/ATMSERS",
            [event(record_id="2074439", family="NCDOT/ATMSERS", provider="NCDOT DriveNC", upstream_id="1196", description="Construction on I-277")],
        )
        wzdx = collection(
            "NCDOT DriveNC WZDx",
            "NCDOT/ATMSERS",
            [event(record_id="1196-1", family="NCDOT/ATMSERS", provider="NCDOT DriveNC WZDx", upstream_id="1196", description="Construction on I-277 / all lanes affected")],
        )
        state = derive_traffic_situation(
            location_label="Indian Trail / 28079",
            center_latitude=35.1115,
            center_longitude=-80.6099,
            radius_miles=75.0,
            event_sources=((drive, current()), (wzdx, current())),
            cameras=None,
            cameras_observation=None,
            signs=None,
            signs_observation=None,
            configured_unavailable=(),
        )
        self.assertIsNotNone(state)
        self.assertEqual(state.source_observation_count, 2)
        self.assertEqual(state.event_kernel_count, 1)
        self.assertEqual(state.kernels[0].source_families, ("NCDOT/ATMSERS",))
        self.assertEqual(len(state.kernels[0].source_record_refs), 2)
        self.assertEqual(state.kernels[0].association_basis, "same-lineage upstream identifier")

    def test_same_lineage_duplicate_closure_counts_one_event_kernel(self):
        drive = collection(
            "NCDOT DriveNC",
            "NCDOT/ATMSERS",
            [event(record_id="drive", family="NCDOT/ATMSERS", provider="NCDOT DriveNC", upstream_id="1196", description="Full closure", full_closure=True)],
        )
        wzdx = collection(
            "NCDOT DriveNC WZDx",
            "NCDOT/ATMSERS",
            [event(record_id="wzdx", family="NCDOT/ATMSERS", provider="NCDOT DriveNC WZDx", upstream_id="1196", description="All lanes closed", full_closure=True)],
        )
        state = derive_traffic_situation(
            location_label="Indian Trail / 28079",
            center_latitude=35.1115,
            center_longitude=-80.6099,
            radius_miles=75.0,
            event_sources=((drive, current()), (wzdx, current())),
            cameras=None,
            cameras_observation=None,
            signs=None,
            signs_observation=None,
            configured_unavailable=(),
        )
        self.assertEqual(state.event_kernel_count, 1)
        self.assertEqual(state.full_closure_count, 1)

    def test_fresh_empty_source_family_remains_visible_as_current_coverage(self):
        empty_cmpd = collection("CMPD", "CMPD CAD", [])
        state = derive_traffic_situation(
            location_label="Indian Trail / 28079",
            center_latitude=35.1115,
            center_longitude=-80.6099,
            radius_miles=75.0,
            event_sources=((empty_cmpd, current()),),
            cameras=None,
            cameras_observation=None,
            signs=None,
            signs_observation=None,
            configured_unavailable=(),
        )
        self.assertIsNotNone(state)
        self.assertEqual(state.event_kernel_count, 0)
        self.assertEqual(state.current_source_families, ("CMPD CAD",))

    def test_similar_independent_reports_are_not_merged_without_earned_association(self):
        ncdot = collection(
            "NCDOT DriveNC",
            "NCDOT/ATMSERS",
            [event(record_id="1", family="NCDOT/ATMSERS", provider="NCDOT DriveNC", upstream_id="A", description="Crash on I-485")],
        )
        cmpd = collection(
            "CMPD",
            "CMPD CAD",
            [event(record_id="2", family="CMPD CAD", provider="CMPD", upstream_id=None, description="ACCIDENT IN ROADWAY", lat=None, lon=None)],
        )
        state = derive_traffic_situation(
            location_label="Indian Trail / 28079",
            center_latitude=35.1115,
            center_longitude=-80.6099,
            radius_miles=75.0,
            event_sources=((ncdot, current()), (cmpd, current())),
            cameras=None,
            cameras_observation=None,
            signs=None,
            signs_observation=None,
            configured_unavailable=(),
        )
        self.assertEqual(state.event_kernel_count, 2)
        self.assertEqual(set(state.current_source_families), {"CMPD CAD", "NCDOT/ATMSERS"})


    def test_tomtom_flow_contributes_coverage_without_becoming_event_corroboration(self):
        tomtom = collection(
            "TomTom Orbis Incident Details",
            "TomTom Traffic",
            [event(record_id="TTI-1", family="TomTom Traffic", provider="TomTom Orbis Incident Details", upstream_id="TTI-1", description="Stopped traffic")],
        )
        probe = TrafficFlowProbeObservation(
            probe_id="ref", label="query reference", source_family="TomTom Traffic",
            provider="TomTom Flow Segment Data", collection_class="commercial_modeled_telemetry",
            query_latitude=35.1, query_longitude=-80.6,
            match_method="nearest_road_fragment_to_query_point", functional_road_class="FRC1",
            current_speed_mph=30, free_flow_speed_mph=60, current_travel_time_seconds=120,
            free_flow_travel_time_seconds=60, confidence=1.0, road_closure=False, openlr="segment",
            geometry=(GeoPoint(35.1, -80.6), GeoPoint(35.11, -80.61)),
        )
        flow = TrafficFlowCollectionState(
            location_label="Indian Trail / 28079", provider="TomTom Flow Segment Data",
            source_family="TomTom Traffic", collection_class="commercial_modeled_telemetry",
            scope_center_latitude=35.1115, scope_center_longitude=-80.6099, scope_radius_miles=75,
            configured_probe_count=1, successful_probe_count=1, probes=(probe,),
        )
        state = derive_traffic_situation(
            location_label="Indian Trail / 28079", center_latitude=35.1115, center_longitude=-80.6099,
            radius_miles=75.0, event_sources=((tomtom, current()),), cameras=None, cameras_observation=None,
            signs=None, signs_observation=None, flow=flow, flow_observation=current("tomtom.flow"),
            configured_unavailable=(),
        )
        self.assertEqual(state.event_kernel_count, 1)
        self.assertEqual(state.flow_probe_count, 1)
        self.assertEqual(state.source_observation_count, 2)
        self.assertIn("TomTom Traffic", state.current_source_families)
        self.assertTrue(any("source independence/event equivalence" in gap for gap in state.collection_gaps))

    def test_unavailable_source_is_not_used_as_current_event_evidence(self):
        stale = collection(
            "NCDOT DriveNC",
            "NCDOT/ATMSERS",
            [event(record_id="1", family="NCDOT/ATMSERS", provider="NCDOT DriveNC", upstream_id="A", description="Crash")],
        )
        unavailable = replace(current(), availability=ObservationAvailability.UNAVAILABLE)
        state = derive_traffic_situation(
            location_label="Indian Trail / 28079",
            center_latitude=35.1115,
            center_longitude=-80.6099,
            radius_miles=75.0,
            event_sources=((stale, unavailable),),
            cameras=None,
            cameras_observation=None,
            signs=None,
            signs_observation=None,
            configured_unavailable=("configured source unavailable: DriveNC events",),
        )
        self.assertIsNone(state)


class TrafficWorkerTests(unittest.TestCase):
    def _worker(self):
        context = create_context()
        config = TrafficConfig.from_mapping(
            {
                "enabled": True,
                "drivenc": {"enabled": True},
                "wzdx": {"enabled": True, "interval_seconds": 900},
                "cmpd": {"enabled": True, "interval_seconds": 180},
                "charlotte_closures": {"enabled": True, "interval_seconds": 900},
            }
        )
        worker = TrafficAwarenessWorker(
            context=context,
            config=config,
            location_label="Indian Trail / 28079",
            latitude=35.1115,
            longitude=-80.6099,
        )
        worker._ensure_entities()
        return context, worker

    def test_prepare_reentry_withdraws_persisted_traffic_authority_without_deleting_state(self):
        context, worker = self._worker()
        prior = collection(
            "NCDOT DriveNC",
            "NCDOT/ATMSERS",
            [event(record_id="1", family="NCDOT/ATMSERS", provider="NCDOT DriveNC", upstream_id="A", description="Crash")],
        )
        ingest_observation_batch(
            context,
            entity_id=DRIVENC_EVENTS_ENTITY_ID,
            adapter_id="drivenc.events",
            observations=(Observation.observed("drivenc.events", prior),),
            publish_cycle=False,
        )
        self.assertEqual(
            context.world.get_component(DRIVENC_EVENTS_ENTITY_ID, ObservationState).availability,
            ObservationAvailability.CURRENT,
        )

        worker.prepare_reentry()

        after = context.world.get_component(DRIVENC_EVENTS_ENTITY_ID, ObservationState)
        self.assertEqual(after.availability, ObservationAvailability.UNAVAILABLE)
        self.assertEqual(context.world.get_component(DRIVENC_EVENTS_ENTITY_ID, TrafficEventCollectionState), prior)
        situation_obs = context.world.get_component(SITUATION_ENTITY_ID, ObservationState)
        self.assertEqual(situation_obs.availability, ObservationAvailability.UNAVAILABLE)

    def test_one_fresh_source_yields_degraded_situation_while_other_configured_sources_are_unavailable(self):
        context, worker = self._worker()
        worker.prepare_reentry()
        fresh = collection(
            "CMPD",
            "CMPD CAD",
            [event(record_id="cmpd", family="CMPD CAD", provider="CMPD", upstream_id=None, description="ACCIDENT", lat=None, lon=None)],
        )
        worker.cmpd_adapter.collect = lambda: (Observation.observed("cmpd.traffic_cad", fresh),)
        worker._collect(entity_id=CMPD_ENTITY_ID, adapter=worker.cmpd_adapter)

        situation = context.world.get_component(SITUATION_ENTITY_ID, TrafficSituationState)
        observation = context.world.get_component(SITUATION_ENTITY_ID, ObservationState)
        self.assertIsNotNone(situation)
        self.assertEqual(observation.availability, ObservationAvailability.DEGRADED)
        self.assertEqual(situation.event_kernel_count, 1)
        self.assertTrue(any("DriveNC events" in gap for gap in situation.collection_gaps))

    def test_fresh_empty_collection_is_current_negative_evidence_not_unavailable(self):
        context, worker = self._worker()
        empty = collection("NCDOT DriveNC", "NCDOT/ATMSERS", [])
        worker.drivenc_events_adapter.collect = lambda: (Observation.observed("drivenc.events", empty),)
        worker._collect(entity_id=DRIVENC_EVENTS_ENTITY_ID, adapter=worker.drivenc_events_adapter)
        observation = context.world.get_component(DRIVENC_EVENTS_ENTITY_ID, ObservationState)
        self.assertEqual(observation.availability, ObservationAvailability.CURRENT)
        self.assertEqual(context.world.get_component(DRIVENC_EVENTS_ENTITY_ID, TrafficEventCollectionState).local_record_count, 0)


if __name__ == "__main__":
    unittest.main()
