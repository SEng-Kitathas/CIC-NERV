import unittest
from datetime import datetime, timezone

from personal_cic.core.world.components import (
    NWSForecastHour, NWSHourlyForecastState, SurfaceObservationNetworkState,
    SurfaceStationObservation, WeatherState,
)
from personal_cic.weather_fusion import _reference_hour, derive_current_weather_estimate


class WeatherFusionTests(unittest.TestCase):
    def test_surface_observation_owns_current_estimate_and_models_remain_comparison(self):
        st=SurfaceStationObservation("KEQY","Monroe","t",35.0,-80.6,8.0,75.0,72.0,90.0,260.0,12.0,20.0,10.0,29.82,1009.0,2500,"MVFR","-RA","raw")
        surface=SurfaceObservationNetworkState("Test","AWC","t","KEQY",2,76.0,72.0,87.0,2.0,(st,))
        om=WeatherState("Test","Open-Meteo","t","America/New_York",79.0,80.0,80.0,0.0,61,90.0,10.0,260.0,20.0)
        hour=NWSForecastHour("2026-08-11T20:00:00-04:00",78.0,72.0,80.0,60.0,5.0,10.0,"SW","Showers")
        nws=NWSHourlyForecastState("Test","NWS","GSP",1,2,"g","u",(hour,))
        out=derive_current_weather_estimate(location_label="Test",surface=surface,surface_usable=True,open_meteo=om,open_meteo_current=True,nws_forecast=nws,nws_current=True)
        self.assertEqual(out.temperature_f,76.0)
        self.assertEqual(out.primary_source,"NOAA/NWS AviationWeather.gov METAR")
        self.assertEqual(out.flight_category,"MVFR")
        self.assertEqual(out.open_meteo_delta_f,3.0)
        self.assertEqual(out.nws_reference_delta_f,2.0)


    def test_nws_reference_period_is_current_period_not_mislabeled_next_hour(self):
        h0=NWSForecastHour("2026-08-11T20:00:00-04:00",88.0,72.0,58.0,14.0,5.0,5.0,"NNW","Partly Cloudy")
        h1=NWSForecastHour("2026-08-11T21:00:00-04:00",84.0,72.0,67.0,12.0,3.0,3.0,"W","Mostly Clear")
        nws=NWSHourlyForecastState("Test","NWS","GSP",1,2,"g","u",(h0,h1))
        ref=_reference_hour(nws,datetime(2026,8,12,0,34,tzinfo=timezone.utc))
        self.assertEqual(ref.start_time,"2026-08-11T20:00:00-04:00")
        self.assertEqual(ref.temperature_f,88.0)

    def test_open_meteo_is_explicit_fallback_not_peer_average(self):
        om=WeatherState("Test","Open-Meteo","t","America/New_York",79.0,80.0,80.0,0.0,1,20.0,10.0,180.0,15.0)
        out=derive_current_weather_estimate(location_label="Test",surface=None,surface_usable=False,open_meteo=om,open_meteo_current=True,nws_forecast=None,nws_current=False)
        self.assertEqual(out.temperature_f,79.0)
        self.assertEqual(out.method,"openmeteo_model_fallback")
        self.assertEqual(out.surface_station_count,0)

    def test_no_current_source_yields_no_estimate(self):
        self.assertIsNone(derive_current_weather_estimate(location_label="Test",surface=None,surface_usable=False,open_meteo=None,open_meteo_current=False,nws_forecast=None,nws_current=False))

if __name__ == "__main__": unittest.main()
