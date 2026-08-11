import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from personal_cic.adapters.tenda.u11_pro import TendaU11ProAdapter, _CommandResult
from personal_cic.bootstrap import (
    TENDA_ID,
    _ingest_observation_batch,
    create_context,
    reconcile_topology,
)
from personal_cic.core.events import EventBus, EventJournal
from personal_cic.core.observations import Observation, ObservationAvailability
from personal_cic.core.world.components import (
    HealthState,
    HealthStatus,
    ObservationState,
    UsbDeviceState,
    WifiLinkState,
)


class ObservationIntegrityTests(unittest.TestCase):
    def _context(self):
        context = create_context()
        reconcile_topology(context)
        return context

    def test_successful_lsusb_without_tenda_is_observed_absence(self):
        with patch(
            "personal_cic.adapters.tenda.u11_pro._run",
            return_value=_CommandResult(True, "Bus 001 Device 001: ID 1d6b:0002 Linux Foundation"),
        ):
            observation = TendaU11ProAdapter._usb_state()

        self.assertIsNotNone(observation.value)
        self.assertFalse(observation.value.present)
        self.assertEqual(observation.value.mode, "absent")

    def test_lsusb_failure_is_unavailable_not_device_absence(self):
        with patch(
            "personal_cic.adapters.tenda.u11_pro._run",
            return_value=_CommandResult(False, detail="command not found: lsusb"),
        ):
            observation = TendaU11ProAdapter._usb_state()

        self.assertIsNone(observation.value)
        self.assertEqual(observation.status.value, "unavailable")


    def test_connected_link_missing_signal_is_partial_not_complete(self):
        def fake_run(*args):
            if args == ("iw", "dev"):
                return _CommandResult(True, "phy#0\n\tInterface wlan0")
            if args == ("iw", "dev", "wlan0", "link"):
                return _CommandResult(
                    True,
                    "Connected to aa:bb:cc:dd:ee:ff (on wlan0)\n"
                    "\tSSID: home\n"
                    "\tfreq: 5785",
                )
            if args == ("ip", "-4", "-br", "addr", "show", "wlan0"):
                return _CommandResult(True, "wlan0 UP 192.168.1.2/24")
            raise AssertionError(args)

        with patch("personal_cic.adapters.tenda.u11_pro._run", side_effect=fake_run):
            observation = TendaU11ProAdapter._wifi_state()

        self.assertEqual(observation.status.value, "partial")
        self.assertIsNotNone(observation.value)
        self.assertTrue(observation.value.connected)
        self.assertIsNone(observation.value.signal_dbm)
        self.assertIn("missing signal", observation.detail)

    def test_unavailable_batch_preserves_prior_domain_state_and_marks_health_unknown(self):
        context = self._context()
        prior_usb = UsbDeviceState(True, "2604:0020", "Tenda", "wifi")
        prior_wifi = WifiLinkState("wlan0", True, "home", 5220, -60, 300.0, 300.0, "192.168.1.2/24")
        context.world.upsert_component(TENDA_ID, prior_usb)
        context.world.upsert_component(TENDA_ID, prior_wifi)

        _ingest_observation_batch(
            context,
            entity_id=TENDA_ID,
            adapter_id="tenda.u11_pro",
            observations=(
                Observation.unavailable("usb.lsusb", "lsusb unavailable"),
                Observation.unavailable("wifi.iw_dev", "iw unavailable"),
            ),
        )

        entity = context.world.entities[TENDA_ID]
        self.assertEqual(entity.get(UsbDeviceState), prior_usb)
        self.assertEqual(entity.get(WifiLinkState), prior_wifi)
        observation = entity.get(ObservationState)
        self.assertEqual(observation.availability, ObservationAvailability.UNAVAILABLE)
        health = entity.get(HealthState)
        self.assertEqual(health.status, HealthStatus.UNKNOWN)
        self.assertIn("telemetry unavailable", health.reasons[0])

    def test_partial_batch_updates_known_value_but_exposes_degradation(self):
        context = self._context()
        new_wifi = WifiLinkState("wlan0", True, "home", 5220, -60, 300.0, 300.0, None)

        _ingest_observation_batch(
            context,
            entity_id=TENDA_ID,
            adapter_id="tenda.u11_pro",
            observations=(
                Observation.observed(
                    "usb.lsusb",
                    UsbDeviceState(True, "2604:0020", "Tenda", "wifi"),
                ),
                Observation.partial("wifi.link", new_wifi, "IPv4 query failed"),
            ),
        )

        entity = context.world.entities[TENDA_ID]
        observation = entity.get(ObservationState)
        self.assertEqual(observation.availability, ObservationAvailability.DEGRADED)
        self.assertEqual(entity.get(WifiLinkState), new_wifi)
        health = entity.get(HealthState)
        self.assertEqual(health.status, HealthStatus.WARNING)
        self.assertIn("telemetry degraded", health.reasons[0])

    def test_observation_heartbeat_is_not_durable_journal_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            events = EventBus()
            journal = EventJournal(path)
            events.observe_all(journal.record)
            context = create_context(events=events)
            reconcile_topology(context)
            if path.exists():
                path.unlink()

            _ingest_observation_batch(
                context,
                entity_id=TENDA_ID,
                adapter_id="tenda.u11_pro",
                observations=(
                    Observation.observed(
                        "usb.lsusb",
                        UsbDeviceState(True, "2604:0020", "Tenda", "wifi"),
                    ),
                    Observation.observed(
                        "wifi.link",
                        WifiLinkState("wlan0", True, "home", 5220, -60, 300.0, 300.0, "192.168.1.2/24"),
                    ),
                ),
            )

            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertNotIn("ObservationCycleCompleted", [record["event_type"] for record in records])


if __name__ == "__main__":
    unittest.main()
