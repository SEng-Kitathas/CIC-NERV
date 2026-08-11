import json
import tempfile
import unittest
from pathlib import Path

from personal_cic.core.events import EventBus, EventJournal, RuntimeStarted


class RuntimeOrderingTests(unittest.TestCase):
    def test_runtime_started_can_be_first_durable_event_after_silent_hydration(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = Path(tmp) / "events.jsonl"
            bus = EventBus()
            journal = EventJournal(journal_path)
            bus.observe_all(journal.record)
            bus.publish(RuntimeStarted(pid=123, config_path="config/runtime.json", restored_entities=2))

            record = json.loads(journal_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["event_type"], "RuntimeStarted")
            self.assertEqual(record["payload"]["restored_entities"], 2)


if __name__ == "__main__":
    unittest.main()
