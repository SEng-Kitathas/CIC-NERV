from dataclasses import dataclass
import re
import subprocess

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import UsbDeviceState, WifiLinkState


@dataclass(frozen=True, slots=True)
class _CommandResult:
    ok: bool
    stdout: str = ""
    detail: str | None = None


def _run(*args: str) -> _CommandResult:
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except FileNotFoundError:
        return _CommandResult(False, detail=f"command not found: {args[0]}")
    except subprocess.TimeoutExpired:
        return _CommandResult(False, detail=f"command timed out: {' '.join(args)}")
    except OSError as exc:
        return _CommandResult(False, detail=f"command failed: {exc}")

    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit status {completed.returncode}"
        return _CommandResult(False, stdout=completed.stdout.strip(), detail=detail)
    return _CommandResult(True, stdout=completed.stdout.strip())


class TendaU11ProAdapter:
    ADAPTER_ID = "tenda.u11_pro"
    ACTIVE_USB_ID = "2604:0020"
    INSTALLER_USB_ID = "a69c:5725"

    @staticmethod
    def _usb_state() -> Observation[UsbDeviceState]:
        result = _run("lsusb")
        if not result.ok:
            return Observation.unavailable("usb.lsusb", result.detail or "lsusb unavailable")

        for line in result.stdout.splitlines():
            lowered = line.lower()
            if TendaU11ProAdapter.ACTIVE_USB_ID in lowered:
                return Observation.observed(
                    "usb.lsusb",
                    UsbDeviceState(
                        present=True,
                        usb_id=TendaU11ProAdapter.ACTIVE_USB_ID,
                        description=line.split(TendaU11ProAdapter.ACTIVE_USB_ID, 1)[-1].strip(),
                        mode="wifi",
                    ),
                )
            if TendaU11ProAdapter.INSTALLER_USB_ID in lowered:
                return Observation.observed(
                    "usb.lsusb",
                    UsbDeviceState(
                        present=True,
                        usb_id=TendaU11ProAdapter.INSTALLER_USB_ID,
                        description=line.split(TendaU11ProAdapter.INSTALLER_USB_ID, 1)[-1].strip(),
                        mode="installer",
                    ),
                )

        # Successful enumeration with no matching device is evidence of absence.
        return Observation.observed(
            "usb.lsusb",
            UsbDeviceState(False, None, None, "absent"),
        )

    @staticmethod
    def _interfaces() -> Observation[list[str]]:
        result = _run("iw", "dev")
        if not result.ok:
            return Observation.unavailable("wifi.iw_dev", result.detail or "iw unavailable")

        interfaces: list[str] = []
        for raw in result.stdout.splitlines():
            line = raw.strip()
            if line.startswith("Interface "):
                name = line.split(None, 1)[1]
                if not name.startswith("p2p-"):
                    interfaces.append(name)
        return Observation.observed("wifi.iw_dev", interfaces)

    @classmethod
    def _wifi_state(cls) -> Observation[WifiLinkState]:
        interfaces_observation = cls._interfaces()
        if interfaces_observation.value is None:
            return Observation.unavailable(
                "wifi.link",
                interfaces_observation.detail or "wireless interfaces unavailable",
            )

        interfaces = interfaces_observation.value
        if not interfaces:
            return Observation.observed(
                "wifi.link",
                WifiLinkState(None, False, None, None, None, None, None, None),
            )

        chosen: str | None = None
        link = ""
        link_failures: list[str] = []
        for interface in interfaces:
            candidate = _run("iw", "dev", interface, "link")
            if not candidate.ok:
                link_failures.append(f"{interface}: {candidate.detail or 'link query failed'}")
                continue
            if chosen is None:
                chosen, link = interface, candidate.stdout
            if candidate.stdout.startswith("Connected to "):
                chosen, link = interface, candidate.stdout
                break

        if chosen is None:
            return Observation.unavailable(
                "wifi.link",
                "; ".join(link_failures) or "no readable wireless link",
            )

        connected = link.startswith("Connected to ")

        def first(pattern: str, cast=str):
            match = re.search(pattern, link, re.MULTILINE)
            if not match:
                return None
            try:
                return cast(match.group(1))
            except (TypeError, ValueError):
                return None

        ip_result = _run("ip", "-4", "-br", "addr", "show", chosen)
        ipv4 = None
        if ip_result.ok:
            for token in ip_result.stdout.split():
                if re.fullmatch(r"\d+\.\d+\.\d+\.\d+/\d+", token):
                    ipv4 = token
                    break

        state = WifiLinkState(
            interface=chosen,
            connected=connected,
            ssid=first(r"^\s*SSID:\s*(.+)$"),
            frequency_mhz=first(r"^\s*freq:\s*(\d+)$", int),
            signal_dbm=first(r"^\s*signal:\s*(-?\d+)\s*dBm$", int),
            rx_mbps=first(r"^\s*rx bitrate:\s*([\d.]+)\s*MBit/s", float),
            tx_mbps=first(r"^\s*tx bitrate:\s*([\d.]+)\s*MBit/s", float),
            ipv4=ipv4,
        )

        partial_reasons = list(link_failures)
        if connected:
            # A successful `iw ... link` command can still return an incomplete
            # snapshot while the driver/firmware is transiently reconciling.
            # Missing connected-link facts are observation degradation, not
            # evidence that those domain values changed to None.
            if state.ssid is None:
                partial_reasons.append(f"{chosen}: connected link missing SSID")
            if state.frequency_mhz is None:
                partial_reasons.append(f"{chosen}: connected link missing frequency")
            if state.signal_dbm is None:
                partial_reasons.append(f"{chosen}: connected link missing signal")

        if not ip_result.ok:
            partial_reasons.append(f"{chosen} IPv4: {ip_result.detail or 'address query failed'}")
        if partial_reasons:
            return Observation.partial("wifi.link", state, "; ".join(partial_reasons))
        return Observation.observed("wifi.link", state)

    def collect(self) -> tuple[Observation[object], ...]:
        return (self._usb_state(), self._wifi_state())
