import json
import unittest
from urllib.error import URLError

from datetime import datetime, timezone

from personal_cic.adapters.world import (
    AviationSurfaceAdapter, NWSAlertsAdapter, NWSHourlyForecastAdapter, OpenMeteoWeatherAdapter,
)
from personal_cic.core.observations import ObservationStatus
from personal_cic.core.world.components import (
    NWSHourlyForecastState, SurfaceObservationNetworkState, WeatherAlertState, WeatherForecastState, WeatherState,
)


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

    def test_aviation_surface_parses_multiple_stations_and_robust_median(self):
        payload = [
            {"icaoId":"KEQY","name":"Monroe","reportTime":"2026-08-11T23:40:00Z","temp":24.0,"dewp":22.0,"wdir":260,"wspd":10,"wgst":18,"visib":"10+","altim":1010.0,"slp":1009.4,"lat":35.02,"lon":-80.62,"fltCat":"VFR","wxString":"-RA","rawOb":"KEQY TEST","clouds":[{"cover":"BKN","base":3500}]},
            {"icaoId":"KCLT","name":"Charlotte","reportTime":"2026-08-11T23:42:00Z","temp":26.0,"dewp":21.0,"wdir":250,"wspd":12,"visib":8,"altim":1009.0,"lat":35.21,"lon":-80.94,"fltCat":"MVFR","rawOb":"KCLT TEST","clouds":[{"cover":"BKN","base":2500}]},
            {"icaoId":"KJQF","name":"Concord","reportTime":"2026-08-11T23:41:00Z","temp":25.0,"dewp":20.0,"wdir":240,"wspd":8,"visib":10,"altim":1011.0,"lat":35.39,"lon":-80.71,"fltCat":"VFR","rawOb":"KJQF TEST","clouds":[]},
        ]
        adapter = AviationSurfaceAdapter(
            location_label="Test", latitude=35.1115, longitude=-80.6099,
            station_ids=("KEQY","KCLT","KJQF"), user_agent="CIC Test",
            opener=lambda *_a, **_k: _Response(payload),
            now=lambda: datetime(2026,8,11,23,45,tzinfo=timezone.utc),
        )
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        self.assertIsInstance(observation.value, SurfaceObservationNetworkState)
        self.assertEqual(observation.value.station_count, 3)
        self.assertEqual(observation.value.selected_station_id, "KEQY")
        self.assertAlmostEqual(observation.value.temperature_median_f, 77.0, places=1)
        self.assertAlmostEqual(observation.value.temperature_spread_f, 3.6, places=1)
        selected = observation.value.stations[0]
        self.assertEqual(selected.ceiling_ft_agl, 3500)
        self.assertGreater(selected.wind_gust_mph, 20)

    def test_aviation_surface_no_current_reports_is_unavailable(self):
        adapter = AviationSurfaceAdapter(
            location_label="Test", latitude=35.1, longitude=-80.6,
            station_ids=("KEQY",), user_agent="CIC Test",
            opener=lambda *_a, **_k: _Response([]),
        )
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
        self.assertIsNone(observation.value)

    def test_nws_hourly_forecast_resolves_point_and_parses_six_hours(self):
        points = {"properties":{"gridId":"GSP","gridX":100,"gridY":70,"forecastHourly":"https://api.weather.gov/gridpoints/GSP/100,70/forecast/hourly"}}
        periods=[]
        for i in range(6):
            periods.append({"startTime":f"2026-08-11T{19+i:02d}:00:00-04:00","temperature":75+i,"temperatureUnit":"F","dewpoint":{"unitCode":"wmoUnit:degC","value":22},"relativeHumidity":{"value":80-i},"probabilityOfPrecipitation":{"value":50+i},"windSpeed":"5 to 10 mph","windDirection":"SW","shortForecast":"Showers"})
        hourly={"properties":{"generatedAt":"g","updateTime":"u","periods":periods}}
        responses=iter([_Response(points),_Response(hourly)])
        adapter=NWSHourlyForecastAdapter(location_label="Test",latitude=35.1,longitude=-80.6,user_agent="CIC Test",opener=lambda *_a,**_k:next(responses))
        observation=adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        self.assertIsInstance(observation.value, NWSHourlyForecastState)
        self.assertEqual(observation.value.office,"GSP")
        self.assertEqual(len(observation.value.hours),6)
        self.assertAlmostEqual(observation.value.hours[0].dewpoint_f,71.6,places=1)
        self.assertEqual(observation.value.hours[0].wind_speed_max_mph,10.0)

    def test_aviation_surface_uses_current_api_window_parameter(self):
        adapter = AviationSurfaceAdapter(
            location_label="Test",
            latitude=35.1,
            longitude=-80.6,
            station_ids=("KEQY", "KCLT"),
            user_agent="CIC Test",
        )
        url = adapter._url()
        self.assertIn("hoursBeforeNow=2", url)
        self.assertNotIn("&hours=", url)


    def test_aviation_surface_rejects_reports_without_observation_time(self):
        payload = [
            {
                "icaoId": "KEQY",
                "temp": 24.0,
                "dewp": 22.0,
                "lat": 35.02,
                "lon": -80.62,
            }
        ]
        adapter = AviationSurfaceAdapter(
            location_label="Test",
            latitude=35.1115,
            longitude=-80.6099,
            station_ids=("KEQY",),
            user_agent="CIC Test",
            opener=lambda *_args, **_kwargs: _Response(payload),
            now=lambda: datetime(2026, 8, 11, 23, 50, tzinfo=timezone.utc),
        )
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
        self.assertIsNone(observation.value)


    def test_nws_forecast_calm_wind_is_explicit_zero(self):
        points = {
            "properties": {
                "forecastHourly": "https://example.test/hourly",
                "gridId": "GSP",
                "gridX": 1,
                "gridY": 2,
            }
        }
        period = {
            "startTime": "2026-08-11T20:00:00-04:00",
            "temperature": 75,
            "temperatureUnit": "F",
            "dewpoint": {"unitCode": "wmoUnit:degC", "value": 20},
            "relativeHumidity": {"unitCode": "wmoUnit:percent", "value": 70},
            "probabilityOfPrecipitation": {"unitCode": "wmoUnit:percent", "value": 20},
            "windSpeed": "Calm",
            "windDirection": "",
            "shortForecast": "Clear",
        }
        hourly = {"properties": {"periods": [period] * 6}}
        payloads = iter([points, hourly])
        adapter = NWSHourlyForecastAdapter(
            location_label="Test",
            latitude=35.1,
            longitude=-80.6,
            user_agent="CIC Test",
            opener=lambda *_args, **_kwargs: _Response(next(payloads)),
        )
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        self.assertEqual(observation.value.hours[0].wind_speed_min_mph, 0.0)
        self.assertEqual(observation.value.hours[0].wind_speed_max_mph, 0.0)
