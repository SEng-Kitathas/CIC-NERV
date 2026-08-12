from __future__ import annotations

from datetime import datetime, timezone
import math
import re
from typing import Iterable

from personal_cic.core.world.components import GeoPoint


def number(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def integer(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None



def boolean(value) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    raw = str(value).strip().casefold()
    if raw in {"true", "yes", "1"}:
        return True
    if raw in {"false", "no", "0"}:
        return False
    return None

def text(value) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def iso_time(value) -> str | None:
    if value in (None, ""):
        return None

    def from_epoch(raw_value: float) -> str | None:
        # ArcGIS REST commonly serializes date fields as Unix epoch milliseconds,
        # while DriveNC uses epoch seconds. Normalize without letting a 13-digit
        # millisecond value masquerade as an impossible far-future second value.
        seconds = float(raw_value)
        while abs(seconds) >= 10_000_000_000:
            seconds /= 1000.0
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(value, (int, float)):
        return from_epoch(float(value))
    raw = str(value).strip()
    if not raw:
        return None
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", raw):
        return from_epoch(float(raw))
    raw = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def haversine_miles(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    radius_miles = 3958.7613
    p1 = math.radians(a_lat)
    p2 = math.radians(b_lat)
    dp = math.radians(b_lat - a_lat)
    dl = math.radians(b_lon - a_lon)
    h = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return radius_miles * 2.0 * math.atan2(math.sqrt(h), math.sqrt(1.0 - h))


def in_scope(
    points: Iterable[GeoPoint],
    *,
    center_latitude: float,
    center_longitude: float,
    radius_miles: float,
) -> bool:
    return any(
        haversine_miles(
            center_latitude,
            center_longitude,
            point.latitude,
            point.longitude,
        ) <= radius_miles
        for point in points
    )


def source_family_for_drivenc(organization: str | None) -> str:
    value = (organization or "").strip()
    low = value.lower()
    if "waze" in low:
        return "Waze"
    if value.upper() == "ATMSERS":
        return "NCDOT/ATMSERS"
    if value:
        return f"DriveNC/{value}"
    return "DriveNC/unknown"


def collection_class_for_drivenc(organization: str | None) -> str:
    return "crowd_report" if "waze" in (organization or "").lower() else "official_report"


def flatten_geojson_geometry(geometry: object) -> tuple[GeoPoint, ...]:
    if not isinstance(geometry, dict):
        return ()
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates")
    points: list[GeoPoint] = []

    def add_pair(pair) -> None:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            return
        lon = number(pair[0])
        lat = number(pair[1])
        if lat is None or lon is None:
            return
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            return
        points.append(GeoPoint(latitude=lat, longitude=lon))

    if kind in {"Point", "MultiPoint", "LineString"}:
        if kind == "Point":
            add_pair(coordinates)
        elif isinstance(coordinates, list):
            for pair in coordinates:
                add_pair(pair)
    elif kind in {"MultiLineString", "Polygon"} and isinstance(coordinates, list):
        for line in coordinates:
            if isinstance(line, list):
                for pair in line:
                    add_pair(pair)
    elif kind == "MultiPolygon" and isinstance(coordinates, list):
        for polygon in coordinates:
            if not isinstance(polygon, list):
                continue
            for ring in polygon:
                if not isinstance(ring, list):
                    continue
                for pair in ring:
                    add_pair(pair)

    return tuple(points)
