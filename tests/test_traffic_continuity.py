from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from personal_cic.core.events import EventBus
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    GeoPoint,
    ObservationState,
    TrafficEventCollectionState,
    TrafficEventObservation,
    TrafficEventKernel,
    TrafficFlowCollectionState,
    TrafficFlowProbeObservation,
    TrafficSituationState,
)


class TrafficContinuityTests(unittest.TestCase):
    def test_nested_traffic_state_round_trips_through_world_snapshot(self):
        world = WorldState(EventBus())
        world.ensure_entity("traffic", "Traffic")
        event = TrafficEventObservation(
            source_record_id="1",
            source_family="NCDOT/ATMSERS",
            provider="NCDOT DriveNC",
            collection_class="official_report",
            event_type="closures",
            event_subtype="construction",
            description="All lanes closed",
            roadway="I-485",
            direction="outer",
            county="Mecklenburg",
            geometry=(GeoPoint(35.11, -80.61), GeoPoint(35.12, -80.62)),
            updated_at="2026-08-12T04:00:00+00:00",
            full_closure=True,
            source_id="1196",
            upstream_event_id="1196",
        )
        state = TrafficEventCollectionState(
            location_label="Indian Trail / 28079",
            provider="NCDOT DriveNC",
            source_family="NCDOT/ATMSERS",
            collection_class="official_report",
            scope_center_latitude=35.1115,
            scope_center_longitude=-80.6099,
            scope_radius_miles=75,
            source_record_count=1,
            local_record_count=1,
            freshest_source_at=event.updated_at,
            events=(event,),
        )
        world.upsert_component("traffic", state)
        world.upsert_component(
            "traffic",
            ObservationState(
                adapter_id="drivenc.events",
                availability=ObservationAvailability.CURRENT,
                checked_at="2026-08-12T04:01:00+00:00",
                last_success_at="2026-08-12T04:01:00+00:00",
            ),
        )

        world.ensure_entity("situation", "Situation")
        situation = TrafficSituationState(
            location_label="Indian Trail / 28079",
            derived_at="2026-08-12T04:01:00+00:00",
            scope_center_latitude=35.1115,
            scope_center_longitude=-80.6099,
            scope_radius_miles=75,
            source_observation_count=1,
            event_kernel_count=1,
            full_closure_count=1,
            camera_count=0,
            active_message_sign_count=0,
            current_source_families=("NCDOT/ATMSERS",),
            collection_gaps=("Waze machine feed not normalized",),
            correlation_mode="exact same-lineage only",
            external_waze_visual_enabled=True,
            external_waze_zoom=11,
            kernels=(
                TrafficEventKernel(
                    kernel_id="K",
                    roadway="I-485",
                    summary="All lanes closed",
                    latitude=35.11,
                    longitude=-80.61,
                    source_families=("NCDOT/ATMSERS",),
                    source_record_refs=("NCDOT DriveNC|1",),
                    association_basis="same-lineage upstream identifier",
                ),
            ),
        )
        world.upsert_component("situation", situation)

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.json"
            world.write_json(path)
            restored = WorldState(EventBus())
            count = restored.hydrate_json(path)

        self.assertEqual(count, 2)
        self.assertEqual(restored.get_component("traffic", TrafficEventCollectionState), state)
        self.assertEqual(restored.get_component("situation", TrafficSituationState), situation)
        self.assertEqual(
            restored.get_component("traffic", ObservationState).availability,
            ObservationAvailability.CURRENT,
        )

    def test_tomtom_event_extensions_and_flow_state_round_trip(self):
        world = WorldState(EventBus())
        world.ensure_entity("tomtom-events", "TomTom Events")
        event = TrafficEventObservation(
            source_record_id="TTI-1", source_family="TomTom Traffic",
            provider="TomTom Orbis Incident Details", collection_class="commercial_report",
            event_type="jam", event_subtype=None, description="Stopped traffic", roadway="US-74",
            direction=None, county=None, geometry=(GeoPoint(35.11, -80.61), GeoPoint(35.12, -80.62)),
            start_at="2026-08-12T15:09:30+00:00", magnitude_of_delay="major", delay_seconds=201,
            length_meters=119.1, road_numbers=("US-74",), from_location="A", to_location="B",
            probability_of_occurrence="certain", time_validity="present", event_details=("Stopped traffic",),
            event_codes=(101,), community_report_count=1, community_last_report_at="2025-06-26T23:36:00+00:00",
            source_organization="TomTom Traffic", source_id="TTI-1", upstream_event_id="TTI-1",
        )
        event_state = TrafficEventCollectionState(
            location_label="Indian Trail", provider="TomTom Orbis Incident Details",
            source_family="TomTom Traffic", collection_class="commercial_report",
            scope_center_latitude=35.1115, scope_center_longitude=-80.6099, scope_radius_miles=75,
            source_record_count=1, local_record_count=1, freshest_source_at=None, events=(event,),
        )
        world.upsert_component("tomtom-events", event_state)

        world.ensure_entity("tomtom-flow", "TomTom Flow")
        flow_probe = TrafficFlowProbeObservation(
            probe_id="ref", label="Query reference", source_family="TomTom Traffic",
            provider="TomTom Flow Segment Data", collection_class="commercial_modeled_telemetry",
            query_latitude=35.22, query_longitude=-80.85, match_method="nearest_road_fragment_to_query_point",
            functional_road_class="FRC2", current_speed_mph=22, free_flow_speed_mph=44,
            current_travel_time_seconds=86, free_flow_travel_time_seconds=43, confidence=1.0,
            road_closure=False, openlr="segment", geometry=(GeoPoint(35.224, -80.859), GeoPoint(35.223, -80.856)),
        )
        flow_state = TrafficFlowCollectionState(
            location_label="Indian Trail", provider="TomTom Flow Segment Data", source_family="TomTom Traffic",
            collection_class="commercial_modeled_telemetry", scope_center_latitude=35.1115,
            scope_center_longitude=-80.6099, scope_radius_miles=75, configured_probe_count=1,
            successful_probe_count=1, probes=(flow_probe,),
        )
        world.upsert_component("tomtom-flow", flow_state)

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.json"
            world.write_json(path)
            restored = WorldState(EventBus())
            count = restored.hydrate_json(path)

        self.assertEqual(count, 2)
        self.assertEqual(restored.get_component("tomtom-events", TrafficEventCollectionState), event_state)
        self.assertEqual(restored.get_component("tomtom-flow", TrafficFlowCollectionState), flow_state)


if __name__ == "__main__":
    unittest.main()
