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

if __name__ == "__main__":
    unittest.main()
