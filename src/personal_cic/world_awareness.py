from __future__ import annotations

from datetime import datetime, timezone
import threading
import time

from personal_cic.adapters.world import (
    AviationSurfaceAdapter,
    NWSAlertsAdapter,
    NWSHourlyForecastAdapter,
    OpenMeteoWeatherAdapter,
    MRMSRadarMosaicAdapter,
    TIGERRadarContextAdapter,
)
from personal_cic.bootstrap import RuntimeContext, ingest_observation_batch
from personal_cic.core.config import WorldAwarenessConfig
from personal_cic.core.observations import (
    Observation,
    ObservationAvailability,
    ObservationStatus,
)
from personal_cic.core.world.components import (
    NWSHourlyForecastState,
    ObservationState,
    SurfaceObservationNetworkState,
    WeatherState,
)
from personal_cic.weather_fusion import derive_current_weather_estimate


WEATHER_ENTITY_ID = "local-weather"
ALERTS_ENTITY_ID = "local-weather-alerts"
SURFACE_ENTITY_ID = "local-weather-surface"
FORECAST_ENTITY_ID = "local-weather-nws-forecast"
ESTIMATE_ENTITY_ID = "local-weather-estimate"
RADAR_ENTITY_ID = "local-weather-radar"
RADAR_CONTEXT_ENTITY_ID = "local-weather-radar-context"


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
        self.surface_adapter = AviationSurfaceAdapter(
            location_label=loc.label,
            latitude=loc.latitude,
            longitude=loc.longitude,
            station_ids=config.surface.station_ids,
            user_agent=config.surface.user_agent,
            max_age_minutes=config.surface.max_age_minutes,
            timeout_seconds=config.surface.timeout_seconds,
        )
        self.forecast_adapter = NWSHourlyForecastAdapter(
            location_label=loc.label,
            latitude=loc.latitude,
            longitude=loc.longitude,
            user_agent=config.forecast.user_agent,
            points_refresh_seconds=config.forecast.points_refresh_seconds,
            timeout_seconds=config.forecast.timeout_seconds,
        )
        self.radar_adapter = MRMSRadarMosaicAdapter(
            location_label=loc.label,
            latitude=loc.latitude,
            longitude=loc.longitude,
            range_miles=config.radar.range_miles,
            image_width=config.radar.image_width,
            image_height=config.radar.image_height,
            max_age_minutes=config.radar.max_age_minutes,
            cache_dir=config.radar.cache_dir,
            loop_frame_capacity=config.radar.loop_frame_capacity,
            user_agent=config.radar.user_agent,
            timeout_seconds=config.radar.timeout_seconds,
        )
        self.radar_context_adapter = TIGERRadarContextAdapter(
            location_label=loc.label,
            latitude=loc.latitude,
            longitude=loc.longitude,
            range_miles=config.radar.range_miles,
            image_width=config.radar.image_width,
            image_height=config.radar.image_height,
            cache_dir=config.radar.cache_dir,
            user_agent=config.radar.user_agent,
            max_age_days=config.radar.context_max_age_days,
            timeout_seconds=config.radar.context_timeout_seconds,
        )
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # Runtime-epoch proof: persisted state cannot use retention to bypass re-entry.
        self._surface_fresh_since_reentry = False

    def _ensure_entities(self) -> None:
        self.context.world.ensure_entity(WEATHER_ENTITY_ID, "Local Weather")
        self.context.world.ensure_entity(ALERTS_ENTITY_ID, "Local Weather Alerts")
        self.context.world.ensure_entity(SURFACE_ENTITY_ID, "Local Surface Observations")
        self.context.world.ensure_entity(FORECAST_ENTITY_ID, "NWS Hourly Forecast")
        self.context.world.ensure_entity(ESTIMATE_ENTITY_ID, "Current Weather Estimate")
        self.context.world.ensure_entity(RADAR_ENTITY_ID, "Local Radar Mosaic")
        self.context.world.ensure_entity(RADAR_CONTEXT_ENTITY_ID, "Local Radar Context")

    def _withdraw(self, entity_id: str, adapter_id: str, reason: str) -> None:
        ingest_observation_batch(
            self.context,
            entity_id=entity_id,
            adapter_id=adapter_id,
            observations=(Observation.unavailable("reentry", reason),),
            publish_cycle=False,
        )

    def prepare_reentry(self) -> None:
        if not self.config.enabled:
            return
        self._surface_fresh_since_reentry = False
        self._ensure_entities()
        if self.config.weather.enabled:
            self._withdraw(WEATHER_ENTITY_ID, self.weather_adapter.ADAPTER_ID, "awaiting fresh Open-Meteo observation")
        if self.config.alerts.enabled:
            self._withdraw(ALERTS_ENTITY_ID, self.alerts_adapter.ADAPTER_ID, "awaiting fresh NWS alert observation")
        if self.config.surface.enabled:
            self._withdraw(SURFACE_ENTITY_ID, self.surface_adapter.ADAPTER_ID, "awaiting fresh AviationWeather METAR observation")
        if self.config.forecast.enabled:
            self._withdraw(FORECAST_ENTITY_ID, self.forecast_adapter.ADAPTER_ID, "awaiting fresh NWS hourly forecast")
        if self.config.radar.enabled:
            self._withdraw(RADAR_ENTITY_ID, self.radar_adapter.ADAPTER_ID, "awaiting fresh MRMS radar observation")
        if self.config.radar.enabled and self.config.radar.context_enabled:
            self._withdraw(
                RADAR_CONTEXT_ENTITY_ID,
                self.radar_context_adapter.ADAPTER_ID,
                "awaiting fresh TIGERweb radar context observation",
            )
        self._withdraw(ESTIMATE_ENTITY_ID, "weather.fusion", "awaiting fresh current-weather source")

    def start(self) -> None:
        if not self.config.enabled or self._thread is not None:
            return
        self._ensure_entities()
        self._thread = threading.Thread(target=self._run, name="personal-cic-world-awareness", daemon=True)
        self._thread.start()

    def stop(self) -> bool:
        """Request bounded shutdown and report whether the worker actually stopped.

        A timeout is not success. Keep the live thread reference when a provider
        call outlives the join budget so runtime shutdown can avoid claiming a
        race-free final snapshot.
        """
        self._stop.set()
        thread = self._thread
        if thread is None:
            return True
        timeout = max(
            self.config.weather.timeout_seconds,
            self.config.alerts.timeout_seconds,
            self.config.surface.timeout_seconds,
            self.config.forecast.timeout_seconds * 2,
            self.config.radar.timeout_seconds * 4,
            self.config.radar.context_timeout_seconds * 2,
        ) + 2.0
        thread.join(timeout=timeout)
        stopped = not thread.is_alive()
        if stopped:
            self._thread = None
        return stopped

    def _recompute_estimate(self) -> None:
        surface = self.context.world.get_component(SURFACE_ENTITY_ID, SurfaceObservationNetworkState)
        surface_obs = self.context.world.get_component(SURFACE_ENTITY_ID, ObservationState)
        weather = self.context.world.get_component(WEATHER_ENTITY_ID, WeatherState)
        weather_obs = self.context.world.get_component(WEATHER_ENTITY_ID, ObservationState)
        forecast = self.context.world.get_component(FORECAST_ENTITY_ID, NWSHourlyForecastState)
        forecast_obs = self.context.world.get_component(FORECAST_ENTITY_ID, ObservationState)
        state = derive_current_weather_estimate(
            location_label=self.config.location.label,
            surface=surface,
            surface_usable=bool(
                surface_obs
                and surface_obs.availability in (
                    ObservationAvailability.CURRENT,
                    ObservationAvailability.DEGRADED,
                )
            ),
            open_meteo=weather,
            open_meteo_current=bool(weather_obs and weather_obs.availability is ObservationAvailability.CURRENT),
            nws_forecast=forecast,
            nws_current=bool(forecast_obs and forecast_obs.availability is ObservationAvailability.CURRENT),
        )
        if state is None:
            observations = (Observation.unavailable("weather.fusion", "no current source available for current-weather estimate"),)
        else:
            observations = (Observation.observed("weather.fusion", state),)
        ingest_observation_batch(
            self.context,
            entity_id=ESTIMATE_ENTITY_ID,
            adapter_id="weather.fusion",
            observations=observations,
            publish_cycle=False,
        )

    def _collect_weather(self) -> None:
        ingest_observation_batch(self.context, entity_id=WEATHER_ENTITY_ID, adapter_id=self.weather_adapter.ADAPTER_ID, observations=self.weather_adapter.collect(), publish_cycle=False)
        self._recompute_estimate()

    def _collect_alerts(self) -> None:
        ingest_observation_batch(self.context, entity_id=ALERTS_ENTITY_ID, adapter_id=self.alerts_adapter.ADAPTER_ID, observations=self.alerts_adapter.collect(), publish_cycle=False)

    @staticmethod
    def _parse_time(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _surface_retention_is_earned(self) -> bool:
        """Return true only for fresh-enough METAR state observed in this runtime epoch."""
        if not self._surface_fresh_since_reentry:
            return False
        state = self.context.world.get_component(
            SURFACE_ENTITY_ID,
            SurfaceObservationNetworkState,
        )
        if state is None:
            return False
        freshest = self._parse_time(state.freshest_observed_at)
        if freshest is None:
            return False
        age_minutes = (
            datetime.now(timezone.utc) - freshest
        ).total_seconds() / 60.0
        return -5.0 <= age_minutes <= self.config.surface.max_age_minutes

    def _collect_surface(self) -> None:
        observations = self.surface_adapter.collect()
        fresh = any(
            observation.status in (ObservationStatus.OBSERVED, ObservationStatus.PARTIAL)
            for observation in observations
        )
        failed = bool(observations) and all(
            observation.status is ObservationStatus.UNAVAILABLE
            for observation in observations
        )

        if fresh:
            self._surface_fresh_since_reentry = True
        elif failed and self._surface_retention_is_earned():
            raw_detail = next(
                (observation.detail for observation in observations if observation.detail),
                "surface retrieval failed",
            )
            observations = (
                Observation.retained(
                    "aviationweather.metar",
                    "retained: latest METAR retrieval failed; last-known surface "
                    f"observation remains inside the configured {self.config.surface.max_age_minutes:g} minute "
                    f"freshness window // {raw_detail}",
                ),
            )

        ingest_observation_batch(
            self.context,
            entity_id=SURFACE_ENTITY_ID,
            adapter_id=self.surface_adapter.ADAPTER_ID,
            observations=observations,
            publish_cycle=False,
        )
        self._recompute_estimate()

    def _collect_forecast(self) -> None:
        ingest_observation_batch(self.context, entity_id=FORECAST_ENTITY_ID, adapter_id=self.forecast_adapter.ADAPTER_ID, observations=self.forecast_adapter.collect(), publish_cycle=False)
        self._recompute_estimate()

    def _collect_radar(self) -> None:
        ingest_observation_batch(
            self.context,
            entity_id=RADAR_ENTITY_ID,
            adapter_id=self.radar_adapter.ADAPTER_ID,
            observations=self.radar_adapter.collect(),
            publish_cycle=False,
        )

    def _collect_radar_context(self) -> None:
        ingest_observation_batch(
            self.context,
            entity_id=RADAR_CONTEXT_ENTITY_ID,
            adapter_id=self.radar_context_adapter.ADAPTER_ID,
            observations=self.radar_context_adapter.collect(),
            publish_cycle=False,
        )

    def _run(self) -> None:
        next_due = {"alerts": 0.0, "surface": 0.0, "weather": 0.0, "forecast": 0.0, "radar": 0.0, "radar_context": 0.0}
        intervals = {
            "alerts": self.config.alerts.interval_seconds,
            "surface": self.config.surface.interval_seconds,
            "weather": self.config.weather.interval_seconds,
            "forecast": self.config.forecast.interval_seconds,
            "radar": self.config.radar.interval_seconds,
            "radar_context": self.config.radar.context_interval_seconds,
        }
        enabled = {
            "alerts": self.config.alerts.enabled,
            "surface": self.config.surface.enabled,
            "weather": self.config.weather.enabled,
            "forecast": self.config.forecast.enabled,
            "radar": self.config.radar.enabled,
            "radar_context": self.config.radar.enabled and self.config.radar.context_enabled,
        }
        collectors = {
            "alerts": self._collect_alerts,
            "surface": self._collect_surface,
            "weather": self._collect_weather,
            "forecast": self._collect_forecast,
            "radar": self._collect_radar,
            "radar_context": self._collect_radar_context,
        }

        while not self._stop.is_set():
            now = time.monotonic()
            for name in ("alerts", "surface", "weather", "forecast", "radar", "radar_context"):
                if not enabled[name] or now < next_due[name]:
                    continue
                collectors[name]()
                next_due[name] = time.monotonic() + intervals[name]
                if self._stop.is_set():
                    break
                now = time.monotonic()

            due = [next_due[name] for name in next_due if enabled[name]]
            wait_for = 1.0 if not due else max(0.1, min(due) - time.monotonic())
            self._stop.wait(min(wait_for, 1.0))
