import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError

from personal_cic.adapters.world.radar_mosaic import MRMSRadarMosaicAdapter
from personal_cic.core.observations import ObservationStatus
from personal_cic.core.world.components import RadarMosaicState


PNG = b"\x89PNG\r\n\x1a\n" + b"radar-test"
WARN_PNG = b"\x89PNG\r\n\x1a\n" + b"warning-test"
LEGEND_PNG = b"\x89PNG\r\n\x1a\n" + b"legend-test"


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class RadarAdapterTests(unittest.TestCase):
    def _listing(self):
        return b"\n".join(
            [
                b"CONUS_L2_BREF_QCD_20260812_010000.tif.gz",
                b"CONUS_L2_BREF_QCD_20260812_010200.tif.gz",
                b"CONUS_L2_BREF_QCD_20260812_010400.tif.gz",
            ]
        )

    def test_radar_adapter_uses_latest_index_time_and_caches_local_pngs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "radar"
            urls = []

            def opener(request, **_kwargs):
                url = request.full_url
                urls.append(url)
                if "RIDGEII" in url:
                    return _Response(self._listing())
                if "GetLegendGraphic" in url:
                    return _Response(LEGEND_PNG)
                if "/wwa/warnings/" in url:
                    return _Response(WARN_PNG)
                if "conus_bref_qcd" in url:
                    return _Response(PNG)
                raise AssertionError(url)

            adapter = MRMSRadarMosaicAdapter(
                location_label="Test",
                latitude=35.1115,
                longitude=-80.6099,
                range_miles=75,
                image_width=900,
                image_height=600,
                max_age_minutes=15,
                cache_dir=cache,
                user_agent="CIC Test",
                opener=opener,
                now=lambda: datetime(2026, 8, 12, 1, 5, tzinfo=timezone.utc),
            )
            observation = adapter.collect()[0]

            self.assertEqual(observation.status, ObservationStatus.OBSERVED)
            self.assertIsInstance(observation.value, RadarMosaicState)
            self.assertEqual(
                observation.value.stream_latest_at,
                "2026-08-12T01:04:00+00:00",
            )
            self.assertEqual(
                observation.value.frame_retrieved_at,
                "2026-08-12T01:05:00+00:00",
            )
            self.assertEqual(
                observation.value.stream_latest_filename,
                "CONUS_L2_BREF_QCD_20260812_010400.tif.gz",
            )
            self.assertEqual(observation.value.product, "BREF.QCD")
            self.assertTrue(observation.value.warning_overlay_available)
            self.assertTrue(observation.value.legend_available)
            self.assertEqual((cache / "latest.png").read_bytes(), PNG)
            self.assertEqual((cache / "warnings.png").read_bytes(), WARN_PNG)
            self.assertEqual((cache / "legend.png").read_bytes(), LEGEND_PNG)
            radar_url = next(url for url in urls if "REQUEST=GetMap" in url and "conus_bref_qcd" in url)
            self.assertIn("SRS=EPSG%3A4326", radar_url)
            self.assertIn("WIDTH=900", radar_url)
            self.assertIn("HEIGHT=600", radar_url)
            self.assertIn("LAYERS=conus_bref_qcd", radar_url)

    def test_radar_bbox_preserves_equal_distance_scale_for_wide_image(self):
        adapter = MRMSRadarMosaicAdapter(
            location_label="Test",
            latitude=35.0,
            longitude=-80.0,
            range_miles=75,
            image_width=900,
            image_height=600,
            max_age_minutes=15,
            cache_dir=Path("state/radar"),
            user_agent="CIC Test",
        )
        west, south, east, north = adapter._bbox()
        lat_miles = (north - south) * 69.0
        lon_miles = (east - west) * 69.0 * __import__("math").cos(__import__("math").radians(35.0))
        self.assertAlmostEqual(lat_miles, 150.0, places=5)
        self.assertAlmostEqual(lon_miles / lat_miles, 1.5, places=5)

    def test_valid_cached_legend_is_reused_without_network_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "radar"
            cache.mkdir()
            (cache / "legend.png").write_bytes(LEGEND_PNG)
            urls = []

            def opener(request, **_kwargs):
                url = request.full_url
                urls.append(url)
                if "RIDGEII" in url:
                    return _Response(self._listing())
                if "/wwa/warnings/" in url:
                    return _Response(WARN_PNG)
                if "conus_bref_qcd" in url:
                    return _Response(PNG)
                if "GetLegendGraphic" in url:
                    raise AssertionError("cached legend should have been reused")
                raise AssertionError(url)

            adapter = MRMSRadarMosaicAdapter(
                location_label="Test",
                latitude=35.1,
                longitude=-80.6,
                range_miles=75,
                image_width=900,
                image_height=600,
                max_age_minutes=15,
                cache_dir=cache,
                user_agent="CIC Test",
                opener=opener,
                now=lambda: datetime(2026, 8, 12, 1, 5, tzinfo=timezone.utc),
            )
            observation = adapter.collect()[0]
            self.assertEqual(observation.status, ObservationStatus.OBSERVED)
            self.assertTrue(observation.value.legend_available)
            self.assertFalse(any("GetLegendGraphic" in url for url in urls))

    def test_stale_radar_index_is_unavailable_without_overwriting_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "radar"
            cache.mkdir()
            old = b"\x89PNG\r\n\x1a\nold"
            (cache / "latest.png").write_bytes(old)

            adapter = MRMSRadarMosaicAdapter(
                location_label="Test",
                latitude=35.1,
                longitude=-80.6,
                range_miles=75,
                image_width=900,
                image_height=600,
                max_age_minutes=15,
                cache_dir=cache,
                user_agent="CIC Test",
                opener=lambda *_args, **_kwargs: _Response(
                    b"CONUS_L2_BREF_QCD_20260812_000000.tif.gz"
                ),
                now=lambda: datetime(2026, 8, 12, 1, 0, tzinfo=timezone.utc),
            )
            observation = adapter.collect()[0]
            self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
            self.assertIsNone(observation.value)
            self.assertEqual((cache / "latest.png").read_bytes(), old)

    def test_warning_overlay_failure_degrades_radar_and_removes_stale_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "radar"
            cache.mkdir()
            (cache / "warnings.png").write_bytes(WARN_PNG)

            def opener(request, **_kwargs):
                url = request.full_url
                if "RIDGEII" in url:
                    return _Response(self._listing())
                if "GetLegendGraphic" in url:
                    return _Response(LEGEND_PNG)
                if "/wwa/warnings/" in url:
                    raise URLError("warning service down")
                if "conus_bref_qcd" in url:
                    return _Response(PNG)
                raise AssertionError(url)

            adapter = MRMSRadarMosaicAdapter(
                location_label="Test",
                latitude=35.1,
                longitude=-80.6,
                range_miles=75,
                image_width=900,
                image_height=600,
                max_age_minutes=15,
                cache_dir=cache,
                user_agent="CIC Test",
                opener=opener,
                now=lambda: datetime(2026, 8, 12, 1, 5, tzinfo=timezone.utc),
            )
            observation = adapter.collect()[0]
            self.assertEqual(observation.status, ObservationStatus.PARTIAL)
            self.assertIsInstance(observation.value, RadarMosaicState)
            self.assertFalse(observation.value.warning_overlay_available)
            self.assertFalse((cache / "warnings.png").exists())
            self.assertIn("warning overlay unavailable", observation.detail)


if __name__ == "__main__":
    unittest.main()
