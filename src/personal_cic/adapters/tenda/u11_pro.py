import re
import subprocess

from personal_cic.core.world.components import UsbDeviceState, WifiLinkState


def _run(*args: str) -> str:
    try:
        return subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


class TendaU11ProAdapter:
    ACTIVE_USB_ID = "2604:0020"
    INSTALLER_USB_ID = "a69c:5725"

    @staticmethod
    def _usb_state() -> UsbDeviceState:
        output = _run("lsusb")
        for line in output.splitlines():
            lowered = line.lower()
            if TendaU11ProAdapter.ACTIVE_USB_ID in lowered:
                return UsbDeviceState(
                    present=True,
                    usb_id=TendaU11ProAdapter.ACTIVE_USB_ID,
                    description=line.split(TendaU11ProAdapter.ACTIVE_USB_ID, 1)[-1].strip(),
                    mode="wifi",
                )
            if TendaU11ProAdapter.INSTALLER_USB_ID in lowered:
                return UsbDeviceState(
                    present=True,
                    usb_id=TendaU11ProAdapter.INSTALLER_USB_ID,
                    description=line.split(TendaU11ProAdapter.INSTALLER_USB_ID, 1)[-1].strip(),
                    mode="installer",
                )
        return UsbDeviceState(False, None, None, "absent")

    @staticmethod
    def _interfaces() -> list[str]:
        output = _run("iw", "dev")
        interfaces: list[str] = []
        for raw in output.splitlines():
            line = raw.strip()
            if line.startswith("Interface "):
                name = line.split(None, 1)[1]
                if not name.startswith("p2p-"):
                    interfaces.append(name)
        return interfaces

    @classmethod
    def _wifi_state(cls) -> WifiLinkState:
        interfaces = cls._interfaces()
        if not interfaces:
            return WifiLinkState(None, False, None, None, None, None, None, None)

        chosen = interfaces[0]
        link = ""
        for interface in interfaces:
            candidate = _run("iw", "dev", interface, "link")
            if candidate.startswith("Connected to "):
                chosen, link = interface, candidate
                break
            if not link:
                link = candidate

        connected = link.startswith("Connected to ")

        def first(pattern: str, cast=str):
            match = re.search(pattern, link, re.MULTILINE)
            if not match:
                return None
            try:
                return cast(match.group(1))
            except (TypeError, ValueError):
                return None

        ip_output = _run("ip", "-4", "-br", "addr", "show", chosen)
        ipv4 = None
        for token in ip_output.split():
            if re.fullmatch(r"\d+\.\d+\.\d+\.\d+/\d+", token):
                ipv4 = token
                break

        return WifiLinkState(
            interface=chosen,
            connected=connected,
            ssid=first(r"^\s*SSID:\s*(.+)$"),
            frequency_mhz=first(r"^\s*freq:\s*(\d+)$", int),
            signal_dbm=first(r"^\s*signal:\s*(-?\d+)\s*dBm$", int),
            rx_mbps=first(r"^\s*rx bitrate:\s*([\d.]+)\s*MBit/s", float),
            tx_mbps=first(r"^\s*tx bitrate:\s*([\d.]+)\s*MBit/s", float),
            ipv4=ipv4,
        )

    def collect(self) -> tuple[object, ...]:
        return (self._usb_state(), self._wifi_state())
