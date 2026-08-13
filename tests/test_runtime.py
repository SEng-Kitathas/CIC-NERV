import json
import tempfile
import unittest
from pathlib import Path

from personal_cic.core.config import RuntimeConfig


class RuntimeConfigTests(unittest.TestCase):
    def _base(self):
        return {
            "collection_interval_seconds": 5,
            "snapshot_interval_seconds": 10,
            "state_path": "state/world.json",
            "event_journal_path": "logs/events.jsonl",
        }

    def _load(self, data):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "runtime.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return RuntimeConfig.load(path)

    def test_runtime_config_loads_paths_and_intervals(self):
        config = self._load(self._base())
        self.assertEqual(config.collection_interval_seconds, 5.0)
        self.assertEqual(config.snapshot_interval_seconds, 10.0)
        self.assertEqual(config.state_path, Path("state/world.json"))
        self.assertEqual(config.event_journal_path, Path("logs/events.jsonl"))
        self.assertFalse(config.presentation.enabled)
        self.assertFalse(config.world_awareness.enabled)


    def test_operator_context_loads_fixed_site_anchor_with_provenance(self):
        data = self._base()
        data["operator_context"] = {
            "site_anchor": {
                "enabled": True,
                "label": "CIC SITE",
                "address": "7004 Dacian Ln, Indian Trail, NC 28079",
                "latitude": 35.12042277,
                "longitude": -80.62950725,
                "position_kind": "fixed_site_anchor",
                "source_lineage": "Union County NC GIS Address_Point",
                "source_record_id": "65294",
                "source_verified_at": "2026-08-13T15:42:00Z",
                "source_artifact_sha256": "5cfcd68382511b5639dab09355a8e26919b50bf83f3f5660fb891488dd674d4b",
            }
        }
        config = self._load(data)
        site = config.operator_context.site_anchor
        self.assertTrue(site.enabled)
        self.assertEqual(site.position_kind, "fixed_site_anchor")
        self.assertAlmostEqual(site.latitude, 35.12042277)
        self.assertAlmostEqual(site.longitude, -80.62950725)
        self.assertEqual(site.source_record_id, "65294")

    def test_operator_context_rejects_enabled_site_anchor_without_coordinates(self):
        data = self._base()
        data["operator_context"] = {"site_anchor": {"enabled": True, "label": "CIC SITE"}}
        with self.assertRaises(ValueError):
            self._load(data)

    def test_runtime_config_loads_loopback_presentation(self):
        data = self._base()
        data["presentation"] = {"enabled": True, "bind_host": "127.0.0.1", "port": 8765}
        config = self._load(data)
        self.assertTrue(config.presentation.enabled)
        self.assertEqual(config.presentation.bind_host, "127.0.0.1")
        self.assertEqual(config.presentation.port, 8765)

    def test_runtime_config_rejects_non_loopback_presentation(self):
        data = self._base()
        data["presentation"] = {"enabled": True, "bind_host": "0.0.0.0", "port": 8765}
        with self.assertRaises(ValueError):
            self._load(data)

    def test_world_awareness_config_loads_independent_provider_cadences(self):
        data = self._base()
        data["world_awareness"] = {
            "enabled": True,
            "location": {"label": "Test", "latitude": 35.1, "longitude": -80.6},
            "weather": {"interval_seconds": 300, "timeout_seconds": 5},
            "alerts": {"interval_seconds": 60, "timeout_seconds": 6, "user_agent": "CIC Test"},
        }
        config = self._load(data)
        self.assertTrue(config.world_awareness.enabled)
        self.assertEqual(config.world_awareness.location.label, "Test")
        self.assertEqual(config.world_awareness.weather.interval_seconds, 300.0)
        self.assertEqual(config.world_awareness.alerts.interval_seconds, 60.0)
        self.assertEqual(config.world_awareness.alerts.user_agent, "CIC Test")

    def test_world_awareness_rejects_too_fast_nws_refresh(self):
        data = self._base()
        data["world_awareness"] = {"enabled": True, "alerts": {"interval_seconds": 10}}
        with self.assertRaises(ValueError):
            self._load(data)

    def test_world_awareness_surface_and_forecast_config(self):
        from personal_cic.core.config import WorldAwarenessConfig
        config=WorldAwarenessConfig.from_mapping({"enabled":True,"surface":{"station_ids":["keqy","kclt"],"interval_seconds":60},"forecast":{"interval_seconds":300,"points_refresh_seconds":21600}})
        self.assertEqual(config.surface.station_ids,("KEQY","KCLT"))
        self.assertEqual(config.surface.interval_seconds,60.0)
        self.assertEqual(config.forecast.interval_seconds,300.0)

    def test_aviationweather_interval_below_one_minute_is_rejected(self):
        from personal_cic.core.config import WorldAwarenessConfig
        with self.assertRaises(ValueError):
            WorldAwarenessConfig.from_mapping({"enabled":True,"surface":{"interval_seconds":30}})

    def test_world_awareness_provider_default_user_agents_are_real_strings(self):
        from personal_cic.core.config import WorldAwarenessConfig

        config = WorldAwarenessConfig.from_mapping({"enabled": True})

        self.assertEqual(
            config.surface.user_agent,
            "Personal-CIC/0.3.6 (local personal system)",
        )
        self.assertEqual(
            config.forecast.user_agent,
            "Personal-CIC/0.3.6 (local personal system)",
        )
        self.assertEqual(
            config.alerts.user_agent,
            "Personal-CIC/0.3.6 (local personal system)",
        )
        self.assertEqual(
            config.radar.user_agent,
            "Personal-CIC/0.3.6 (local personal system)",
        )

    def test_world_awareness_radar_config(self):
        from personal_cic.core.config import WorldAwarenessConfig

        config = WorldAwarenessConfig.from_mapping(
            {
                "enabled": True,
                "radar": {
                    "interval_seconds": 120,
                    "range_miles": 90,
                    "image_width": 1000,
                    "image_height": 700,
                    "cache_dir": "state/test-radar",
                },
            }
        )
        self.assertEqual(config.radar.interval_seconds, 120.0)
        self.assertEqual(config.radar.range_miles, 90.0)
        self.assertEqual(config.radar.image_width, 1000)
        self.assertEqual(config.radar.cache_dir, Path("state/test-radar"))
        self.assertEqual(config.radar.loop_frame_capacity, 15)
        self.assertTrue(config.radar.context_enabled)
        self.assertEqual(config.radar.context_interval_seconds, 21600.0)

    def test_world_awareness_radar_loop_and_context_config(self):
        from personal_cic.core.config import WorldAwarenessConfig

        config = WorldAwarenessConfig.from_mapping(
            {
                "enabled": True,
                "radar": {
                    "loop_frame_capacity": 9,
                    "context_enabled": False,
                    "context_interval_seconds": 7200,
                    "context_timeout_seconds": 4,
                    "context_max_age_days": 14,
                },
            }
        )
        self.assertEqual(config.radar.loop_frame_capacity, 9)
        self.assertFalse(config.radar.context_enabled)
        self.assertEqual(config.radar.context_interval_seconds, 7200.0)
        self.assertEqual(config.radar.context_timeout_seconds, 4.0)
        self.assertEqual(config.radar.context_max_age_days, 14.0)

    def test_world_awareness_rejects_invalid_radar_loop_and_context_cadence(self):
        from personal_cic.core.config import WorldAwarenessConfig

        for radar in (
            {"loop_frame_capacity": 2},
            {"loop_frame_capacity": 31},
            {"context_interval_seconds": 3599},
            {"context_timeout_seconds": 0},
            {"context_max_age_days": 0},
        ):
            with self.subTest(radar=radar):
                with self.assertRaises(ValueError):
                    WorldAwarenessConfig.from_mapping(
                        {"enabled": True, "radar": radar}
                    )

    def test_world_awareness_rejects_too_fast_radar_refresh(self):
        from personal_cic.core.config import WorldAwarenessConfig

        with self.assertRaises(ValueError):
            WorldAwarenessConfig.from_mapping(
                {"enabled": True, "radar": {"interval_seconds": 30}}
            )

    def test_runtime_rejects_nonpositive_or_nonfinite_core_intervals(self):
        for key, value in (
            ("collection_interval_seconds", 0),
            ("collection_interval_seconds", -1),
            ("snapshot_interval_seconds", 0),
            ("snapshot_interval_seconds", "nan"),
        ):
            with self.subTest(key=key, value=value):
                data = self._base()
                data[key] = value
                with self.assertRaises(ValueError):
                    self._load(data)

    def test_config_rejects_string_boolean_instead_of_coercing_it_true(self):
        data = self._base()
        data["presentation"] = {"enabled": "false"}
        with self.assertRaises(ValueError):
            self._load(data)

    def test_config_rejects_nonfinite_nested_provider_values(self):
        data = self._base()
        data["world_awareness"] = {
            "enabled": True,
            "weather": {"interval_seconds": "nan"},
        }
        with self.assertRaises(ValueError):
            self._load(data)

    def test_operator_context_requires_provenance_for_enabled_site_anchor(self):
        data = self._base()
        data["operator_context"] = {
            "site_anchor": {
                "enabled": True,
                "latitude": 35.1,
                "longitude": -80.6,
            }
        }
        with self.assertRaises(ValueError):
            self._load(data)

    def test_operator_context_requires_timezone_aware_verification_time(self):
        data = self._base()
        data["operator_context"] = {
            "site_anchor": {
                "enabled": True,
                "address": "Test",
                "latitude": 35.1,
                "longitude": -80.6,
                "source_lineage": "test",
                "source_record_id": "1",
                "source_verified_at": "2026-08-13T12:00:00",
                "source_artifact_sha256": "a" * 64,
            }
        }
        with self.assertRaises(ValueError):
            self._load(data)

    def test_nested_config_collections_reject_wrong_json_shapes(self):
        from personal_cic.core.config import WorldAwarenessConfig

        invalid = (
            {"surface": {"station_ids": "KEQY"}},
            {"traffic": {"scope_counties": "Union"}},
            {"traffic": {"tomtom": {"flow_probes": {"probe_id": "x"}}}},
        )
        for mapping in invalid:
            with self.subTest(mapping=mapping):
                with self.assertRaises(ValueError):
                    WorldAwarenessConfig.from_mapping(mapping)

    def test_runtime_root_null_is_rejected_as_config_error(self):
        with self.assertRaisesRegex(ValueError, "runtime must be a JSON object"):
            self._load(None)

    def test_config_rejects_non_string_identity_and_provenance_fields(self):
        cases = []
        data = self._base()
        data["world_awareness"] = {"location": {"label": None}}
        cases.append(data)

        data = self._base()
        data["operator_context"] = {
            "site_anchor": {
                "enabled": True,
                "label": "CIC SITE",
                "address": None,
                "latitude": 35.1,
                "longitude": -80.6,
                "source_lineage": "test",
                "source_record_id": "1",
                "source_verified_at": "2026-08-13T12:00:00Z",
                "source_artifact_sha256": "a" * 64,
            }
        }
        cases.append(data)

        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    self._load(data)

    def test_tomtom_flow_probe_rejects_non_string_identity(self):
        from personal_cic.core.config import TrafficFlowProbeConfig

        with self.assertRaises(ValueError):
            TrafficFlowProbeConfig.from_mapping(
                {"probe_id": None, "label": "x", "latitude": 35.0, "longitude": -80.0}
            )



if __name__ == "__main__":
    unittest.main()
