import json
from pathlib import Path
import tempfile
import unittest

from personal_cic.presentation.weather_feed import build_weather_feed


class WeatherFeedTests(unittest.TestCase):
    def test_feed_projects_only_material_weather_events(self):
        records=[
            {"event_type":"ComponentUpdated","payload":{"entity_id":"local-weather-alerts","component_name":"WeatherAlertState","previous":{"active_count":0},"current":{"active_count":1,"highest_severity":"Severe"},"significance":"material","event_id":"1","occurred_at":"t1"}},
            {"event_type":"ComponentUpdated","payload":{"entity_id":"local-weather","component_name":"WeatherState","previous":{},"current":{},"significance":"sample","event_id":"2","occurred_at":"t2"}},
            {"event_type":"ComponentUpdated","payload":{"entity_id":"engage-one","component_name":"ComputeState","previous":{},"current":{},"significance":"material","event_id":"3","occurred_at":"t3"}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"events.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in records)+"\n")
            feed=build_weather_feed(path)
        self.assertEqual(len(feed),1)
        self.assertEqual(feed[0]["category"],"ALERT")
        self.assertIn("activated",feed[0]["title"])

    def test_radar_feed_names_warning_overlay_availability_change(self):
        records=[
            {"event_type":"ComponentUpdated","payload":{"entity_id":"local-weather-radar","component_name":"RadarMosaicState","previous":{"warning_overlay_available":True,"product":"BREF.QCD","range_miles":75},"current":{"warning_overlay_available":False,"product":"BREF.QCD","range_miles":75},"significance":"material","event_id":"r1","occurred_at":"t1"}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"events.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in records)+"\n")
            feed=build_weather_feed(path)
        self.assertEqual(feed[0]["category"],"RADAR")
        self.assertIn("warning-overlay availability",feed[0]["title"])
        self.assertIn("true -> false",feed[0]["detail"])

    def test_feed_suppresses_expected_reentry_provider_lifecycle(self):
        records=[
            {"event_type":"ComponentUpdated","payload":{"entity_id":"local-weather-surface","component_name":"ObservationState","previous":{"availability":"current","reasons":[]},"current":{"availability":"unavailable","reasons":["reentry: awaiting fresh AviationWeather METAR observation"]},"significance":"material","event_id":"1","occurred_at":"t1"}},
            {"event_type":"ComponentUpdated","payload":{"entity_id":"local-weather-surface","component_name":"ObservationState","previous":{"availability":"unavailable","reasons":["reentry: awaiting fresh AviationWeather METAR observation"]},"current":{"availability":"current","reasons":[]},"significance":"material","event_id":"2","occurred_at":"t2"}},
            {"event_type":"ComponentUpdated","payload":{"entity_id":"local-weather-surface","component_name":"ObservationState","previous":{"availability":"current","reasons":[]},"current":{"availability":"unavailable","reasons":["METAR request failed: timeout"]},"significance":"material","event_id":"3","occurred_at":"t3"}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"events.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in records)+"\n")
            feed=build_weather_feed(path)
        self.assertEqual(len(feed),1)
        self.assertEqual(feed[0]["category"],"PROVIDER")
        self.assertIn("UNAVAILABLE",feed[0]["title"])


import io


def _bounded_weather_record(event_id, old_code, new_code):
    return json.dumps({
        "event_type":"ComponentUpdated",
        "payload":{
            "entity_id":"local-weather",
            "significance":"material",
            "component_name":"WeatherState",
            "previous":{"weather_code":old_code},
            "current":{"weather_code":new_code},
            "occurred_at":"2026-08-24T00:00:00+00:00",
            "event_id":event_id,
        },
    },separators=(",",":")).encode()+b"\n"


class _GuardedReader(io.BytesIO):
    def __init__(self,payload):
        super().__init__(payload)
        self.max_requested=0
        self.read_calls=0

    def read(self,size=-1):
        if size < 0:
            raise AssertionError("unbounded read forbidden")
        if size > 512*1024:
            raise AssertionError(f"oversized read: {size}")
        self.max_requested=max(self.max_requested,size)
        self.read_calls+=1
        return super().read(size)


class _GuardedPath:
    def __init__(self,payload):
        self.payload=payload
        self.reader=None

    def exists(self):
        return True

    def open(self,mode):
        if mode != "rb":
            raise AssertionError(mode)
        self.reader=_GuardedReader(self.payload)
        return self.reader


class WeatherFeedBoundedAcquisitionTests(unittest.TestCase):
    def test_large_journal_acquisition_is_bounded_before_projection(self):
        path=_GuardedPath(
            b"x"*(700*1024)+b"\n"
            +_bounded_weather_record("newest",1,2)
        )
        feed=build_weather_feed(path)
        self.assertEqual([x["event_id"] for x in feed],["newest"])
        self.assertEqual(path.reader.read_calls,1)
        self.assertLessEqual(path.reader.max_requested,512*1024)

    def test_small_journal_preserves_order_and_limit(self):
        payload=b"".join(
            _bounded_weather_record(f"event-{i}",i,i+1)
            for i in range(4)
        )
        path=_GuardedPath(payload)
        feed=build_weather_feed(path,limit=2)
        self.assertEqual(
            [x["event_id"] for x in feed],
            ["event-3","event-2"],
        )
        self.assertLessEqual(path.reader.max_requested,len(payload))


if __name__ == "__main__": unittest.main()
