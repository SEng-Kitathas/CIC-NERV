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
    SurfaceStationObservation,
    SurfaceObservationNetworkState,
    NWSForecastHour,
    NWSHourlyForecastState,
    CurrentWeatherEstimateState,
    RadarMosaicState,
    RadarFrameReference,
    RadarContextState,
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
        SurfaceObservationNetworkState,
        NWSHourlyForecastState,
        CurrentWeatherEstimateState,
        RadarMosaicState,
        RadarContextState,
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
    elif component_type is SurfaceObservationNetworkState:
        values["stations"] = tuple(
            SurfaceStationObservation(**item)
            for item in values.get("stations", [])
            if isinstance(item, dict)
        )
    elif component_type is NWSHourlyForecastState:
        values["hours"] = tuple(
            NWSForecastHour(**item)
            for item in values.get("hours", [])
            if isinstance(item, dict)
        )
    elif component_type is CurrentWeatherEstimateState:
        legacy = (
            ("nws_next_hour_temperature_f", "nws_reference_temperature_f"),
            ("nws_next_hour_delta_f", "nws_reference_delta_f"),
            ("nws_next_hour_start", "nws_reference_start"),
        )
        for old_name, new_name in legacy:
            if new_name not in values and old_name in values:
                values[new_name] = values.pop(old_name)
    elif component_type is RadarMosaicState:
        # 0.3.3 RC1 used names that could imply the separately retrieved WMS
        # frame was bound to a specific RIDGEII GeoTIFF. Preserve the useful
        # source-stream freshness witness without manufacturing that binding.
        if "stream_latest_filename" not in values and "source_filename" in values:
            values["stream_latest_filename"] = values.pop("source_filename")
        if "stream_latest_at" not in values and "source_product_at" in values:
            values["stream_latest_at"] = values.pop("source_product_at")
        values.setdefault("frame_retrieved_at", None)
        values["frames"] = tuple(
            RadarFrameReference(**item)
            for item in values.get("frames", [])
            if isinstance(item, dict)
        )
        values.setdefault("loop_frame_capacity", 15)
    elif component_type is ObservationState:
        values["availability"] = ObservationAvailability(values["availability"])
        if isinstance(values.get("reasons"), list):
            values["reasons"] = tuple(values["reasons"])

    return component_type(**values)
