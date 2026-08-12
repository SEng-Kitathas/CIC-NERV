import tempfile
import unittest
from pathlib import Path

from personal_cic.core.events import EventBus
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    CICNode,
    HealthState,
    HealthStatus,
    MemoryState,
    ObservationState,
    WeatherAlertState,
    WeatherAlertSummary,
)


class WorldContinuityTests(unittest.TestCase):
    def test_snapshot_round_trip_restores_typed_components_without_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "world.json"

            first_events = EventBus()
            first = WorldState(first_events)
            first.ensure_entity("engage", "Engage")
            first.upsert_component("engage", CICNode())
            first.upsert_component("engage", MemoryState(16_000, 12_000, 25.0))
            first.upsert_component("engage", HealthState(HealthStatus.NOMINAL, ()))
            first.upsert_component(
                "engage",
                ObservationState(
                    adapter_id="linux.host",
                    availability=ObservationAvailability.CURRENT,
                    checked_at="2026-08-10T22:00:00+00:00",
                    last_success_at="2026-08-10T22:00:00+00:00",
                    reasons=(),
                ),
            )
            first.write_json(state_path)

            second_events = EventBus()
            second = WorldState(second_events)
            restored = second.hydrate_json(state_path)

            self.assertEqual(restored, 1)
            self.assertEqual(second_events.published_count, 0)
            entity = second.entities["engage"]
            self.assertIsInstance(entity.get(CICNode), CICNode)
            self.assertEqual(entity.get(MemoryState), MemoryState(16_000, 12_000, 25.0))
            self.assertEqual(entity.get(HealthState), HealthState(HealthStatus.NOMINAL, ()))
            self.assertEqual(
                entity.get(ObservationState).availability,
                ObservationAvailability.CURRENT,
            )

    def test_schema_v1_health_state_remains_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "world-v1.json"
            state_path.write_text(
                '{"schema_version":1,"entities":{"engage":{"label":"Engage","components":{"HealthState":{"status":"nominal","reasons":[]}}}}}',
                encoding="utf-8",
            )

            world = WorldState(EventBus())
            restored = world.hydrate_json(state_path)

            self.assertEqual(restored, 1)
            self.assertEqual(
                world.entities["engage"].get(HealthState),
                HealthState(HealthStatus.NOMINAL, ()),
            )

    def test_weather_alert_nested_state_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.json"
            world = WorldState(EventBus())
            world.ensure_entity("local-weather-alerts", "Local Weather Alerts")
            world.upsert_component(
                "local-weather-alerts",
                WeatherAlertState(
                    location_label="Test",
                    provider="National Weather Service",
                    active_count=1,
                    highest_severity="Severe",
                    provider_updated_at="2026-08-11T22:00:00+00:00",
                    alerts=(WeatherAlertSummary(
                        alert_id="a1", event="Warning", severity="Severe", urgency="Immediate",
                        headline="Test warning", sent_at=None, effective_at=None, expires_at=None,
                    ),),
                ),
            )
            world.write_json(path)
            restored = WorldState(EventBus())
            restored.hydrate_json(path)
            state = restored.get_component("local-weather-alerts", WeatherAlertState)
            self.assertIsInstance(state.alerts, tuple)
            self.assertIsInstance(state.alerts[0], WeatherAlertSummary)
            self.assertEqual(state.alerts[0].alert_id, "a1")

    def test_surface_and_nws_forecast_nested_components_round_trip(self):
        from personal_cic.core.world.components import NWSForecastHour, NWSHourlyForecastState, SurfaceObservationNetworkState, SurfaceStationObservation
        station=SurfaceStationObservation("KEQY","Monroe","t",35.0,-80.6,8.0,75.0,70.0,80.0,260.0,10.0,15.0,10.0,29.8,1010.0,3000,"VFR",None,"raw")
        surface=SurfaceObservationNetworkState("Test","AWC","t","KEQY",1,75.0,70.0,80.0,0.0,(station,))
        hour=NWSForecastHour("h",76.0,70.0,80.0,50.0,5.0,10.0,"SW","Showers")
        forecast=NWSHourlyForecastState("Test","NWS","GSP",1,2,"g","u",(hour,))
        world=WorldState(EventBus())
        world.ensure_entity("surface","Surface"); world.upsert_component("surface",surface); world.upsert_component("surface",forecast)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"world.json"; world.write_json(path)
            restored=WorldState(EventBus()); restored.hydrate_json(path)
        self.assertEqual(restored.get_component("surface", SurfaceObservationNetworkState),surface)
        self.assertEqual(restored.get_component("surface", NWSHourlyForecastState),forecast)

    def test_radar_mosaic_round_trip(self):
        from personal_cic.core.world.components import RadarMosaicState

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
            image_sha256="abc",
            warning_overlay_available=True,
            warning_image_sha256="def",
            legend_available=True,
            legend_image_sha256="ghi",
        )
        world = WorldState(EventBus())
        world.ensure_entity("local-weather-radar", "Radar")
        world.upsert_component("local-weather-radar", state)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.json"
            world.write_json(path)
            restored = WorldState(EventBus())
            count = restored.hydrate_json(path)
        self.assertEqual(count, 1)
        self.assertEqual(
            restored.get_component("local-weather-radar", RadarMosaicState),
            state,
        )

    def test_radar_rc1_snapshot_migrates_without_false_frame_binding(self):
        from personal_cic.core.world.components import RadarMosaicState
        import json

        payload = {
            "schema_version": 3,
            "entities": {
                "local-weather-radar": {
                    "label": "Local Radar",
                    "components": {
                        "RadarMosaicState": {
                            "location_label": "Test",
                            "provider": "NOAA/NWS MRMS + NWS GeoServer",
                            "product": "BREF.QCD",
                            "layer": "conus_bref_qcd",
                            "source_filename": "CONUS_L2_BREF_QCD_20260812_010400.tif.gz",
                            "source_product_at": "2026-08-12T01:04:00+00:00",
                            "west": -82.0,
                            "south": 34.0,
                            "east": -79.0,
                            "north": 36.0,
                            "range_miles": 75.0,
                            "image_width": 900,
                            "image_height": 600,
                            "image_sha256": "abc",
                            "warning_overlay_available": True,
                            "warning_image_sha256": "def",
                            "legend_available": True,
                            "legend_image_sha256": "ghi",
                        }
                    },
                }
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            world = WorldState(EventBus())
            restored = world.hydrate_json(path)

        self.assertEqual(restored, 1)
        state = world.get_component("local-weather-radar", RadarMosaicState)
        self.assertEqual(
            state.stream_latest_filename,
            "CONUS_L2_BREF_QCD_20260812_010400.tif.gz",
        )
        self.assertEqual(state.stream_latest_at, "2026-08-12T01:04:00+00:00")
        # RC1 never recorded the separately retrieved WMS frame time, so the
        # migration must not invent one from the RIDGEII stream timestamp.
        self.assertIsNone(state.frame_retrieved_at)

    def test_rc1_estimate_snapshot_field_names_migrate_on_hydration(self):
        from personal_cic.core.world.components import CurrentWeatherEstimateState
        payload = {
            "schema_version": 2,
            "entities": {
                "local-weather-estimate": {
                    "label": "Current Weather Estimate",
                    "components": {
                        "CurrentWeatherEstimateState": {
                            "location_label": "Test",
                            "derived_at": "2026-08-12T00:34:02+00:00",
                            "method": "surface_median + nearest_station_context",
                            "primary_source": "NOAA/NWS AviationWeather.gov METAR",
                            "surface_station_count": 3,
                            "temperature_f": 73.0,
                            "dewpoint_f": 71.0,
                            "relative_humidity_percent": 94.0,
                            "wind_direction_deg": 0.0,
                            "wind_speed_mph": 0.0,
                            "wind_gust_mph": None,
                            "visibility_sm": 6.0,
                            "altimeter_inhg": 30.01,
                            "ceiling_ft_agl": 12000,
                            "flight_category": "VFR",
                            "surface_temperature_spread_f": 1.4,
                            "open_meteo_temperature_f": 75.5,
                            "open_meteo_delta_f": 2.5,
                            "nws_next_hour_temperature_f": 88.0,
                            "nws_next_hour_delta_f": 15.0,
                            "nws_next_hour_start": "2026-08-11T20:00:00-04:00"
                        }
                    }
                }
            }
        }
        import json
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"world.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            world=WorldState(EventBus())
            restored=world.hydrate_json(path)
        self.assertEqual(restored,1)
        state=world.get_component("local-weather-estimate",CurrentWeatherEstimateState)
        self.assertEqual(state.nws_reference_temperature_f,88.0)
        self.assertEqual(state.nws_reference_delta_f,15.0)
        self.assertEqual(state.nws_reference_start,"2026-08-11T20:00:00-04:00")


if __name__ == "__main__":
    unittest.main()
