import unittest
from unittest.mock import patch

from personal_cic.adapters.linux.host import LinuxHostAdapter
from personal_cic.core.config import HealthThresholds
from personal_cic.holons.systems.materiality import telemetry_significance


THRESHOLDS = HealthThresholds(
    cpu_warning_percent=80,
    cpu_critical_percent=95,
    memory_warning_percent=85,
    memory_critical_percent=95,
    storage_warning_percent=90,
    storage_critical_percent=97,
    temperature_warning_c=80,
    temperature_critical_c=90,
    wifi_signal_warning_dbm=-75,
)


class _Reading:
    def __init__(self, current, label):
        self.current = current
        self.label = label


class TemperatureSourceStabilityTests(unittest.TestCase):
    @patch("personal_cic.adapters.linux.host.psutil.sensors_temperatures")
    def test_hottest_sensor_handoff_keeps_logical_source_stable(self, mocked):
        mocked.side_effect = [
            {
                "coretemp": [
                    _Reading(47.0, "Package id 0"),
                    _Reading(50.0, "Core 0"),
                ]
            },
            {
                "coretemp": [
                    _Reading(51.0, "Package id 0"),
                    _Reading(48.0, "Core 0"),
                ]
            },
        ]

        first = LinuxHostAdapter._temperature()
        second = LinuxHostAdapter._temperature()

        self.assertEqual(first.value.celsius, 50.0)
        self.assertEqual(second.value.celsius, 51.0)
        self.assertEqual(
            first.value.source,
            "psutil:sensors_temperatures:max",
        )
        self.assertEqual(first.value.source, second.value.source)
        self.assertEqual(
            telemetry_significance(
                first.value,
                second.value,
                THRESHOLDS,
            ),
            "sample",
        )

    @patch("personal_cic.adapters.linux.host.psutil.sensors_temperatures")
    def test_logical_temperature_is_maximum_across_exposed_sensors(self, mocked):
        mocked.return_value = {
            "coretemp": [
                _Reading(46.0, "Package id 0"),
                _Reading(49.0, "Core 0"),
            ],
            "acpitz": [
                _Reading(52.0, "temp1"),
            ],
        }

        observation = LinuxHostAdapter._temperature()

        self.assertEqual(observation.value.celsius, 52.0)
        self.assertEqual(
            observation.value.source,
            "psutil:sensors_temperatures:max",
        )


if __name__ == "__main__":
    unittest.main()
