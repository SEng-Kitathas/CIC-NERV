from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import statistics
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import (
    SurfaceObservationNetworkState,
    SurfaceStationObservation,
)


_KT_TO_MPH = 1.150779448
_HPA_PER_INHG = 33.8638866667


def _c_to_f(value: float | None) -> float | None:
    return None if value is None else value * 9.0 / 5.0 + 32.0


def _number(value) -> float | None:
    if value in (None, "", "M"):
        return None
    if isinstance(value, str):
        cleaned = value.strip().rstrip("+")
        if not cleaned:
            return None
        value = cleaned
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _time(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value) -> str | None:
    parsed = _time(value)
    return None if parsed is None else parsed.isoformat()


def _haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_mi = 3958.7613
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius_mi * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _rh(temp_c: float | None, dew_c: float | None) -> float | None:
    if temp_c is None or dew_c is None:
        return None
    a, b = 17.625, 243.04
    try:
        value = 100.0 * math.exp((a * dew_c) / (b + dew_c) - (a * temp_c) / (b + temp_c))
    except (ValueError, ZeroDivisionError):
        return None
    return max(0.0, min(100.0, value))


def _ceiling(clouds) -> int | None:
    if not isinstance(clouds, list):
        return None
    bases = []
    for layer in clouds:
        if not isinstance(layer, dict):
            continue
        cover = str(layer.get("cover") or layer.get("amount") or "").upper()
        base = _number(layer.get("base") if "base" in layer else layer.get("base_ft_agl"))
        if cover in {"BKN", "OVC", "VV"} and base is not None:
            bases.append(int(base))
    return min(bases) if bases else None


class AviationSurfaceAdapter:
    ADAPTER_ID = "aviationweather.metar"
    BASE_URL = "https://aviationweather.gov/api/data/metar"

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        station_ids: tuple[str, ...],
        user_agent: str,
        max_age_minutes: float = 90.0,
        timeout_seconds: float = 8.0,
        opener=urlopen,
        now=lambda: datetime.now(timezone.utc),
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.station_ids = station_ids
        self.user_agent = user_agent
        self.max_age_minutes = max_age_minutes
        self.timeout_seconds = timeout_seconds
        self._opener = opener
        self._now = now

    def _url(self) -> str:
        params = {"ids": ",".join(self.station_ids), "format": "json", "hoursBeforeNow": 2}
        return f"{self.BASE_URL}?{urlencode(params)}"

    def _station(self, row: dict) -> SurfaceStationObservation | None:
        station_id = str(row.get("icaoId") or row.get("stationId") or row.get("station_id") or "").strip().upper()
        if not station_id:
            return None
        temp_c = _number(row.get("temp") if "temp" in row else row.get("temperature"))
        dew_c = _number(row.get("dewp") if "dewp" in row else row.get("dewpoint"))
        observed = _iso(row.get("reportTime") or row.get("obsTime") or row.get("observationTime"))
        lat = _number(row.get("lat") if "lat" in row else row.get("latitude"))
        lon = _number(row.get("lon") if "lon" in row else row.get("longitude"))
        distance = None if lat is None or lon is None else _haversine_mi(self.latitude, self.longitude, lat, lon)
        altim = _number(row.get("altim") if "altim" in row else row.get("altimeter"))
        if altim is not None and altim > 100:
            altim /= _HPA_PER_INHG
        vis = _number(row.get("visib") if "visib" in row else row.get("visibility"))
        wspd = _number(row.get("wspd") if "wspd" in row else row.get("windSpeed"))
        wgst = _number(row.get("wgst") if "wgst" in row else row.get("windGust"))
        return SurfaceStationObservation(
            station_id=station_id,
            station_name=None if row.get("name") is None else str(row.get("name")),
            observed_at=observed,
            latitude=lat,
            longitude=lon,
            distance_mi=None if distance is None else round(distance, 2),
            temperature_f=_c_to_f(temp_c),
            dewpoint_f=_c_to_f(dew_c),
            relative_humidity_percent=_rh(temp_c, dew_c),
            wind_direction_deg=_number(row.get("wdir") if "wdir" in row else row.get("windDirection")),
            wind_speed_mph=None if wspd is None else wspd * _KT_TO_MPH,
            wind_gust_mph=None if wgst is None else wgst * _KT_TO_MPH,
            visibility_sm=vis,
            altimeter_inhg=altim,
            sea_level_pressure_hpa=_number(row.get("slp") if "slp" in row else row.get("seaLevelPressure")),
            ceiling_ft_agl=_ceiling(row.get("clouds")),
            flight_category=None if row.get("fltCat") is None else str(row.get("fltCat")),
            present_weather=None if row.get("wxString") is None else str(row.get("wxString")),
            raw_metar=None if row.get("rawOb") is None else str(row.get("rawOb")),
        )

    def _parse(self, payload) -> SurfaceObservationNetworkState:
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            rows = payload["data"]
        elif isinstance(payload, list):
            rows = payload
        else:
            raise ValueError("AviationWeather payload is not a METAR list")

        latest: dict[str, SurfaceStationObservation] = {}
        now = self._now().astimezone(timezone.utc)
        for row in rows:
            if not isinstance(row, dict):
                continue
            station = self._station(row)
            if station is None:
                continue
            observed = _time(station.observed_at)
            if observed is None:
                # A surface report with unknown observation time cannot be called current.
                continue
            age_minutes = (now - observed).total_seconds() / 60.0
            if age_minutes > self.max_age_minutes or age_minutes < -5.0:
                continue
            prior = latest.get(station.station_id)
            prior_time = _time(prior.observed_at) if prior else None
            if prior is None or (observed is not None and (prior_time is None or observed > prior_time)):
                latest[station.station_id] = station

        stations = sorted(
            latest.values(),
            key=lambda item: (
                float("inf") if item.distance_mi is None else item.distance_mi,
                item.station_id,
            ),
        )
        if not stations:
            raise ValueError("no current METAR observations returned for configured stations")

        temps = [s.temperature_f for s in stations if s.temperature_f is not None]
        dewps = [s.dewpoint_f for s in stations if s.dewpoint_f is not None]
        temp_median = None if not temps else float(statistics.median(temps))
        dewp_median = None if not dewps else float(statistics.median(dewps))
        rhs = [s.relative_humidity_percent for s in stations if s.relative_humidity_percent is not None]
        rh = None if not rhs else float(statistics.median(rhs))
        observed_times = [_time(s.observed_at) for s in stations]
        observed_times = [t for t in observed_times if t is not None]
        freshest = max(observed_times).isoformat() if observed_times else None
        spread = None if len(temps) < 2 else max(temps) - min(temps)
        return SurfaceObservationNetworkState(
            location_label=self.location_label,
            provider="NOAA/NWS AviationWeather.gov METAR",
            freshest_observed_at=freshest,
            selected_station_id=stations[0].station_id,
            station_count=len(stations),
            temperature_median_f=temp_median,
            dewpoint_median_f=dewp_median,
            relative_humidity_percent=rh,
            temperature_spread_f=spread,
            stations=tuple(stations),
        )

    def collect(self) -> tuple[Observation[object], ...]:
        request = Request(self._url(), headers={"User-Agent": self.user_agent, "Accept": "application/json"})
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                if getattr(response, "status", 200) == 204:
                    raise ValueError("AviationWeather returned no recent METAR data")
                raw = response.read()
                if not raw:
                    raise ValueError("AviationWeather returned an empty response")
                payload = json.loads(raw.decode("utf-8"))
            state = self._parse(payload)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return (Observation.unavailable("aviationweather.metar", f"METAR request failed: {exc}"),)
        return (Observation.observed("aviationweather.metar", state),)
