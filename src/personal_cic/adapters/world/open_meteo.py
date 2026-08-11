from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import WeatherForecastState, WeatherState


class OpenMeteoWeatherAdapter:
    ADAPTER_ID = "openmeteo.weather"
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    CURRENT_FIELDS = (
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "weather_code",
        "cloud_cover",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
    )
    DAILY_FIELDS = (
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_probability_max",
        "sunrise",
        "sunset",
    )

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        timeout_seconds: float = 8.0,
        opener=urlopen,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def _url(self) -> str:
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": ",".join(self.CURRENT_FIELDS),
            "daily": ",".join(self.DAILY_FIELDS),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
            "forecast_days": 2,
        }
        return f"{self.BASE_URL}?{urlencode(params)}"

    @staticmethod
    def _number(value):
        return None if value is None else float(value)

    @staticmethod
    def _integer(value):
        return None if value is None else int(value)

    def _parse_current(self, payload: dict) -> WeatherState:
        current = payload["current"]
        return WeatherState(
            location_label=self.location_label,
            provider="Open-Meteo",
            provider_observed_at=current.get("time"),
            provider_timezone=payload.get("timezone"),
            temperature_f=self._number(current.get("temperature_2m")),
            apparent_temperature_f=self._number(current.get("apparent_temperature")),
            relative_humidity_percent=self._number(current.get("relative_humidity_2m")),
            precipitation_in=self._number(current.get("precipitation")),
            weather_code=self._integer(current.get("weather_code")),
            cloud_cover_percent=self._number(current.get("cloud_cover")),
            wind_speed_mph=self._number(current.get("wind_speed_10m")),
            wind_direction_deg=self._number(current.get("wind_direction_10m")),
            wind_gust_mph=self._number(current.get("wind_gusts_10m")),
        )

    def _parse_forecast(self, payload: dict) -> WeatherForecastState:
        daily = payload["daily"]

        def first(name):
            values = daily.get(name) or []
            return values[0] if values else None

        return WeatherForecastState(
            location_label=self.location_label,
            provider="Open-Meteo",
            provider_timezone=payload.get("timezone"),
            forecast_date=first("time"),
            high_f=self._number(first("temperature_2m_max")),
            low_f=self._number(first("temperature_2m_min")),
            precipitation_probability_max_percent=self._number(
                first("precipitation_probability_max")
            ),
            sunrise=first("sunrise"),
            sunset=first("sunset"),
        )

    def collect(self) -> tuple[Observation[object], ...]:
        request = Request(
            self._url(),
            headers={"User-Agent": "Personal-CIC/0.3.1"},
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            detail = f"Open-Meteo request failed: {exc}"
            return (
                Observation.unavailable("openmeteo.current", detail),
                Observation.unavailable("openmeteo.daily", detail),
            )

        observations: list[Observation[object]] = []
        try:
            observations.append(
                Observation.observed("openmeteo.current", self._parse_current(payload))
            )
        except (KeyError, TypeError, ValueError) as exc:
            observations.append(
                Observation.unavailable("openmeteo.current", f"current parse failed: {exc}")
            )

        try:
            observations.append(
                Observation.observed("openmeteo.daily", self._parse_forecast(payload))
            )
        except (KeyError, TypeError, ValueError) as exc:
            observations.append(
                Observation.unavailable("openmeteo.daily", f"daily parse failed: {exc}")
            )

        return tuple(observations)
