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


if __name__ == "__main__":
    unittest.main()
