import json
import tempfile
import unittest
from pathlib import Path

from personal_cic.core.config import RuntimeConfig


class RuntimeConfigTests(unittest.TestCase):
    def test_runtime_config_loads_paths_and_intervals(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runtime.json"
            path.write_text(
                json.dumps(
                    {
                        "collection_interval_seconds": 5,
                        "snapshot_interval_seconds": 10,
                        "state_path": "state/world.json",
                        "event_journal_path": "logs/events.jsonl",
                    }
                ),
                encoding="utf-8",
            )

            config = RuntimeConfig.load(path)
            self.assertEqual(config.collection_interval_seconds, 5.0)
            self.assertEqual(config.snapshot_interval_seconds, 10.0)
            self.assertEqual(config.state_path, Path("state/world.json"))
            self.assertEqual(config.event_journal_path, Path("logs/events.jsonl"))
            self.assertFalse(config.presentation.enabled)
            self.assertEqual(config.presentation.bind_host, "127.0.0.1")
            self.assertEqual(config.presentation.port, 8765)

def test_runtime_config_loads_loopback_presentation(self):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "runtime.json"
        path.write_text(
            json.dumps(
                {
                    "collection_interval_seconds": 5,
                    "snapshot_interval_seconds": 10,
                    "state_path": "state/world.json",
                    "event_journal_path": "logs/events.jsonl",
                    "presentation": {
                        "enabled": True,
                        "bind_host": "127.0.0.1",
                        "port": 8765,
                    },
                }
            ),
            encoding="utf-8",
        )

        config = RuntimeConfig.load(path)

        self.assertTrue(config.presentation.enabled)
        self.assertEqual(config.presentation.bind_host, "127.0.0.1")
        self.assertEqual(config.presentation.port, 8765)

def test_runtime_config_rejects_non_loopback_presentation(self):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "runtime.json"
        path.write_text(
            json.dumps(
                {
                    "collection_interval_seconds": 5,
                    "snapshot_interval_seconds": 10,
                    "state_path": "state/world.json",
                    "event_journal_path": "logs/events.jsonl",
                    "presentation": {
                        "enabled": True,
                        "bind_host": "0.0.0.0",
                        "port": 8765,
                    },
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            RuntimeConfig.load(path)


if __name__ == "__main__":
    unittest.main()
