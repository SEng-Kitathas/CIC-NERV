from argparse import ArgumentParser
from pathlib import Path
import os
import signal
import threading
import time

from personal_cic.bootstrap import collect_once, create_context, reconcile_topology
from personal_cic.core.config import RuntimeConfig
from personal_cic.core.events import EventBus, EventJournal, RuntimeStarted, RuntimeStopping
from personal_cic.core.events import utc_now_iso
from personal_cic.presentation import PresentationServer
from personal_cic.runtime_authority import (
    DurableStateLease,
    WorkerAuthorityFailure,
    WorkerLifecycle,
    WorkerRuntimeStatus,
)
from personal_cic.world_awareness import WorldAwarenessWorker
from personal_cic.traffic_awareness import TrafficAwarenessWorker


class PersistentRuntime:
    def __init__(
        self,
        runtime_config_path: Path,
        health_config_path: Path,
    ) -> None:
        self.runtime_config_path = runtime_config_path
        self.runtime_config = RuntimeConfig.load(runtime_config_path)
        self._durable_lease = DurableStateLease(self.runtime_config.state_path)
        self._durable_lease.acquire()

        try:
            self.events = EventBus()
            self.journal = EventJournal(self.runtime_config.event_journal_path)
            self.context = create_context(
                events=self.events,
                health_config_path=health_config_path,
                restore_state_path=self.runtime_config.state_path,
            )
            self.stop_event = threading.Event()
            self.stop_reason = "requested"
            self._last_snapshot_monotonic = 0.0
            self._runtime_started_at: str | None = None
            self._worker_failure_lock = threading.Lock()
            self._worker_failure: WorkerRuntimeStatus | None = None
            self.presentation: PresentationServer | None = None
            self.world_awareness: WorldAwarenessWorker | None = None
            self.traffic_awareness: TrafficAwarenessWorker | None = None
            if self.runtime_config.presentation.enabled:
                self.presentation = PresentationServer(
                    world=self.context.world,
                    host=self.runtime_config.presentation.bind_host,
                    port=self.runtime_config.presentation.port,
                    runtime_metadata=self._presentation_metadata,
                    event_journal_path=self.runtime_config.event_journal_path,
                    radar_cache_dir=self.runtime_config.world_awareness.radar.cache_dir,
                    site_anchor=self.runtime_config.operator_context.site_anchor,
                )
            if self.runtime_config.world_awareness.enabled:
                self.world_awareness = WorldAwarenessWorker(
                    context=self.context,
                    config=self.runtime_config.world_awareness,
                    on_terminal_failure=self._record_worker_failure,
                )
                traffic = self.runtime_config.world_awareness.traffic
                if traffic.enabled:
                    location = self.runtime_config.world_awareness.location
                    self.traffic_awareness = TrafficAwarenessWorker(
                        context=self.context,
                        config=traffic,
                        location_label=location.label,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        on_terminal_failure=self._record_worker_failure,
                    )
        except Exception:
            self._durable_lease.release()
            raise

    def request_stop(self, reason: str) -> None:
        self.stop_reason = reason
        self.stop_event.set()

    def _worker_statuses(self) -> tuple[WorkerRuntimeStatus, ...]:
        statuses: list[WorkerRuntimeStatus] = []
        for worker in (self.world_awareness, self.traffic_awareness):
            if worker is not None:
                statuses.append(worker.runtime_status())
        return tuple(statuses)

    def _record_worker_failure(self, status: WorkerRuntimeStatus) -> None:
        with self._worker_failure_lock:
            if self._worker_failure is None:
                self._worker_failure = status
                self.stop_reason = (
                    f"enabled collection worker failed: {status.name}: "
                    f"{status.terminal_failure or 'unknown terminal failure'}"
                )
        self.stop_event.set()

    def _raise_if_worker_failed(self) -> None:
        for worker in (self.world_awareness, self.traffic_awareness):
            if worker is None:
                continue
            status = worker.supervision_status()
            if status.lifecycle is WorkerLifecycle.FAILED:
                self._record_worker_failure(status)

        with self._worker_failure_lock:
            failure = self._worker_failure
        if failure is not None:
            raise WorkerAuthorityFailure(
                f"{failure.name}: "
                f"{failure.terminal_failure or 'worker no longer alive'}"
            )

    def _presentation_metadata(self) -> dict:
        return {
            "pid": os.getpid(),
            "started_at": self._runtime_started_at,
            "workers": {
                status.name: status.as_dict()
                for status in self._worker_statuses()
            },
        }

    def _snapshot_if_due(self, force: bool = False) -> None:
        now = time.monotonic()
        due = (
            now - self._last_snapshot_monotonic
            >= self.runtime_config.snapshot_interval_seconds
        )
        if force or due:
            self.context.world.write_json(self.runtime_config.state_path)
            self._last_snapshot_monotonic = now

    def _run_owned(self) -> None:
        # Attach the durable observer only after silent state hydration. The first
        # new event of this process lifetime is therefore RuntimeStarted.
        self.events.observe_all(self.journal.record)
        self._runtime_started_at = utc_now_iso()
        self.events.publish(
            RuntimeStarted(
                pid=os.getpid(),
                config_path=str(self.runtime_config_path),
                restored_entities=self.context.restored_entities,
            )
        )
        reconcile_topology(self.context)

        # Re-entry gate: presentation must never expose persisted remote CURRENT
        # authority before fresh provider observation has been attempted.
        if self.world_awareness is not None:
            self.world_awareness.prepare_reentry()
        if self.traffic_awareness is not None:
            self.traffic_awareness.prepare_reentry()

        try:
            # Start and supervise enabled collection mechanisms before opening the
            # presentation surface. Re-entry has already withdrawn persisted remote
            # authority, so early collection is safe while immediate worker failure
            # cannot briefly expose an apparently healthy operator surface.
            if self.world_awareness is not None:
                self.world_awareness.start()
                self._raise_if_worker_failed()
            if self.traffic_awareness is not None:
                self.traffic_awareness.start()
                self._raise_if_worker_failed()
            if self.presentation is not None:
                self.presentation.start()

            self._raise_if_worker_failed()
            while not self.stop_event.is_set():
                cycle_started = time.monotonic()
                self._raise_if_worker_failed()
                collect_once(self.context)
                self._snapshot_if_due()
                self._raise_if_worker_failed()

                elapsed = time.monotonic() - cycle_started
                wait_for = max(
                    0.0,
                    self.runtime_config.collection_interval_seconds - elapsed,
                )
                self.stop_event.wait(wait_for)

            # A worker callback wakes the main loop immediately. Do not convert
            # that terminal failure into a normal requested stop merely because
            # the stop event is also the wake-up primitive.
            self._raise_if_worker_failed()
        finally:
            incomplete_workers: list[str] = []
            if self.traffic_awareness is not None and not self.traffic_awareness.stop():
                incomplete_workers.append("traffic-awareness")
            if self.world_awareness is not None and not self.world_awareness.stop():
                incomplete_workers.append("world-awareness")
            if self.presentation is not None:
                self.presentation.stop()

            with self._worker_failure_lock:
                worker_failure = self._worker_failure

            stopping_reason = self.stop_reason
            if incomplete_workers:
                stopping_reason = (
                    f"{self.stop_reason}; incomplete worker shutdown: "
                    + ", ".join(incomplete_workers)
                )
                # A remote worker can still mutate WorldState until the process
                # exits. Skipping the forced snapshot is safer than persisting a
                # state while falsely claiming graceful quiescence.
            elif worker_failure is not None:
                # The last clean periodic snapshot may contain retained/current
                # remote state, but startup re-entry withdraws that authority before
                # presentation. Do not create a new final snapshot that could be
                # mistaken for a gracefully quiesced runtime after worker failure.
                stopping_reason = self.stop_reason
            else:
                self._snapshot_if_due(force=True)
            self.events.publish(RuntimeStopping(reason=stopping_reason))

    def run(self) -> None:
        try:
            self._run_owned()
        finally:
            self._durable_lease.release()




def default_runtime_config_path() -> Path:
    # Configuration intent is deployment-local mutable state.
    config_home = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    return config_home / 'personal-cic' / 'runtime.json'


def main() -> None:
    parser = ArgumentParser(description="Personal CIC persistent runtime")
    parser.add_argument(
        "--config",
        default=str(default_runtime_config_path()),
        help="runtime configuration file",
    )
    parser.add_argument(
        "--health-config",
        default="config/health.json",
        help="health threshold configuration file",
    )
    args = parser.parse_args()

    runtime = PersistentRuntime(
        runtime_config_path=Path(args.config),
        health_config_path=Path(args.health_config),
    )

    def stop_for_signal(signum, _frame):
        runtime.request_stop(signal.Signals(signum).name)

    signal.signal(signal.SIGINT, stop_for_signal)
    signal.signal(signal.SIGTERM, stop_for_signal)

    runtime.run()


if __name__ == "__main__":
    main()
