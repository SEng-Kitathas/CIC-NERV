from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class CICNode:
    pass


@dataclass(frozen=True, slots=True)
class LinuxHost:
    pass


@dataclass(frozen=True, slots=True)
class WiFiRadio:
    pass


@dataclass(frozen=True, slots=True)
class RFObserver:
    pass


@dataclass(frozen=True, slots=True)
class USBDevice:
    pass


@dataclass(frozen=True, slots=True)
class ComputeState:
    cpu_percent: float
    logical_cpus: int
    load_1m: float
    load_per_cpu: float


@dataclass(frozen=True, slots=True)
class MemoryState:
    total_bytes: int
    available_bytes: int
    used_percent: float


@dataclass(frozen=True, slots=True)
class StorageState:
    mountpoint: str
    total_bytes: int
    free_bytes: int
    used_percent: float


@dataclass(frozen=True, slots=True)
class UptimeState:
    uptime_seconds: int


@dataclass(frozen=True, slots=True)
class TemperatureState:
    celsius: Optional[float]
    source: Optional[str]


@dataclass(frozen=True, slots=True)
class UsbDeviceState:
    present: bool
    usb_id: Optional[str]
    description: Optional[str]
    mode: str


@dataclass(frozen=True, slots=True)
class WifiLinkState:
    interface: Optional[str]
    connected: bool
    ssid: Optional[str]
    frequency_mhz: Optional[int]
    signal_dbm: Optional[int]
    rx_mbps: Optional[float]
    tx_mbps: Optional[float]
    ipv4: Optional[str]


@dataclass(frozen=True, slots=True)
class HealthState:
    status: str
    reasons: tuple[str, ...]
