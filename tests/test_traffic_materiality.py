from dataclasses import replace
import unittest

from personal_cic.core.config import HealthThresholds
from personal_cic.core.world.components import (
    GeoPoint,
    TrafficCameraCollectionState,
    TrafficCameraObservation,
    TrafficEventCollectionState,
    TrafficEventKernel,
    TrafficEventObservation,
    TrafficMessageSignCollectionState,
    TrafficMessageSignObservation,
    TrafficFlowCollectionState,
    TrafficFlowProbeObservation,
    TrafficSituationState,
)
from personal_cic.holons.systems.materiality import telemetry_significance


THRESHOLDS = HealthThresholds(
    cpu_warning_percent=80,
    cpu_critical_percent=95,
    memory_warning_percent=80,
    memory_critical_percent=95,
    storage_warning_percent=80,
    storage_critical_percent=95,
    temperature_warning_c=80,
    temperature_critical_c=95,
    wifi_signal_warning_dbm=-72,
)


def event(updated_at="2026-08-12T04:00:00+00:00", description="Crash", lanes="1 lane closed"):
    return TrafficEventObservation(
        source_record_id="1",
        source_family="NCDOT/ATMSERS",
        provider="NCDOT DriveNC",
        collection_class="official_report",
        event_type="incident",
        event_subtype="crash",
        description=description,
        roadway="I-485",
        direction="inner",
        county="Mecklenburg",
        geometry=(GeoPoint(35.11, -80.61),),
        updated_at=updated_at,
        lanes_affected=lanes,
        upstream_event_id="A",
    )


def events_state(e):
    return TrafficEventCollectionState(
        location_label="Indian Trail / 28079",
        provider="NCDOT DriveNC",
        source_family="NCDOT/ATMSERS",
        collection_class="official_report",
        scope_center_latitude=35.1115,
        scope_center_longitude=-80.6099,
        scope_radius_miles=75,
        source_record_count=1,
        local_record_count=1,
        freshest_source_at=e.updated_at,
        events=(e,),
    )


class TrafficMaterialityTests(unittest.TestCase):
    def test_provider_timestamp_refresh_without_semantic_event_change_is_sample(self):
        old = events_state(event(updated_at="2026-08-12T04:00:00+00:00"))
        new_event = event(updated_at="2026-08-12T04:01:00+00:00")
        new = replace(events_state(new_event), freshest_source_at=new_event.updated_at)
        self.assertEqual(telemetry_significance(old, new, THRESHOLDS), "sample")

    def test_lane_or_description_change_is_material(self):
        old = events_state(event())
        new = events_state(event(description="Crash now blocks all lanes", lanes="all lanes closed"))
        self.assertEqual(telemetry_significance(old, new, THRESHOLDS), "material")

    def test_camera_video_url_rotation_is_sample_when_operational_availability_is_unchanged(self):
        c1 = TrafficCameraObservation(
            camera_id="1", source_family="NCDOT/ATMSERS", provider="DriveNC", source_id="9",
            county="Mecklenburg", roadway="I-485", direction="Outer", location="cam",
            latitude=35.11, longitude=-80.61, status="Enabled", page_url="https://example.invalid/1",
            video_url="https://example.invalid/a.m3u8",
        )
        c2 = replace(c1, video_url="https://example.invalid/b.m3u8")
        base = dict(
            location_label="Indian Trail", provider="DriveNC", source_family="NCDOT/ATMSERS",
            scope_center_latitude=35.1115, scope_center_longitude=-80.6099, scope_radius_miles=75,
            source_record_count=1, local_record_count=1,
        )
        old = TrafficCameraCollectionState(**base, cameras=(c1,))
        new = TrafficCameraCollectionState(**base, cameras=(c2,))
        self.assertEqual(telemetry_significance(old, new, THRESHOLDS), "sample")

    def test_message_sign_text_transition_is_material(self):
        s1 = TrafficMessageSignObservation(
            sign_id="S", source_family="NCDOT/ATMSERS", provider="DriveNC", county="Union",
            roadway="US-74", direction=None, name="DMS", latitude=35.1, longitude=-80.67,
            updated_at="2026-08-12T04:00:00+00:00", messages=("NO_MESSAGE",),
        )
        s2 = replace(s1, updated_at="2026-08-12T04:01:00+00:00", messages=("LEFT LANE CLOSED",))
        base = dict(
            location_label="Indian Trail", provider="DriveNC", source_family="NCDOT/ATMSERS",
            scope_center_latitude=35.1115, scope_center_longitude=-80.6099, scope_radius_miles=75,
            source_record_count=1, local_record_count=1,
        )
        old = TrafficMessageSignCollectionState(**base, active_message_count=0, signs=(s1,))
        new = TrafficMessageSignCollectionState(**base, active_message_count=1, signs=(s2,))
        self.assertEqual(telemetry_significance(old, new, THRESHOLDS), "material")


    def test_flow_speed_churn_inside_same_semantic_band_is_sample(self):
        def state(speed):
            probe = TrafficFlowProbeObservation(
                probe_id="x", label="query ref", source_family="TomTom Traffic",
                provider="TomTom Flow Segment Data", collection_class="commercial_modeled_telemetry",
                query_latitude=35.1, query_longitude=-80.6,
                match_method="nearest_road_fragment_to_query_point",
                functional_road_class="FRC1", current_speed_mph=speed, free_flow_speed_mph=60,
                current_travel_time_seconds=60, free_flow_travel_time_seconds=55, confidence=1.0,
                road_closure=False, openlr="same", geometry=(GeoPoint(35.1, -80.6), GeoPoint(35.11, -80.61)),
            )
            return TrafficFlowCollectionState(
                location_label="Indian Trail", provider="TomTom Flow Segment Data",
                source_family="TomTom Traffic", collection_class="commercial_modeled_telemetry",
                scope_center_latitude=35.1115, scope_center_longitude=-80.6099, scope_radius_miles=75,
                configured_probe_count=1, successful_probe_count=1, probes=(probe,),
            )
        self.assertEqual(telemetry_significance(state(58), state(55), THRESHOLDS), "sample")

    def test_flow_crossing_congestion_band_is_material(self):
        def state(speed):
            probe = TrafficFlowProbeObservation(
                probe_id="x", label="query ref", source_family="TomTom Traffic",
                provider="TomTom Flow Segment Data", collection_class="commercial_modeled_telemetry",
                query_latitude=35.1, query_longitude=-80.6,
                match_method="nearest_road_fragment_to_query_point",
                functional_road_class="FRC1", current_speed_mph=speed, free_flow_speed_mph=60,
                current_travel_time_seconds=60, free_flow_travel_time_seconds=55, confidence=1.0,
                road_closure=False, openlr="same", geometry=(GeoPoint(35.1, -80.6), GeoPoint(35.11, -80.61)),
            )
            return TrafficFlowCollectionState(
                location_label="Indian Trail", provider="TomTom Flow Segment Data",
                source_family="TomTom Traffic", collection_class="commercial_modeled_telemetry",
                scope_center_latitude=35.1115, scope_center_longitude=-80.6099, scope_radius_miles=75,
                configured_probe_count=1, successful_probe_count=1, probes=(probe,),
            )
        self.assertEqual(telemetry_significance(state(58), state(30), THRESHOLDS), "material")

    def test_flow_matched_segment_identity_change_is_material(self):
        probe = TrafficFlowProbeObservation(
            probe_id="x", label="query ref", source_family="TomTom Traffic",
            provider="TomTom Flow Segment Data", collection_class="commercial_modeled_telemetry",
            query_latitude=35.1, query_longitude=-80.6,
            match_method="nearest_road_fragment_to_query_point",
            functional_road_class="FRC1", current_speed_mph=60, free_flow_speed_mph=60,
            current_travel_time_seconds=60, free_flow_travel_time_seconds=60, confidence=1.0,
            road_closure=False, openlr="segment-a", geometry=(GeoPoint(35.1, -80.6),),
        )
        base = dict(
            location_label="Indian Trail", provider="TomTom Flow Segment Data", source_family="TomTom Traffic",
            collection_class="commercial_modeled_telemetry", scope_center_latitude=35.1115,
            scope_center_longitude=-80.6099, scope_radius_miles=75, configured_probe_count=1, successful_probe_count=1,
        )
        old = TrafficFlowCollectionState(**base, probes=(probe,))
        new = TrafficFlowCollectionState(**base, probes=(replace(probe, openlr="segment-b"),))
        self.assertEqual(telemetry_significance(old, new, THRESHOLDS), "material")

    def test_situation_derived_timestamp_change_is_sample(self):
        kernel = TrafficEventKernel(
            kernel_id="K", roadway="I-485", summary="Crash", latitude=35.11, longitude=-80.61,
            source_families=("NCDOT/ATMSERS",), source_record_refs=("DriveNC|1",),
            association_basis="same-lineage upstream identifier",
        )
        old = TrafficSituationState(
            location_label="Indian Trail", derived_at="2026-08-12T04:00:00+00:00",
            scope_center_latitude=35.1115, scope_center_longitude=-80.6099, scope_radius_miles=75,
            source_observation_count=1, event_kernel_count=1, full_closure_count=0, camera_count=0,
            active_message_sign_count=0, current_source_families=("NCDOT/ATMSERS",),
            collection_gaps=("gap",), correlation_mode="exact only", external_waze_visual_enabled=True,
            external_waze_zoom=11, kernels=(kernel,),
        )
        new = replace(old, derived_at="2026-08-12T04:01:00+00:00")
        self.assertEqual(telemetry_significance(old, new, THRESHOLDS), "sample")


if __name__ == "__main__":
    unittest.main()
