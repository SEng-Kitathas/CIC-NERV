from typing import Any

from personal_cic.core.config import HealthThresholds
from personal_cic.core.world.components import (
    ComputeState,
    HealthState,
    MemoryState,
    StorageState,
    TemperatureState,
    UptimeState,
    UsbDeviceState,
    WifiLinkState,
)


def _band(value: float, warning: float, critical: float) -> int:
    if value >= critical:
        return 2
    if value >= warning:
        return 1
    return 0


def telemetry_significance(
    previous: Any,
    current: Any,
    thresholds: HealthThresholds,
) -> str:
    """Classify an observation as durable operational change or transient sample."""

    if previous is None:
        return "material"

    # Health is already derived semantic state; any change matters.
    if isinstance(current, HealthState):
        return "material"

    # Uptime belongs in current world state but not in the durable event history.
    if isinstance(current, UptimeState):
        return "sample"

    if isinstance(current, ComputeState) and isinstance(previous, ComputeState):
        old_band = _band(
            previous.cpu_percent,
            thresholds.cpu_warning_percent,
            thresholds.cpu_critical_percent,
        )
        new_band = _band(
            current.cpu_percent,
            thresholds.cpu_warning_percent,
            thresholds.cpu_critical_percent,
        )
        if old_band != new_band or abs(current.cpu_percent - previous.cpu_percent) >= 10:
            return "material"
        return "sample"

    if isinstance(current, MemoryState) and isinstance(previous, MemoryState):
        old_band = _band(
            previous.used_percent,
            thresholds.memory_warning_percent,
            thresholds.memory_critical_percent,
        )
        new_band = _band(
            current.used_percent,
            thresholds.memory_warning_percent,
            thresholds.memory_critical_percent,
        )
        if old_band != new_band or abs(current.used_percent - previous.used_percent) >= 5:
            return "material"
        return "sample"

    if isinstance(current, StorageState) and isinstance(previous, StorageState):
        old_band = _band(
            previous.used_percent,
            thresholds.storage_warning_percent,
            thresholds.storage_critical_percent,
        )
        new_band = _band(
            current.used_percent,
            thresholds.storage_warning_percent,
            thresholds.storage_critical_percent,
        )
        if (
            old_band != new_band
            or current.mountpoint != previous.mountpoint
            or abs(current.used_percent - previous.used_percent) >= 1
        ):
            return "material"
        return "sample"

    if isinstance(current, TemperatureState) and isinstance(previous, TemperatureState):
        if current.source != previous.source:
            return "material"
        if current.celsius is None or previous.celsius is None:
            return "material" if current.celsius != previous.celsius else "sample"
        return "material" if abs(current.celsius - previous.celsius) >= 3 else "sample"

    if isinstance(current, UsbDeviceState) and isinstance(previous, UsbDeviceState):
        return "material" if current != previous else "sample"

    if isinstance(current, WifiLinkState) and isinstance(previous, WifiLinkState):
        structural_old = (
            previous.interface,
            previous.connected,
            previous.ssid,
            previous.frequency_mhz,
            previous.ipv4,
        )
        structural_new = (
            current.interface,
            current.connected,
            current.ssid,
            current.frequency_mhz,
            current.ipv4,
        )
        if structural_old != structural_new:
            return "material"

        if current.signal_dbm is not None and previous.signal_dbm is not None:
            if abs(current.signal_dbm - previous.signal_dbm) >= 5:
                return "material"

        # Link-rate churn is useful live telemetry, not an operational event.
        return "sample"

    return "material"
