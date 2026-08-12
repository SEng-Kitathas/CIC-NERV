import unittest

from personal_cic.core.config import HealthThresholds
from personal_cic.core.world.components import (
    CurrentWeatherEstimateState, NWSForecastHour, NWSHourlyForecastState, SurfaceObservationNetworkState, SurfaceStationObservation, WeatherAlertState, WeatherForecastState, WeatherState,
)
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

    def test_surface_numeric_drift_is_sample_but_station_or_flight_category_change_is_material(self):
        def st(cat="VFR", temp=75.0):
            return SurfaceStationObservation("KEQY","Monroe","t",35.0,-80.6,8.0,temp,70.0,80.0,260.0,10.0,15.0,10.0,29.8,1010.0,3000,cat,None,"raw")
        old=SurfaceObservationNetworkState("Test","AWC","t","KEQY",1,75.0,70.0,80.0,0.0,(st(),))
        drift=SurfaceObservationNetworkState("Test","AWC","t2","KEQY",1,76.0,70.0,78.0,0.0,(st(temp=76.0),))
        changed=SurfaceObservationNetworkState("Test","AWC","t3","KEQY",1,76.0,70.0,78.0,0.0,(st(cat="MVFR",temp=76.0),))
        self.assertEqual(telemetry_significance(old,drift,THRESHOLDS),"sample")
        self.assertEqual(telemetry_significance(old,changed,THRESHOLDS),"material")

    def test_nws_forecast_pop_band_change_is_material(self):
        h1=NWSForecastHour("t",75,None,None,20,5,10,"SW","Showers")
        h2=NWSForecastHour("t",75,None,None,70,5,10,"SW","Showers")
        old=NWSHourlyForecastState("Test","NWS","GSP",1,2,"g","u",(h1,))
        new=NWSHourlyForecastState("Test","NWS","GSP",1,2,"g2","u2",(h2,))
        self.assertEqual(telemetry_significance(old,new,THRESHOLDS),"material")

    def test_estimate_numeric_drift_is_sample_but_source_change_is_material(self):
        args=("Test","t","surface_median + nearest_station_context","NOAA/NWS AviationWeather.gov METAR",2,75.0,70.0,80.0,260.0,10.0,15.0,10.0,29.8,3000,"VFR",2.0,77.0,2.0,76.0,1.0,"h")
        old=CurrentWeatherEstimateState(*args)
        drift=CurrentWeatherEstimateState(*args[:5],76.0,*args[6:])
        fallback=CurrentWeatherEstimateState("Test","t2","openmeteo_model_fallback","Open-Meteo",0,77.0,None,80.0,260.0,10.0,15.0,None,None,None,None,None,77.0,0.0,76.0,-1.0,"h")
        self.assertEqual(telemetry_significance(old,drift,THRESHOLDS),"sample")
        self.assertEqual(telemetry_significance(old,fallback,THRESHOLDS),"material")

    def test_nws_forecast_window_roll_without_semantic_change_is_sample(self):
        old_h=NWSForecastHour("2026-08-11T20:00:00-04:00",80.0,70.0,70.0,12.0,3.0,3.0,"W","Mostly Clear")
        new_h=NWSForecastHour("2026-08-11T21:00:00-04:00",79.0,70.0,72.0,15.0,3.0,3.0,"W","Mostly Clear")
        old=NWSHourlyForecastState("Test","NWS","GSP",1,2,"g","u",(old_h,))
        new=NWSHourlyForecastState("Test","NWS","GSP",1,2,"g2","u2",(new_h,))
        self.assertEqual(telemetry_significance(old,new,THRESHOLDS),"sample")
