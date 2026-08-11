import unittest

from personal_cic.core.config import HealthThresholds
from personal_cic.core.world.components import WeatherAlertState, WeatherForecastState, WeatherState
from personal_cic.holons.systems.materiality import telemetry_significance

THRESHOLDS = HealthThresholds(80,95,85,95,90,97,80,90,-75)


def weather(**changes):
    base = dict(location_label="Test", provider="Open-Meteo", provider_observed_at="t1", provider_timezone="America/New_York", temperature_f=80.0,
                apparent_temperature_f=81.0, relative_humidity_percent=50.0, precipitation_in=0.0,
                weather_code=1, cloud_cover_percent=20.0, wind_speed_mph=5.0, wind_direction_deg=180.0,
                wind_gust_mph=8.0)
    base.update(changes)
    return WeatherState(**base)


class WorldAwarenessMaterialityTests(unittest.TestCase):
    def test_normal_weather_value_churn_is_sample(self):
        self.assertEqual(telemetry_significance(weather(), weather(temperature_f=82.0, provider_observed_at="t2"), THRESHOLDS), "sample")

    def test_condition_change_is_material(self):
        self.assertEqual(telemetry_significance(weather(), weather(weather_code=95), THRESHOLDS), "material")

    def test_precipitation_start_is_material(self):
        self.assertEqual(telemetry_significance(weather(), weather(precipitation_in=0.1), THRESHOLDS), "material")

    def test_same_day_forecast_revision_is_sample(self):
        a=WeatherForecastState("Test","Open-Meteo","America/New_York","2026-08-11",90,70,30,"sunrise","sunset")
        b=WeatherForecastState("Test","Open-Meteo","America/New_York","2026-08-11",92,71,40,"sunrise","sunset")
        self.assertEqual(telemetry_significance(a,b,THRESHOLDS),"sample")

    def test_alert_collection_updated_timestamp_churn_is_sample(self):
        a=WeatherAlertState("Test","NWS",0,None,"t1",())
        b=WeatherAlertState("Test","NWS",0,None,"t2",())
        self.assertEqual(telemetry_significance(a,b,THRESHOLDS),"sample")

    def test_alert_change_is_material(self):
        a=WeatherAlertState("Test","NWS",0,None,"t1",())
        b=WeatherAlertState("Test","NWS",1,"Severe","t2",())
        self.assertEqual(telemetry_significance(a,b,THRESHOLDS),"material")
