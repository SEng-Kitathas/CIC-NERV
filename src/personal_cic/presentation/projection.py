from datetime import datetime, timezone
import statistics
from typing import Any

from personal_cic.core.world import WorldState


_HEALTH_ORDER = {
    "unknown": 0,
    "nominal": 1,
    "warning": 2,
    "critical": 3,
}

_OBS_ORDER = {
    "current": 0,
    "degraded": 1,
    "unavailable": 2,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freshness_seconds(checked_at: str | None) -> float | None:
    if not checked_at:
        return None
    try:
        checked = datetime.fromisoformat(checked_at)
    except ValueError:
        return None
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    return max(
        0.0,
        round((datetime.now(timezone.utc) - checked).total_seconds(), 3),
    )


def _component(entity: dict[str, Any], name: str) -> dict[str, Any] | None:
    value = entity.get("components", {}).get(name)
    return value if isinstance(value, dict) else None


def _worst(values: list[str], order: dict[str, int], default: str) -> str:
    known = [value for value in values if value in order]
    if not known:
        return default
    return max(known, key=lambda value: order[value])


def build_systems_projection(
    world: WorldState,
    *,
    runtime_pid: int | None = None,
    runtime_started_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only operator projection from one atomic WorldState snapshot.

    Presentation owns no device truth and performs no hardware queries.  Every
    displayed domain value comes from the CIC WorldState snapshot.
    """

    snapshot = world.snapshot()
    entities = snapshot.get("entities", {})

    host = entities.get("engage-one", {})
    tenda = entities.get("tenda-u11-pro", {})

    host_obs = _component(host, "ObservationState") or {}
    host_health = _component(host, "HealthState") or {}
    compute = _component(host, "ComputeState") or {}
    memory = _component(host, "MemoryState") or {}
    storage = _component(host, "StorageState") or {}
    temperature = _component(host, "TemperatureState") or {}
    uptime = _component(host, "UptimeState") or {}

    tenda_obs = _component(tenda, "ObservationState") or {}
    tenda_health = _component(tenda, "HealthState") or {}
    usb = _component(tenda, "UsbDeviceState") or {}
    wifi = _component(tenda, "WifiLinkState") or {}

    health_values = [
        str(host_health.get("status", "unknown")),
        str(tenda_health.get("status", "unknown")),
    ]
    observation_values = [
        str(host_obs.get("availability", "unavailable")),
        str(tenda_obs.get("availability", "unavailable")),
    ]

    frequency = wifi.get("frequency_mhz")
    if isinstance(frequency, (int, float)):
        if frequency >= 5925:
            band = "6 GHz"
        elif frequency >= 4900:
            band = "5 GHz"
        elif frequency >= 2400:
            band = "2.4 GHz"
        else:
            band = "other"
    else:
        band = None

    return {
        "api_version": 1,
        "presentation": {
            "mode": "read-only",
            "generated_at": _now_iso(),
            "world_schema_version": snapshot.get("schema_version"),
        },
        "runtime": {
            "pid": runtime_pid,
            "started_at": runtime_started_at,
        },
        "summary": {
            "health": _worst(health_values, _HEALTH_ORDER, "unknown"),
            "observation": _worst(
                observation_values,
                _OBS_ORDER,
                "unavailable",
            ),
            "wlan_connected": bool(wifi.get("connected", False)),
        },
        "host": {
            "entity_id": "engage-one",
            "label": host.get("label", "engage-one"),
            "health": {
                "status": host_health.get("status", "unknown"),
                "reasons": host_health.get("reasons", []),
            },
            "observation": {
                "availability": host_obs.get("availability", "unavailable"),
                "adapter_id": host_obs.get("adapter_id"),
                "checked_at": host_obs.get("checked_at"),
                "last_success_at": host_obs.get("last_success_at"),
                "freshness_seconds": _freshness_seconds(
                    host_obs.get("checked_at")
                ),
                "reasons": host_obs.get("reasons", []),
            },
            "compute": compute,
            "memory": memory,
            "storage": storage,
            "temperature": temperature,
            "uptime": uptime,
        },
        "tenda": {
            "entity_id": "tenda-u11-pro",
            "label": tenda.get("label", "tenda-u11-pro"),
            "health": {
                "status": tenda_health.get("status", "unknown"),
                "reasons": tenda_health.get("reasons", []),
            },
            "observation": {
                "availability": tenda_obs.get(
                    "availability",
                    "unavailable",
                ),
                "adapter_id": tenda_obs.get("adapter_id"),
                "checked_at": tenda_obs.get("checked_at"),
                "last_success_at": tenda_obs.get("last_success_at"),
                "freshness_seconds": _freshness_seconds(
                    tenda_obs.get("checked_at")
                ),
                "reasons": tenda_obs.get("reasons", []),
            },
            "usb": usb,
            "wifi": {
                **wifi,
                "band": band,
            },
        },
    }


_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}


def build_world_projection(world: WorldState, *, feed: list[dict] | None = None) -> dict[str, Any]:
    """Project source-aware world observations without promoting them beyond scope."""

    snapshot = world.snapshot()
    entities = snapshot.get("entities", {})
    weather_entity = entities.get("local-weather", {})
    alerts_entity = entities.get("local-weather-alerts", {})
    surface_entity = entities.get("local-weather-surface", {})
    forecast_entity = entities.get("local-weather-nws-forecast", {})
    estimate_entity = entities.get("local-weather-estimate", {})

    weather = _component(weather_entity, "WeatherState") or {}
    forecast_daily = _component(weather_entity, "WeatherForecastState") or {}
    weather_obs = _component(weather_entity, "ObservationState") or {}
    alerts = _component(alerts_entity, "WeatherAlertState") or {}
    alerts_obs = _component(alerts_entity, "ObservationState") or {}
    surface = _component(surface_entity, "SurfaceObservationNetworkState") or {}
    surface_obs = _component(surface_entity, "ObservationState") or {}
    nws_forecast = _component(forecast_entity, "NWSHourlyForecastState") or {}
    forecast_obs = _component(forecast_entity, "ObservationState") or {}
    estimate = _component(estimate_entity, "CurrentWeatherEstimateState") or {}
    estimate_obs = _component(estimate_entity, "ObservationState") or {}

    weather_code = weather.get("weather_code")
    location = (
        estimate.get("location_label") or surface.get("location_label") or weather.get("location_label")
        or alerts.get("location_label") or "configured local area"
    )

    def obs(value):
        return {
            "availability": value.get("availability", "unavailable"),
            "adapter_id": value.get("adapter_id"),
            "checked_at": value.get("checked_at"),
            "last_success_at": value.get("last_success_at"),
            "freshness_seconds": _freshness_seconds(value.get("checked_at")),
            "reasons": value.get("reasons", []),
        }

    stations = surface.get("stations") or []

    def station_values(key):
        return [float(station[key]) for station in stations if isinstance(station, dict) and isinstance(station.get(key), (int, float))]

    wind_speeds = station_values("wind_speed_mph")
    gusts = station_values("wind_gust_mph")
    visibilities = station_values("visibility_sm")
    ceilings = station_values("ceiling_ft_agl")
    surface_projection = {
        **surface,
        "wind_speed_median_mph": None if not wind_speeds else statistics.median(wind_speeds),
        "wind_gust_max_mph": None if not gusts else max(gusts),
        "visibility_min_sm": None if not visibilities else min(visibilities),
        "ceiling_min_ft_agl": None if not ceilings else int(min(ceilings)),
        "observation": obs(surface_obs),
    }

    return {
        "api_version": 2,
        "presentation": {
            "mode": "read-only",
            "generated_at": _now_iso(),
            "world_schema_version": snapshot.get("schema_version"),
        },
        "location": {"label": location},
        "estimate": {
            **estimate,
            "current_now": estimate_obs.get("availability") == "current",
            "observation": obs(estimate_obs),
        },
        "surface": surface_projection,
        "weather": {
            **weather,
            "condition": _WEATHER_CODES.get(weather_code, "Unknown") if weather_code is not None else None,
            "observation": obs(weather_obs),
            "forecast": forecast_daily,
        },
        "nws_forecast": {**nws_forecast, "observation": obs(forecast_obs)},
        "alerts": {
            **alerts,
            "authoritative_now": alerts_obs.get("availability") == "current",
            "observation": obs(alerts_obs),
        },
        "feed": list(feed or []),
    }
