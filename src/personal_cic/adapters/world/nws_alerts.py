from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import WeatherAlertState, WeatherAlertSummary


_SEVERITY_ORDER = {
    "Extreme": 4,
    "Severe": 3,
    "Moderate": 2,
    "Minor": 1,
    "Unknown": 0,
    None: 0,
}


class NWSAlertsAdapter:
    ADAPTER_ID = "nws.alerts"
    BASE_URL = "https://api.weather.gov/alerts/active"

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        user_agent: str,
        timeout_seconds: float = 8.0,
        opener=urlopen,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def _url(self) -> str:
        point = f"{self.latitude},{self.longitude}"
        return f"{self.BASE_URL}?{urlencode({'point': point})}"

    @staticmethod
    def _summary(feature: dict) -> WeatherAlertSummary:
        props = feature.get("properties") or {}
        alert_id = str(feature.get("id") or props.get("id") or "unknown")
        return WeatherAlertSummary(
            alert_id=alert_id,
            event=str(props.get("event") or "Unknown alert"),
            severity=str(props.get("severity") or "Unknown"),
            urgency=None if props.get("urgency") is None else str(props.get("urgency")),
            headline=str(props.get("headline") or props.get("event") or "Weather alert"),
            sent_at=props.get("sent"),
            effective_at=props.get("effective"),
            expires_at=props.get("expires"),
        )

    def _parse(self, payload: dict) -> WeatherAlertState:
        if not isinstance(payload, dict):
            raise ValueError("NWS payload is not an object")
        if "features" not in payload or not isinstance(payload["features"], list):
            raise ValueError("NWS payload missing alert features list")
        features = payload["features"]
        alerts = [self._summary(feature) for feature in features if isinstance(feature, dict)]
        alerts.sort(
            key=lambda alert: (
                -_SEVERITY_ORDER.get(alert.severity, 0),
                alert.event,
                alert.alert_id,
            )
        )
        highest = alerts[0].severity if alerts else None
        return WeatherAlertState(
            location_label=self.location_label,
            provider="National Weather Service",
            active_count=len(alerts),
            highest_severity=highest,
            provider_updated_at=payload.get("updated"),
            alerts=tuple(alerts[:8]),
        )

    def collect(self) -> tuple[Observation[object], ...]:
        request = Request(
            self._url(),
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/geo+json",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            state = self._parse(payload)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return (
                Observation.unavailable("nws.alerts", f"NWS alerts request failed: {exc}"),
            )

        return (Observation.observed("nws.alerts", state),)
