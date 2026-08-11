import json
import tempfile
import unittest
from pathlib import Path

from personal_cic.core.config import RuntimeConfig


class RuntimeConfigTests(unittest.TestCase):
    def _base(self):
        return {
            "collection_interval_seconds": 5,
            "snapshot_interval_seconds": 10,
            "state_path": "state/world.json",
            "event_journal_path": "logs/events.jsonl",
        }

    def _load(self, data):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "runtime.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return RuntimeConfig.load(path)

    def test_runtime_config_loads_paths_and_intervals(self):
        config = self._load(self._base())
        self.assertEqual(config.collection_interval_seconds, 5.0)
        self.assertEqual(config.snapshot_interval_seconds, 10.0)
        self.assertEqual(config.state_path, Path("state/world.json"))
        self.assertEqual(config.event_journal_path, Path("logs/events.jsonl"))
        self.assertFalse(config.presentation.enabled)
        self.assertFalse(config.world_awareness.enabled)

    def test_runtime_config_loads_loopback_presentation(self):
        data = self._base()
        data["presentation"] = {"enabled": True, "bind_host": "127.0.0.1", "port": 8765}
        config = self._load(data)
        self.assertTrue(config.presentation.enabled)
        self.assertEqual(config.presentation.bind_host, "127.0.0.1")
        self.assertEqual(config.presentation.port, 8765)

    def test_runtime_config_rejects_non_loopback_presentation(self):
        data = self._base()
        data["presentation"] = {"enabled": True, "bind_host": "0.0.0.0", "port": 8765}
        with self.assertRaises(ValueError):
            self._load(data)

    def test_world_awareness_config_loads_independent_provider_cadences(self):
        data = self._base()
        data["world_awareness"] = {
            "enabled": True,
            "location": {"label": "Test", "latitude": 35.1, "longitude": -80.6},
            "weather": {"interval_seconds": 300, "timeout_seconds": 5},
            "alerts": {"interval_seconds": 60, "timeout_seconds": 6, "user_agent": "CIC Test"},
        }
        config = self._load(data)
        self.assertTrue(config.world_awareness.enabled)
        self.assertEqual(config.world_awareness.location.label, "Test")
        self.assertEqual(config.world_awareness.weather.interval_seconds, 300.0)
        self.assertEqual(config.world_awareness.alerts.interval_seconds, 60.0)
        self.assertEqual(config.world_awareness.alerts.user_agent, "CIC Test")

    def test_world_awareness_rejects_too_fast_nws_refresh(self):
        data = self._base()
        data["world_awareness"] = {"enabled": True, "alerts": {"interval_seconds": 10}}
        with self.assertRaises(ValueError):
            self._load(data)


if __name__ == "__main__":
    unittest.main()
