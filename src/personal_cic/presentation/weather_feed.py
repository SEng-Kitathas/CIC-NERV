from __future__ import annotations

from pathlib import Path
import json

_WEATHER_ENTITIES = {
    "local-weather",
    "local-weather-alerts",
    "local-weather-surface",
    "local-weather-nws-forecast",
    "local-weather-estimate",
}


def _item(record: dict) -> dict | None:
    if record.get("event_type") != "ComponentUpdated":
        return None
    p = record.get("payload") or {}
    if p.get("entity_id") not in _WEATHER_ENTITIES or p.get("significance") != "material":
        return None
    name = p.get("component_name")
    previous = p.get("previous") or {}
    current = p.get("current") or {}
    category = "WX"
    title = f"{name} changed"
    detail = ""
    if name == "WeatherAlertState":
        category = "ALERT"
        old_count = previous.get("active_count")
        new_count = current.get("active_count")
        sev = current.get("highest_severity") or "none"
        if old_count == 0 and isinstance(new_count, int) and new_count > 0:
            title = "NWS alert activated"
        elif isinstance(old_count, int) and old_count > 0 and new_count == 0:
            title = "NWS alerts cleared"
        else:
            title = "NWS alert product revised"
        detail = f"active {old_count} -> {new_count} // severity {sev}"
    elif name == "SurfaceObservationNetworkState":
        category = "OBS"
        title = "Surface observation network changed"
        detail = f"selected {current.get('selected_station_id') or '--'} // stations {current.get('station_count','--')}"
    elif name == "NWSHourlyForecastState":
        category = "FORECAST"
        title = "NWS hourly forecast changed"
        hours = current.get("hours") or []
        if hours:
            h = hours[0]
            detail = f"{h.get('short_forecast') or '--'} // PoP {h.get('precipitation_probability_percent')}%"
    elif name == "CurrentWeatherEstimateState":
        category = "FUSION"
        title = "Current-weather estimate source changed"
        detail = f"{current.get('method') or '--'} // {current.get('primary_source') or '--'}"
    elif name == "ObservationState":
        previous_reasons = [str(x) for x in (previous.get("reasons") or [])]
        current_reasons = [str(x) for x in (current.get("reasons") or [])]
        if any(reason.startswith("reentry:") for reason in previous_reasons + current_reasons):
            return None
        category = "PROVIDER"
        title = f"Provider observation {str(current.get('availability') or 'unknown').upper()}"
        detail = " // ".join(current_reasons[:2])
    elif name == "WeatherState":
        category = "WX"
        title = "Open-Meteo current condition changed"
        detail = f"weather code {previous.get('weather_code')} -> {current.get('weather_code')}"
    return {
        "occurred_at": p.get("occurred_at"),
        "event_id": p.get("event_id"),
        "category": category,
        "title": title,
        "detail": detail,
        "entity_id": p.get("entity_id"),
        "component": name,
    }


def build_weather_feed(path: Path | None, limit: int = 24) -> list[dict]:
    if path is None or not path.exists():
        return []
    # The CIC journal is intentionally sparse. Bound the projection scan anyway.
    data = path.read_bytes()
    if len(data) > 512 * 1024:
        data = data[-512 * 1024:]
        first_newline = data.find(b"\n")
        if first_newline >= 0:
            data = data[first_newline + 1:]
    items = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = _item(record)
        if item is not None:
            items.append(item)
    return items[-limit:][::-1]
