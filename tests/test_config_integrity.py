import json
import tempfile
import unittest
from pathlib import Path

from personal_cic.core.config import HealthThresholds


class HealthConfigIntegrityTests(unittest.TestCase):
    def _load(self, data):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "health.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return HealthThresholds.load(path)

    def _base(self):
        return {
            "cpu_warning_percent": 80,
            "cpu_critical_percent": 95,
            "memory_warning_percent": 85,
            "memory_critical_percent": 95,
            "storage_warning_percent": 90,
            "storage_critical_percent": 97,
            "temperature_warning_c": 80,
            "temperature_critical_c": 90,
            "wifi_signal_warning_dbm": -75,
        }

    def test_valid_thresholds_load(self):
        thresholds = self._load(self._base())
        self.assertEqual(thresholds.cpu_warning_percent, 80.0)
        self.assertEqual(thresholds.wifi_signal_warning_dbm, -75)

    def test_percentage_threshold_order_and_range_are_enforced(self):
        for field, value in (
            ("cpu_warning_percent", 96),
            ("memory_critical_percent", 101),
            ("storage_warning_percent", -1),
        ):
            with self.subTest(field=field, value=value):
                data = self._base()
                data[field] = value
                with self.assertRaises(ValueError):
                    self._load(data)

    def test_temperature_warning_must_be_below_critical(self):
        data = self._base()
        data["temperature_warning_c"] = 90
        with self.assertRaises(ValueError):
            self._load(data)

    def test_wifi_threshold_must_be_valid_dbm(self):
        data = self._base()
        data["wifi_signal_warning_dbm"] = 5
        with self.assertRaises(ValueError):
            self._load(data)

    def test_nan_threshold_is_rejected(self):
        data = self._base()
        data["cpu_warning_percent"] = "nan"
        with self.assertRaises(ValueError):
            self._load(data)

    def test_health_root_null_is_rejected_as_config_error(self):
        with self.assertRaisesRegex(ValueError, "health must be a JSON object"):
            self._load(None)



if __name__ == "__main__":
    unittest.main()
