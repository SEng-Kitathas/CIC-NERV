from enum import Enum

from personal_cic.core.observations import ObservationAvailability
from typing import Any

from .components import (
    CICNode,
    ComputeState,
    HealthState,
    HealthStatus,
    LinuxHost,
    MemoryState,
    ObservationState,
    RFObserver,
    StorageState,
    TemperatureState,
    UptimeState,
    USBDevice,
    UsbDeviceState,
    WiFiRadio,
    WifiLinkState,
    WeatherAlertState,
    WeatherAlertSummary,
    WeatherForecastState,
    WeatherState,
)


COMPONENT_TYPES = {
    cls.__name__: cls
    for cls in (
        CICNode,
        LinuxHost,
        WiFiRadio,
        RFObserver,
        USBDevice,
        ComputeState,
        MemoryState,
        StorageState,
        UptimeState,
        TemperatureState,
        UsbDeviceState,
        WifiLinkState,
        ObservationState,
        HealthState,
        WeatherState,
        WeatherForecastState,
        WeatherAlertState,
    )
}


def encode_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [encode_value(item) for item in value]
    if isinstance(value, list):
        return [encode_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): encode_value(item) for key, item in value.items()}
    return value


def decode_component(name: str, payload: dict[str, Any]) -> object | None:
    component_type = COMPONENT_TYPES.get(name)
    if component_type is None:
        return None

    values = dict(payload)
    if component_type is HealthState:
        values["status"] = HealthStatus(values["status"])
        if isinstance(values.get("reasons"), list):
            values["reasons"] = tuple(values["reasons"])
    elif component_type is WeatherAlertState:
        values["alerts"] = tuple(
            WeatherAlertSummary(**item)
            for item in values.get("alerts", [])
            if isinstance(item, dict)
        )
    elif component_type is ObservationState:
        values["availability"] = ObservationAvailability(values["availability"])
        if isinstance(values.get("reasons"), list):
            values["reasons"] = tuple(values["reasons"])

    return component_type(**values)
