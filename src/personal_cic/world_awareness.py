from __future__ import annotations

import threading
import time

from personal_cic.adapters.world import NWSAlertsAdapter, OpenMeteoWeatherAdapter
from personal_cic.bootstrap import RuntimeContext, ingest_observation_batch
from personal_cic.core.config import WorldAwarenessConfig
from personal_cic.core.observations import Observation


WEATHER_ENTITY_ID = "local-weather"
ALERTS_ENTITY_ID = "local-weather-alerts"


class WorldAwarenessWorker:
    """Slow remote-provider observation loop isolated from local 5-second sensing."""

    def __init__(self, *, context: RuntimeContext, config: WorldAwarenessConfig) -> None:
        self.context = context
        self.config = config
        loc = config.location
        self.weather_adapter = OpenMeteoWeatherAdapter(
            location_label=loc.label,
            latitude=loc.latitude,
            longitude=loc.longitude,
            timeout_seconds=config.weather.timeout_seconds,
        )
        self.alerts_adapter = NWSAlertsAdapter(
            location_label=loc.label,
            latitude=loc.latitude,
            longitude=loc.longitude,
            user_agent=config.alerts.user_agent,
            timeout_seconds=config.alerts.timeout_seconds,
        )
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _ensure_entities(self) -> None:
        self.context.world.ensure_entity(WEATHER_ENTITY_ID, "Local Weather")
        self.context.world.ensure_entity(ALERTS_ENTITY_ID, "Local Weather Alerts")

    def prepare_reentry(self) -> None:
        """Withdraw restored remote freshness before presentation becomes visible.

        Persisted domain values remain available as last-known state, but a process
        restart must not inherit CURRENT authority for remote provider observations.
        Fresh provider requests must re-earn that state.
        """

        if not self.config.enabled:
            return

        self._ensure_entities()

        if self.config.weather.enabled:
            ingest_observation_batch(
                self.context,
                entity_id=WEATHER_ENTITY_ID,
                adapter_id=self.weather_adapter.ADAPTER_ID,
                observations=(
                    Observation.unavailable(
                        "reentry",
                        "awaiting fresh Open-Meteo observation",
                    ),
                ),
                publish_cycle=False,
            )

        if self.config.alerts.enabled:
            ingest_observation_batch(
                self.context,
                entity_id=ALERTS_ENTITY_ID,
                adapter_id=self.alerts_adapter.ADAPTER_ID,
                observations=(
                    Observation.unavailable(
                        "reentry",
                        "awaiting fresh NWS alert observation",
                    ),
                ),
                publish_cycle=False,
            )

    def start(self) -> None:
        if not self.config.enabled or self._thread is not None:
            return
        self._ensure_entities()
        self._thread = threading.Thread(
            target=self._run,
            name="personal-cic-world-awareness",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            timeout = max(
                self.config.weather.timeout_seconds,
                self.config.alerts.timeout_seconds,
            ) + 2.0
            self._thread.join(timeout=timeout)
        self._thread = None

    def _collect_weather(self) -> None:
        ingest_observation_batch(
            self.context,
            entity_id=WEATHER_ENTITY_ID,
            adapter_id=self.weather_adapter.ADAPTER_ID,
            observations=self.weather_adapter.collect(),
            publish_cycle=False,
        )

    def _collect_alerts(self) -> None:
        ingest_observation_batch(
            self.context,
            entity_id=ALERTS_ENTITY_ID,
            adapter_id=self.alerts_adapter.ADAPTER_ID,
            observations=self.alerts_adapter.collect(),
            publish_cycle=False,
        )

    def _run(self) -> None:
        next_weather = 0.0
        next_alerts = 0.0

        while not self._stop.is_set():
            now = time.monotonic()

            if self.config.weather.enabled and now >= next_weather:
                self._collect_weather()
                next_weather = time.monotonic() + self.config.weather.interval_seconds

            if self._stop.is_set():
                break

            if self.config.alerts.enabled and now >= next_alerts:
                self._collect_alerts()
                next_alerts = time.monotonic() + self.config.alerts.interval_seconds

            due = [
                value
                for enabled, value in (
                    (self.config.weather.enabled, next_weather),
                    (self.config.alerts.enabled, next_alerts),
                )
                if enabled
            ]
            wait_for = 1.0 if not due else max(0.1, min(due) - time.monotonic())
            self._stop.wait(min(wait_for, 1.0))
