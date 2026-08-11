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


if __name__ == "__main__":
    unittest.main()
