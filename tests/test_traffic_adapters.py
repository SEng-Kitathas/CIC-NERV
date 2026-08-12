import json
import os
import unittest
from unittest.mock import patch

from personal_cic.adapters.world.cmpd_traffic import CMPDTrafficCADAdapter
from personal_cic.adapters.world.charlotte_closures import CharlotteStreetClosuresAdapter
from personal_cic.adapters.world.drivenc_traffic import (
    DriveNCCamerasAdapter,
    DriveNCEventsAdapter,
    DriveNCMessageSignsAdapter,
)
from personal_cic.adapters.world.wzdx_traffic import DriveNCWZDxAdapter
from personal_cic.core.observations import ObservationStatus


class _Response:
    def __init__(self, payload, *, status=200):
        self.payload = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def _opener(payload):
    def open_it(_request, timeout=None):
        return _Response(payload)
    return open_it


COMMON = {
    "location_label": "Indian Trail / 28079",
    "latitude": 35.1115,
    "longitude": -80.6099,
    "radius_miles": 75.0,
}


class DriveNCAdapterTests(unittest.TestCase):
    def test_http_200_wrong_schema_is_unavailable_not_valid_empty(self):
        adapter = DriveNCEventsAdapter(
            **COMMON,
            api_key_env="TEST_DRIVENC_KEY",
            timeout_seconds=1,
            opener=_opener(json.dumps({"message": "service moved"})),
        )
        with patch.dict(os.environ, {"TEST_DRIVENC_KEY": "abc"}, clear=False):
            observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
        self.assertIsNone(observation.value)
        self.assertIn("not an array", observation.detail)

    def test_missing_api_key_is_unavailable_without_request(self):
        called = False

        def opener(*_args, **_kwargs):
            nonlocal called
            called = True
            raise AssertionError("network should not be called without a key")

        adapter = DriveNCEventsAdapter(
            **COMMON,
            api_key_env="TEST_MISSING_DRIVENC_KEY",
            timeout_seconds=1,
            opener=opener,
        )
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEST_MISSING_DRIVENC_KEY", None)
            observation = adapter.collect()[0]
        self.assertFalse(called)
        self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
        self.assertIn("TEST_MISSING_DRIVENC_KEY", observation.detail)

    def test_events_are_spatially_filtered_not_selected_by_local_words(self):
        payload = [
            {
                "ID": 1,
                "SourceId": "local-1",
                "Organization": "ATMSERS",
                "EventType": "incidents",
                "EventSubType": "crash",
                "Description": "Crash on US-74 in Mecklenburg County",
                "County": "Mecklenburg",
                "RoadwayName": "US-74",
                "Latitude": 35.12,
                "Longitude": -80.61,
            },
            {
                "ID": 2,
                "SourceId": "far-2",
                "Organization": "ATMSERS",
                "EventType": "roadwork",
                "Description": "Union Chapel Road near Matthews Mill Pond Road",
                "County": "Robeson",
                "RoadwayName": "Union Chapel Rd",
                "Latitude": 34.72,
                "Longitude": -79.11,
            },
        ]
        adapter = DriveNCEventsAdapter(
            **COMMON,
            api_key_env="KEY",
            timeout_seconds=1,
            opener=_opener(json.dumps(payload)),
        )
        with patch.dict(os.environ, {"KEY": "abc"}, clear=False):
            observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        self.assertEqual(observation.value.source_record_count, 2)
        self.assertEqual(observation.value.local_record_count, 1)
        self.assertEqual(observation.value.events[0].source_record_id, "1")

    def test_drivenc_preserves_organization_lineage_and_crowd_class(self):
        payload = [
            {
                "ID": 9,
                "SourceId": "waze-77",
                "Organization": "Waze",
                "EventType": "incident",
                "EventSubType": "POLICE",
                "Description": "Police reported",
                "County": "Union",
                "RoadwayName": "US-74",
                "Latitude": 35.10,
                "Longitude": -80.62,
            }
        ]
        adapter = DriveNCEventsAdapter(
            **COMMON,
            api_key_env="KEY",
            timeout_seconds=1,
            opener=_opener(json.dumps(payload)),
        )
        with patch.dict(os.environ, {"KEY": "abc"}, clear=False):
            event = adapter.collect()[0].value.events[0]
        self.assertEqual(event.source_family, "Waze")
        self.assertEqual(event.collection_class, "crowd_report")
        self.assertEqual(event.upstream_event_id, "waze-77")

    def test_drive_nc_failure_detail_cannot_persist_query_credential(self):
        secret = "super-secret-drive-key"

        def opener(request, timeout=None):
            raise ValueError(f"failed URL {request.full_url}")

        adapter = DriveNCEventsAdapter(
            **COMMON,
            api_key_env="KEY",
            timeout_seconds=1,
            opener=opener,
        )
        with patch.dict(os.environ, {"KEY": secret}, clear=False):
            observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.UNAVAILABLE)
        self.assertNotIn(secret, observation.detail)
        self.assertIn("<REDACTED>", observation.detail)

    def test_false_string_full_closure_is_not_promoted_to_true(self):
        payload = [{
            "ID": 10,
            "SourceId": "10",
            "Organization": "ATMSERS",
            "EventType": "roadwork",
            "Description": "Lane work",
            "County": "Mecklenburg",
            "Latitude": 35.12,
            "Longitude": -80.61,
            "IsFullClosure": "false",
        }]
        adapter = DriveNCEventsAdapter(
            **COMMON,
            api_key_env="KEY",
            timeout_seconds=1,
            opener=_opener(json.dumps(payload)),
        )
        with patch.dict(os.environ, {"KEY": "abc"}, clear=False):
            event = adapter.collect()[0].value.events[0]
        self.assertIs(event.full_closure, False)

    def test_camera_preserves_direct_hls_view_without_promoting_it_to_event(self):
        payload = [
            {
                "Id": 4020,
                "SourceId": "5135",
                "Source": "IVDs-Division 10",
                "County": "Mecklenburg",
                "Roadway": "I-485",
                "Direction": "Outer",
                "Location": "CCTV10-I485-30.1O_I85",
                "Latitude": 35.13,
                "Longitude": -80.70,
                "Views": [
                    {
                        "Status": "Enabled",
                        "Url": "https://www.drivenc.gov/map/Cctv/4020",
                        "VideoUrl": "https://example.invalid/camera.m3u8",
                    }
                ],
            }
        ]
        adapter = DriveNCCamerasAdapter(
            **COMMON,
            api_key_env="KEY",
            timeout_seconds=1,
            opener=_opener(json.dumps(payload)),
        )
        with patch.dict(os.environ, {"KEY": "abc"}, clear=False):
            camera = adapter.collect()[0].value.cameras[0]
        self.assertEqual(camera.camera_id, "4020")
        self.assertTrue(camera.video_url.endswith(".m3u8"))
        self.assertEqual(camera.source_family, "NCDOT/IVDs-Division 10")

    def test_message_sign_no_message_is_valid_negative_infrastructure_state(self):
        payload = [
            {
                "Id": "A",
                "County": "Union",
                "Roadway": "US-74",
                "DirectionOfTravel": "Unknown",
                "Name": "DMS-A",
                "Latitude": 35.10,
                "Longitude": -80.67,
                "LastUpdated": 1786510521,
                "Messages": ["NO_MESSAGE"],
            },
            {
                "Id": "B",
                "County": "Mecklenburg",
                "Roadway": "I-277",
                "DirectionOfTravel": "Unknown",
                "Name": "DMS-B",
                "Latitude": 35.22,
                "Longitude": -80.85,
                "LastUpdated": 1786510549,
                "Messages": ["LEFT\nLANE\nCLOSED", "REDUCE\nSPEED"],
            },
        ]
        adapter = DriveNCMessageSignsAdapter(
            **COMMON,
            api_key_env="KEY",
            timeout_seconds=1,
            opener=_opener(json.dumps(payload)),
        )
        with patch.dict(os.environ, {"KEY": "abc"}, clear=False):
            state = adapter.collect()[0].value
        self.assertEqual(state.local_record_count, 2)
        self.assertEqual(state.active_message_count, 1)
        self.assertEqual(state.source_family, "NCDOT/ATMS DMS")
        self.assertEqual(state.signs[0].messages, ("NO_MESSAGE",))


class OtherTrafficAdapterTests(unittest.TestCase):
    def test_wzdx_uses_geometry_and_preserves_atmsers_upstream_identity(self):
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "1196-1",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-80.62, 35.11], [-80.63, 35.12]],
                    },
                    "properties": {
                        "road_event_id": "1196",
                        "start_date": "2026-06-02T23:00:00Z",
                        "end_date": "2026-09-30T10:00:00Z",
                        "vehicle_impact": "all-lanes-closed",
                        "lanes": [{"type": "general", "status": "closed"}],
                        "core_details": {
                            "data_source_id": "ATMSERS",
                            "description": "Construction on I-277",
                            "direction": "eastbound",
                            "event_type": "work-zone",
                            "road_names": ["I-277"],
                            "update_date": "2026-07-24T20:01:00Z",
                        },
                    },
                }
            ],
        }
        adapter = DriveNCWZDxAdapter(**COMMON, timeout_seconds=1, opener=_opener(json.dumps(payload)))
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        event = observation.value.events[0]
        self.assertEqual(event.source_family, "NCDOT/ATMSERS")
        self.assertEqual(event.upstream_event_id, "1196")
        self.assertTrue(event.full_closure)
        self.assertEqual(len(event.geometry), 2)

    def test_cmpd_live_table_is_a_distinct_official_reporting_lineage(self):
        page = """
        <table><tr><th>Event Date/Time</th><th>Division</th><th>Address</th><th>Description</th></tr>
        <tr><td>8/11/2026 11:18:45 PM</td><td>STEELE CREEK</td><td>426 WESTINGHOUSE BV</td><td>ACCIDENT IN ROADWAY-PROPERTY DAMAGE</td></tr></table>
        """
        adapter = CMPDTrafficCADAdapter(**COMMON, timeout_seconds=1, opener=_opener(page))
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        event = observation.value.events[0]
        self.assertEqual(event.source_family, "CMPD CAD")
        self.assertEqual(event.collection_class, "official_report")
        self.assertEqual(event.reported_at, "2026-08-12T03:18:45+00:00")
        self.assertEqual(event.geometry, ())

    def test_charlotte_layer_zero_is_queried_as_geojson_feature_layer(self):
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": 7,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-80.61, 35.11], [-80.62, 35.12]],
                    },
                    "properties": {
                        "StreetName": "Example Rd",
                        "Description": "Bridge closure",
                        "ClosureType": "full closure",
                        "Status": "Full Closed",
                    },
                }
            ],
        }
        adapter = CharlotteStreetClosuresAdapter(
            **COMMON, timeout_seconds=1, opener=_opener(json.dumps(payload))
        )
        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        state = observation.value
        self.assertEqual(state.local_record_count, 1)
        self.assertEqual(state.events[0].source_family, "City of Charlotte/CDOT")
        self.assertEqual(state.events[0].roadway, "Example Rd")

    def test_charlotte_current_cdot_schema_preserves_identity_and_epoch_milliseconds(self):
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": 42,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-80.61, 35.11], [-80.62, 35.12]],
                    },
                    "properties": {
                        "ClosureID": "closure-42",
                        "BLOCKNM": "Example Blvd",
                        "LOCDESC": "Between A St and B St",
                        "COMMENT": "Utility repair",
                        "BLOCKTYPE": "Construction",
                        "ClosureType": "Street",
                        "FULLCLOSE": "Yes",
                        "DIRECTION": "EAST",
                        "ACTIVE": "Yes",
                        "STARTDATE": 1786507200000,
                        "ENDDATE": 1786514400000,
                        "CreationDate": 1786500000000,
                        "last_edited_date": 1786503600000,
                        "SpecialProject": "TEST",
                    },
                }
            ],
        }
        adapter = CharlotteStreetClosuresAdapter(
            **COMMON, timeout_seconds=1, opener=_opener(json.dumps(payload))
        )
        self.assertIn("gis.charlottenc.gov", adapter._url())
        self.assertIn("StreetClosuresAndDetours%2FMapServer%2F0%2Fquery", adapter._url().replace("/", "%2F"))
        self.assertIn("ACTIVE+%3D+%27Yes%27", adapter._url())

        observation = adapter.collect()[0]
        self.assertEqual(observation.status, ObservationStatus.OBSERVED)
        event = observation.value.events[0]
        self.assertEqual(event.source_record_id, "closure-42")
        self.assertEqual(event.roadway, "Example Blvd")
        self.assertEqual(event.event_type, "Construction")
        self.assertEqual(event.event_subtype, "Street")
        self.assertTrue(event.full_closure)
        self.assertEqual(event.direction, "EAST")
        self.assertIn("Between A St and B St", event.description)
        self.assertIn("Utility repair", event.description)
        self.assertTrue(event.start_at.startswith("2026-"))
        self.assertTrue(event.updated_at.startswith("2026-"))


if __name__ == "__main__":
    unittest.main()
