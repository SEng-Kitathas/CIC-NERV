from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import TrafficEventCollectionState, TrafficEventObservation


class _TrafficTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_row = False
        self._in_cell = False
        self._parts: list[str] = []
        self._row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        lower = tag.lower()
        if lower == "tr":
            self._in_row = True
            self._row = []
        elif lower in {"td", "th"} and self._in_row:
            self._in_cell = True
            self._parts = []

    def handle_data(self, data):
        if self._in_cell:
            self._parts.append(data)

    def handle_endtag(self, tag):
        lower = tag.lower()
        if lower in {"td", "th"} and self._in_cell:
            self._row.append(" ".join("".join(self._parts).split()))
            self._in_cell = False
            self._parts = []
        elif lower == "tr" and self._in_row:
            if self._row:
                self.rows.append(self._row)
            self._row = []
            self._in_row = False


class CMPDTrafficCADAdapter:
    ADAPTER_ID = "cmpd.traffic_cad"
    PROVIDER = "Charlotte-Mecklenburg Police Department live traffic CAD"
    SOURCE_FAMILY = "CMPD CAD"
    BASE_URL = "https://cmpdinfo.charlottenc.gov/traffic"

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

    @staticmethod
    def _event_time(value: str) -> str | None:
        try:
            parsed = datetime.strptime(value.strip(), "%m/%d/%Y %I:%M:%S %p")
        except ValueError:
            return None
        parsed = parsed.replace(tzinfo=ZoneInfo("America/New_York"))
        return parsed.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _record_id(values: tuple[str, str, str, str]) -> str:
        canonical = "\x1f".join(item.strip() for item in values).encode("utf-8")
        return sha256(canonical).hexdigest()[:24]

    def _parse(self, payload: str) -> tuple[TrafficEventCollectionState, int]:
        parser = _TrafficTableParser()
        parser.feed(payload)
        rows = parser.rows
        if not rows:
            raise ValueError("CMPD traffic page contained no table rows")

        header_index = None
        for index, row in enumerate(rows):
            normalized = [cell.casefold() for cell in row]
            if "event date/time" in normalized and "address" in normalized and "description" in normalized:
                header_index = index
                break
        if header_index is None:
            raise ValueError("CMPD traffic table header not found")

        header = [cell.casefold() for cell in rows[header_index]]
        try:
            time_i = header.index("event date/time")
            division_i = header.index("division")
            address_i = header.index("address")
            description_i = header.index("description")
        except ValueError as exc:
            raise ValueError(f"CMPD traffic table missing expected column: {exc}") from exc

        events: list[TrafficEventObservation] = []
        malformed = 0
        for row in rows[header_index + 1 :]:
            if len(row) <= max(time_i, division_i, address_i, description_i):
                malformed += 1
                continue
            raw_time = row[time_i]
            division = row[division_i].strip()
            address = row[address_i].strip()
            description = row[description_i].strip()
            if not raw_time or not address or not description:
                malformed += 1
                continue
            observed_at = self._event_time(raw_time)
            if observed_at is None:
                malformed += 1
                continue
            record_values = (raw_time, division, address, description)
            event_type = description.split("-", 1)[0].strip().lower().replace(" ", "_")
            events.append(
                TrafficEventObservation(
                    source_record_id=self._record_id(record_values),
                    source_family=self.SOURCE_FAMILY,
                    provider=self.PROVIDER,
                    collection_class="official_report",
                    event_type=event_type or "traffic_event",
                    event_subtype=description,
                    description=description,
                    roadway=address,
                    direction=None,
                    county="Mecklenburg",
                    geometry=(),
                    reported_at=observed_at,
                    updated_at=None,
                    start_at=observed_at,
                    end_at=None,
                    severity=None,
                    full_closure=None,
                    lanes_affected=None,
                    major_event=None,
                    source_organization="CMPD",
                    source_id=None,
                    upstream_event_id=None,
                )
            )

        events.sort(key=lambda item: (item.reported_at or "", item.source_record_id), reverse=True)
        freshest = max((event.reported_at for event in events if event.reported_at), default=None)
        state = TrafficEventCollectionState(
            location_label=self.location_label,
            provider=self.PROVIDER,
            source_family=self.SOURCE_FAMILY,
            collection_class="official_report",
            scope_center_latitude=self.latitude,
            scope_center_longitude=self.longitude,
            scope_radius_miles=self.radius_miles,
            source_record_count=max(0, len(rows) - header_index - 1),
            local_record_count=len(events),
            freshest_source_at=freshest,
            events=tuple(events),
        )
        return state, malformed

    def collect(self) -> tuple[Observation[object], ...]:
        request = Request(
            self.BASE_URL,
            headers={
                "User-Agent": "Personal-CIC/0.3.6 (local personal system)",
                "Accept": "text/html",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
            if not raw:
                raise ValueError("CMPD traffic page returned an empty response")
            state, malformed = self._parse(raw.decode("utf-8", errors="replace"))
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, TypeError, ValueError) as exc:
            return (Observation.unavailable(self.ADAPTER_ID, f"CMPD traffic CAD request failed: {exc}"),)
        if malformed:
            return (
                Observation.partial(
                    self.ADAPTER_ID,
                    state,
                    f"CMPD traffic CAD omitted {malformed} malformed table rows",
                ),
            )
        return (Observation.observed(self.ADAPTER_ID, state),)
