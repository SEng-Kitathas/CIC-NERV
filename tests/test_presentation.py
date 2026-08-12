from hashlib import sha256
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
    RadarMosaicState,
    RadarFrameReference,
    RadarContextState,
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
        self.assertIn("RADAR // MRMS BREF.QCD + NWS WARNINGS", body)
        self.assertIn("MRMS STREAM AGE", body)
        self.assertIn("id=\"radar-image\"", body)
        self.assertIn("syncRadarFrames", body)
        self.assertIn("id=\"radar-stage\"", body)
        self.assertIn("rs.style.aspectRatio", body)
        self.assertIn("rd.warning_overlay_current", body)
        self.assertIn('id="radar-context"', body)
        self.assertIn('id="radar-play"', body)
        self.assertIn('id="radar-prev"', body)
        self.assertIn('id="radar-next"', body)
        self.assertIn("radarAutoplay=true", body)
        self.assertIn("WMS RETR", body)
        self.assertIn("MRMS STREAM", body)
        self.assertNotIn("fetch('https://tigerweb", body)
        self.assertNotIn('fetch("https://tigerweb', body)
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
        self.assertEqual(projection["api_version"],4)
        self.assertEqual(projection["surface"]["selected_station_id"],"KEQY")
        self.assertEqual(projection["surface"]["wind_speed_median_mph"],10.0)
        self.assertEqual(projection["surface"]["wind_gust_max_mph"],15.0)
        self.assertEqual(projection["surface"]["visibility_min_sm"],10.0)
        self.assertEqual(projection["surface"]["ceiling_min_ft_agl"],3000)
        self.assertEqual(projection["nws_forecast"]["hours"][0]["short_forecast"],"Showers")
        self.assertTrue(projection["estimate"]["current_now"])
        self.assertNotIn("authoritative_now", projection["estimate"])
        self.assertEqual(projection["feed"][0]["category"],"ALERT")

    def test_world_projection_exposes_radar_metadata_and_local_image_routes(self):
        self.world.ensure_entity("local-weather-radar", "Radar")
        state = RadarMosaicState(
            location_label="Test",
            provider="NOAA/NWS MRMS + NWS GeoServer",
            product="BREF.QCD",
            layer="conus_bref_qcd",
            stream_latest_filename="CONUS_L2_BREF_QCD_20260812_010400.tif.gz",
            stream_latest_at="2026-08-12T01:04:00+00:00",
            frame_retrieved_at="2026-08-12T01:04:05+00:00",
            west=-82.0,
            south=34.0,
            east=-79.0,
            north=36.0,
            range_miles=75.0,
            image_width=900,
            image_height=600,
            image_sha256="a" * 64,
            warning_overlay_available=True,
            warning_image_sha256="b" * 64,
            legend_available=True,
            legend_image_sha256="c" * 64,
            frames=(RadarFrameReference(
                "2026-08-12T01:04:05+00:00",
                "a" * 64,
                "b" * 64,
                "2026-08-12T01:04:00+00:00",
            ),),
            loop_frame_capacity=15,
        )
        self.world.upsert_component("local-weather-radar", state)
        self.world.upsert_component(
            "local-weather-radar",
            ObservationState(
                "nws.mrms.radar",
                ObservationAvailability.CURRENT,
                "2026-08-12T01:05:00+00:00",
                "2026-08-12T01:05:00+00:00",
                (),
            ),
        )
        projection = build_world_projection(self.world)
        radar = projection["radar"]
        self.assertTrue(radar["current_now"])
        self.assertTrue(radar["displayable_now"])
        self.assertEqual(radar["image_url"], "/radar/frames/" + "a" * 64 + ".png")
        self.assertEqual(radar["warning_image_url"], "/radar/warning-frames/" + "b" * 64 + ".png")
        self.assertEqual(len(radar["frames"]), 1)
        self.assertEqual(radar["frames"][0]["image_url"], radar["image_url"])
        self.assertNotIn("http", radar["image_url"])

    def test_unavailable_radar_keeps_last_known_frame_but_never_current_warning_overlay(self):
        self.world.ensure_entity("local-weather-radar", "Radar")
        state = RadarMosaicState(
            location_label="Test",
            provider="NOAA/NWS MRMS + NWS GeoServer",
            product="BREF.QCD",
            layer="conus_bref_qcd",
            stream_latest_filename="CONUS_L2_BREF_QCD_20260812_010400.tif.gz",
            stream_latest_at="2026-08-12T01:04:00+00:00",
            frame_retrieved_at="2026-08-12T01:04:05+00:00",
            west=-82.0,
            south=34.0,
            east=-79.0,
            north=36.0,
            range_miles=75.0,
            image_width=900,
            image_height=600,
            image_sha256="a" * 64,
            warning_overlay_available=True,
            warning_image_sha256="b" * 64,
            legend_available=True,
            legend_image_sha256="c" * 64,
        )
        self.world.upsert_component("local-weather-radar", state)
        self.world.upsert_component(
            "local-weather-radar",
            ObservationState(
                "nws.mrms.radar",
                ObservationAvailability.UNAVAILABLE,
                "2026-08-12T01:06:00+00:00",
                "2026-08-12T01:05:00+00:00",
                ("provider unavailable",),
            ),
        )
        radar = build_world_projection(self.world)["radar"]
        self.assertEqual(radar["frame_state"], "LAST KNOWN")
        self.assertFalse(radar["warning_overlay_current"])
        self.assertEqual(radar["warning_overlay_state"], "LAST KNOWN")
        self.assertIsNotNone(radar["image_url"])
        self.assertIsNone(radar["warning_image_url"])

    def test_http_server_serves_only_fixed_cached_radar_images(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            radar = b"\x89PNG\r\n\x1a\nradar"
            warnings = b"\x89PNG\r\n\x1a\nwarn"
            (cache / "latest.png").write_bytes(radar)
            (cache / "warnings.png").write_bytes(warnings)

            server = PresentationServer(
                world=self.world,
                host="127.0.0.1",
                port=0,
                runtime_metadata=lambda: {},
                radar_cache_dir=cache,
            )
            server.start()
            self.addCleanup(server.stop)

            with urlopen(
                f"http://127.0.0.1:{server.bound_port}/radar/latest.png?sha={sha256(radar).hexdigest()}",
                timeout=2,
            ) as response:
                self.assertEqual(response.read(), radar)
                self.assertEqual(response.headers.get_content_type(), "image/png")

            with self.assertRaises(HTTPError) as mismatch:
                urlopen(
                    f"http://127.0.0.1:{server.bound_port}/radar/latest.png?sha={'0' * 64}",
                    timeout=2,
                )
            self.assertEqual(mismatch.exception.code, 409)

            with self.assertRaises(HTTPError) as captured:
                urlopen(
                    f"http://127.0.0.1:{server.bound_port}/radar/not-allowed.png",
                    timeout=2,
                )
            self.assertEqual(captured.exception.code, 404)

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
    def test_world_projection_exposes_hash_bound_radar_context(self):
        self.world.ensure_entity("local-weather-radar-context", "Radar Context")
        state = RadarContextState(
            location_label="Test",
            provider="U.S. Census Bureau TIGERweb",
            retrieved_at="2026-08-12T01:00:00+00:00",
            west=-82.0, south=34.0, east=-79.0, north=36.0,
            context_sha256="d" * 64,
            content_sha256="e" * 64,
            county_count=3, primary_road_count=5, secondary_road_count=7, place_count=9,
        )
        self.world.upsert_component("local-weather-radar-context", state)
        self.world.upsert_component(
            "local-weather-radar-context",
            ObservationState(
                "census.tiger.radar_context", ObservationAvailability.CURRENT,
                "2026-08-12T01:00:00+00:00", "2026-08-12T01:00:00+00:00", (),
            ),
        )
        context = build_world_projection(self.world)["radar_context"]
        self.assertEqual(context["context_state"], "CURRENT")
        self.assertEqual(context["content_sha256"], "e" * 64)
        self.assertEqual(context["context_url"], "/radar/context.json?sha=" + "d" * 64)

    def test_http_server_serves_hash_named_loop_frames_and_context_only(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            frames = cache / "frames"
            warnings = cache / "warning_frames"
            frames.mkdir(); warnings.mkdir()
            radar = b"\x89PNG\r\n\x1a\nframe"
            warning = b"\x89PNG\r\n\x1a\nwarning-frame"
            radar_hash = sha256(radar).hexdigest()
            warning_hash = sha256(warning).hexdigest()
            (frames / f"{radar_hash}.png").write_bytes(radar)
            (warnings / f"{warning_hash}.png").write_bytes(warning)
            context = json.dumps({"provider": "Census", "counties": []}, sort_keys=True).encode()
            context_hash = sha256(context).hexdigest()
            (cache / "context.json").write_bytes(context)

            server = PresentationServer(
                world=self.world, host="127.0.0.1", port=0,
                runtime_metadata=lambda: {}, radar_cache_dir=cache,
            )
            server.start(); self.addCleanup(server.stop)
            base = f"http://127.0.0.1:{server.bound_port}"

            with urlopen(base + f"/radar/frames/{radar_hash}.png", timeout=2) as response:
                self.assertEqual(response.read(), radar)
            with urlopen(base + f"/radar/warning-frames/{warning_hash}.png", timeout=2) as response:
                self.assertEqual(response.read(), warning)
            with urlopen(base + f"/radar/context.json?sha={context_hash}", timeout=2) as response:
                self.assertEqual(response.read(), context)

            with self.assertRaises(HTTPError) as wrong_context:
                urlopen(base + "/radar/context.json?sha=" + "0" * 64, timeout=2)
            self.assertEqual(wrong_context.exception.code, 409)

            with self.assertRaises(HTTPError) as invalid_frame:
                urlopen(base + "/radar/frames/not-a-hash.png", timeout=2)
            self.assertEqual(invalid_frame.exception.code, 400)

    def test_world_page_uses_safe_local_context_and_real_frame_loop_controls(self):
        from personal_cic.presentation.pages import WORLD_HTML

        for marker in (
            'id="radar-context"', 'id="radar-play"', 'id="radar-prev"',
            'id="radar-next"', 'radarAutoplay=true', 'syncRadarFrames',
            'warning_image_url', 'WMS RETR', 'MRMS STREAM',
            'id="radar-ring-1"', 'id="radar-ring-3"',
        ):
            self.assertIn(marker, WORLD_HTML)
        self.assertIn("text.textContent", WORLD_HTML)
        self.assertNotIn("context.innerHTML", WORLD_HTML)
        self.assertNotIn("fetch('https://tigerweb", WORLD_HTML)
        self.assertNotIn('fetch("https://tigerweb', WORLD_HTML)

    def test_radar_loop_refresh_preserves_playback_position_and_requires_three_frames(self):
        from personal_cic.presentation.pages import WORLD_HTML

        self.assertIn("const radarAutoplayMinFrames=3", WORLD_HTML)
        self.assertIn("if(next<0)next=radarFrames.length-1", WORLD_HTML)
        self.assertNotIn("if(next<0||radarPlaying||radarAutoplay)", WORLD_HTML)
        self.assertIn("radarFrames.length>=radarAutoplayMinFrames", WORLD_HTML)
        self.assertIn("building distinct frames // autoplay at", WORLD_HTML)
        self.assertIn('aria-label="Previous radar frame"', WORLD_HTML)
        self.assertIn('aria-label="Next radar frame"', WORLD_HTML)


if __name__ == "__main__":
    unittest.main()
