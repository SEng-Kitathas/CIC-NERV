from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import TrafficEventCollectionState, TrafficEventObservation
from .traffic_common import flatten_geojson_geometry, in_scope, iso_time, text


class DriveNCWZDxAdapter:
    ADAPTER_ID = "drivenc.wzdx"
    PROVIDER = "NCDOT DriveNC WZDx"
    BASE_URL = "https://www.drivenc.gov/api/wzdx"

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        radius_miles: float,
        timeout_seconds: float = 20.0,
        opener=urlopen,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.radius_miles = radius_miles
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    @staticmethod
    def _source_family(data_source_id: str | None) -> str:
        if (data_source_id or "").upper() == "ATMSERS":
            return "NCDOT/ATMSERS"
        return f"NCDOT/WZDx/{data_source_id}" if data_source_id else "NCDOT/WZDx/unknown"

    def _parse(self, payload: dict) -> tuple[TrafficEventCollectionState, int]:
        if not isinstance(payload, dict):
            raise ValueError("DriveNC WZDx payload is not an object")
        if payload.get("type") != "FeatureCollection":
            raise ValueError("DriveNC WZDx payload is not a GeoJSON FeatureCollection")
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("DriveNC WZDx payload missing features list")

        events: list[TrafficEventObservation] = []
        malformed = 0
        for feature in features:
            if not isinstance(feature, dict):
                malformed += 1
                continue
            props = feature.get("properties")
            core = props.get("core_details") if isinstance(props, dict) else None
            if not isinstance(props, dict) or not isinstance(core, dict):
                malformed += 1
                continue
            record_id = text(feature.get("id"))
            road_event_id = text(props.get("road_event_id"))
            if record_id is None or road_event_id is None:
                malformed += 1
                continue
            points = flatten_geojson_geometry(feature.get("geometry"))
            if not points:
                malformed += 1
                continue
            if not in_scope(
                points,
                center_latitude=self.latitude,
                center_longitude=self.longitude,
                radius_miles=self.radius_miles,
            ):
                continue
            road_names = core.get("road_names")
            roadway = None
            if isinstance(road_names, list):
                names = [str(item).strip() for item in road_names if str(item).strip()]
                roadway = " / ".join(names) if names else None
            data_source_id = text(core.get("data_source_id"))
            lanes = props.get("lanes")
            lane_parts = []
            if isinstance(lanes, list):
                for lane in lanes:
                    if not isinstance(lane, dict):
                        continue
                    lane_type = text(lane.get("type")) or "lane"
                    status = text(lane.get("status")) or "unknown"
                    lane_parts.append(f"{lane_type}:{status}")
            events.append(
                TrafficEventObservation(
                    source_record_id=record_id,
                    source_family=self._source_family(data_source_id),
                    provider=self.PROVIDER,
                    collection_class="official_report",
                    event_type=text(core.get("event_type")) or "work-zone",
                    event_subtype=None,
                    description=text(core.get("description")) or "DriveNC WZDx work zone",
                    roadway=roadway,
                    direction=text(core.get("direction")),
                    county=None,
                    geometry=points,
                    reported_at=None,
                    updated_at=iso_time(core.get("update_date")),
                    start_at=iso_time(props.get("start_date")),
                    end_at=iso_time(props.get("end_date")),
                    severity=text(props.get("vehicle_impact")),
                    full_closure=True if str(props.get("vehicle_impact") or "").lower() == "all-lanes-closed" else None,
                    lanes_affected="; ".join(lane_parts) if lane_parts else None,
                    major_event=None,
                    source_organization=data_source_id,
                    source_id=road_event_id,
                    upstream_event_id=road_event_id,
                )
            )

        events.sort(key=lambda item: (item.source_family, item.upstream_event_id or "", item.source_record_id))
        fresh_times = [event.updated_at for event in events if event.updated_at]
        families = sorted({event.source_family for event in events})
        family_label = families[0] if len(families) == 1 else "mixed" if families else "NCDOT/WZDx"
        state = TrafficEventCollectionState(
            location_label=self.location_label,
            provider=self.PROVIDER,
            source_family=family_label,
            collection_class="official_report",
            scope_center_latitude=self.latitude,
            scope_center_longitude=self.longitude,
            scope_radius_miles=self.radius_miles,
            source_record_count=len(features),
            local_record_count=len(events),
            freshest_source_at=max(fresh_times) if fresh_times else None,
            events=tuple(events),
        )
        return state, malformed

    def collect(self) -> tuple[Observation[object], ...]:
        request = Request(
            self.BASE_URL,
            headers={
                "User-Agent": "Personal-CIC/0.3.6 (local personal system)",
                "Accept": "application/json",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
            if not raw:
                raise ValueError("DriveNC WZDx returned an empty response")
            payload = json.loads(raw.decode("utf-8"))
            state, malformed = self._parse(payload)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return (Observation.unavailable(self.ADAPTER_ID, f"DriveNC WZDx request failed: {exc}"),)
        if malformed:
            return (
                Observation.partial(
                    self.ADAPTER_ID,
                    state,
                    f"DriveNC WZDx omitted {malformed} malformed source features",
                ),
            )
        return (Observation.observed(self.ADAPTER_ID, state),)
