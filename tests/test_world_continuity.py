import tempfile
import unittest
from pathlib import Path

from personal_cic.core.events import EventBus
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    CICNode,
    HealthState,
    HealthStatus,
    MemoryState,
    ObservationState,
    WeatherAlertState,
    WeatherAlertSummary,
)


class WorldContinuityTests(unittest.TestCase):
    def test_snapshot_round_trip_restores_typed_components_without_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "world.json"

            first_events = EventBus()
            first = WorldState(first_events)
            first.ensure_entity("engage", "Engage")
            first.upsert_component("engage", CICNode())
            first.upsert_component("engage", MemoryState(16_000, 12_000, 25.0))
            first.upsert_component("engage", HealthState(HealthStatus.NOMINAL, ()))
            first.upsert_component(
                "engage",
                ObservationState(
                    adapter_id="linux.host",
                    availability=ObservationAvailability.CURRENT,
                    checked_at="2026-08-10T22:00:00+00:00",
                    last_success_at="2026-08-10T22:00:00+00:00",
                    reasons=(),
                ),
            )
            first.write_json(state_path)

            second_events = EventBus()
            second = WorldState(second_events)
            restored = second.hydrate_json(state_path)

            self.assertEqual(restored, 1)
            self.assertEqual(second_events.published_count, 0)
            entity = second.entities["engage"]
            self.assertIsInstance(entity.get(CICNode), CICNode)
            self.assertEqual(entity.get(MemoryState), MemoryState(16_000, 12_000, 25.0))
            self.assertEqual(entity.get(HealthState), HealthState(HealthStatus.NOMINAL, ()))
            self.assertEqual(
                entity.get(ObservationState).availability,
                ObservationAvailability.CURRENT,
            )

    def test_schema_v1_health_state_remains_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "world-v1.json"
            state_path.write_text(
                '{"schema_version":1,"entities":{"engage":{"label":"Engage","components":{"HealthState":{"status":"nominal","reasons":[]}}}}}',
                encoding="utf-8",
            )

            world = WorldState(EventBus())
            restored = world.hydrate_json(state_path)

            self.assertEqual(restored, 1)
            self.assertEqual(
                world.entities["engage"].get(HealthState),
                HealthState(HealthStatus.NOMINAL, ()),
            )

    def test_weather_alert_nested_state_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.json"
            world = WorldState(EventBus())
            world.ensure_entity("local-weather-alerts", "Local Weather Alerts")
            world.upsert_component(
                "local-weather-alerts",
                WeatherAlertState(
                    location_label="Test",
                    provider="National Weather Service",
                    active_count=1,
                    highest_severity="Severe",
                    provider_updated_at="2026-08-11T22:00:00+00:00",
                    alerts=(WeatherAlertSummary(
                        alert_id="a1", event="Warning", severity="Severe", urgency="Immediate",
                        headline="Test warning", sent_at=None, effective_at=None, expires_at=None,
                    ),),
                ),
            )
            world.write_json(path)
            restored = WorldState(EventBus())
            restored.hydrate_json(path)
            state = restored.get_component("local-weather-alerts", WeatherAlertState)
            self.assertIsInstance(state.alerts, tuple)
            self.assertIsInstance(state.alerts[0], WeatherAlertSummary)
            self.assertEqual(state.alerts[0].alert_id, "a1")


if __name__ == "__main__":
    unittest.main()
