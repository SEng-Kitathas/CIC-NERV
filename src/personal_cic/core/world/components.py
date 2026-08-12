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

@dataclass(frozen=True, slots=True)
class SurfaceStationObservation:
    station_id: str
    station_name: str | None
    observed_at: str | None
    latitude: float | None
    longitude: float | None
    distance_mi: float | None
    temperature_f: float | None
    dewpoint_f: float | None
    relative_humidity_percent: float | None
    wind_direction_deg: float | None
    wind_speed_mph: float | None
    wind_gust_mph: float | None
    visibility_sm: float | None
    altimeter_inhg: float | None
    sea_level_pressure_hpa: float | None
    ceiling_ft_agl: int | None
    flight_category: str | None
    present_weather: str | None
    raw_metar: str | None


@dataclass(frozen=True, slots=True)
class SurfaceObservationNetworkState:
    location_label: str
    provider: str
    freshest_observed_at: str | None
    selected_station_id: str | None
    station_count: int
    temperature_median_f: float | None
    dewpoint_median_f: float | None
    relative_humidity_percent: float | None
    temperature_spread_f: float | None
    stations: tuple[SurfaceStationObservation, ...] = ()


@dataclass(frozen=True, slots=True)
class NWSForecastHour:
    start_time: str
    temperature_f: float | None
    dewpoint_f: float | None
    relative_humidity_percent: float | None
    precipitation_probability_percent: float | None
    wind_speed_min_mph: float | None
    wind_speed_max_mph: float | None
    wind_direction: str | None
    short_forecast: str | None


@dataclass(frozen=True, slots=True)
class NWSHourlyForecastState:
    location_label: str
    provider: str
    office: str | None
    grid_x: int | None
    grid_y: int | None
    generated_at: str | None
    updated_at: str | None
    hours: tuple[NWSForecastHour, ...] = ()


@dataclass(frozen=True, slots=True)
class CurrentWeatherEstimateState:
    location_label: str
    derived_at: str
    method: str
    primary_source: str
    surface_station_count: int
    temperature_f: float | None
    dewpoint_f: float | None
    relative_humidity_percent: float | None
    wind_direction_deg: float | None
    wind_speed_mph: float | None
    wind_gust_mph: float | None
    visibility_sm: float | None
    altimeter_inhg: float | None
    ceiling_ft_agl: int | None
    flight_category: str | None
    surface_temperature_spread_f: float | None
    open_meteo_temperature_f: float | None
    open_meteo_delta_f: float | None
    nws_reference_temperature_f: float | None
    nws_reference_delta_f: float | None
    nws_reference_start: str | None


@dataclass(frozen=True, slots=True)
class RadarMosaicState:
    location_label: str
    provider: str
    product: str
    layer: str
    stream_latest_filename: str
    stream_latest_at: str
    frame_retrieved_at: str | None
    west: float
    south: float
    east: float
    north: float
    range_miles: float
    image_width: int
    image_height: int
    image_sha256: str
    warning_overlay_available: bool
    warning_image_sha256: str | None
    legend_available: bool
    legend_image_sha256: str | None
