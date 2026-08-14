import json
import tempfile
import unittest
from pathlib import Path

from personal_cic.core.events import EventBus, EventJournal, RuntimeStarted
from personal_cic.runtime import PersistentRuntime
from personal_cic.runtime_authority import (
    WorkerLifecycle,
    WorkerRuntimeStatus,
)


def _running_status(name: str) -> WorkerRuntimeStatus:
    return WorkerRuntimeStatus(
        name=name,
        lifecycle=WorkerLifecycle.RUNNING,
        started_at="2026-08-13T00:00:00+00:00",
        last_cycle_started_at=None,
        last_cycle_completed_at=None,
        stopped_at=None,
        terminal_failure=None,
    )


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

    def test_remote_reentry_precedes_presentation_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            runtime_config = tmp / "runtime.json"
            runtime_config.write_text(
                json.dumps(
                    {
                        "collection_interval_seconds": 5,
                        "snapshot_interval_seconds": 5,
                        "state_path": str(tmp / "world.json"),
                        "event_journal_path": str(tmp / "events.jsonl"),
                    }
                ),
                encoding="utf-8",
            )

            runtime = PersistentRuntime(
                runtime_config_path=runtime_config,
                health_config_path=Path("config/health.json"),
            )
            calls = []

            class FakePresentation:
                def start(self_inner):
                    self.assertIn("prepare-reentry", calls)
                    calls.append("presentation-start")

                def stop(self_inner):
                    calls.append("presentation-stop")

            class FakeAwareness:
                def prepare_reentry(self_inner):
                    calls.append("prepare-reentry")

                def start(self_inner):
                    calls.append("world-start")
                    runtime.request_stop("test")

                def runtime_status(self_inner):
                    return _running_status("world-awareness")

                def supervision_status(self_inner):
                    return _running_status("world-awareness")

                def stop(self_inner):
                    calls.append("world-stop")
                    return True

            runtime.presentation = FakePresentation()
            runtime.world_awareness = FakeAwareness()
            runtime.run()

            self.assertLess(
                calls.index("prepare-reentry"),
                calls.index("presentation-start"),
            )
            self.assertLess(
                calls.index("world-start"),
                calls.index("presentation-start"),
            )
    def test_incomplete_remote_worker_shutdown_skips_forced_final_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            runtime_config = tmp / "runtime.json"
            state_path = tmp / "world.json"
            journal_path = tmp / "events.jsonl"
            runtime_config.write_text(
                json.dumps(
                    {
                        "collection_interval_seconds": 5,
                        "snapshot_interval_seconds": 5,
                        "state_path": str(state_path),
                        "event_journal_path": str(journal_path),
                    }
                ),
                encoding="utf-8",
            )
            runtime = PersistentRuntime(
                runtime_config_path=runtime_config,
                health_config_path=Path("config/health.json"),
            )

            class StuckAwareness:
                def prepare_reentry(self_inner):
                    return None

                def start(self_inner):
                    runtime.request_stop("test")

                def runtime_status(self_inner):
                    return _running_status("world-awareness")

                def supervision_status(self_inner):
                    return _running_status("world-awareness")

                def stop(self_inner):
                    return False

            runtime.world_awareness = StuckAwareness()
            runtime.run()

            self.assertFalse(state_path.exists())
            records = [
                json.loads(line)
                for line in journal_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(records[-1]["event_type"], "RuntimeStopping")
            self.assertIn(
                "incomplete worker shutdown: world-awareness",
                records[-1]["payload"]["reason"],
            )


if __name__ == "__main__":
    unittest.main()
