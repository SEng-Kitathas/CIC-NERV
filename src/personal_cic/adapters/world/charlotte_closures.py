from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import TrafficEventCollectionState, TrafficEventObservation
from .traffic_common import boolean, flatten_geojson_geometry, in_scope, iso_time, text


class CharlotteStreetClosuresAdapter:
    ADAPTER_ID = "charlotte.street_closures"
    PROVIDER = "City of Charlotte Street Closures and Detours"
    SOURCE_FAMILY = "City of Charlotte/CDOT"
    # Current public CDOT closure layer used by the City of Charlotte interactive
    # Street Closure Map. The older ArcGIS Online FeatureServer item resolves to
    # a stale endpoint; the city-operated MapServer is the live public authority.
    LAYER_URL = (
        "https://gis.charlottenc.gov/arcgis/rest/services/CDOT/"
        "StreetClosuresAndDetours/MapServer/0/query"
    )

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        radius_miles: float,
        timeout_seconds: float = 8.0,
        opener=urlopen,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.radius_miles = radius_miles
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def _url(self) -> str:
        return self.LAYER_URL + "?" + urlencode(
            {
                "where": "ACTIVE = 'Yes'",
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "geojson",
                "resultRecordCount": "2000",
            }
        )

    @staticmethod
    def _pick(props: dict, *names: str):
        folded = {str(key).casefold(): value for key, value in props.items()}
        for name in names:
            value = folded.get(name.casefold())
            if value not in (None, ""):
                return value
        return None

    def _event(self, feature: dict) -> TrafficEventObservation | None:
        props = feature.get("properties")
        if not isinstance(props, dict):
            return None
        points = flatten_geojson_geometry(feature.get("geometry"))
        if not points:
            return None
        if not in_scope(
            points,
            center_latitude=self.latitude,
            center_longitude=self.longitude,
            radius_miles=self.radius_miles,
        ):
            return None

        # Prefer the city's stable closure identity over the ArcGIS OBJECTID.
        record_id = text(
            self._pick(props, "ClosureID", "GlobalID", "OBJECTID", "FID", "ID")
        ) or text(feature.get("id"))
        if record_id is None:
            return None

        roadway = text(
            self._pick(
                props,
                "BLOCKNM",
                "StreetName",
                "Street",
                "Roadway",
                "RoadName",
            )
        )
        location_detail = text(self._pick(props, "LOCDESC", "Location", "Address"))
        comment = text(self._pick(props, "COMMENT", "Comments", "Details", "Description"))
        description_parts: list[str] = []
        for item in (location_detail, comment):
            if item and item not in description_parts:
                description_parts.append(item)
        description = " — ".join(description_parts) or roadway or "Charlotte street closure/detour"

        event_type = text(
            self._pick(props, "BLOCKTYPE", "Reason", "EventType", "Type")
        ) or "street_closure"
        closure_type = text(self._pick(props, "ClosureType", "Type"))
        full = boolean(self._pick(props, "FULLCLOSE", "FullClosure", "IsFullClosure"))

        start = iso_time(self._pick(props, "STARTDATE", "StartDate", "StartTime", "BeginDate", "FromDate"))
        end = iso_time(self._pick(props, "ENDDATE", "EndDate", "EndTime", "ToDate", "PlannedEndDate"))
        reported = iso_time(self._pick(props, "CreationDate", "CreateDate", "created_date"))
        updated = iso_time(
            self._pick(props, "last_edited_date", "EditDate", "LastUpdated", "Modified", "UpdateDate")
        )
        direction = text(self._pick(props, "DIRECTION", "Direction", "DirectionOfTravel"))
        lanes = "All access closed" if full is True else None
        major_event = text(self._pick(props, "SpecialProject"))

        return TrafficEventObservation(
            source_record_id=record_id,
            source_family=self.SOURCE_FAMILY,
            provider=self.PROVIDER,
            collection_class="official_report",
            event_type=event_type,
            event_subtype=closure_type,
            description=description,
            roadway=roadway,
            direction=direction,
            county="Mecklenburg",
            geometry=points,
            reported_at=reported,
            updated_at=updated,
            start_at=start,
            end_at=end,
            severity=None,
            full_closure=full,
            lanes_affected=lanes,
            major_event=major_event,
            source_organization="City of Charlotte/CDOT",
            source_id=record_id,
            upstream_event_id=record_id,
        )

    def _parse(self, payload: dict) -> tuple[TrafficEventCollectionState, int]:
        if not isinstance(payload, dict):
            raise ValueError("Charlotte closure payload is not an object")
        if payload.get("type") != "FeatureCollection":
            raise ValueError("Charlotte closure payload is not GeoJSON FeatureCollection")
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("Charlotte closure payload missing features list")

        events: list[TrafficEventObservation] = []
        malformed = 0
        for feature in features:
            if not isinstance(feature, dict):
                malformed += 1
                continue
            event = self._event(feature)
            if event is None:
                geometry = feature.get("geometry")
                props = feature.get("properties")
                # Off-scope records are expected; only structurally broken local-looking
                # records should degrade the collection. Without valid geometry we cannot
                # establish locality, so represent the source row as malformed.
                if not isinstance(geometry, dict) or not isinstance(props, dict):
                    malformed += 1
                continue
            events.append(event)
        events.sort(key=lambda item: item.source_record_id)
        fresh_times = [event.updated_at for event in events if event.updated_at]
        return (
            TrafficEventCollectionState(
                location_label=self.location_label,
                provider=self.PROVIDER,
                source_family=self.SOURCE_FAMILY,
                collection_class="official_report",
                scope_center_latitude=self.latitude,
                scope_center_longitude=self.longitude,
                scope_radius_miles=self.radius_miles,
                source_record_count=len(features),
                local_record_count=len(events),
                freshest_source_at=max(fresh_times) if fresh_times else None,
                events=tuple(events),
            ),
            malformed,
        )

    def collect(self) -> tuple[Observation[object], ...]:
        request = Request(
            self._url(),
            headers={
                "User-Agent": "Personal-CIC/0.3.6 (local personal system)",
                "Accept": "application/geo+json, application/json",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
            if not raw:
                raise ValueError("Charlotte street-closure service returned an empty response")
            payload = json.loads(raw.decode("utf-8"))
            if isinstance(payload, dict) and payload.get("error"):
                raise ValueError(f"Charlotte ArcGIS error: {payload['error']}")
            state, malformed = self._parse(payload)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return (Observation.unavailable(self.ADAPTER_ID, f"Charlotte street-closure request failed: {exc}"),)
        if malformed:
            return (
                Observation.partial(
                    self.ADAPTER_ID,
                    state,
                    f"Charlotte street closures omitted {malformed} malformed source features",
                ),
            )
        return (Observation.observed(self.ADAPTER_ID, state),)
