from __future__ import annotations

from datetime import datetime, timezone

from personal_cic.core.events import utc_now_iso
from personal_cic.core.world.components import (
    CurrentWeatherEstimateState,
    NWSHourlyForecastState,
    SurfaceObservationNetworkState,
    WeatherState,
)


def _reference_hour(forecast: NWSHourlyForecastState | None, now: datetime):
    """Return the forecast period corresponding to now when possible."""
    if forecast is None or not forecast.hours:
        return None
    parsed = []
    for hour in forecast.hours:
        try:
            start = datetime.fromisoformat(hour.start_time.replace("Z", "+00:00"))
        except ValueError:
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        parsed.append((start.astimezone(timezone.utc), hour))
    if not parsed:
        return forecast.hours[0]
    parsed.sort(key=lambda item: item[0])
    at_or_before_now = [item for item in parsed if item[0] <= now]
    return at_or_before_now[-1][1] if at_or_before_now else parsed[0][1]


def derive_current_weather_estimate(
    *,
    location_label: str,
    surface: SurfaceObservationNetworkState | None,
    surface_current: bool,
    open_meteo: WeatherState | None,
    open_meteo_current: bool,
    nws_forecast: NWSHourlyForecastState | None,
    nws_current: bool,
) -> CurrentWeatherEstimateState | None:
    derived_at = utc_now_iso()
    now = datetime.fromisoformat(derived_at).astimezone(timezone.utc)
    selected = None
    if surface and surface.stations and surface.selected_station_id:
        selected = next((s for s in surface.stations if s.station_id == surface.selected_station_id), None)

    if surface_current and surface and surface.temperature_median_f is not None:
        temp = surface.temperature_median_f
        dew = surface.dewpoint_median_f
        rh = surface.relative_humidity_percent
        method = "surface_median + nearest_station_context"
        primary = "NOAA/NWS AviationWeather.gov METAR"
        wind_dir = selected.wind_direction_deg if selected else None
        wind_speed = selected.wind_speed_mph if selected else None
        wind_gust = selected.wind_gust_mph if selected else None
        visibility = selected.visibility_sm if selected else None
        altimeter = selected.altimeter_inhg if selected else None
        ceiling = selected.ceiling_ft_agl if selected else None
        flight_category = selected.flight_category if selected else None
        station_count = surface.station_count
        spread = surface.temperature_spread_f
    elif open_meteo_current and open_meteo and open_meteo.temperature_f is not None:
        temp = open_meteo.temperature_f
        dew = None
        rh = open_meteo.relative_humidity_percent
        method = "openmeteo_model_fallback"
        primary = "Open-Meteo"
        wind_dir = open_meteo.wind_direction_deg
        wind_speed = open_meteo.wind_speed_mph
        wind_gust = open_meteo.wind_gust_mph
        visibility = altimeter = ceiling = flight_category = None
        station_count = 0
        spread = None
    else:
        return None

    om_temp = open_meteo.temperature_f if open_meteo_current and open_meteo else None
    nws_hour = _reference_hour(nws_forecast, now) if nws_current else None
    nws_temp = nws_hour.temperature_f if nws_hour else None
    return CurrentWeatherEstimateState(
        location_label=location_label,
        derived_at=derived_at,
        method=method,
        primary_source=primary,
        surface_station_count=station_count,
        temperature_f=temp,
        dewpoint_f=dew,
        relative_humidity_percent=rh,
        wind_direction_deg=wind_dir,
        wind_speed_mph=wind_speed,
        wind_gust_mph=wind_gust,
        visibility_sm=visibility,
        altimeter_inhg=altimeter,
        ceiling_ft_agl=ceiling,
        flight_category=flight_category,
        surface_temperature_spread_f=spread,
        open_meteo_temperature_f=om_temp,
        open_meteo_delta_f=None if om_temp is None or temp is None else om_temp - temp,
        nws_reference_temperature_f=nws_temp,
        nws_reference_delta_f=None if nws_temp is None or temp is None else nws_temp - temp,
        nws_reference_start=None if nws_hour is None else nws_hour.start_time,
    )
