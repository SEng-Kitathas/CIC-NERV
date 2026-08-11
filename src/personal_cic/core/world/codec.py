from typing import Any

from .components import (
    CICNode,
    ComputeState,
    HealthState,
    LinuxHost,
    MemoryState,
    RFObserver,
    StorageState,
    TemperatureState,
    UptimeState,
    USBDevice,
    UsbDeviceState,
    WiFiRadio,
    WifiLinkState,
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
        HealthState,
    )
}


def decode_component(name: str, payload: dict[str, Any]) -> object | None:
    component_type = COMPONENT_TYPES.get(name)
    if component_type is None:
        return None

    values = dict(payload)
    if component_type is HealthState and isinstance(values.get("reasons"), list):
        values["reasons"] = tuple(values["reasons"])

    return component_type(**values)
