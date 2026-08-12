from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import (
    GeoPoint,
    TrafficCameraCollectionState,
    TrafficCameraObservation,
    TrafficEventCollectionState,
    TrafficEventObservation,
    TrafficMessageSignCollectionState,
    TrafficMessageSignObservation,
)
from .traffic_common import (
    boolean,
    collection_class_for_drivenc,
    in_scope,
    iso_time,
    number,
    source_family_for_drivenc,
    text,
)


class _DriveNCBase:
    BASE_URL = "https://www.drivenc.gov/api/v2/get"
    PROVIDER = "NCDOT DriveNC"

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        radius_miles: float,
        api_key_env: str,
        timeout_seconds: float,
        scope_counties: tuple[str, ...] = ("Union", "Mecklenburg"),
        opener=urlopen,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.radius_miles = radius_miles
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds
        self.scope_counties = tuple(c.casefold() for c in scope_counties)
        self._opener = opener

    def _key(self) -> str | None:
        value = os.environ.get(self.api_key_env)
        return None if value is None or not value.strip() else value.strip()

    def _request_json(self, resource: str):
        key = self._key()
        if key is None:
            raise ValueError(f"DriveNC API key environment variable {self.api_key_env} is not set")
        url = f"{self.BASE_URL}/{resource}?{urlencode({'key': key, 'format': 'json'})}"
        request = Request(
            url,
            headers={
                "User-Agent": "Personal-CIC/0.3.6 (local personal system)",
                "Accept": "application/json",
            },
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            raw = response.read()
        if not raw:
            raise ValueError(f"DriveNC {resource} returned an empty response")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"DriveNC {resource} payload is not an array")
        return payload

    def _fallback_county_scope(self, county: str | None) -> bool:
        return bool(county and county.casefold() in self.scope_counties)

    def _safe_error(self, resource: str, exc: BaseException) -> str:
        # A DriveNC credential travels in the query string. Never allow an
        # exception representation to persist that credential into WorldState,
        # the event journal, or operator presentation.
        key = self._key()
        detail = str(exc)
        if key:
            detail = detail.replace(key, "<REDACTED>")
            detail = detail.replace(urlencode({"key": key})[4:], "<REDACTED>")
        return f"DriveNC {resource} request failed ({type(exc).__name__}): {detail}"


class DriveNCEventsAdapter(_DriveNCBase):
    ADAPTER_ID = "drivenc.events"

    @staticmethod
    def _points(row: dict) -> tuple[GeoPoint, ...]:
        points: list[GeoPoint] = []
        pairs = (
            (row.get("Latitude"), row.get("Longitude")),
            (row.get("LatitudeSecondary"), row.get("LongitudeSecondary")),
        )
        for raw_lat, raw_lon in pairs:
            lat = number(raw_lat)
            lon = number(raw_lon)
            if lat is None or lon is None:
                continue
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                point = GeoPoint(latitude=lat, longitude=lon)
                if point not in points:
                    points.append(point)
        return tuple(points)

    def _event(self, row: dict) -> TrafficEventObservation | None:
        record_id = text(row.get("ID"))
        if record_id is None:
            return None
        organization = text(row.get("Organization"))
        points = self._points(row)
        county = text(row.get("County"))
        if points:
            local = in_scope(
                points,
                center_latitude=self.latitude,
                center_longitude=self.longitude,
                radius_miles=self.radius_miles,
            )
        else:
            local = self._fallback_county_scope(county)
        if not local:
            return None

        source_id = text(row.get("SourceId"))
        upstream_event_id = source_id
        return TrafficEventObservation(
            source_record_id=record_id,
            source_family=source_family_for_drivenc(organization),
            provider=self.PROVIDER,
            collection_class=collection_class_for_drivenc(organization),
            event_type=text(row.get("EventType")) or "unknown",
            event_subtype=text(row.get("EventSubType")),
            description=text(row.get("Description")) or "DriveNC traffic event",
            roadway=text(row.get("RoadwayName")),
            direction=text(row.get("DirectionOfTravel")),
            county=county,
            geometry=points,
            reported_at=iso_time(row.get("Reported")),
            updated_at=iso_time(row.get("LastUpdated")),
            start_at=iso_time(row.get("StartDate")),
            end_at=iso_time(row.get("PlannedEndDate")),
            severity=text(row.get("Severity")),
            full_closure=boolean(row.get("IsFullClosure")),
            lanes_affected=text(row.get("LanesAffected")),
            major_event=text(row.get("MajorEvent")),
            source_organization=organization,
            source_id=source_id,
            upstream_event_id=upstream_event_id,
        )

    def _parse(self, payload: list) -> tuple[TrafficEventCollectionState, int]:
        events: list[TrafficEventObservation] = []
        malformed = 0
        for row in payload:
            if not isinstance(row, dict):
                malformed += 1
                continue
            try:
                event = self._event(row)
            except (TypeError, ValueError):
                malformed += 1
                continue
            if event is not None:
                events.append(event)
        events.sort(key=lambda item: (item.source_family, item.source_record_id))
        fresh_times = [event.updated_at for event in events if event.updated_at]
        families = sorted({event.source_family for event in events})
        family_label = families[0] if len(families) == 1 else "mixed" if families else "NCDOT/ATMSERS"
        return (
            TrafficEventCollectionState(
                location_label=self.location_label,
                provider=self.PROVIDER,
                source_family=family_label,
                collection_class="mixed" if any(e.collection_class == "crowd_report" for e in events) else "official_report",
                scope_center_latitude=self.latitude,
                scope_center_longitude=self.longitude,
                scope_radius_miles=self.radius_miles,
                source_record_count=len(payload),
                local_record_count=len(events),
                freshest_source_at=max(fresh_times) if fresh_times else None,
                events=tuple(events),
            ),
            malformed,
        )

    def collect(self) -> tuple[Observation[object], ...]:
        try:
            payload = self._request_json("event")
            state, malformed = self._parse(payload)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return (Observation.unavailable(self.ADAPTER_ID, self._safe_error("events", exc)),)
        if malformed:
            return (
                Observation.partial(
                    self.ADAPTER_ID,
                    state,
                    f"DriveNC events parsed with {malformed} malformed source records omitted",
                ),
            )
        return (Observation.observed(self.ADAPTER_ID, state),)


class DriveNCCamerasAdapter(_DriveNCBase):
    ADAPTER_ID = "drivenc.cameras"

    def _camera(self, row: dict) -> TrafficCameraObservation | None:
        camera_id = text(row.get("Id"))
        lat = number(row.get("Latitude"))
        lon = number(row.get("Longitude"))
        if camera_id is None or lat is None or lon is None:
            return None
        point = GeoPoint(latitude=lat, longitude=lon)
        if not in_scope(
            (point,),
            center_latitude=self.latitude,
            center_longitude=self.longitude,
            radius_miles=self.radius_miles,
        ):
            return None
        views = row.get("Views")
        views = views if isinstance(views, list) else []
        chosen = next((view for view in views if isinstance(view, dict) and str(view.get("Status") or "").lower() == "enabled"), None)
        if chosen is None:
            chosen = next((view for view in views if isinstance(view, dict)), {})
        source = text(row.get("Source"))
        source_family = f"NCDOT/{source}" if source else "NCDOT/DriveNC Cameras"
        return TrafficCameraObservation(
            camera_id=camera_id,
            source_family=source_family,
            provider=self.PROVIDER,
            source_id=text(row.get("SourceId")),
            county=text(row.get("County")),
            roadway=text(row.get("Roadway")),
            direction=text(row.get("Direction")),
            location=text(row.get("Location")),
            latitude=lat,
            longitude=lon,
            status=text(chosen.get("Status")) if isinstance(chosen, dict) else None,
            page_url=text(chosen.get("Url")) if isinstance(chosen, dict) else None,
            video_url=text(chosen.get("VideoUrl")) if isinstance(chosen, dict) else None,
        )

    def _parse(self, payload: list) -> tuple[TrafficCameraCollectionState, int]:
        cameras: list[TrafficCameraObservation] = []
        malformed = 0
        for row in payload:
            if not isinstance(row, dict):
                malformed += 1
                continue
            camera = self._camera(row)
            if camera is None:
                # A valid off-scope row is not malformed. Missing required camera
                # identity/coordinates cannot be distinguished here, so count it only
                # if it claims to be in a configured fallback county.
                if self._fallback_county_scope(text(row.get("County"))) and (
                    text(row.get("Id")) is None
                    or number(row.get("Latitude")) is None
                    or number(row.get("Longitude")) is None
                ):
                    malformed += 1
                continue
            cameras.append(camera)
        cameras.sort(key=lambda item: item.camera_id)
        families = sorted({camera.source_family for camera in cameras})
        family_label = (
            families[0]
            if len(families) == 1
            else "mixed"
            if families
            else "NCDOT/DriveNC Cameras"
        )
        return (
            TrafficCameraCollectionState(
                location_label=self.location_label,
                provider=self.PROVIDER,
                source_family=family_label,
                scope_center_latitude=self.latitude,
                scope_center_longitude=self.longitude,
                scope_radius_miles=self.radius_miles,
                source_record_count=len(payload),
                local_record_count=len(cameras),
                cameras=tuple(cameras),
            ),
            malformed,
        )

    def collect(self) -> tuple[Observation[object], ...]:
        try:
            payload = self._request_json("cameras")
            state, malformed = self._parse(payload)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return (Observation.unavailable(self.ADAPTER_ID, self._safe_error("cameras", exc)),)
        if malformed:
            return (Observation.partial(self.ADAPTER_ID, state, f"DriveNC cameras omitted {malformed} malformed local records"),)
        return (Observation.observed(self.ADAPTER_ID, state),)


class DriveNCMessageSignsAdapter(_DriveNCBase):
    ADAPTER_ID = "drivenc.message_signs"

    def _sign(self, row: dict) -> TrafficMessageSignObservation | None:
        sign_id = text(row.get("Id"))
        lat = number(row.get("Latitude"))
        lon = number(row.get("Longitude"))
        if sign_id is None or lat is None or lon is None:
            return None
        point = GeoPoint(latitude=lat, longitude=lon)
        if not in_scope(
            (point,),
            center_latitude=self.latitude,
            center_longitude=self.longitude,
            radius_miles=self.radius_miles,
        ):
            return None
        raw_messages = row.get("Messages")
        messages = tuple(
            str(value).strip()
            for value in raw_messages
            if str(value).strip()
        ) if isinstance(raw_messages, list) else ()
        return TrafficMessageSignObservation(
            sign_id=sign_id,
            source_family="NCDOT/ATMS DMS",
            provider=self.PROVIDER,
            county=text(row.get("County")),
            roadway=text(row.get("Roadway")),
            direction=text(row.get("DirectionOfTravel")),
            name=text(row.get("Name")),
            latitude=lat,
            longitude=lon,
            updated_at=iso_time(row.get("LastUpdated")),
            messages=messages,
        )

    def _parse(self, payload: list) -> tuple[TrafficMessageSignCollectionState, int]:
        signs: list[TrafficMessageSignObservation] = []
        malformed = 0
        for row in payload:
            if not isinstance(row, dict):
                malformed += 1
                continue
            sign = self._sign(row)
            if sign is None:
                if self._fallback_county_scope(text(row.get("County"))) and (
                    text(row.get("Id")) is None
                    or number(row.get("Latitude")) is None
                    or number(row.get("Longitude")) is None
                ):
                    malformed += 1
                continue
            signs.append(sign)
        signs.sort(key=lambda item: item.sign_id)
        active = sum(
            1 for sign in signs
            if any(message.upper() != "NO_MESSAGE" for message in sign.messages)
        )
        return (
            TrafficMessageSignCollectionState(
                location_label=self.location_label,
                provider=self.PROVIDER,
                source_family="NCDOT/ATMS DMS",
                scope_center_latitude=self.latitude,
                scope_center_longitude=self.longitude,
                scope_radius_miles=self.radius_miles,
                source_record_count=len(payload),
                local_record_count=len(signs),
                active_message_count=active,
                signs=tuple(signs),
            ),
            malformed,
        )

    def collect(self) -> tuple[Observation[object], ...]:
        try:
            payload = self._request_json("messagesigns")
            state, malformed = self._parse(payload)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return (Observation.unavailable(self.ADAPTER_ID, self._safe_error("message-sign", exc)),)
        if malformed:
            return (Observation.partial(self.ADAPTER_ID, state, f"DriveNC message signs omitted {malformed} malformed local records"),)
        return (Observation.observed(self.ADAPTER_ID, state),)
