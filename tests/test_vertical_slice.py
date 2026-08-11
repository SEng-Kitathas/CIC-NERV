import tempfile
import unittest
from pathlib import Path

from personal_cic.core.config import HealthThresholds
from personal_cic.core.events import ComponentUpdated, EventBus, EventJournal
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    ComputeState,
    HealthState,
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
    wifi_signal_warning_dbm=-75,
)


class VerticalSliceTests(unittest.TestCase):
    def setUp(self):
        self.events = EventBus()
        self.world = WorldState(self.events)
        self.world.ensure_entity("node", "Test Node")
        self.health = HealthSystem(self.world, THRESHOLDS)
        self.events.subscribe(ComponentUpdated, self.health.on_component_updated)

    def test_nominal_health_is_derived_from_components(self):
        self.world.upsert_component("node", ComputeState(12.0, 4, 0.3, 0.075))
        self.world.upsert_component("node", MemoryState(16_000, 10_000, 37.5))
        self.world.upsert_component("node", StorageState("/", 100_000, 60_000, 40.0))
        health = self.world.entities["node"].get(HealthState)
        self.assertEqual(health.status, "nominal")

    def test_bad_wifi_drives_critical_health(self):
        self.world.upsert_component(
            "node",
            WifiLinkState("wlan0", False, None, None, None, None, None, None),
        )
        health = self.world.entities["node"].get(HealthState)
        self.assertEqual(health.status, "critical")
        self.assertIn("Wi-Fi disconnected", health.reasons)

    def test_query_is_component_based(self):
        self.world.upsert_component("node", ComputeState(12.0, 4, 0.3, 0.075))
        matches = self.world.query(ComputeState)
        self.assertEqual([entity.entity_id for entity in matches], ["node"])

    def test_event_journal_is_append_only_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = Path(tmp) / "events.jsonl"
            journal = EventJournal(journal_path)
            self.events.subscribe_all(journal.record)

            self.world.upsert_component("node", ComputeState(12.0, 4, 0.3, 0.075))
            first_size = journal_path.stat().st_size
            self.world.upsert_component("node", MemoryState(16_000, 10_000, 37.5))
            second_size = journal_path.stat().st_size

            self.assertGreater(first_size, 0)
            self.assertGreater(second_size, first_size)
            lines = journal_path.read_text(encoding="utf-8").splitlines()
            self.assertGreaterEqual(len(lines), 2)
            self.assertIn('"event_type":"ComponentUpdated"', lines[0])


if __name__ == "__main__":
    unittest.main()
