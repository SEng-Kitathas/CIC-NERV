import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from personal_cic.core.events import EventBus
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    ComputeState,
    HealthState,
    HealthStatus,
    MemoryState,
    ObservationState,
    StorageState,
    TemperatureState,
    UptimeState,
    UsbDeviceState,
    WifiLinkState,
    WeatherAlertState,
    WeatherForecastState,
    WeatherState,
    CurrentWeatherEstimateState,
    NWSForecastHour,
    NWSHourlyForecastState,
    SurfaceObservationNetworkState,
    SurfaceStationObservation,
)
from personal_cic.presentation import (
    PresentationServer,
    build_systems_projection,
    build_world_projection,
)


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(EventBus())
        self.world.ensure_entity("engage-one", "HP Engage One Model 145")
        self.world.ensure_entity("tenda-u11-pro", "Tenda U11 Pro")

        self.world.upsert_component(
            "engage-one",
            ComputeState(12.5, 4, 0.4, 0.1),
        )
        self.world.upsert_component(
            "engage-one",
            MemoryState(16_000, 10_000, 37.5),
        )
        self.world.upsert_component(
            "engage-one",
            StorageState("/", 100_000, 60_000, 40.0),
        )
        self.world.upsert_component(
            "engage-one",
            TemperatureState(
                41.0,
                "psutil:sensors_temperatures:max",
            ),
        )
        self.world.upsert_component(
            "engage-one",
            UptimeState(3600),
        )
        self.world.upsert_component(
            "engage-one",
            ObservationState(
                "linux.host",
                ObservationAvailability.CURRENT,
                "2026-08-11T20:00:00+00:00",
                "2026-08-11T20:00:00+00:00",
                (),
            ),
        )
        self.world.upsert_component(
            "engage-one",
            HealthState(HealthStatus.NOMINAL, ()),
        )

        self.world.upsert_component(
            "tenda-u11-pro",
            UsbDeviceState(
                True,
                "2604:0020",
                "Tenda AIC 8800D80",
                "wifi",
            ),
        )
        self.world.upsert_component(
            "tenda-u11-pro",
            WifiLinkState(
                "wlxc83a35465764",
                True,
                "TEST",
                5785,
                -60,
                300.0,
                200.0,
                "192.168.1.2/24",
            ),
        )
        self.world.upsert_component(
            "tenda-u11-pro",
            ObservationState(
                "tenda.u11_pro",
                ObservationAvailability.CURRENT,
                "2026-08-11T20:00:00+00:00",
                "2026-08-11T20:00:00+00:00",
                (),
            ),
        )
        self.world.upsert_component(
            "tenda-u11-pro",
            HealthState(HealthStatus.NOMINAL, ()),
        )

    def test_projection_is_read_only_world_projection(self):
        before = self.world.snapshot()

        projection = build_systems_projection(
            self.world,
            runtime_pid=123,
            runtime_started_at="2026-08-11T19:59:00+00:00",
        )

        after = self.world.snapshot()

        self.assertEqual(before, after)
        self.assertEqual(projection["summary"]["health"], "nominal")
        self.assertTrue(projection["summary"]["wlan_connected"])
        self.assertEqual(projection["tenda"]["wifi"]["band"], "5 GHz")
        self.assertEqual(
            projection["host"]["temperature"]["source"],
            "psutil:sensors_temperatures:max",
        )

    def test_http_server_exposes_json_and_rejects_mutation(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {
                "pid": 123,
                "started_at": "2026-08-11T19:59:00+00:00",
            },
        )
        server.start()
        self.addCleanup(server.stop)

        port = server.bound_port
        self.assertIsNotNone(port)

        with urlopen(
            f"http://127.0.0.1:{port}/api/v1/systems",
            timeout=2,
        ) as response:
            payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["presentation"]["mode"], "read-only")
            self.assertEqual(payload["runtime"]["pid"], 123)

        request = Request(
            f"http://127.0.0.1:{port}/api/v1/systems",
            method="POST",
            data=b"{}",
        )
        with self.assertRaises(HTTPError) as captured:
            urlopen(request, timeout=2)

        self.assertEqual(captured.exception.code, 405)

    def test_http_root_is_systems_surface(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(
            f"http://127.0.0.1:{server.bound_port}/",
            timeout=2,
        ) as response:
            body = response.read().decode("utf-8")

        self.assertIn("PERSONAL CIC // SYSTEMS", body)
        self.assertIn("READ-ONLY", body)
        self.assertIn("/api/v1/systems", body)

    def test_world_projection_exposes_provider_freshness_without_inventing_internet_or_health(self):
        self.world.ensure_entity("local-weather", "Local Weather")
        self.world.ensure_entity("local-weather-alerts", "Local Weather Alerts")
        self.world.upsert_component("local-weather", WeatherState("Test", "Open-Meteo", "2026-08-11T18:00", "America/New_York", 88.0, 90.0, 55.0, 0.0, 2, 40.0, 5.0, 180.0, 9.0))
        self.world.upsert_component("local-weather", WeatherForecastState("Test", "Open-Meteo", "America/New_York", "2026-08-11", 91.0, 72.0, 40.0, "06:39", "20:18"))
        self.world.upsert_component("local-weather", ObservationState("openmeteo.weather", ObservationAvailability.CURRENT, "2026-08-11T20:00:00+00:00", "2026-08-11T20:00:00+00:00", ()))
        self.world.upsert_component("local-weather-alerts", WeatherAlertState("Test", "National Weather Service", 0, None, "2026-08-11T20:00:00+00:00", ()))
        self.world.upsert_component("local-weather-alerts", ObservationState("nws.alerts", ObservationAvailability.CURRENT, "2026-08-11T20:00:00+00:00", "2026-08-11T20:00:00+00:00", ()))
        projection = build_world_projection(self.world)
        self.assertEqual(projection["weather"]["condition"], "Partly cloudy")
        self.assertTrue(projection["alerts"]["authoritative_now"])
        self.assertNotIn("internet", projection)
        self.assertNotIn("health", projection["weather"])

    def test_http_world_endpoint_and_page_are_read_only(self):
        self.world.ensure_entity("local-weather", "Local Weather")
        self.world.ensure_entity("local-weather-alerts", "Local Weather Alerts")
        server = PresentationServer(world=self.world, host="127.0.0.1", port=0, runtime_metadata=lambda: {})
        server.start(); self.addCleanup(server.stop)
        with urlopen(f"http://127.0.0.1:{server.bound_port}/world", timeout=2) as response:
            body=response.read().decode("utf-8")
        self.assertIn("PERSONAL CIC // WORLD", body)
        self.assertIn("Open-Meteo", body)
        self.assertIn("CC BY 4.0", body)
        with urlopen(f"http://127.0.0.1:{server.bound_port}/api/v1/world", timeout=2) as response:
            payload=json.loads(response.read())
        self.assertEqual(payload["presentation"]["mode"], "read-only")
        request=Request(f"http://127.0.0.1:{server.bound_port}/api/v1/world", method="POST", data=b"{}")
        with self.assertRaises(HTTPError) as captured:
            urlopen(request, timeout=2)
        self.assertEqual(captured.exception.code, 405)

    def test_world_projection_exposes_surface_forecast_estimate_and_feed(self):
        self.world.ensure_entity("local-weather-surface","Surface")
        self.world.ensure_entity("local-weather-nws-forecast","Forecast")
        self.world.ensure_entity("local-weather-estimate","Estimate")
        station=SurfaceStationObservation("KEQY","Monroe","t",35.0,-80.6,8.0,75.0,70.0,80.0,260.0,10.0,15.0,10.0,29.8,1010.0,3000,"VFR",None,"raw")
        self.world.upsert_component("local-weather-surface",SurfaceObservationNetworkState("Test","AWC","t","KEQY",1,75.0,70.0,80.0,0.0,(station,)))
        self.world.upsert_component("local-weather-surface",ObservationState("aviationweather.metar",ObservationAvailability.CURRENT,"2026-08-11T20:00:00+00:00","2026-08-11T20:00:00+00:00",()))
        hour=NWSForecastHour("h",76.0,70.0,80.0,50.0,5.0,10.0,"SW","Showers")
        self.world.upsert_component("local-weather-nws-forecast",NWSHourlyForecastState("Test","NWS","GSP",1,2,"g","u",(hour,)))
        self.world.upsert_component("local-weather-nws-forecast",ObservationState("nws.forecast.hourly",ObservationAvailability.CURRENT,"2026-08-11T20:00:00+00:00","2026-08-11T20:00:00+00:00",()))
        estimate=CurrentWeatherEstimateState("Test","d","surface_median + nearest_station_context","NOAA/NWS AviationWeather.gov METAR",1,75.0,70.0,80.0,260.0,10.0,15.0,10.0,29.8,3000,"VFR",0.0,77.0,2.0,76.0,1.0,"h")
        self.world.upsert_component("local-weather-estimate",estimate)
        self.world.upsert_component("local-weather-estimate",ObservationState("weather.fusion",ObservationAvailability.CURRENT,"2026-08-11T20:00:00+00:00","2026-08-11T20:00:00+00:00",()))
        projection=build_world_projection(self.world,feed=[{"category":"ALERT","title":"Test","detail":"x"}])
        self.assertEqual(projection["api_version"],2)
        self.assertEqual(projection["surface"]["selected_station_id"],"KEQY")
        self.assertEqual(projection["surface"]["wind_speed_median_mph"],10.0)
        self.assertEqual(projection["surface"]["wind_gust_max_mph"],15.0)
        self.assertEqual(projection["surface"]["visibility_min_sm"],10.0)
        self.assertEqual(projection["surface"]["ceiling_min_ft_agl"],3000)
        self.assertEqual(projection["nws_forecast"]["hours"][0]["short_forecast"],"Showers")
        self.assertTrue(projection["estimate"]["current_now"])
        self.assertNotIn("authoritative_now", projection["estimate"])
        self.assertEqual(projection["feed"][0]["category"],"ALERT")

    def test_world_page_does_not_interpolate_provider_strings_through_inner_html(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(
            f"http://127.0.0.1:{server.bound_port}/world",
            timeout=2,
        ) as response:
            body = response.read().decode("utf-8")

        self.assertIn("const cell=", body)
        self.assertIn("replaceChildren()", body)
        self.assertNotIn("tr.innerHTML=", body)
        self.assertNotIn("div.innerHTML=", body)

if __name__ == "__main__":
    unittest.main()
