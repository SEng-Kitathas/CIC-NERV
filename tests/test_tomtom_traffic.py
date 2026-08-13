import json
import os
import unittest
from unittest.mock import patch

from personal_cic.adapters.world.tomtom_traffic import (
    FlowProbeSpec,
    TomTomFlowAdapter,
    TomTomIncidentsAdapter,
)
from personal_cic.core.config import TomTomTrafficConfig
from personal_cic.core.observations import ObservationStatus


class _Response:
    def __init__(self, payload):
        self.payload = payload if isinstance(payload, bytes) else payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


COMMON = {
    "location_label": "Indian Trail / 28079",
    "latitude": 35.1115,
    "longitude": -80.6099,
    "radius_miles": 75.0,
    "api_key_env": "TEST_TOMTOM_KEY",
    "timeout_seconds": 1,
}


def incident_payload(*, incident_id="TTI-1", lat=35.12, lon=-80.61, reports=1):
    return {
        "incidents": [
            {
                "type": "Feature",
                "properties": {
                    "id": incident_id,
                    "iconCategory": "jam",
                    "magnitudeOfDelay": "major",
                    "startTime": "2026-08-12T15:09:30Z",
                    "endTime": "2026-08-12T15:44:30Z",
                    "from": "South Main Street",
                    "to": "Park Avenue",
                    "lengthInMeters": 119.1,
                    "delayInSeconds": 201,
                    "roadNumbers": ["US-74"],
                    "timeValidity": "present",
                    "probabilityOfOccurrence": "certain",
                    "numberOfReports": reports,
                    "lastReportTime": "2025-06-26T23:36:00Z" if reports else None,
                    "events": [
                        {
                            "code": 101,
                            "description": "Stopped traffic",
                            "iconCategory": "jam",
                        }
                    ],
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon, lat], [lon - 0.001, lat]],
                },
            }
        ]
    }


def flow_payload(*, speed=22, free=44, openlr="C8aADRkMbBZIBwGK/1UWHA=="):
    return {
        "flowSegmentData": {
            "frc": "FRC2",
            "currentSpeed": speed,
            "freeFlowSpeed": free,
            "currentTravelTime": 86,
            "freeFlowTravelTime": 43,
            "confidence": 1,
            "roadClosure": False,
            "coordinates": {
                "coordinate": [
                    {"latitude": 35.22448, "longitude": -80.85910},
                    {"latitude": 35.22366, "longitude": -80.85613},
                ]
            },
            "openlr": openlr,
            "@version": "4",
        }
    }


class TomTomIncidentAdapterTests(unittest.TestCase):
    def test_api_key_is_header_only_and_same_incident_is_deduped_across_tiles(self):
        requests = []

        def opener(request, timeout=None):
            requests.append(request)
            return _Response(json.dumps(incident_payload()))

        adapter = TomTomIncidentsAdapter(**COMMON, opener=opener)
        with patch.dict(os.environ, {"TEST_TOMTOM_KEY": "secret-key-123"}, clear=False):
            observation = adapter.collect()[0]

        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        self.assertEqual(len(requests), 9)
        self.assertEqual(observation.value.source_record_count, 1)
        self.assertEqual(observation.value.local_record_count, 1)
        for request in requests:
            self.assertNotIn("secret-key-123", request.full_url)
            headers = {k.casefold(): v for k, v in request.header_items()}
            self.assertEqual(headers["tomtom-api-key"], "secret-key-123")

    def test_current_incident_preserves_stale_community_metadata_without_becoming_crowd_lineage(self):
        adapter = TomTomIncidentsAdapter(
            **COMMON,
            opener=lambda *_args, **_kwargs: _Response(json.dumps(incident_payload())),
        )
        with patch.dict(os.environ, {"TEST_TOMTOM_KEY": "abc123456789"}, clear=False):
            event = adapter.collect()[0].value.events[0]

        self.assertEqual(event.source_family, "TomTom Traffic")
        self.assertEqual(event.collection_class, "commercial_report")
        self.assertEqual(event.community_report_count, 1)
        self.assertEqual(event.community_last_report_at, "2025-06-26T23:36:00+00:00")
        self.assertEqual(event.event_details, ("Stopped traffic",))
        self.assertEqual(event.event_codes, (101,))
        self.assertEqual(event.road_numbers, ("US-74",))
        self.assertIsNone(event.full_closure)

    def test_spatial_filter_uses_geometry_not_road_name(self):
        far = incident_payload(incident_id="far", lat=34.0, lon=-79.0)
        adapter = TomTomIncidentsAdapter(
            **COMMON,
            opener=lambda *_args, **_kwargs: _Response(json.dumps(far)),
        )
        with patch.dict(os.environ, {"TEST_TOMTOM_KEY": "abc123456789"}, clear=False):
            observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        self.assertEqual(observation.value.source_record_count, 1)
        self.assertEqual(observation.value.local_record_count, 0)

    def test_wrong_200_schema_is_unavailable_not_valid_empty(self):
        adapter = TomTomIncidentsAdapter(
            **COMMON,
            opener=lambda *_args, **_kwargs: _Response(json.dumps({"message": "moved"})),
        )
        with patch.dict(os.environ, {"TEST_TOMTOM_KEY": "abc123456789"}, clear=False):
            observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
        self.assertIsNone(observation.value)
        self.assertIn("payload is not an object with an incidents array", observation.detail)

    def test_one_failed_tile_yields_partial_useful_state(self):
        calls = 0

        def opener(_request, timeout=None):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TimeoutError("first tile timed out")
            return _Response(json.dumps(incident_payload()))

        adapter = TomTomIncidentsAdapter(**COMMON, opener=opener)
        with patch.dict(os.environ, {"TEST_TOMTOM_KEY": "abc123456789"}, clear=False):
            observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.PARTIAL)
        self.assertEqual(observation.value.local_record_count, 1)
        self.assertIn("1 of 9 bounded incident requests unavailable", observation.detail)


class TomTomFlowAdapterTests(unittest.TestCase):
    def test_flow_preserves_query_reference_and_matched_segment_identity(self):
        probe = FlowProbeSpec("uptown-ref", "I-277 Uptown reference", 35.22441, -80.85751)
        requests = []

        def opener(request, timeout=None):
            requests.append(request)
            return _Response(json.dumps(flow_payload()))

        adapter = TomTomFlowAdapter(**COMMON, probes=(probe,), opener=opener)
        with patch.dict(os.environ, {"TEST_TOMTOM_KEY": "secret-flow-key"}, clear=False):
            observation = adapter.collect()[0]

        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        state = observation.value
        self.assertEqual(state.successful_probe_count, 1)
        result = state.probes[0]
        self.assertEqual(result.label, "I-277 Uptown reference")
        self.assertEqual(result.match_method, "nearest_road_fragment_to_query_point")
        self.assertEqual(result.functional_road_class, "FRC2")
        self.assertEqual(result.current_speed_mph, 22)
        self.assertEqual(result.free_flow_speed_mph, 44)
        self.assertEqual(result.openlr, "C8aADRkMbBZIBwGK/1UWHA==")
        self.assertEqual(len(result.geometry), 2)
        self.assertIn("key=secret-flow-key", requests[0].full_url)

    def test_flow_request_failure_redacts_query_key(self):
        secret = "secret-flow-key"

        def opener(request, timeout=None):
            raise ValueError(f"failed URL {request.full_url}")

        adapter = TomTomFlowAdapter(
            **COMMON,
            probes=(FlowProbeSpec("one", "one", 35.1, -80.6),),
            opener=opener,
        )
        with patch.dict(os.environ, {"TEST_TOMTOM_KEY": secret}, clear=False):
            observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
        self.assertNotIn(secret, observation.detail)
        self.assertIn("<REDACTED>", observation.detail)

    def test_some_probe_failures_are_partial_not_absent(self):
        calls = 0

        def opener(_request, timeout=None):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise TimeoutError("probe unavailable")
            return _Response(json.dumps(flow_payload()))

        probes = (
            FlowProbeSpec("one", "one", 35.1, -80.6),
            FlowProbeSpec("two", "two", 35.2, -80.7),
        )
        adapter = TomTomFlowAdapter(**COMMON, probes=probes, opener=opener)
        with patch.dict(os.environ, {"TEST_TOMTOM_KEY": "abc123456789"}, clear=False):
            observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.PARTIAL)
        self.assertEqual(observation.value.configured_probe_count, 2)
        self.assertEqual(observation.value.successful_probe_count, 1)


class TomTomConfigTests(unittest.TestCase):
    def test_default_probe_ids_are_unique_and_labels_are_reference_not_identity_claims(self):
        config = TomTomTrafficConfig()
        ids = [probe.probe_id for probe in config.flow_probes]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(config.api_key_env, "TOMTOM_API_KEY")
        self.assertGreaterEqual(config.incidents_interval_seconds, 900)
        self.assertGreaterEqual(config.flow_interval_seconds, 60)
        self.assertTrue(all(probe.label for probe in config.flow_probes))

    def test_duplicate_probe_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "probe_id values must be unique"):
            TomTomTrafficConfig.from_mapping({
                "flow_probes": [
                    {"probe_id": "x", "label": "a", "latitude": 35.1, "longitude": -80.6},
                    {"probe_id": "x", "label": "b", "latitude": 35.2, "longitude": -80.7},
                ]
            })


if __name__ == "__main__":
    unittest.main()
