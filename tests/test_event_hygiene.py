import tempfile
import unittest
from pathlib import Path

from personal_cic.core.config import HealthThresholds
from personal_cic.core.events import ComponentUpdated, EventJournal
from personal_cic.core.world.components import (
    StorageState,
    UptimeState,
    WifiLinkState,
)
from personal_cic.holons.systems.materiality import telemetry_significance


THRESHOLDS = HealthThresholds(
    cpu_warning_percent=80,
    cpu_critical_percent=95,
    memory_warning_percent=85,
    memory_critical_percent=95,
    storage_warning_percent=90,
    storage_critical_percent=97,
    wifi_signal_warning_dbm=-75,
)


class EventHygieneTests(unittest.TestCase):
    def test_uptime_tick_is_sample_after_initial_observation(self):
        self.assertEqual(
            telemetry_significance(UptimeState(100), UptimeState(105), THRESHOLDS),
            "sample",
        )

    def test_tiny_storage_free_space_change_is_sample(self):
        old = StorageState("/", 100_000, 60_000, 40.0)
        new = StorageState("/", 100_000, 59_984, 40.0)
        self.assertEqual(
            telemetry_significance(old, new, THRESHOLDS),
            "sample",
        )

    def test_wifi_disconnect_is_material(self):
        old = WifiLinkState("wlan0", True, "home", 5220, -65, 300.0, 300.0, "192.168.1.2/24")
        new = WifiLinkState("wlan0", False, None, None, None, None, None, None)
        self.assertEqual(
            telemetry_significance(old, new, THRESHOLDS),
            "material",
        )

    def test_journal_skips_sample_component_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            journal = EventJournal(path)

            journal.record(
                ComponentUpdated(
                    entity_id="node",
                    component_name="UptimeState",
                    previous=UptimeState(100),
                    current=UptimeState(105),
                    significance="sample",
                )
            )
            self.assertFalse(path.exists())

            journal.record(
                ComponentUpdated(
                    entity_id="node",
                    component_name="WifiLinkState",
                    previous=None,
                    current=WifiLinkState("wlan0", True, "home", 5220, -65, 300.0, 300.0, "192.168.1.2/24"),
                    significance="material",
                )
            )
            self.assertTrue(path.exists())
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
