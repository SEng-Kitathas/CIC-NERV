from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import (
    GeoPoint,
    TrafficEventCollectionState,
    TrafficEventObservation,
    TrafficFlowCollectionState,
    TrafficFlowProbeObservation,
)
from .traffic_common import (
    boolean,
    flatten_geojson_geometry,
    in_scope,
    integer,
    iso_time,
    number,
    text,
)


@dataclass(frozen=True, slots=True)
class FlowProbeSpec:
    probe_id: str
    label: str
    latitude: float
    longitude: float


class _TomTomBase:
    SOURCE_FAMILY = "TomTom Traffic"

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        radius_miles: float,
        api_key_env: str,
        timeout_seconds: float,
        opener=urlopen,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.radius_miles = radius_miles
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def _key(self) -> str | None:
        value = os.environ.get(self.api_key_env)
        return None if value is None or not value.strip() else value.strip()

    def _require_key(self) -> str:
        key = self._key()
        if key is None:
            raise ValueError(f"TomTom API key environment variable {self.api_key_env} is not set")
        return key

    def _safe_error(self, context: str, exc: BaseException) -> str:
        key = self._key()
        detail = str(exc)
        if key:
            detail = detail.replace(key, "<REDACTED>")
            detail = detail.replace(quote_plus(key), "<REDACTED>")
        return f"TomTom {context} request failed ({type(exc).__name__}): {detail}"


class TomTomIncidentsAdapter(_TomTomBase):
    """TomTom Orbis Incident Details collector.

    Incident Details permits at most 10,000 km² per bounding box. CIC tiles the
    configured local envelope into <=90 km cells, deduplicates by TomTom incident
    ID, then applies its actual radial scope. The default 75-mile scope resolves
    to the nine requests proven during target reconnaissance.
    """

    ADAPTER_ID = "tomtom.incidents"
    PROVIDER = "TomTom Orbis Incident Details"
    COLLECTION_CLASS = "commercial_report"
    ENDPOINT = "https://api.tomtom.com/maps/orbis/traffic/incidents/details"
    ATTRIBUTES = (
        "incidents("
        "type,"
        "geometry(type,coordinates),"
        "properties("
        "id,iconCategory,magnitudeOfDelay,"
        "events(description,code,iconCategory),"
        "startTime,endTime,from,to,lengthInMeters,delayInSeconds,"
        "roadNumbers,timeValidity,probabilityOfOccurrence,"
        "numberOfReports,lastReportTime"
        ")"
        ")"
    )
    TILE_SIDE_KM = 90.0
    MAX_TILES_PER_CYCLE = 9

    def _tiles(self) -> tuple[tuple[float, float, float, float], ...]:
        radius_km = self.radius_miles * 1.609344
        diameter_km = radius_km * 2.0
        grid = max(1, math.ceil(diameter_km / self.TILE_SIDE_KM))
        if grid * grid > self.MAX_TILES_PER_CYCLE:
            raise ValueError(
                "configured TomTom incident scope would exceed "
                f"{self.MAX_TILES_PER_CYCLE} bounded requests per collection cycle"
            )

        dlat = radius_km / 111.32
        cosine = max(0.01, abs(math.cos(math.radians(self.latitude))))
        dlon = radius_km / (111.32 * cosine)
        lat_min = self.latitude - dlat
        lat_max = self.latitude + dlat
        lon_min = self.longitude - dlon
        lon_max = self.longitude + dlon
        lat_edges = [lat_min + (lat_max - lat_min) * i / grid for i in range(grid + 1)]
        lon_edges = [lon_min + (lon_max - lon_min) * i / grid for i in range(grid + 1)]
        return tuple(
            (lon_edges[col], lat_edges[row], lon_edges[col + 1], lat_edges[row + 1])
            for row in range(grid)
            for col in range(grid)
        )

    def _request_tile(self, bbox: tuple[float, float, float, float]) -> list[dict]:
        key = self._require_key()
        query = urlencode(
            {
                "apiVersion": "2",
                "bbox": ",".join(f"{value:.7f}" for value in bbox),
                "timeValidity": "present",
            }
        )
        request = Request(
            f"{self.ENDPOINT}?{query}",
            headers={
                "User-Agent": "Personal-CIC/0.3.6 (local personal system)",
                "Accept": "application/json",
                "Accept-Language": "en-US",
                "TomTom-Api-Key": key,
                "Attributes": self.ATTRIBUTES,
            },
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            raw = response.read()
        if not raw:
            raise ValueError("Incident Details returned an empty response")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("incidents"), list):
            raise ValueError("Incident Details payload is not an object with an incidents array")
        return [item for item in payload["incidents"] if isinstance(item, dict)]

    @staticmethod
    def _event_details(properties: dict) -> tuple[tuple[str, ...], tuple[int, ...]]:
        details: list[str] = []
        codes: list[int] = []
        for item in properties.get("events") or []:
            if not isinstance(item, dict):
                continue
            description = text(item.get("description"))
            code = integer(item.get("code"))
            if description is not None:
                details.append(description)
            if code is not None:
                codes.append(code)
        return tuple(details), tuple(codes)

    def _event(self, item: dict) -> TrafficEventObservation | None:
        properties = item.get("properties")
        if not isinstance(properties, dict):
            return None
        record_id = text(properties.get("id"))
        category = text(properties.get("iconCategory"))
        if record_id is None or category is None:
            return None

        geometry = flatten_geojson_geometry(item.get("geometry"))
        if not geometry or not in_scope(
            geometry,
            center_latitude=self.latitude,
            center_longitude=self.longitude,
            radius_miles=self.radius_miles,
        ):
            return None

        details, codes = self._event_details(properties)
        road_numbers = tuple(
            value
            for raw in (properties.get("roadNumbers") or [])
            if (value := text(raw)) is not None
        )
        roadway = " / ".join(road_numbers) if road_numbers else None
        description = " // ".join(details) if details else category

        return TrafficEventObservation(
            source_record_id=record_id,
            source_family=self.SOURCE_FAMILY,
            provider=self.PROVIDER,
            collection_class=self.COLLECTION_CLASS,
            event_type=category,
            event_subtype=None,
            description=description,
            roadway=roadway,
            direction=None,
            county=None,
            geometry=geometry,
            reported_at=None,
            updated_at=None,
            start_at=iso_time(properties.get("startTime")),
            end_at=iso_time(properties.get("endTime")),
            severity=text(properties.get("magnitudeOfDelay")),
            # TomTom's `roadClosed` category is preserved as source evidence but
            # is not silently promoted into CIC's stronger provider-independent
            # `full_closure` proposition.
            full_closure=None,
            lanes_affected=None,
            major_event=None,
            source_organization="TomTom Traffic",
            source_id=record_id,
            upstream_event_id=record_id,
            magnitude_of_delay=text(properties.get("magnitudeOfDelay")),
            delay_seconds=integer(properties.get("delayInSeconds")),
            length_meters=number(properties.get("lengthInMeters")),
            road_numbers=road_numbers,
            from_location=text(properties.get("from")),
            to_location=text(properties.get("to")),
            probability_of_occurrence=text(properties.get("probabilityOfOccurrence")),
            time_validity=text(properties.get("timeValidity")),
            event_details=details,
            event_codes=codes,
            community_report_count=integer(properties.get("numberOfReports")),
            community_last_report_at=iso_time(properties.get("lastReportTime")),
        )

    def collect(self) -> tuple[Observation[object], ...]:
        try:
            self._require_key()
            tiles = self._tiles()
        except Exception as exc:
            return (Observation.unavailable(self.ADAPTER_ID, self._safe_error("incident", exc)),)

        records: dict[str, dict] = {}
        tile_errors: list[str] = []
        successful_tiles = 0
        for index, bbox in enumerate(tiles, start=1):
            try:
                rows = self._request_tile(bbox)
                successful_tiles += 1
                for row in rows:
                    properties = row.get("properties")
                    record_id = text(properties.get("id")) if isinstance(properties, dict) else None
                    if record_id is not None:
                        records[record_id] = row
            except Exception as exc:
                tile_errors.append(f"tile {index}/{len(tiles)}: {self._safe_error('incident', exc)}")

        if successful_tiles == 0:
            detail = "; ".join(tile_errors) or "no TomTom incident tile could be observed"
            return (Observation.unavailable(self.ADAPTER_ID, detail),)

        events: list[TrafficEventObservation] = []
        malformed = 0
        for row in records.values():
            try:
                event = self._event(row)
            except Exception:
                malformed += 1
                continue
            if event is not None:
                events.append(event)
        events.sort(key=lambda event: event.source_record_id)

        state = TrafficEventCollectionState(
            location_label=self.location_label,
            provider=self.PROVIDER,
            source_family=self.SOURCE_FAMILY,
            collection_class=self.COLLECTION_CLASS,
            scope_center_latitude=self.latitude,
            scope_center_longitude=self.longitude,
            scope_radius_miles=self.radius_miles,
            source_record_count=len(records),
            local_record_count=len(events),
            # Incident Details v2 does not expose one trustworthy provider update
            # time for the incident collection. Retrieval freshness lives in the
            # separate ObservationState instead of being manufactured here.
            freshest_source_at=None,
            events=tuple(events),
        )

        details: list[str] = []
        if tile_errors:
            details.append(
                f"{len(tile_errors)} of {len(tiles)} bounded incident requests unavailable"
            )
        if malformed:
            details.append(f"{malformed} incident records malformed or unrepresentable")
        if details:
            return (Observation.partial(self.ADAPTER_ID, state, "; ".join(details)),)
        return (Observation.observed(self.ADAPTER_ID, state),)


class TomTomFlowAdapter(_TomTomBase):
    ADAPTER_ID = "tomtom.flow"
    PROVIDER = "TomTom Flow Segment Data"
    COLLECTION_CLASS = "commercial_modeled_telemetry"
    ENDPOINT = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative/10/json"

    def __init__(self, *, probes: tuple[FlowProbeSpec, ...], **kwargs) -> None:
        super().__init__(**kwargs)
        self.probes = probes

    def _request_probe(self, probe: FlowProbeSpec) -> dict:
        key = self._require_key()
        query = urlencode(
            {
                "point": f"{probe.latitude},{probe.longitude}",
                "unit": "mph",
                "openLr": "true",
                "key": key,
            }
        )
        request = Request(
            f"{self.ENDPOINT}?{query}",
            headers={
                "User-Agent": "Personal-CIC/0.3.6 (local personal system)",
                "Accept": "application/json",
            },
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            raw = response.read()
        if not raw:
            raise ValueError("Flow Segment Data returned an empty response")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("flowSegmentData"), dict):
            raise ValueError("Flow Segment Data payload lacks flowSegmentData object")
        return payload["flowSegmentData"]

    def _probe(self, spec: FlowProbeSpec, payload: dict) -> TrafficFlowProbeObservation:
        coordinates = payload.get("coordinates")
        raw_points = coordinates.get("coordinate") if isinstance(coordinates, dict) else None
        geometry: list[GeoPoint] = []
        for item in raw_points or []:
            if not isinstance(item, dict):
                continue
            lat = number(item.get("latitude"))
            lon = number(item.get("longitude"))
            if lat is None or lon is None or not -90 <= lat <= 90 or not -180 <= lon <= 180:
                continue
            geometry.append(GeoPoint(latitude=lat, longitude=lon))
        if not geometry:
            raise ValueError(f"flow probe {spec.probe_id} returned no valid matched-segment geometry")

        current_speed = number(payload.get("currentSpeed"))
        free_flow_speed = number(payload.get("freeFlowSpeed"))
        confidence = number(payload.get("confidence"))
        if current_speed is None or free_flow_speed is None or confidence is None:
            raise ValueError(f"flow probe {spec.probe_id} lacks required speed/confidence values")

        return TrafficFlowProbeObservation(
            probe_id=spec.probe_id,
            label=spec.label,
            source_family=self.SOURCE_FAMILY,
            provider=self.PROVIDER,
            collection_class=self.COLLECTION_CLASS,
            query_latitude=spec.latitude,
            query_longitude=spec.longitude,
            match_method="nearest_road_fragment_to_query_point",
            functional_road_class=text(payload.get("frc")),
            current_speed_mph=current_speed,
            free_flow_speed_mph=free_flow_speed,
            current_travel_time_seconds=integer(payload.get("currentTravelTime")),
            free_flow_travel_time_seconds=integer(payload.get("freeFlowTravelTime")),
            confidence=confidence,
            road_closure=boolean(payload.get("roadClosure")),
            openlr=text(payload.get("openlr")),
            geometry=tuple(geometry),
        )

    def collect(self) -> tuple[Observation[object], ...]:
        try:
            self._require_key()
        except Exception as exc:
            return (Observation.unavailable(self.ADAPTER_ID, self._safe_error("flow", exc)),)

        probes: list[TrafficFlowProbeObservation] = []
        failures: list[str] = []
        for spec in self.probes:
            try:
                payload = self._request_probe(spec)
                probes.append(self._probe(spec, payload))
            except Exception as exc:
                failures.append(f"{spec.probe_id}: {self._safe_error('flow', exc)}")

        if not probes:
            return (
                Observation.unavailable(
                    self.ADAPTER_ID,
                    "; ".join(failures) or "no configured TomTom flow probe could be observed",
                ),
            )

        probes.sort(key=lambda item: item.probe_id)
        state = TrafficFlowCollectionState(
            location_label=self.location_label,
            provider=self.PROVIDER,
            source_family=self.SOURCE_FAMILY,
            collection_class=self.COLLECTION_CLASS,
            scope_center_latitude=self.latitude,
            scope_center_longitude=self.longitude,
            scope_radius_miles=self.radius_miles,
            configured_probe_count=len(self.probes),
            successful_probe_count=len(probes),
            probes=tuple(probes),
        )
        if failures:
            return (
                Observation.partial(
                    self.ADAPTER_ID,
                    state,
                    f"{len(failures)} of {len(self.probes)} configured nearest-segment probes unavailable",
                ),
            )
        return (Observation.observed(self.ADAPTER_ID, state),)
