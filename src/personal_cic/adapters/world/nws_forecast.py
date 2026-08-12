from __future__ import annotations

import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import NWSForecastHour, NWSHourlyForecastState


def _number(value):
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _qv(value) -> tuple[float | None, str | None]:
    if not isinstance(value, dict):
        return None, None
    return _number(value.get("value")), None if value.get("unitCode") is None else str(value.get("unitCode"))


def _to_f(value: float | None, unit: str | None) -> float | None:
    if value is None:
        return None
    if unit and ("degC" in unit or unit.upper() == "C"):
        return value * 9.0 / 5.0 + 32.0
    return value


def _wind_range(text: str | None) -> tuple[float | None, float | None]:
    if not text:
        return None, None
    if text.strip().lower() == "calm":
        return 0.0, 0.0
    values = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    if not values:
        return None, None
    if "kt" in text.lower():
        values = [v * 1.150779448 for v in values]
    return min(values), max(values)


class NWSHourlyForecastAdapter:
    ADAPTER_ID = "nws.forecast.hourly"
    POINTS_URL = "https://api.weather.gov/points/{lat},{lon}"

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        user_agent: str,
        points_refresh_seconds: float = 21600.0,
        timeout_seconds: float = 8.0,
        opener=urlopen,
        monotonic=time.monotonic,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.user_agent = user_agent
        self.points_refresh_seconds = points_refresh_seconds
        self.timeout_seconds = timeout_seconds
        self._opener = opener
        self._monotonic = monotonic
        self._forecast_url: str | None = None
        self._grid: tuple[str | None, int | None, int | None] = (None, None, None)
        self._points_checked_at = float("-inf")

    def _request_json(self, url: str) -> dict:
        request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/geo+json"})
        with self._opener(request, timeout=self.timeout_seconds) as response:
            raw = response.read()
        if not raw:
            raise ValueError("NWS returned an empty response")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("NWS payload is not an object")
        return payload

    def _resolve(self) -> None:
        now = self._monotonic()
        if self._forecast_url and now - self._points_checked_at < self.points_refresh_seconds:
            return
        url = self.POINTS_URL.format(lat=self.latitude, lon=self.longitude)
        payload = self._request_json(url)
        props = payload.get("properties") or {}
        forecast_url = props.get("forecastHourly")
        if not forecast_url:
            raise ValueError("NWS points response missing forecastHourly")
        self._forecast_url = str(forecast_url)
        self._grid = (
            None if props.get("gridId") is None else str(props.get("gridId")),
            None if props.get("gridX") is None else int(props.get("gridX")),
            None if props.get("gridY") is None else int(props.get("gridY")),
        )
        self._points_checked_at = now

    def _parse_hour(self, period: dict) -> NWSForecastHour:
        temp = _number(period.get("temperature"))
        temp = _to_f(temp, None if period.get("temperatureUnit") is None else str(period.get("temperatureUnit")))
        dew, dew_unit = _qv(period.get("dewpoint"))
        rh, _ = _qv(period.get("relativeHumidity"))
        pop, _ = _qv(period.get("probabilityOfPrecipitation"))
        wmin, wmax = _wind_range(None if period.get("windSpeed") is None else str(period.get("windSpeed")))
        start = period.get("startTime")
        if not start:
            raise ValueError("NWS hourly period missing startTime")
        return NWSForecastHour(
            start_time=str(start),
            temperature_f=temp,
            dewpoint_f=_to_f(dew, dew_unit),
            relative_humidity_percent=rh,
            precipitation_probability_percent=pop,
            wind_speed_min_mph=wmin,
            wind_speed_max_mph=wmax,
            wind_direction=None if period.get("windDirection") is None else str(period.get("windDirection")),
            short_forecast=None if period.get("shortForecast") is None else str(period.get("shortForecast")),
        )

    def _parse(self, payload: dict) -> NWSHourlyForecastState:
        props = payload.get("properties") or {}
        periods = props.get("periods")
        if not isinstance(periods, list) or not periods:
            raise ValueError("NWS hourly forecast missing periods")
        hours = tuple(self._parse_hour(p) for p in periods[:6] if isinstance(p, dict))
        if not hours:
            raise ValueError("NWS hourly forecast contained no usable periods")
        office, grid_x, grid_y = self._grid
        return NWSHourlyForecastState(
            location_label=self.location_label,
            provider="National Weather Service",
            office=office,
            grid_x=grid_x,
            grid_y=grid_y,
            generated_at=props.get("generatedAt"),
            updated_at=props.get("updateTime") or props.get("updated"),
            hours=hours,
        )

    def collect(self) -> tuple[Observation[object], ...]:
        try:
            self._resolve()
            assert self._forecast_url is not None
            payload = self._request_json(self._forecast_url)
            state = self._parse(payload)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, TypeError, ValueError, AssertionError) as exc:
            # A failed cached endpoint is re-resolved on the next cycle.
            self._forecast_url = None
            return (Observation.unavailable("nws.forecast.hourly", f"NWS forecast request failed: {exc}"),)
        return (Observation.observed("nws.forecast.hourly", state),)
