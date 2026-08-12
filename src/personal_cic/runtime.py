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
            )
        if self.runtime_config.world_awareness.enabled:
            self.world_awareness = WorldAwarenessWorker(
                context=self.context,
                config=self.runtime_config.world_awareness,
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
                )

    def request_stop(self, reason: str) -> None:
        self.stop_reason = reason
        self.stop_event.set()

    def _presentation_metadata(self) -> dict:
        return {
            "pid": os.getpid(),
            "started_at": self._runtime_started_at,
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

    def run(self) -> None:
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
            if self.presentation is not None:
                self.presentation.start()
            if self.world_awareness is not None:
                self.world_awareness.start()
            if self.traffic_awareness is not None:
                self.traffic_awareness.start()

            while not self.stop_event.is_set():
                cycle_started = time.monotonic()
                collect_once(self.context)
                self._snapshot_if_due()

                elapsed = time.monotonic() - cycle_started
                wait_for = max(
                    0.0,
                    self.runtime_config.collection_interval_seconds - elapsed,
                )
                self.stop_event.wait(wait_for)
        finally:
            if self.traffic_awareness is not None:
                self.traffic_awareness.stop()
            if self.world_awareness is not None:
                self.world_awareness.stop()
            if self.presentation is not None:
                self.presentation.stop()
            self._snapshot_if_due(force=True)
            self.events.publish(RuntimeStopping(reason=self.stop_reason))


def main() -> None:
    parser = ArgumentParser(description="Personal CIC persistent runtime")
    parser.add_argument(
        "--config",
        default="config/runtime.json",
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
