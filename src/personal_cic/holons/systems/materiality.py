from typing import Any

from personal_cic.core.config import HealthThresholds
from personal_cic.core.world.components import (
    ComputeState,
    HealthState,
    MemoryState,
    ObservationState,
    StorageState,
    TemperatureState,
    UptimeState,
    UsbDeviceState,
    WifiLinkState,
    WeatherAlertState,
    WeatherForecastState,
    WeatherState,
)


def _high_band(value: float, warning: float, critical: float) -> int:
    if value >= critical:
        return 2
    if value >= warning:
        return 1
    return 0


def _low_band(value: int, warning: int) -> int:
    return 1 if value <= warning else 0


def telemetry_significance(
    previous: Any,
    current: Any,
    thresholds: HealthThresholds,
) -> str:
    """Separate live sampling from durable operational history.

    Raw telemetry remains current in WorldState. The event journal records semantic
    boundary crossings and structural changes, not normal workload/radio churn.
    """

    if previous is None:
        return "material"

    if isinstance(current, HealthState):
        return "material"

    if isinstance(current, ObservationState) and isinstance(previous, ObservationState):
        semantic_old = (previous.availability, previous.reasons)
        semantic_new = (current.availability, current.reasons)
        return "material" if semantic_old != semantic_new else "sample"

    if isinstance(current, UptimeState):
        return "sample"

    if isinstance(current, ComputeState) and isinstance(previous, ComputeState):
        old_band = _high_band(
            previous.cpu_percent,
            thresholds.cpu_warning_percent,
            thresholds.cpu_critical_percent,
        )
        new_band = _high_band(
            current.cpu_percent,
            thresholds.cpu_warning_percent,
            thresholds.cpu_critical_percent,
        )
        return "material" if old_band != new_band else "sample"

    if isinstance(current, MemoryState) and isinstance(previous, MemoryState):
        old_band = _high_band(
            previous.used_percent,
            thresholds.memory_warning_percent,
            thresholds.memory_critical_percent,
        )
        new_band = _high_band(
            current.used_percent,
            thresholds.memory_warning_percent,
            thresholds.memory_critical_percent,
        )
        return "material" if old_band != new_band else "sample"

    if isinstance(current, StorageState) and isinstance(previous, StorageState):
        if current.mountpoint != previous.mountpoint:
            return "material"
        old_band = _high_band(
            previous.used_percent,
            thresholds.storage_warning_percent,
            thresholds.storage_critical_percent,
        )
        new_band = _high_band(
            current.used_percent,
            thresholds.storage_warning_percent,
            thresholds.storage_critical_percent,
        )
        return "material" if old_band != new_band else "sample"

    if isinstance(current, TemperatureState) and isinstance(previous, TemperatureState):
        if current.source != previous.source:
            return "material"
        if current.celsius is None or previous.celsius is None:
            return "material" if current.celsius != previous.celsius else "sample"
        old_band = _high_band(
            previous.celsius,
            thresholds.temperature_warning_c,
            thresholds.temperature_critical_c,
        )
        new_band = _high_band(
            current.celsius,
            thresholds.temperature_warning_c,
            thresholds.temperature_critical_c,
        )
        return "material" if old_band != new_band else "sample"

    if isinstance(current, UsbDeviceState) and isinstance(previous, UsbDeviceState):
        return "material" if current != previous else "sample"

    if isinstance(current, WeatherState) and isinstance(previous, WeatherState):
        structural_old = (
            previous.provider,
            previous.location_label,
            previous.provider_timezone,
            previous.weather_code,
            bool(previous.precipitation_in and previous.precipitation_in > 0),
        )
        structural_new = (
            current.provider,
            current.location_label,
            current.provider_timezone,
            current.weather_code,
            bool(current.precipitation_in and current.precipitation_in > 0),
        )
        return "material" if structural_old != structural_new else "sample"

    if isinstance(current, WeatherForecastState) and isinstance(previous, WeatherForecastState):
        structural_old = (
            previous.provider,
            previous.location_label,
            previous.provider_timezone,
            previous.forecast_date,
        )
        structural_new = (
            current.provider,
            current.location_label,
            current.provider_timezone,
            current.forecast_date,
        )
        return "material" if structural_old != structural_new else "sample"

    if isinstance(current, WeatherAlertState) and isinstance(previous, WeatherAlertState):
        semantic_old = (
            previous.location_label,
            previous.provider,
            previous.active_count,
            previous.highest_severity,
            previous.alerts,
        )
        semantic_new = (
            current.location_label,
            current.provider,
            current.active_count,
            current.highest_severity,
            current.alerts,
        )
        return "material" if semantic_old != semantic_new else "sample"

    if isinstance(current, WifiLinkState) and isinstance(previous, WifiLinkState):
        structural_old = (
            previous.interface,
            previous.connected,
            previous.ssid,
            previous.ipv4,
        )
        structural_new = (
            current.interface,
            current.connected,
            current.ssid,
            current.ipv4,
        )
        if structural_old != structural_new:
            return "material"

        # Frequency/channel and bitrate are radio telemetry, not durable
        # operational meaning by themselves. Normal AP band steering in the
        # Engage soak test moved 5 GHz -> 2.4 GHz -> 5 GHz without a link loss.
        # A future RF/health model may derive a semantic band transition.

        # Missing signal on an otherwise structurally stable link is likewise
        # observation-quality degradation. ObservationState owns that truth;
        # do not create a false durable WifiLinkState transition for None.
        if previous.signal_dbm is None or current.signal_dbm is None:
            return "sample"

        old_band = _low_band(previous.signal_dbm, thresholds.wifi_signal_warning_dbm)
        new_band = _low_band(current.signal_dbm, thresholds.wifi_signal_warning_dbm)
        return "material" if old_band != new_band else "sample"

    return "material"
