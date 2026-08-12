import unittest

from personal_cic.bootstrap import create_context, ingest_observation_batch
from personal_cic.core.config import WorldAwarenessConfig
from personal_cic.core.observations import Observation, ObservationAvailability
from personal_cic.world_awareness import WorldAwarenessWorker
from personal_cic.core.world.components import ObservationState, WeatherState


class WorldAwarenessIngestTests(unittest.TestCase):
    def test_unavailable_remote_fetch_preserves_last_known_weather(self):
        context = create_context()
        context.world.ensure_entity("local-weather", "Local Weather")
        prior = WeatherState("Test", "Open-Meteo", "t0", "America/New_York", 80.0, 81.0, 50.0, 0.0, 1, 20.0, 5.0, 180.0, 8.0)
        ingest_observation_batch(context, entity_id="local-weather", adapter_id="openmeteo.weather", observations=(Observation.observed("openmeteo.current", prior),), publish_cycle=False)
        ingest_observation_batch(context, entity_id="local-weather", adapter_id="openmeteo.weather", observations=(Observation.unavailable("openmeteo.current", "offline"),), publish_cycle=False)
        self.assertEqual(context.world.get_component("local-weather", WeatherState), prior)
        observation=context.world.get_component("local-weather", ObservationState)
        self.assertEqual(observation.availability, ObservationAvailability.UNAVAILABLE)
        self.assertIn("offline", observation.reasons[0])

    def test_reentry_preserves_last_known_weather_but_withdraws_current_authority(self):
        context = create_context()
        context.world.ensure_entity("local-weather", "Local Weather")
        context.world.ensure_entity("local-weather-alerts", "Local Weather Alerts")

        prior = WeatherState(
            "Test",
            "Open-Meteo",
            "t0",
            "America/New_York",
            80.0,
            81.0,
            50.0,
            0.0,
            1,
            20.0,
            5.0,
            180.0,
            8.0,
        )

        ingest_observation_batch(
            context,
            entity_id="local-weather",
            adapter_id="openmeteo.weather",
            observations=(Observation.observed("openmeteo.current", prior),),
            publish_cycle=False,
        )
        before = context.world.get_component("local-weather", ObservationState)

        worker = WorldAwarenessWorker(
            context=context,
            config=WorldAwarenessConfig.from_mapping({"enabled": True}),
        )
        worker.prepare_reentry()

        self.assertEqual(
            context.world.get_component("local-weather", WeatherState),
            prior,
        )
        after = context.world.get_component("local-weather", ObservationState)
        self.assertEqual(after.availability, ObservationAvailability.UNAVAILABLE)
        self.assertEqual(after.last_success_at, before.last_success_at)
        self.assertIn("awaiting fresh Open-Meteo observation", after.reasons[0])

        alerts_obs = context.world.get_component(
            "local-weather-alerts",
            ObservationState,
        )
        self.assertEqual(
            alerts_obs.availability,
            ObservationAvailability.UNAVAILABLE,
        )
        self.assertIn("awaiting fresh NWS alert observation", alerts_obs.reasons[0])

        for entity_id, reason in (("local-weather-surface", "awaiting fresh AviationWeather METAR observation"), ("local-weather-nws-forecast", "awaiting fresh NWS hourly forecast"), ("local-weather-estimate", "awaiting fresh current-weather source")):
            state = context.world.get_component(entity_id, ObservationState)
            self.assertEqual(state.availability, ObservationAvailability.UNAVAILABLE)
            self.assertIn(reason, state.reasons[0])
