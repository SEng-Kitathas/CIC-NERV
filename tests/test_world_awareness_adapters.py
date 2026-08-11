import json
import unittest
from urllib.error import URLError

from personal_cic.adapters.world import NWSAlertsAdapter, OpenMeteoWeatherAdapter
from personal_cic.core.observations import ObservationStatus
from personal_cic.core.world.components import WeatherAlertState, WeatherForecastState, WeatherState


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self): return self.payload


class WorldAwarenessAdapterTests(unittest.TestCase):
    def test_open_meteo_parses_current_and_daily_forecast(self):
        payload = {
            "timezone": "America/New_York",
            "current": {
                "time": "2026-08-11T18:00",
                "temperature_2m": 88.2,
                "relative_humidity_2m": 55,
                "apparent_temperature": 91.0,
                "precipitation": 0.0,
                "weather_code": 2,
                "cloud_cover": 42,
                "wind_speed_10m": 7.2,
                "wind_direction_10m": 210,
                "wind_gusts_10m": 13.4,
            },
            "daily": {
                "time": ["2026-08-11", "2026-08-12"],
                "temperature_2m_max": [91.0, 90.0],
                "temperature_2m_min": [72.0, 71.0],
                "precipitation_probability_max": [40, 30],
                "sunrise": ["2026-08-11T06:39", "2026-08-12T06:40"],
                "sunset": ["2026-08-11T20:18", "2026-08-12T20:17"],
            },
        }
        adapter = OpenMeteoWeatherAdapter(
            location_label="Test",
            latitude=35.1,
            longitude=-80.6,
            opener=lambda *_args, **_kwargs: _Response(payload),
        )
        observations = adapter.collect()
        self.assertEqual([o.status for o in observations], [ObservationStatus.OBSERVED, ObservationStatus.OBSERVED])
        self.assertIsInstance(observations[0].value, WeatherState)
        self.assertIsInstance(observations[1].value, WeatherForecastState)
        self.assertEqual(observations[0].value.weather_code, 2)
        self.assertEqual(observations[0].value.provider_timezone, "America/New_York")
        self.assertEqual(observations[1].value.high_f, 91.0)

    def test_open_meteo_network_failure_is_unavailable_without_domain_value(self):
        def fail(*_args, **_kwargs): raise URLError("offline")
        adapter = OpenMeteoWeatherAdapter(location_label="Test", latitude=35.1, longitude=-80.6, opener=fail)
        observations = adapter.collect()
        self.assertTrue(all(o.status is ObservationStatus.UNAVAILABLE for o in observations))
        self.assertTrue(all(o.value is None for o in observations))

    def test_nws_alerts_parses_and_sorts_by_severity(self):
        payload = {
            "updated": "2026-08-11T22:00:00+00:00",
            "features": [
                {"id": "minor", "properties": {"event": "Heat Advisory", "severity": "Minor", "urgency": "Expected", "headline": "Minor alert", "sent": "2026-08-11T20:00:00+00:00"}},
                {"id": "severe", "properties": {"event": "Severe Thunderstorm Warning", "severity": "Severe", "urgency": "Immediate", "headline": "Severe alert", "sent": "2026-08-11T21:00:00+00:00"}},
            ],
        }
        adapter = NWSAlertsAdapter(
            location_label="Test",
            latitude=35.1,
            longitude=-80.6,
            user_agent="CIC Test",
            opener=lambda *_args, **_kwargs: _Response(payload),
        )
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        self.assertIsInstance(observation.value, WeatherAlertState)
        self.assertEqual(observation.value.active_count, 2)
        self.assertEqual(observation.value.highest_severity, "Severe")
        self.assertEqual(observation.value.alerts[0].alert_id, "severe")

    def test_nws_empty_active_result_is_successful_negative_evidence(self):
        adapter = NWSAlertsAdapter(
            location_label="Test",
            latitude=35.1,
            longitude=-80.6,
            user_agent="CIC Test",
            opener=lambda *_args, **_kwargs: _Response({"updated": "now", "features": []}),
        )
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        self.assertEqual(observation.value.active_count, 0)
        self.assertEqual(observation.value.alerts, ())
    def test_nws_malformed_success_response_is_not_negative_evidence(self):
        adapter = NWSAlertsAdapter(
            location_label="Test",
            latitude=35.1,
            longitude=-80.6,
            user_agent="CIC Test",
            opener=lambda *_args, **_kwargs: _Response({"updated": "now"}),
        )
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
        self.assertIsNone(observation.value)
