import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

from personal_cic.adapters.world.radar_context import TIGERRadarContextAdapter
from personal_cic.core.observations import ObservationStatus
from personal_cic.core.world.components import RadarContextState


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def _geo_feature(geometry_type, coordinates, name):
    return {
        "type": "Feature",
        "properties": {"BASENAME": name},
        "geometry": {"type": geometry_type, "coordinates": coordinates},
    }


class RadarContextTests(unittest.TestCase):
    def _payload_for_url(self, url: str) -> bytes:
        if "State_County" in url:
            payload = {
                "type": "FeatureCollection",
                "features": [
                    _geo_feature(
                        "Polygon",
                        [[[-81.0, 34.5], [-80.0, 34.5], [-80.0, 35.5], [-81.0, 34.5]]],
                        "Union",
                    )
                ],
            }
        elif "Transportation/MapServer/1" in url:
            payload = {
                "type": "FeatureCollection",
                "features": [
                    _geo_feature(
                        "LineString",
                        [[-81.0, 35.0], [-80.0, 35.2]],
                        "I-485",
                    )
                ],
            }
        elif "Transportation/MapServer/3" in url:
            payload = {
                "type": "FeatureCollection",
                "features": [
                    _geo_feature(
                        "LineString",
                        [[-80.9, 35.1], [-80.1, 35.1]],
                        "US 74",
                    )
                ],
            }
        elif "MapServer/4" in url:
            payload = {
                "features": [
                    {"attributes": {"BASENAME": "Monroe", "INTPTLAT": "35.0", "INTPTLON": "-80.55"}}
                ]
            }
        elif "MapServer/5" in url:
            payload = {
                "features": [
                    {"attributes": {"BASENAME": "Indian Trail", "INTPTLAT": "35.08", "INTPTLON": "-80.66"}}
                ]
            }
        else:
            raise AssertionError(url)
        return json.dumps(payload).encode()

    def _adapter(self, cache, *, opener, now):
        return TIGERRadarContextAdapter(
            location_label="Test",
            latitude=35.1115,
            longitude=-80.6099,
            range_miles=75,
            image_width=900,
            image_height=600,
            cache_dir=cache,
            user_agent="CIC Test",
            max_age_days=30,
            opener=opener,
            now=now,
        )

    def test_tiger_context_queries_expected_layers_with_bbox_and_4326(self):
        with tempfile.TemporaryDirectory() as tmp:
            urls = []

            def opener(request, **_kwargs):
                urls.append(request.full_url)
                return _Response(self._payload_for_url(request.full_url))

            adapter = self._adapter(
                Path(tmp), opener=opener,
                now=lambda: datetime(2026, 8, 12, 2, 0, tzinfo=timezone.utc),
            )
            observation = adapter.collect()[0]

            self.assertEqual(observation.status, ObservationStatus.OBSERVED)
            self.assertIsInstance(observation.value, RadarContextState)
            self.assertEqual(len(urls), 5)
            self.assertTrue(any("State_County/MapServer/1/query" in u for u in urls))
            self.assertTrue(any("Transportation/MapServer/1/query" in u for u in urls))
            self.assertTrue(any("Transportation/MapServer/3/query" in u for u in urls))
            self.assertTrue(any("MapServer/4/query" in u for u in urls))
            self.assertTrue(any("MapServer/5/query" in u for u in urls))
            for url in urls:
                query = parse_qs(urlsplit(url).query)
                self.assertEqual(query["inSR"], ["4326"])
                self.assertEqual(query["outSR"], ["4326"])
                self.assertEqual(query["geometryType"], ["esriGeometryEnvelope"])
                self.assertIn("geometry", query)

    def test_context_artifact_hash_changes_with_refresh_time_but_content_hash_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = [datetime(2026, 8, 12, 2, 0, tzinfo=timezone.utc)]

            def opener(request, **_kwargs):
                return _Response(self._payload_for_url(request.full_url))

            adapter = self._adapter(Path(tmp), opener=opener, now=lambda: clock[0])
            first = adapter.collect()[0].value
            clock[0] += timedelta(hours=6)
            second = adapter.collect()[0].value

            self.assertNotEqual(first.retrieved_at, second.retrieved_at)
            self.assertNotEqual(first.context_sha256, second.context_sha256)
            self.assertEqual(first.content_sha256, second.content_sha256)
            payload = json.loads((Path(tmp) / "context.json").read_text())
            self.assertEqual(payload["content_sha256"], second.content_sha256)
            self.assertEqual(second.county_count, 1)
            self.assertEqual(second.primary_road_count, 1)
            self.assertEqual(second.secondary_road_count, 1)
            self.assertEqual(second.place_count, 2)


    def test_context_content_hash_is_stable_when_service_feature_order_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = [datetime(2026, 8, 12, 2, 0, tzinfo=timezone.utc)]
            reverse = [False]

            def opener(request, **_kwargs):
                payload = json.loads(self._payload_for_url(request.full_url))
                if payload.get("type") == "FeatureCollection":
                    feature = payload["features"][0]
                    other = json.loads(json.dumps(feature))
                    other["properties"]["BASENAME"] = "ZZZ " + str(
                        other["properties"].get("BASENAME", "")
                    )
                    payload["features"] = [feature, other]
                    if reverse[0]:
                        payload["features"].reverse()
                return _Response(json.dumps(payload).encode())

            adapter = self._adapter(Path(tmp), opener=opener, now=lambda: clock[0])
            first = adapter.collect()[0].value
            reverse[0] = True
            clock[0] += timedelta(hours=6)
            second = adapter.collect()[0].value

            self.assertNotEqual(first.context_sha256, second.context_sha256)
            self.assertEqual(first.content_sha256, second.content_sha256)

    def test_context_refresh_failure_uses_recent_valid_cache_as_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = [datetime(2026, 8, 12, 2, 0, tzinfo=timezone.utc)]

            def good(request, **_kwargs):
                return _Response(self._payload_for_url(request.full_url))

            adapter = self._adapter(Path(tmp), opener=good, now=lambda: clock[0])
            current = adapter.collect()[0]
            self.assertEqual(current.status, ObservationStatus.OBSERVED)

            clock[0] += timedelta(days=1)
            adapter.opener = lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("offline"))
            fallback = adapter.collect()[0]
            self.assertEqual(fallback.status, ObservationStatus.PARTIAL)
            self.assertEqual(fallback.value.context_sha256, current.value.context_sha256)
            self.assertIn("using cached context", fallback.detail)

    def test_context_stale_or_hash_corrupt_cache_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = [datetime(2026, 8, 12, 2, 0, tzinfo=timezone.utc)]

            def good(request, **_kwargs):
                return _Response(self._payload_for_url(request.full_url))

            adapter = self._adapter(Path(tmp), opener=good, now=lambda: clock[0])
            self.assertEqual(adapter.collect()[0].status, ObservationStatus.OBSERVED)

            cache = Path(tmp) / "context.json"
            data = json.loads(cache.read_text())
            data["places"].append({"name": "Tampered", "lat": 35.0, "lon": -80.0})
            cache.write_text(json.dumps(data))
            adapter.opener = lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("offline"))
            corrupt = adapter.collect()[0]
            self.assertEqual(corrupt.status, ObservationStatus.UNAVAILABLE)

            # Restore a valid cache, then age it beyond policy.
            adapter.opener = good
            self.assertEqual(adapter.collect()[0].status, ObservationStatus.OBSERVED)
            clock[0] += timedelta(days=31)
            adapter.opener = lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("offline"))
            stale = adapter.collect()[0]
            self.assertEqual(stale.status, ObservationStatus.UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()
