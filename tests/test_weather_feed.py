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


if __name__ == "__main__": unittest.main()
