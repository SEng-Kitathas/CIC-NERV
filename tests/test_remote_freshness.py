import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from personal_cic.bootstrap import create_context, ingest_observation_batch
from personal_cic.core.config import WorldAwarenessConfig
from personal_cic.core.observations import (
    Observation,
    ObservationAvailability,
    ObservationStatus,
)
from personal_cic.core.world.components import (
    CurrentWeatherEstimateState,
    ObservationState,
    SurfaceObservationNetworkState,
    SurfaceStationObservation,
    WeatherState,
)
from personal_cic.world_awareness import (
    ESTIMATE_ENTITY_ID,
    SURFACE_ENTITY_ID,
    WEATHER_ENTITY_ID,
    WorldAwarenessWorker,
)


def _surface_state(observed_at: str) -> SurfaceObservationNetworkState:
    station = SurfaceStationObservation(
        "KEQY",
        "Monroe",
        observed_at,
        35.0,
        -80.6,
        6.7,
        73.0,
        71.0,
        93.0,
        40.0,
        4.6,
        None,
        10.0,
        30.05,
        1017.5,
        11000,
        "VFR",
        None,
        "raw",
    )
    return SurfaceObservationNetworkState(
        "Test",
        "NOAA/NWS AviationWeather.gov METAR",
        observed_at,
        "KEQY",
        1,
        73.0,
        71.0,
        93.0,
        0.0,
        (station,),
    )


def _open_meteo() -> WeatherState:
    return WeatherState(
        "Test",
        "Open-Meteo",
        "2026-08-12T03:00:00+00:00",
        "America/New_York",
        76.0,
        78.0,
        90.0,
        0.0,
        3,
        90.0,
        5.0,
        180.0,
        10.0,
    )


class RemoteFreshnessTests(unittest.TestCase):
    def _worker(self, *, max_age_minutes=90.0):
        context = create_context()
        config = WorldAwarenessConfig.from_mapping(
            {
                "enabled": True,
                "surface": {
                    "enabled": True,
                    "interval_seconds": 60,
                    "max_age_minutes": max_age_minutes,
                },
            }
        )
        worker = WorldAwarenessWorker(context=context, config=config)
        worker._ensure_entities()
        ingest_observation_batch(
            context,
            entity_id=WEATHER_ENTITY_ID,
            adapter_id="openmeteo.weather",
            observations=(Observation.observed("openmeteo.current", _open_meteo()),),
            publish_cycle=False,
        )
        return context, worker

    def test_retained_observation_is_degraded_without_new_domain_value_or_success_time(self):
        context, _ = self._worker()
        now = datetime.now(timezone.utc).isoformat()
        prior = _surface_state(now)
        ingest_observation_batch(
            context,
            entity_id=SURFACE_ENTITY_ID,
            adapter_id="aviationweather.metar",
            observations=(Observation.observed("aviationweather.metar", prior),),
            publish_cycle=False,
        )
        before = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)

        retained = Observation.retained(
            "aviationweather.metar",
            "retained: transient retrieval failure",
        )
        self.assertEqual(retained.status, ObservationStatus.RETAINED)
        ingest_observation_batch(
            context,
            entity_id=SURFACE_ENTITY_ID,
            adapter_id="aviationweather.metar",
            observations=(retained,),
            publish_cycle=False,
        )

        after = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)
        self.assertEqual(after.availability, ObservationAvailability.DEGRADED)
        self.assertEqual(after.last_success_at, before.last_success_at)
        self.assertEqual(context.world.get_component(SURFACE_ENTITY_ID, SurfaceObservationNetworkState), prior)

    def test_transient_metar_failure_retains_fresh_surface_and_does_not_flip_fusion_source(self):
        context, worker = self._worker()
        now = datetime.now(timezone.utc).isoformat()
        surface = _surface_state(now)

        worker.surface_adapter.collect = lambda: (
            Observation.observed("aviationweather.metar", surface),
        )
        worker._collect_surface()
        estimate_before = context.world.get_component(ESTIMATE_ENTITY_ID, CurrentWeatherEstimateState)
        self.assertEqual(estimate_before.primary_source, "NOAA/NWS AviationWeather.gov METAR")
        self.assertTrue(worker._surface_fresh_since_reentry)

        worker.surface_adapter.collect = lambda: (
            Observation.unavailable(
                "aviationweather.metar",
                "METAR request failed: The read operation timed out",
            ),
        )
        worker._collect_surface()

        surface_obs = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)
        estimate_after = context.world.get_component(ESTIMATE_ENTITY_ID, CurrentWeatherEstimateState)
        estimate_obs = context.world.get_component(ESTIMATE_ENTITY_ID, ObservationState)

        self.assertEqual(surface_obs.availability, ObservationAvailability.DEGRADED)
        self.assertIn("retained:", surface_obs.reasons[0])
        self.assertEqual(estimate_obs.availability, ObservationAvailability.CURRENT)
        self.assertEqual(estimate_after.primary_source, "NOAA/NWS AviationWeather.gov METAR")
        self.assertEqual(estimate_after.method, "surface_median + nearest_station_context")

    def test_retention_cannot_bypass_reentry_before_fresh_runtime_success(self):
        context, worker = self._worker()
        now = datetime.now(timezone.utc).isoformat()
        surface = _surface_state(now)
        ingest_observation_batch(
            context,
            entity_id=SURFACE_ENTITY_ID,
            adapter_id="aviationweather.metar",
            observations=(Observation.observed("aviationweather.metar", surface),),
            publish_cycle=False,
        )

        worker.prepare_reentry()
        self.assertFalse(worker._surface_fresh_since_reentry)
        # A different provider may freshly re-earn its own authority; this must
        # not allow persisted METAR state to bypass the surface re-entry gate.
        ingest_observation_batch(
            context,
            entity_id=WEATHER_ENTITY_ID,
            adapter_id="openmeteo.weather",
            observations=(Observation.observed("openmeteo.current", _open_meteo()),),
            publish_cycle=False,
        )
        worker.surface_adapter.collect = lambda: (
            Observation.unavailable(
                "aviationweather.metar",
                "METAR request failed: timeout",
            ),
        )
        worker._collect_surface()

        surface_obs = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)
        estimate = context.world.get_component(ESTIMATE_ENTITY_ID, CurrentWeatherEstimateState)
        self.assertEqual(surface_obs.availability, ObservationAvailability.UNAVAILABLE)
        self.assertEqual(estimate.primary_source, "Open-Meteo")

    def test_retained_surface_expires_by_domain_report_age_not_failure_count(self):
        context, worker = self._worker(max_age_minutes=1.0)
        now = datetime.now(timezone.utc)
        fresh = _surface_state(now.isoformat())

        worker.surface_adapter.collect = lambda: (
            Observation.observed("aviationweather.metar", fresh),
        )
        worker._collect_surface()
        self.assertTrue(worker._surface_fresh_since_reentry)

        stale = replace(
            fresh,
            freshest_observed_at=(now - timedelta(minutes=2)).isoformat(),
            stations=(replace(fresh.stations[0], observed_at=(now - timedelta(minutes=2)).isoformat()),),
        )
        context.world.upsert_component(SURFACE_ENTITY_ID, stale, significance="sample")

        worker.surface_adapter.collect = lambda: (
            Observation.unavailable(
                "aviationweather.metar",
                "METAR request failed: timeout",
            ),
        )
        worker._collect_surface()

        surface_obs = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)
        estimate = context.world.get_component(ESTIMATE_ENTITY_ID, CurrentWeatherEstimateState)
        self.assertEqual(surface_obs.availability, ObservationAvailability.UNAVAILABLE)
        self.assertEqual(estimate.primary_source, "Open-Meteo")


    def test_prepare_reentry_revokes_previously_earned_surface_retention(self):
        context, worker = self._worker()
        now = datetime.now(timezone.utc).isoformat()
        surface = _surface_state(now)
        worker.surface_adapter.collect = lambda: (
            Observation.observed("aviationweather.metar", surface),
        )
        worker._collect_surface()
        self.assertTrue(worker._surface_fresh_since_reentry)

        worker.prepare_reentry()

        self.assertFalse(worker._surface_fresh_since_reentry)
        surface_obs = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)
        self.assertEqual(surface_obs.availability, ObservationAvailability.UNAVAILABLE)
        self.assertIn("awaiting fresh AviationWeather METAR observation", surface_obs.reasons[0])

    def test_repeated_retained_failures_do_not_advance_last_success(self):
        context, worker = self._worker()
        now = datetime.now(timezone.utc).isoformat()
        surface = _surface_state(now)
        worker.surface_adapter.collect = lambda: (
            Observation.observed("aviationweather.metar", surface),
        )
        worker._collect_surface()
        first = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)

        worker.surface_adapter.collect = lambda: (
            Observation.unavailable("aviationweather.metar", "METAR request failed: timeout"),
        )
        worker._collect_surface()
        second = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)
        worker._collect_surface()
        third = context.world.get_component(SURFACE_ENTITY_ID, ObservationState)

        self.assertEqual(first.last_success_at, second.last_success_at)
        self.assertEqual(second.last_success_at, third.last_success_at)
        self.assertEqual(third.availability, ObservationAvailability.DEGRADED)


if __name__ == "__main__":
    unittest.main()
