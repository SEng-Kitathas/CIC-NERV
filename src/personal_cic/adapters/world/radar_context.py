from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import RadarContextState
from .radar_mosaic import radar_bbox


class TIGERRadarContextAdapter:
    """Build a restrained local map-context artifact from Census TIGERweb.

    The browser never calls Census directly. GeoJSON is normalized and cached
    locally; WorldState carries only provenance/hash/count metadata.
    """

    ADAPTER_ID = "census.tiger.radar_context"
    PROVIDER = "U.S. Census Bureau TIGERweb"
    COUNTY_URL = (
        "https://tigerweb.geo.census.gov/arcgis/rest/services/"
        "TIGERweb/State_County/MapServer/1/query"
    )
    # Generalized primary-road layer is deliberate at a ~150-mile-tall radar
    # view: it preserves operational context without turning the overlay into a
    # street map. TIGERweb labels this layer "Primary Roads 2_1M scale".
    PRIMARY_ROAD_URL = (
        "https://tigerweb.geo.census.gov/arcgis/rest/services/"
        "TIGERweb/Transportation/MapServer/1/query"
    )
    SECONDARY_ROAD_URL = (
        "https://tigerweb.geo.census.gov/arcgis/rest/services/"
        "TIGERweb/Transportation/MapServer/3/query"
    )
    INCORPORATED_PLACE_URL = (
        "https://tigerweb.geo.census.gov/arcgis/rest/services/"
        "TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4/query"
    )
    CDP_URL = (
        "https://tigerweb.geo.census.gov/arcgis/rest/services/"
        "TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/5/query"
    )

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        range_miles: float,
        image_width: int,
        image_height: int,
        cache_dir: Path,
        user_agent: str,
        max_age_days: float,
        timeout_seconds: float = 8.0,
        opener: Callable = urlopen,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.range_miles = range_miles
        self.image_width = image_width
        self.image_height = image_height
        self.cache_dir = Path(cache_dir)
        self.user_agent = user_agent
        self.max_age_days = max_age_days
        self.timeout_seconds = timeout_seconds
        self.opener = opener
        self.now = now or (lambda: datetime.now(timezone.utc))

    @property
    def cache_path(self) -> Path:
        return self.cache_dir / "context.json"

    def _bbox(self) -> tuple[float, float, float, float]:
        return radar_bbox(
            latitude=self.latitude,
            longitude=self.longitude,
            range_miles=self.range_miles,
            image_width=self.image_width,
            image_height=self.image_height,
        )

    def _query_url(
        self,
        base_url: str,
        *,
        out_fields: str,
        return_geometry: bool,
        geojson: bool,
    ) -> str:
        west, south, east, north = self._bbox()
        params = {
            "where": "1=1",
            "geometry": f"{west:.6f},{south:.6f},{east:.6f},{north:.6f}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "outSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": out_fields,
            "returnGeometry": "true" if return_geometry else "false",
            "f": "geojson" if geojson else "json",
        }
        return base_url + "?" + urlencode(params)

    def _request_json(self, url: str) -> dict:
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/geo+json, application/json",
            },
        )
        with self.opener(request, timeout=self.timeout_seconds) as response:
            payload = response.read()
        data = json.loads(payload.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("TIGERweb response was not a JSON object")
        if data.get("error"):
            raise ValueError(f"TIGERweb error: {data['error']}")
        return data

    @staticmethod
    def _normalize_geo_features(
        payload: dict,
        *,
        allowed_types: tuple[str, ...],
        kind: str,
    ) -> list[dict]:
        if payload.get("type") != "FeatureCollection":
            raise ValueError(f"TIGERweb {kind} response was not GeoJSON FeatureCollection")
        result: list[dict] = []
        for feature in payload.get("features", []):
            if not isinstance(feature, dict):
                continue
            geometry = feature.get("geometry")
            if not isinstance(geometry, dict) or geometry.get("type") not in allowed_types:
                continue
            props = feature.get("properties") or {}
            name = props.get("BASENAME") or props.get("NAME")
            result.append(
                {
                    "name": None if name is None else str(name),
                    "geometry": geometry,
                }
            )
        # ArcGIS does not owe callers a stable feature order unless a query
        # explicitly requests one. Canonicalize locally so semantically
        # identical context cannot manufacture a new content hash merely
        # because the service returned features in another order.
        result.sort(
            key=lambda item: (
                item["name"] or "",
                json.dumps(
                    item["geometry"],
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            )
        )
        return result

    @staticmethod
    def _normalize_places(payload: dict) -> list[dict]:
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("TIGERweb place response contained no features array")
        result: list[dict] = []
        for feature in features:
            if not isinstance(feature, dict):
                continue
            attrs = feature.get("attributes") or {}
            name = attrs.get("BASENAME") or attrs.get("NAME")
            try:
                lat = float(attrs.get("INTPTLAT"))
                lon = float(attrs.get("INTPTLON"))
            except (TypeError, ValueError):
                continue
            if name:
                result.append({"name": str(name), "lat": lat, "lon": lon})
        return result

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(payload)
        tmp.replace(path)

    @staticmethod
    def _content_sha(data: dict) -> str:
        semantic = {
            key: value
            for key, value in data.items()
            if key not in {"retrieved_at", "content_sha256"}
        }
        payload = json.dumps(
            semantic,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def _state_from_bytes(self, payload: bytes) -> RadarContextState:
        data = json.loads(payload.decode("utf-8"))
        bounds = data.get("bounds") or {}
        computed_content_sha = self._content_sha(data)
        declared_content_sha = data.get("content_sha256")
        if declared_content_sha is not None and str(declared_content_sha) != computed_content_sha:
            raise ValueError("cached TIGERweb context content hash mismatch")
        content_sha = computed_content_sha
        return RadarContextState(
            location_label=self.location_label,
            provider=str(data.get("provider", self.PROVIDER)),
            retrieved_at=str(data["retrieved_at"]),
            west=float(bounds["west"]),
            south=float(bounds["south"]),
            east=float(bounds["east"]),
            north=float(bounds["north"]),
            context_sha256=sha256(payload).hexdigest(),
            content_sha256=content_sha,
            county_count=len(data.get("counties") or []),
            primary_road_count=len(data.get("primary_roads") or []),
            secondary_road_count=len(data.get("secondary_roads") or []),
            place_count=len(data.get("places") or []),
        )

    def _cached_fallback(self) -> RadarContextState | None:
        if not self.cache_path.exists():
            return None
        try:
            payload = self.cache_path.read_bytes()
            state = self._state_from_bytes(payload)
            retrieved = datetime.fromisoformat(state.retrieved_at)
            if retrieved.tzinfo is None:
                retrieved = retrieved.replace(tzinfo=timezone.utc)
            now = self.now()
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            age_days = (now.astimezone(timezone.utc) - retrieved.astimezone(timezone.utc)).total_seconds() / 86400
            if age_days > self.max_age_days:
                return None
            return state
        except Exception:
            return None

    def collect(self) -> tuple[Observation[object], ...]:
        queries = {
            "counties": self._query_url(
                self.COUNTY_URL,
                out_fields="BASENAME,NAME",
                return_geometry=True,
                geojson=True,
            ),
            "primary_roads": self._query_url(
                self.PRIMARY_ROAD_URL,
                out_fields="BASENAME,NAME",
                return_geometry=True,
                geojson=True,
            ),
            "secondary_roads": self._query_url(
                self.SECONDARY_ROAD_URL,
                out_fields="BASENAME,NAME",
                return_geometry=True,
                geojson=True,
            ),
            "incorporated": self._query_url(
                self.INCORPORATED_PLACE_URL,
                out_fields="BASENAME,NAME,INTPTLAT,INTPTLON",
                return_geometry=False,
                geojson=False,
            ),
            "cdp": self._query_url(
                self.CDP_URL,
                out_fields="BASENAME,NAME,INTPTLAT,INTPTLON",
                return_geometry=False,
                geojson=False,
            ),
        }
        try:
            with ThreadPoolExecutor(max_workers=len(queries)) as pool:
                futures = {
                    key: pool.submit(self._request_json, url)
                    for key, url in queries.items()
                }
                results = {key: future.result() for key, future in futures.items()}

            counties = self._normalize_geo_features(
                results["counties"],
                allowed_types=("Polygon", "MultiPolygon"),
                kind="counties",
            )
            primary = self._normalize_geo_features(
                results["primary_roads"],
                allowed_types=("LineString", "MultiLineString"),
                kind="primary roads",
            )
            secondary = self._normalize_geo_features(
                results["secondary_roads"],
                allowed_types=("LineString", "MultiLineString"),
                kind="secondary roads",
            )
            places = self._normalize_places(results["incorporated"])
            places.extend(self._normalize_places(results["cdp"]))
            deduped_places: dict[tuple[str, float, float], dict] = {}
            for place in places:
                key = (place["name"], round(place["lat"], 5), round(place["lon"], 5))
                deduped_places[key] = place

            west, south, east, north = self._bbox()
            now = self.now()
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            normalized = {
                "provider": self.PROVIDER,
                "retrieved_at": now.astimezone(timezone.utc).isoformat(),
                "bounds": {
                    "west": west,
                    "south": south,
                    "east": east,
                    "north": north,
                },
                "counties": counties,
                "primary_roads": primary,
                "secondary_roads": secondary,
                "places": sorted(deduped_places.values(), key=lambda item: item["name"]),
            }
            normalized["content_sha256"] = self._content_sha(normalized)
            payload = json.dumps(
                normalized,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            self._atomic_write(self.cache_path, payload)
            return (Observation.observed(self.ADAPTER_ID, self._state_from_bytes(payload)),)
        except Exception as exc:
            cached = self._cached_fallback()
            if cached is not None:
                return (
                    Observation.partial(
                        self.ADAPTER_ID,
                        cached,
                        f"TIGERweb refresh failed; using cached context: {exc}",
                    ),
                )
            return (
                Observation.unavailable(
                    self.ADAPTER_ID,
                    f"TIGERweb context fetch failed: {exc}",
                ),
            )
