import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from personal_cic.core.events import EventBus, EventJournal, RuntimeStarted
from personal_cic.traffic_awareness import TrafficAwarenessWorker
from personal_cic.world_awareness import WorldAwarenessWorker


class _FakeThread:
    def __init__(self, *, alive):
        self.alive = alive
        self.join_timeouts = []

    def join(self, timeout=None):
        self.join_timeouts.append(timeout)

    def is_alive(self):
        return self.alive


class ConcurrencyIntegrityTests(unittest.TestCase):
    def test_event_journal_remains_parseable_under_concurrent_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            bus = EventBus()
            bus.observe_all(EventJournal(path).record)

            def publish(worker_id):
                for index in range(100):
                    bus.publish(
                        RuntimeStarted(
                            pid=worker_id * 1000 + index,
                            config_path=f"worker-{worker_id}",
                            restored_entities=index,
                        )
                    )

            threads = [threading.Thread(target=publish, args=(i,)) for i in range(4)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 400)
            records = [json.loads(line) for line in lines]
            self.assertEqual(len({r["payload"]["event_id"] for r in records}), 400)
            self.assertEqual(bus.published_count, 400)

    def test_world_worker_does_not_forget_a_thread_that_outlives_stop_budget(self):
        worker = WorldAwarenessWorker.__new__(WorldAwarenessWorker)
        worker._stop = threading.Event()
        thread = _FakeThread(alive=True)
        worker._thread = thread
        provider = SimpleNamespace(timeout_seconds=1.0)
        worker.config = SimpleNamespace(
            weather=provider, alerts=provider, surface=provider, forecast=provider,
            radar=SimpleNamespace(timeout_seconds=1.0, context_timeout_seconds=1.0),
        )
        self.assertFalse(worker.stop())
        self.assertIs(worker._thread, thread)
        self.assertTrue(worker._stop.is_set())

    def test_traffic_worker_does_not_forget_a_thread_that_outlives_stop_budget(self):
        worker = TrafficAwarenessWorker.__new__(TrafficAwarenessWorker)
        worker._stop = threading.Event()
        thread = _FakeThread(alive=True)
        worker._thread = thread
        provider = SimpleNamespace(timeout_seconds=1.0)
        worker.config = SimpleNamespace(
            drivenc=provider, wzdx=provider, cmpd=provider,
            charlotte_closures=provider, tomtom=provider,
        )
        self.assertFalse(worker.stop())
        self.assertIs(worker._thread, thread)
        self.assertTrue(worker._stop.is_set())


if __name__ == "__main__":
    unittest.main()
