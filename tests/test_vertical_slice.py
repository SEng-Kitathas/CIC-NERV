import tempfile
import unittest
from pathlib import Path

from personal_cic.core.config import HealthThresholds
from personal_cic.core.events import (
    ComponentUpdated,
    EventBus,
    EventJournal,
    ObservationCycleCompleted,
)
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    ComputeState,
    HealthState,
    HealthStatus,
    MemoryState,
    StorageState,
    WifiLinkState,
)
from personal_cic.holons.systems.health import HealthSystem


THRESHOLDS = HealthThresholds(
    cpu_warning_percent=80,
    cpu_critical_percent=95,
    memory_warning_percent=85,
    memory_critical_percent=95,
    storage_warning_percent=90,
    storage_critical_percent=97,
    temperature_warning_c=80,
    temperature_critical_c=90,
    wifi_signal_warning_dbm=-75,
)


class VerticalSliceTests(unittest.TestCase):
    def setUp(self):
        self.events = EventBus()
        self.world = WorldState(self.events)
        self.world.ensure_entity("node", "Test Node")
        self.health = HealthSystem(self.world, THRESHOLDS)
        self.events.subscribe(
            ObservationCycleCompleted,
            self.health.on_observation_cycle_completed,
        )

    def _derive(self):
        self.events.publish(
            ObservationCycleCompleted(
                entity_id="node",
                adapter_id="test",
                availability=ObservationAvailability.CURRENT,
            )
        )

    def test_nominal_health_is_derived_from_components(self):
        self.world.upsert_component("node", ComputeState(12.0, 4, 0.3, 0.075))
        self.world.upsert_component("node", MemoryState(16_000, 10_000, 37.5))
        self.world.upsert_component("node", StorageState("/", 100_000, 60_000, 40.0))
        self._derive()
        health = self.world.entities["node"].get(HealthState)
        self.assertEqual(health.status, HealthStatus.NOMINAL)

    def test_bad_wifi_drives_critical_health(self):
        self.world.upsert_component(
            "node",
            WifiLinkState("wlan0", False, None, None, None, None, None, None),
        )
        self._derive()
        health = self.world.entities["node"].get(HealthState)
        self.assertEqual(health.status, HealthStatus.CRITICAL)
        self.assertIn("Wi-Fi disconnected", health.reasons)

    def test_query_is_component_based(self):
        self.world.upsert_component("node", ComputeState(12.0, 4, 0.3, 0.075))
        matches = self.world.query(ComputeState)
        self.assertEqual([entity.entity_id for entity in matches], ["node"])

    def test_journal_records_cause_before_derived_health(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = Path(tmp) / "events.jsonl"
            journal = EventJournal(journal_path)
            self.events.observe_all(journal.record)

            self.world.upsert_component("node", ComputeState(12.0, 4, 0.3, 0.075))
            self._derive()
            lines = journal_path.read_text(encoding="utf-8").splitlines()

            self.assertIn('"component_name":"ComputeState"', lines[0])
            self.assertIn('"component_name":"HealthState"', lines[1])


if __name__ == "__main__":
    unittest.main()
