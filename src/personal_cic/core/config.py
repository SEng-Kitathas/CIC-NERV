from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import math
import re


_DEFAULT_USER_AGENT = "Personal-CIC/0.3.6 (local personal system)"


def _mapping(data: object | None, *, label: str) -> dict | None:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return data


def _bool(data: dict, key: str, default: bool, *, label: str) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{label}.{key} must be a JSON boolean")
    return value


def _float(value: object, *, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number, not a boolean")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{label} must be a finite number")
    return parsed


def _int(value: object, *, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer, not a boolean")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{label} must be an integer")
    if isinstance(value, str) and str(parsed) != value.strip():
        raise ValueError(f"{label} must be an integer")
    return parsed


def _required_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_text(value: object | None, *, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    return value.strip()


def _aware_iso8601(value: object, *, label: str) -> str:
    text = _required_text(value, label=label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone offset")
    return text


def _env_name(value: object, *, label: str) -> str:
    text = _required_text(value, label=label)
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text) is None:
        raise ValueError(f"{label} must be a valid environment-variable name")
    return text


@dataclass(frozen=True, slots=True)
class PresentationConfig:
    enabled: bool = False
    bind_host: str = "127.0.0.1"
    port: int = 8765

    @classmethod
    def from_mapping(cls, data: dict | None) -> "PresentationConfig":
        data = _mapping(data, label="presentation")
        if not data:
            return cls()

        bind_host = str(data.get("bind_host", "127.0.0.1"))
        if bind_host != "127.0.0.1":
            raise ValueError(
                "Presentation is intentionally loopback-only; "
                "bind_host must be 127.0.0.1"
            )

        port = _int(data.get("port", 8765), label="presentation.port")
        if not 1 <= port <= 65535:
            raise ValueError("presentation port must be between 1 and 65535")

        return cls(
            enabled=_bool(data, "enabled", False, label="presentation"),
            bind_host=bind_host,
            port=port,
        )


@dataclass(frozen=True, slots=True)
class AwarenessLocationConfig:
    label: str = "Indian Trail / 28079"
    latitude: float = 35.1115
    longitude: float = -80.6099

    @classmethod
    def from_mapping(cls, data: dict | None) -> "AwarenessLocationConfig":
        data = _mapping(data, label="world_awareness.location")
        if not data:
            return cls()
        latitude = _float(data.get("latitude", 35.1115), label="world_awareness.location.latitude")
        longitude = _float(data.get("longitude", -80.6099), label="world_awareness.location.longitude")
        if not -90 <= latitude <= 90:
            raise ValueError("world awareness latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise ValueError("world awareness longitude must be between -180 and 180")
        return cls(
            label=_required_text(data.get("label", "Indian Trail / 28079"), label="world_awareness.location.label"),
            latitude=latitude,
            longitude=longitude,
        )


@dataclass(frozen=True, slots=True)
class SiteAnchorConfig:
    enabled: bool = False
    label: str = "CIC SITE"
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    position_kind: str = "fixed_site_anchor"
    source_lineage: str = ""
    source_record_id: str = ""
    source_verified_at: str = ""
    source_artifact_sha256: str = ""

    @classmethod
    def from_mapping(cls, data: dict | None) -> "SiteAnchorConfig":
        data = _mapping(data, label="operator_context.site_anchor")
        if not data:
            return cls()
        enabled = _bool(data, "enabled", False, label="operator_context.site_anchor")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        latitude = None if latitude is None else _float(latitude, label="operator_context.site_anchor.latitude")
        longitude = None if longitude is None else _float(longitude, label="operator_context.site_anchor.longitude")
        if enabled and latitude is None:
            raise ValueError("enabled site anchor requires latitude")
        if enabled and longitude is None:
            raise ValueError("enabled site anchor requires longitude")
        if latitude is not None and not -90 <= latitude <= 90:
            raise ValueError("site anchor latitude must be between -90 and 90")
        if longitude is not None and not -180 <= longitude <= 180:
            raise ValueError("site anchor longitude must be between -180 and 180")
        position_kind = _required_text(data.get("position_kind", "fixed_site_anchor"), label="operator_context.site_anchor.position_kind")
        if position_kind != "fixed_site_anchor":
            raise ValueError("site anchor position_kind must be fixed_site_anchor")
        source_sha = _optional_text(data.get("source_artifact_sha256"), label="operator_context.site_anchor.source_artifact_sha256").lower()
        if source_sha and (len(source_sha) != 64 or any(c not in "0123456789abcdef" for c in source_sha)):
            raise ValueError("site anchor source_artifact_sha256 must be a SHA-256 hex digest")

        address = _optional_text(data.get("address"), label="operator_context.site_anchor.address")
        source_lineage = _optional_text(data.get("source_lineage"), label="operator_context.site_anchor.source_lineage")
        source_record_id = _optional_text(data.get("source_record_id"), label="operator_context.site_anchor.source_record_id")
        source_verified_at = _optional_text(data.get("source_verified_at"), label="operator_context.site_anchor.source_verified_at")
        if enabled:
            address = _required_text(address, label="operator_context.site_anchor.address")
            source_lineage = _required_text(source_lineage, label="operator_context.site_anchor.source_lineage")
            source_record_id = _required_text(source_record_id, label="operator_context.site_anchor.source_record_id")
            source_verified_at = _aware_iso8601(
                source_verified_at,
                label="operator_context.site_anchor.source_verified_at",
            )
            if not source_sha:
                raise ValueError("enabled site anchor requires source_artifact_sha256")

        return cls(
            enabled=enabled,
            label=_required_text(data.get("label", "CIC SITE"), label="operator_context.site_anchor.label"),
            address=address,
            latitude=latitude,
            longitude=longitude,
            position_kind=position_kind,
            source_lineage=source_lineage,
            source_record_id=source_record_id,
            source_verified_at=source_verified_at,
            source_artifact_sha256=source_sha,
        )


@dataclass(frozen=True, slots=True)
class OperatorContextConfig:
    site_anchor: SiteAnchorConfig = field(default_factory=SiteAnchorConfig)

    @classmethod
    def from_mapping(cls, data: dict | None) -> "OperatorContextConfig":
        data = _mapping(data, label="operator_context")
        if not data:
            return cls()
        return cls(site_anchor=SiteAnchorConfig.from_mapping(data.get("site_anchor")))


@dataclass(frozen=True, slots=True)
class RemoteProviderConfig:
    enabled: bool = True
    interval_seconds: float = 300.0
    timeout_seconds: float = 8.0

    @classmethod
    def from_mapping(
        cls,
        data: dict | None,
        *,
        default_interval_seconds: float,
    ) -> "RemoteProviderConfig":
        data = _mapping(data, label="remote_provider")
        if not data:
            return cls(interval_seconds=default_interval_seconds)
        interval = _float(data.get("interval_seconds", default_interval_seconds), label="remote_provider.interval_seconds")
        timeout = _float(data.get("timeout_seconds", 8.0), label="remote_provider.timeout_seconds")
        if interval <= 0:
            raise ValueError("provider interval_seconds must be > 0")
        if timeout <= 0:
            raise ValueError("provider timeout_seconds must be > 0")
        return cls(
            enabled=_bool(data, "enabled", True, label="remote_provider"),
            interval_seconds=interval,
            timeout_seconds=timeout,
        )


@dataclass(frozen=True, slots=True)
class NWSAlertsConfig:
    enabled: bool = True
    interval_seconds: float = 60.0
    timeout_seconds: float = 8.0
    user_agent: str = _DEFAULT_USER_AGENT

    @classmethod
    def from_mapping(cls, data: dict | None) -> "NWSAlertsConfig":
        data = _mapping(data, label="world_awareness.alerts")
        if not data:
            return cls()
        interval = _float(data.get("interval_seconds", 60.0), label="world_awareness.alerts.interval_seconds")
        timeout = _float(data.get("timeout_seconds", 8.0), label="world_awareness.alerts.timeout_seconds")
        user_agent = _required_text(data.get("user_agent", _DEFAULT_USER_AGENT), label="world_awareness.alerts.user_agent")
        if interval < 30.0:
            raise ValueError(
                "NWS alert interval_seconds must be >= 30 seconds to respect "
                "the documented refresh recommendation"
            )
        if timeout <= 0:
            raise ValueError("NWS alert timeout_seconds must be > 0")
        if not user_agent:
            raise ValueError("NWS alerts require a non-empty User-Agent")
        return cls(
            enabled=_bool(data, "enabled", True, label="world_awareness.alerts"),
            interval_seconds=interval,
            timeout_seconds=timeout,
            user_agent=user_agent,
        )


@dataclass(frozen=True, slots=True)
class AviationSurfaceConfig:
    enabled: bool = True
    interval_seconds: float = 60.0
    timeout_seconds: float = 8.0
    user_agent: str = _DEFAULT_USER_AGENT
    station_ids: tuple[str, ...] = ("KEQY", "KCLT", "KJQF")
    max_age_minutes: float = 90.0

    @classmethod
    def from_mapping(cls, data: dict | None) -> "AviationSurfaceConfig":
        data = _mapping(data, label="world_awareness.surface")
        if not data:
            return cls()
        interval = _float(data.get("interval_seconds", 60.0), label="world_awareness.surface.interval_seconds")
        timeout = _float(data.get("timeout_seconds", 8.0), label="world_awareness.surface.timeout_seconds")
        user_agent = _required_text(data.get("user_agent", _DEFAULT_USER_AGENT), label="world_awareness.surface.user_agent")
        raw_ids = data.get("station_ids", ["KEQY", "KCLT", "KJQF"])
        if not isinstance(raw_ids, list) or not all(isinstance(item, str) for item in raw_ids):
            raise ValueError("world_awareness.surface.station_ids must be a JSON array of strings")
        station_ids = tuple(item.strip().upper() for item in raw_ids if item.strip())
        max_age = _float(data.get("max_age_minutes", 90.0), label="world_awareness.surface.max_age_minutes")
        if interval < 60.0:
            raise ValueError("AviationWeather interval_seconds must be >= 60 seconds")
        if timeout <= 0:
            raise ValueError("AviationWeather timeout_seconds must be > 0")
        if not user_agent:
            raise ValueError("AviationWeather requires a non-empty User-Agent")
        if not station_ids:
            raise ValueError("AviationWeather requires at least one station ID")
        if max_age <= 0:
            raise ValueError("AviationWeather max_age_minutes must be > 0")
        return cls(_bool(data, "enabled", True, label="world_awareness.surface"), interval, timeout, user_agent, station_ids, max_age)


@dataclass(frozen=True, slots=True)
class NWSForecastConfig:
    enabled: bool = True
    interval_seconds: float = 300.0
    timeout_seconds: float = 8.0
    user_agent: str = _DEFAULT_USER_AGENT
    points_refresh_seconds: float = 21600.0

    @classmethod
    def from_mapping(cls, data: dict | None) -> "NWSForecastConfig":
        data = _mapping(data, label="world_awareness.forecast")
        if not data:
            return cls()
        interval = _float(data.get("interval_seconds", 300.0), label="world_awareness.forecast.interval_seconds")
        timeout = _float(data.get("timeout_seconds", 8.0), label="world_awareness.forecast.timeout_seconds")
        user_agent = _required_text(data.get("user_agent", _DEFAULT_USER_AGENT), label="world_awareness.forecast.user_agent")
        refresh = _float(data.get("points_refresh_seconds", 21600.0), label="world_awareness.forecast.points_refresh_seconds")
        if interval < 60.0:
            raise ValueError("NWS forecast interval_seconds must be >= 60 seconds")
        if timeout <= 0:
            raise ValueError("NWS forecast timeout_seconds must be > 0")
        if refresh < interval:
            raise ValueError("NWS points_refresh_seconds must be >= forecast interval")
        if not user_agent:
            raise ValueError("NWS forecast requires a non-empty User-Agent")
        return cls(_bool(data, "enabled", True, label="world_awareness.forecast"), interval, timeout, user_agent, refresh)


@dataclass(frozen=True, slots=True)
class RadarConfig:
    enabled: bool = True
    interval_seconds: float = 120.0
    timeout_seconds: float = 8.0
    user_agent: str = _DEFAULT_USER_AGENT
    range_miles: float = 75.0
    image_width: int = 900
    image_height: int = 600
    max_age_minutes: float = 15.0
    cache_dir: Path = Path("state/radar")
    loop_frame_capacity: int = 15
    context_enabled: bool = True
    context_interval_seconds: float = 21600.0
    context_timeout_seconds: float = 8.0
    context_max_age_days: float = 30.0

    @classmethod
    def from_mapping(cls, data: dict | None) -> "RadarConfig":
        data = _mapping(data, label="world_awareness.radar")
        if not data:
            return cls()
        interval = _float(data.get("interval_seconds", 120.0), label="world_awareness.radar.interval_seconds")
        timeout = _float(data.get("timeout_seconds", 8.0), label="world_awareness.radar.timeout_seconds")
        user_agent = _required_text(data.get("user_agent", _DEFAULT_USER_AGENT), label="world_awareness.radar.user_agent")
        range_miles = _float(data.get("range_miles", 75.0), label="world_awareness.radar.range_miles")
        image_width = _int(data.get("image_width", 900), label="world_awareness.radar.image_width")
        image_height = _int(data.get("image_height", 600), label="world_awareness.radar.image_height")
        max_age = _float(data.get("max_age_minutes", 15.0), label="world_awareness.radar.max_age_minutes")
        cache_dir = Path(_required_text(data.get("cache_dir", "state/radar"), label="world_awareness.radar.cache_dir"))
        loop_frame_capacity = _int(data.get("loop_frame_capacity", 15), label="world_awareness.radar.loop_frame_capacity")
        context_enabled = _bool(data, "context_enabled", True, label="world_awareness.radar")
        context_interval = _float(data.get("context_interval_seconds", 21600.0), label="world_awareness.radar.context_interval_seconds")
        context_timeout = _float(data.get("context_timeout_seconds", 8.0), label="world_awareness.radar.context_timeout_seconds")
        context_max_age_days = _float(data.get("context_max_age_days", 30.0), label="world_awareness.radar.context_max_age_days")
        if interval < 60.0:
            raise ValueError("MRMS radar interval_seconds must be >= 60 seconds")
        if timeout <= 0:
            raise ValueError("MRMS radar timeout_seconds must be > 0")
        if not user_agent:
            raise ValueError("MRMS radar requires a non-empty User-Agent")
        if not 10.0 <= range_miles <= 300.0:
            raise ValueError("MRMS radar range_miles must be between 10 and 300")
        if not 256 <= image_width <= 1600 or not 256 <= image_height <= 1200:
            raise ValueError("MRMS radar image dimensions are outside supported bounds")
        if max_age <= 0:
            raise ValueError("MRMS radar max_age_minutes must be > 0")
        if not 3 <= loop_frame_capacity <= 30:
            raise ValueError("MRMS radar loop_frame_capacity must be between 3 and 30")
        if context_interval < 3600.0:
            raise ValueError("radar context interval_seconds must be >= 3600 seconds")
        if context_timeout <= 0:
            raise ValueError("radar context timeout_seconds must be > 0")
        if context_max_age_days <= 0:
            raise ValueError("radar context max age must be > 0 days")
        return cls(
            enabled=_bool(data, "enabled", True, label="world_awareness.radar"),
            interval_seconds=interval,
            timeout_seconds=timeout,
            user_agent=user_agent,
            range_miles=range_miles,
            image_width=image_width,
            image_height=image_height,
            max_age_minutes=max_age,
            cache_dir=cache_dir,
            loop_frame_capacity=loop_frame_capacity,
            context_enabled=context_enabled,
            context_interval_seconds=context_interval,
            context_timeout_seconds=context_timeout,
            context_max_age_days=context_max_age_days,
        )


@dataclass(frozen=True, slots=True)
class TrafficProviderConfig:
    enabled: bool = True
    interval_seconds: float = 300.0
    timeout_seconds: float = 8.0

    @classmethod
    def from_mapping(
        cls,
        data: dict | None,
        *,
        default_interval_seconds: float,
        min_interval_seconds: float = 30.0,
        default_timeout_seconds: float = 8.0,
    ) -> "TrafficProviderConfig":
        data = _mapping(data, label="traffic.provider")
        if not data:
            return cls(interval_seconds=default_interval_seconds, timeout_seconds=default_timeout_seconds)
        interval = _float(data.get("interval_seconds", default_interval_seconds), label="traffic.provider.interval_seconds")
        timeout = _float(data.get("timeout_seconds", default_timeout_seconds), label="traffic.provider.timeout_seconds")
        if interval < min_interval_seconds:
            raise ValueError(f"traffic provider interval_seconds must be >= {min_interval_seconds:g}")
        if timeout <= 0:
            raise ValueError("traffic provider timeout_seconds must be > 0")
        return cls(
            enabled=_bool(data, "enabled", True, label="traffic.provider"),
            interval_seconds=interval,
            timeout_seconds=timeout,
        )


@dataclass(frozen=True, slots=True)
class DriveNCTrafficConfig:
    enabled: bool = True
    events_interval_seconds: float = 60.0
    cameras_interval_seconds: float = 1800.0
    signs_interval_seconds: float = 60.0
    timeout_seconds: float = 8.0
    api_key_env: str = "DRIVENC_API_KEY"

    @classmethod
    def from_mapping(cls, data: dict | None) -> "DriveNCTrafficConfig":
        data = _mapping(data, label="traffic.drivenc")
        if not data:
            return cls()
        events = _float(data.get("events_interval_seconds", 60.0), label="traffic.drivenc.events_interval_seconds")
        cameras = _float(data.get("cameras_interval_seconds", 1800.0), label="traffic.drivenc.cameras_interval_seconds")
        signs = _float(data.get("signs_interval_seconds", 60.0), label="traffic.drivenc.signs_interval_seconds")
        timeout = _float(data.get("timeout_seconds", 8.0), label="traffic.drivenc.timeout_seconds")
        api_key_env = _env_name(data.get("api_key_env", "DRIVENC_API_KEY"), label="traffic.drivenc.api_key_env")
        # DriveNC documents a ten-calls-per-60-second throttle. CIC keeps each
        # recurring resource at or below one call per minute; startup may make
        # three distinct calls and remains comfortably below that contract.
        if events < 60.0 or signs < 60.0:
            raise ValueError("DriveNC event/sign intervals must be >= 60 seconds")
        if cameras < 300.0:
            raise ValueError("DriveNC camera interval must be >= 300 seconds")
        if timeout <= 0:
            raise ValueError("DriveNC timeout_seconds must be > 0")
        if not api_key_env:
            raise ValueError("DriveNC api_key_env must be non-empty")
        return cls(
            enabled=_bool(data, "enabled", True, label="traffic.drivenc"),
            events_interval_seconds=events,
            cameras_interval_seconds=cameras,
            signs_interval_seconds=signs,
            timeout_seconds=timeout,
            api_key_env=api_key_env,
        )


@dataclass(frozen=True, slots=True)
class TrafficFlowProbeConfig:
    probe_id: str
    label: str
    latitude: float
    longitude: float

    @classmethod
    def from_mapping(cls, data: dict) -> "TrafficFlowProbeConfig":
        data = _mapping(data, label="traffic.tomtom.flow_probe")
        if data is None:
            raise ValueError("traffic.tomtom.flow_probe must be a JSON object")
        probe_id = _required_text(data.get("probe_id"), label="traffic.tomtom.flow_probe.probe_id")
        label = _required_text(data.get("label", probe_id), label="traffic.tomtom.flow_probe.label")
        latitude = _float(data.get("latitude"), label="traffic.tomtom.flow_probe.latitude")
        longitude = _float(data.get("longitude"), label="traffic.tomtom.flow_probe.longitude")
        if not probe_id:
            raise ValueError("TomTom flow probe requires a non-empty probe_id")
        if not label:
            raise ValueError("TomTom flow probe requires a non-empty label")
        if not -90 <= latitude <= 90:
            raise ValueError("TomTom flow probe latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise ValueError("TomTom flow probe longitude must be between -180 and 180")
        return cls(probe_id, label, latitude, longitude)


def _default_tomtom_flow_probes() -> tuple[TrafficFlowProbeConfig, ...]:
    # These are intentionally reference/query points, not asserted roadway identity.
    # Flow Segment Data returns the nearest road fragment and that matched geometry
    # remains the authoritative segment identity.
    return (
        TrafficFlowProbeConfig("cic-center", "collection-scope center reference", 35.1115, -80.6099),
        TrafficFlowProbeConfig("us74-union-west-ref", "US-74 Union west reference", 35.0990, -80.67671),
        TrafficFlowProbeConfig("us74-bypass-ref", "US-74 Bypass reference", 35.04747, -80.57052),
        TrafficFlowProbeConfig("i485-southwest-ref", "I-485 southwest reference", 35.14671, -80.93992),
        TrafficFlowProbeConfig("i485-west-ref", "I-485 west reference", 35.20945, -80.96827),
        TrafficFlowProbeConfig("i85-charlotte-ref", "I-85 Charlotte reference", 35.27831, -80.79670),
        TrafficFlowProbeConfig("i277-uptown-ref", "I-277 Uptown reference", 35.22441, -80.85751),
    )


@dataclass(frozen=True, slots=True)
class TomTomTrafficConfig:
    enabled: bool = True
    incidents_interval_seconds: float = 14400.0
    flow_interval_seconds: float = 1200.0
    timeout_seconds: float = 8.0
    api_key_env: str = "TOMTOM_API_KEY"
    flow_probes: tuple[TrafficFlowProbeConfig, ...] = field(default_factory=_default_tomtom_flow_probes)

    @classmethod
    def from_mapping(cls, data: dict | None) -> "TomTomTrafficConfig":
        data = _mapping(data, label="traffic.tomtom")
        if not data:
            return cls()
        incidents_interval = _float(data.get("incidents_interval_seconds", 14400.0), label="traffic.tomtom.incidents_interval_seconds")
        flow_interval = _float(data.get("flow_interval_seconds", 1200.0), label="traffic.tomtom.flow_interval_seconds")
        timeout = _float(data.get("timeout_seconds", 8.0), label="traffic.tomtom.timeout_seconds")
        api_key_env = _env_name(data.get("api_key_env", "TOMTOM_API_KEY"), label="traffic.tomtom.api_key_env")
        raw_probes = data.get("flow_probes")
        if raw_probes is not None and not isinstance(raw_probes, list):
            raise ValueError("traffic.tomtom.flow_probes must be a JSON array")
        probes = (
            _default_tomtom_flow_probes()
            if raw_probes is None
            else tuple(
                TrafficFlowProbeConfig.from_mapping(item)
                for item in raw_probes
            )
        )
        if incidents_interval < 900.0:
            raise ValueError("TomTom incident interval_seconds must be >= 900 seconds")
        if flow_interval < 60.0:
            raise ValueError("TomTom flow interval_seconds must be >= 60 seconds")
        if timeout <= 0:
            raise ValueError("TomTom timeout_seconds must be > 0")
        if not api_key_env:
            raise ValueError("TomTom api_key_env must be non-empty")
        if not probes:
            raise ValueError("TomTom flow_probes must contain at least one probe")
        ids = [probe.probe_id for probe in probes]
        if len(ids) != len(set(ids)):
            raise ValueError("TomTom flow probe_id values must be unique")
        return cls(
            enabled=_bool(data, "enabled", True, label="traffic.tomtom"),
            incidents_interval_seconds=incidents_interval,
            flow_interval_seconds=flow_interval,
            timeout_seconds=timeout,
            api_key_env=api_key_env,
            flow_probes=probes,
        )


@dataclass(frozen=True, slots=True)
class TrafficConfig:
    enabled: bool = True
    radius_miles: float = 75.0
    scope_counties: tuple[str, ...] = ("Union", "Mecklenburg")
    drivenc: DriveNCTrafficConfig = field(default_factory=DriveNCTrafficConfig)
    wzdx: TrafficProviderConfig = field(
        default_factory=lambda: TrafficProviderConfig(interval_seconds=900.0, timeout_seconds=30.0)
    )
    cmpd: TrafficProviderConfig = field(
        default_factory=lambda: TrafficProviderConfig(interval_seconds=180.0, timeout_seconds=8.0)
    )
    charlotte_closures: TrafficProviderConfig = field(
        default_factory=lambda: TrafficProviderConfig(interval_seconds=900.0, timeout_seconds=8.0)
    )
    tomtom: TomTomTrafficConfig = field(default_factory=TomTomTrafficConfig)
    external_waze_visual_enabled: bool = True
    external_waze_zoom: int = 11

    @classmethod
    def from_mapping(cls, data: dict | None) -> "TrafficConfig":
        data = _mapping(data, label="world_awareness.traffic")
        if not data:
            return cls()
        radius = _float(data.get("radius_miles", 75.0), label="world_awareness.traffic.radius_miles")
        if not 5.0 <= radius <= 300.0:
            raise ValueError("traffic radius_miles must be between 5 and 300")
        raw_counties = data.get("scope_counties", ["Union", "Mecklenburg"])
        if not isinstance(raw_counties, list) or not all(isinstance(item, str) for item in raw_counties):
            raise ValueError("traffic scope_counties must be a JSON array of strings")
        counties = tuple(item.strip() for item in raw_counties if item.strip())
        if not counties:
            raise ValueError("traffic scope_counties must contain at least one county")
        zoom = _int(data.get("external_waze_zoom", 11), label="world_awareness.traffic.external_waze_zoom")
        if not 3 <= zoom <= 17:
            raise ValueError("external_waze_zoom must be between 3 and 17")
        return cls(
            enabled=_bool(data, "enabled", True, label="world_awareness.traffic"),
            radius_miles=radius,
            scope_counties=counties,
            drivenc=DriveNCTrafficConfig.from_mapping(data.get("drivenc")),
            wzdx=TrafficProviderConfig.from_mapping(
                data.get("wzdx"),
                default_interval_seconds=900.0,
                min_interval_seconds=300.0,
                default_timeout_seconds=30.0,
            ),
            cmpd=TrafficProviderConfig.from_mapping(
                data.get("cmpd"),
                default_interval_seconds=180.0,
                min_interval_seconds=60.0,
                default_timeout_seconds=8.0,
            ),
            charlotte_closures=TrafficProviderConfig.from_mapping(
                data.get("charlotte_closures"),
                default_interval_seconds=900.0,
                min_interval_seconds=300.0,
                default_timeout_seconds=8.0,
            ),
            tomtom=TomTomTrafficConfig.from_mapping(data.get("tomtom")),
            external_waze_visual_enabled=_bool(data, "external_waze_visual_enabled", True, label="world_awareness.traffic"),
            external_waze_zoom=zoom,
        )


@dataclass(frozen=True, slots=True)
class WorldAwarenessConfig:
    enabled: bool = False
    location: AwarenessLocationConfig = field(default_factory=AwarenessLocationConfig)
    weather: RemoteProviderConfig = field(
        default_factory=lambda: RemoteProviderConfig(interval_seconds=300.0)
    )
    alerts: NWSAlertsConfig = field(default_factory=NWSAlertsConfig)
    surface: AviationSurfaceConfig = field(default_factory=AviationSurfaceConfig)
    forecast: NWSForecastConfig = field(default_factory=NWSForecastConfig)
    radar: RadarConfig = field(default_factory=RadarConfig)
    traffic: TrafficConfig = field(default_factory=TrafficConfig)

    @classmethod
    def from_mapping(cls, data: dict | None) -> "WorldAwarenessConfig":
        data = _mapping(data, label="world_awareness")
        if not data:
            return cls()
        return cls(
            enabled=_bool(data, "enabled", False, label="world_awareness"),
            location=AwarenessLocationConfig.from_mapping(data.get("location")),
            weather=RemoteProviderConfig.from_mapping(
                data.get("weather"),
                default_interval_seconds=300.0,
            ),
            alerts=NWSAlertsConfig.from_mapping(data.get("alerts")),
            surface=AviationSurfaceConfig.from_mapping(data.get("surface")),
            forecast=NWSForecastConfig.from_mapping(data.get("forecast")),
            radar=RadarConfig.from_mapping(data.get("radar")),
            traffic=TrafficConfig.from_mapping(data.get("traffic")),
        )


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    collection_interval_seconds: float
    snapshot_interval_seconds: float
    state_path: Path
    event_journal_path: Path
    presentation: PresentationConfig = field(default_factory=PresentationConfig)
    operator_context: OperatorContextConfig = field(default_factory=OperatorContextConfig)
    world_awareness: WorldAwarenessConfig = field(default_factory=WorldAwarenessConfig)

    @classmethod
    def load(cls, path: Path) -> "RuntimeConfig":
        raw = json.loads(path.read_text(encoding="utf-8"))
        data = _mapping(raw, label="runtime")
        if data is None:
            raise ValueError("runtime must be a JSON object")
        collection = _float(
            data.get("collection_interval_seconds"),
            label="runtime.collection_interval_seconds",
        )
        snapshot = _float(
            data.get("snapshot_interval_seconds"),
            label="runtime.snapshot_interval_seconds",
        )
        if collection <= 0:
            raise ValueError("runtime.collection_interval_seconds must be > 0")
        if snapshot <= 0:
            raise ValueError("runtime.snapshot_interval_seconds must be > 0")
        state_path = Path(_required_text(data.get("state_path"), label="runtime.state_path"))
        journal_path = Path(_required_text(data.get("event_journal_path"), label="runtime.event_journal_path"))
        return cls(
            collection_interval_seconds=collection,
            snapshot_interval_seconds=snapshot,
            state_path=state_path,
            event_journal_path=journal_path,
            presentation=PresentationConfig.from_mapping(data.get("presentation")),
            operator_context=OperatorContextConfig.from_mapping(data.get("operator_context")),
            world_awareness=WorldAwarenessConfig.from_mapping(data.get("world_awareness")),
        )


@dataclass(frozen=True, slots=True)
class HealthThresholds:
    cpu_warning_percent: float
    cpu_critical_percent: float
    memory_warning_percent: float
    memory_critical_percent: float
    storage_warning_percent: float
    storage_critical_percent: float
    temperature_warning_c: float
    temperature_critical_c: float
    wifi_signal_warning_dbm: int

    @classmethod
    def load(cls, path: Path) -> "HealthThresholds":
        raw = json.loads(path.read_text(encoding="utf-8"))
        data = _mapping(raw, label="health")
        if data is None:
            raise ValueError("health must be a JSON object")
        values = {
            "cpu_warning_percent": _float(data.get("cpu_warning_percent"), label="health.cpu_warning_percent"),
            "cpu_critical_percent": _float(data.get("cpu_critical_percent"), label="health.cpu_critical_percent"),
            "memory_warning_percent": _float(data.get("memory_warning_percent"), label="health.memory_warning_percent"),
            "memory_critical_percent": _float(data.get("memory_critical_percent"), label="health.memory_critical_percent"),
            "storage_warning_percent": _float(data.get("storage_warning_percent"), label="health.storage_warning_percent"),
            "storage_critical_percent": _float(data.get("storage_critical_percent"), label="health.storage_critical_percent"),
            "temperature_warning_c": _float(data.get("temperature_warning_c"), label="health.temperature_warning_c"),
            "temperature_critical_c": _float(data.get("temperature_critical_c"), label="health.temperature_critical_c"),
        }
        for family in ("cpu", "memory", "storage"):
            warning = values[f"{family}_warning_percent"]
            critical = values[f"{family}_critical_percent"]
            if not 0.0 <= warning < critical <= 100.0:
                raise ValueError(
                    f"health {family} thresholds must satisfy 0 <= warning < critical <= 100"
                )
        if not values["temperature_warning_c"] < values["temperature_critical_c"]:
            raise ValueError("health temperature warning must be below critical")
        wifi = _int(data.get("wifi_signal_warning_dbm"), label="health.wifi_signal_warning_dbm")
        if not -127 <= wifi <= 0:
            raise ValueError("health.wifi_signal_warning_dbm must be between -127 and 0 dBm")
        return cls(**values, wifi_signal_warning_dbm=wifi)
