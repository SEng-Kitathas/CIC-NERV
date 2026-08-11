from dataclasses import dataclass
from enum import Enum
from typing import Optional

from personal_cic.core.observations import ObservationAvailability


class HealthStatus(str, Enum):
    UNKNOWN = "unknown"
    NOMINAL = "nominal"
    WARNING = "warning"
    CRITICAL = "critical"


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
class ObservationState:
    adapter_id: str
    availability: ObservationAvailability
    checked_at: str
    last_success_at: str | None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HealthState:
    status: HealthStatus
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WeatherState:
    location_label: str
    provider: str
    provider_observed_at: str | None
    provider_timezone: str | None
    temperature_f: float | None
    apparent_temperature_f: float | None
    relative_humidity_percent: float | None
    precipitation_in: float | None
    weather_code: int | None
    cloud_cover_percent: float | None
    wind_speed_mph: float | None
    wind_direction_deg: float | None
    wind_gust_mph: float | None


@dataclass(frozen=True, slots=True)
class WeatherForecastState:
    location_label: str
    provider: str
    provider_timezone: str | None
    forecast_date: str | None
    high_f: float | None
    low_f: float | None
    precipitation_probability_max_percent: float | None
    sunrise: str | None
    sunset: str | None


@dataclass(frozen=True, slots=True)
class WeatherAlertSummary:
    alert_id: str
    event: str
    severity: str
    urgency: str | None
    headline: str
    sent_at: str | None
    effective_at: str | None
    expires_at: str | None


@dataclass(frozen=True, slots=True)
class WeatherAlertState:
    location_label: str
    provider: str
    active_count: int
    highest_severity: str | None
    provider_updated_at: str | None
    alerts: tuple[WeatherAlertSummary, ...] = ()
