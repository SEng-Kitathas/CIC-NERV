import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from personal_cic.runtime import PersistentRuntime
from personal_cic.runtime_authority import (
    DurableStateLease,
    DurableStateLeaseError,
    WorkerAuthorityFailure,
    WorkerLifecycle,
    WorkerLiveness,
)
from personal_cic.traffic_awareness import TrafficAwarenessWorker
from personal_cic.world_awareness import WorldAwarenessWorker


class RuntimeAuthorityTests(unittest.TestCase):
    def _runtime_config(self, root: Path) -> Path:
        path = root / "runtime.json"
        path.write_text(
            json.dumps(
                {
                    "collection_interval_seconds": 0.05,
                    "snapshot_interval_seconds": 0.05,
                    "state_path": str(root / "world.json"),
                    "event_journal_path": str(root / "events.jsonl"),
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_durable_state_lease_rejects_second_writer_until_release(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            state_path = Path(tmp_name) / "world.json"
            first = DurableStateLease(state_path)
            second = DurableStateLease(state_path)
            first.acquire()
            self.addCleanup(first.release)

            with self.assertRaises(DurableStateLeaseError):
                second.acquire()

            first.release()
            second.acquire()
            self.assertTrue(second.held)
            second.release()

    def test_second_runtime_is_rejected_before_journal_publication(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            config = self._runtime_config(root)
            first = PersistentRuntime(config, Path("config/health.json"))
            self.addCleanup(first._durable_lease.release)

            with self.assertRaises(DurableStateLeaseError):
                PersistentRuntime(config, Path("config/health.json"))

            self.assertFalse((root / "events.jsonl").exists())
            self.assertFalse((root / "world.json").exists())

    def _assert_worker_failure_is_captured(self, worker, name: str):
        callbacks = []
        worker._stop = threading.Event()
        worker._thread = None
        worker._liveness = WorkerLiveness(name)
        worker._on_terminal_failure = callbacks.append

        def fail():
            raise RuntimeError("forced worker failure")

        worker._run = fail
        worker._run_guarded()

        status = worker.runtime_status()
        self.assertEqual(status.lifecycle, WorkerLifecycle.FAILED)
        self.assertIn("RuntimeError", status.terminal_failure)
        self.assertEqual(callbacks, [status])

    def test_world_worker_terminal_exception_becomes_typed_failure(self):
        worker = WorldAwarenessWorker.__new__(WorldAwarenessWorker)
        self._assert_worker_failure_is_captured(worker, "world-awareness")

    def test_traffic_worker_terminal_exception_becomes_typed_failure(self):
        worker = TrafficAwarenessWorker.__new__(TrafficAwarenessWorker)
        self._assert_worker_failure_is_captured(worker, "traffic-awareness")

    def test_runtime_worker_failure_is_process_failure_and_skips_final_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            config = self._runtime_config(root)
            runtime = PersistentRuntime(config, Path("config/health.json"))

            liveness = WorkerLiveness("world-awareness")
            liveness.mark_starting()
            liveness.mark_running()

            class FailedWorker:
                def prepare_reentry(self_inner):
                    return None

                def start(self_inner):
                    status = liveness.mark_failed("forced terminal failure")
                    runtime._record_worker_failure(status)

                def runtime_status(self_inner):
                    return liveness.snapshot()

                def supervision_status(self_inner):
                    return liveness.snapshot()

                def stop(self_inner):
                    return True

            runtime.world_awareness = FailedWorker()

            with self.assertRaises(WorkerAuthorityFailure):
                runtime.run()

            self.assertFalse((root / "world.json").exists())
            records = [
                json.loads(line)
                for line in (root / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(records[-1]["event_type"], "RuntimeStopping")
            self.assertIn(
                "enabled collection worker failed: world-awareness",
                records[-1]["payload"]["reason"],
            )

    def test_persistent_runtime_collects_local_before_presentation_without_duplicate_startup_cycle(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            runtime = PersistentRuntime(
                self._runtime_config(root),
                Path("config/health.json"),
            )
            order = []

            class FakePresentation:
                def start(self_inner):
                    order.append("presentation")
                    runtime.request_stop("test complete")

                def stop(self_inner):
                    return None

            runtime.presentation = FakePresentation()

            def collect(_context):
                order.append("collect")

            with patch("personal_cic.runtime.collect_once", side_effect=collect):
                runtime.run()

            self.assertEqual(order, ["collect", "presentation"])
            self.assertIsNone(runtime._local_collection_failure)

    def test_unexpected_local_collection_failure_blocks_presentation_and_final_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            runtime = PersistentRuntime(
                self._runtime_config(root),
                Path("config/health.json"),
            )
            presentation_started = False

            class FakePresentation:
                def start(self_inner):
                    nonlocal presentation_started
                    presentation_started = True

                def stop(self_inner):
                    return None

            runtime.presentation = FakePresentation()

            with patch(
                "personal_cic.runtime.collect_once",
                side_effect=RuntimeError("forced local collection failure"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "forced local collection failure",
                ):
                    runtime.run()

            self.assertFalse(presentation_started)
            self.assertIsNotNone(runtime._local_collection_failure)
            self.assertFalse((root / "world.json").exists())
            records = [
                json.loads(line)
                for line in (root / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(records[-1]["event_type"], "RuntimeStopping")
            self.assertIn(
                "local collection failed during startup_qualification",
                records[-1]["payload"]["reason"],
            )

    def test_remote_worker_failure_during_local_startup_gate_blocks_presentation(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            runtime = PersistentRuntime(
                self._runtime_config(root),
                Path("config/health.json"),
            )
            presentation_started = False
            liveness = WorkerLiveness("world-awareness")
            liveness.mark_starting()
            liveness.mark_running()

            class FakeWorker:
                def prepare_reentry(self_inner):
                    return None

                def start(self_inner):
                    return None

                def runtime_status(self_inner):
                    return liveness.snapshot()

                def supervision_status(self_inner):
                    return liveness.snapshot()

                def stop(self_inner):
                    return True

            class FakePresentation:
                def start(self_inner):
                    nonlocal presentation_started
                    presentation_started = True

                def stop(self_inner):
                    return None

            runtime.world_awareness = FakeWorker()
            runtime.presentation = FakePresentation()

            def collect(_context):
                status = liveness.mark_failed("forced during local gate")
                runtime._record_worker_failure(status)

            with patch("personal_cic.runtime.collect_once", side_effect=collect):
                with self.assertRaises(WorkerAuthorityFailure):
                    runtime.run()

            self.assertFalse(presentation_started)
            self.assertFalse((root / "world.json").exists())

    def test_requested_stop_during_worker_start_does_not_run_local_startup_collection(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            runtime = PersistentRuntime(
                self._runtime_config(root),
                Path("config/health.json"),
            )

            class FakeWorker:
                def prepare_reentry(self_inner):
                    return None

                def start(self_inner):
                    runtime.request_stop("test requested during worker start")

                def runtime_status(self_inner):
                    liveness = WorkerLiveness("world-awareness")
                    liveness.mark_starting()
                    liveness.mark_running()
                    return liveness.snapshot()

                def supervision_status(self_inner):
                    liveness = WorkerLiveness("world-awareness")
                    liveness.mark_starting()
                    liveness.mark_running()
                    return liveness.snapshot()

                def stop(self_inner):
                    return True

            class FakePresentation:
                def start(self_inner):
                    return None

                def stop(self_inner):
                    return None

            runtime.world_awareness = FakeWorker()
            runtime.presentation = FakePresentation()

            with patch("personal_cic.runtime.collect_once") as collect:
                runtime.run()

            collect.assert_not_called()

    def test_runtime_metadata_exposes_worker_liveness_without_world_authority(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            runtime = PersistentRuntime(
                self._runtime_config(root),
                Path("config/health.json"),
            )
            self.addCleanup(runtime._durable_lease.release)

            liveness = WorkerLiveness("world-awareness")
            liveness.mark_starting()
            liveness.mark_running()

            class FakeWorker:
                def runtime_status(self_inner):
                    return liveness.snapshot()

            runtime.world_awareness = FakeWorker()
            metadata = runtime._presentation_metadata()
            status = metadata["workers"]["world-awareness"]
            self.assertEqual(status["lifecycle"], "running")
            self.assertNotIn("world_authority", status)


if __name__ == "__main__":
    unittest.main()
