from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass(frozen=True, slots=True)
class PresentationConfig:
    enabled: bool = False
    bind_host: str = "127.0.0.1"
    port: int = 8765

    @classmethod
    def from_mapping(cls, data: dict | None) -> "PresentationConfig":
        if not data:
            return cls()

        bind_host = str(data.get("bind_host", "127.0.0.1"))
        if bind_host != "127.0.0.1":
            raise ValueError(
                "Presentation is intentionally loopback-only; "
                "bind_host must be 127.0.0.1"
            )

        port = int(data.get("port", 8765))
        if not 1 <= port <= 65535:
            raise ValueError("presentation port must be between 1 and 65535")

        return cls(
            enabled=bool(data.get("enabled", False)),
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
        if not data:
            return cls()
        latitude = float(data.get("latitude", 35.1115))
        longitude = float(data.get("longitude", -80.6099))
        if not -90 <= latitude <= 90:
            raise ValueError("world awareness latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise ValueError("world awareness longitude must be between -180 and 180")
        return cls(
            label=str(data.get("label", "Indian Trail / 28079")),
            latitude=latitude,
            longitude=longitude,
        )


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
        if not data:
            return cls(interval_seconds=default_interval_seconds)
        interval = float(data.get("interval_seconds", default_interval_seconds))
        timeout = float(data.get("timeout_seconds", 8.0))
        if interval <= 0:
            raise ValueError("provider interval_seconds must be > 0")
        if timeout <= 0:
            raise ValueError("provider timeout_seconds must be > 0")
        return cls(
            enabled=bool(data.get("enabled", True)),
            interval_seconds=interval,
            timeout_seconds=timeout,
        )


@dataclass(frozen=True, slots=True)
class NWSAlertsConfig:
    enabled: bool = True
    interval_seconds: float = 60.0
    timeout_seconds: float = 8.0
    user_agent: str = "Personal-CIC/0.3.4 (local personal system)"

    @classmethod
    def from_mapping(cls, data: dict | None) -> "NWSAlertsConfig":
        if not data:
            return cls()
        interval = float(data.get("interval_seconds", 60.0))
        timeout = float(data.get("timeout_seconds", 8.0))
        user_agent = str(data.get("user_agent", "Personal-CIC/0.3.4 (local personal system)")).strip()
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
            enabled=bool(data.get("enabled", True)),
            interval_seconds=interval,
            timeout_seconds=timeout,
            user_agent=user_agent,
        )


@dataclass(frozen=True, slots=True)
class AviationSurfaceConfig:
    enabled: bool = True
    interval_seconds: float = 60.0
    timeout_seconds: float = 8.0
    user_agent: str = "Personal-CIC/0.3.4 (local personal system)"
    station_ids: tuple[str, ...] = ("KEQY", "KCLT", "KJQF")
    max_age_minutes: float = 90.0

    @classmethod
    def from_mapping(cls, data: dict | None) -> "AviationSurfaceConfig":
        if not data:
            return cls()
        interval = float(data.get("interval_seconds", 60.0))
        timeout = float(data.get("timeout_seconds", 8.0))
        user_agent = str(data.get("user_agent", "Personal-CIC/0.3.4 (local personal system)")).strip()
        raw_ids = data.get("station_ids", ["KEQY", "KCLT", "KJQF"])
        station_ids = tuple(str(item).strip().upper() for item in raw_ids if str(item).strip())
        max_age = float(data.get("max_age_minutes", 90.0))
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
        return cls(bool(data.get("enabled", True)), interval, timeout, user_agent, station_ids, max_age)


@dataclass(frozen=True, slots=True)
class NWSForecastConfig:
    enabled: bool = True
    interval_seconds: float = 300.0
    timeout_seconds: float = 8.0
    user_agent: str = "Personal-CIC/0.3.4 (local personal system)"
    points_refresh_seconds: float = 21600.0

    @classmethod
    def from_mapping(cls, data: dict | None) -> "NWSForecastConfig":
        if not data:
            return cls()
        interval = float(data.get("interval_seconds", 300.0))
        timeout = float(data.get("timeout_seconds", 8.0))
        user_agent = str(data.get("user_agent", "Personal-CIC/0.3.4 (local personal system)")).strip()
        refresh = float(data.get("points_refresh_seconds", 21600.0))
        if interval < 60.0:
            raise ValueError("NWS forecast interval_seconds must be >= 60 seconds")
        if timeout <= 0:
            raise ValueError("NWS forecast timeout_seconds must be > 0")
        if refresh < interval:
            raise ValueError("NWS points_refresh_seconds must be >= forecast interval")
        if not user_agent:
            raise ValueError("NWS forecast requires a non-empty User-Agent")
        return cls(bool(data.get("enabled", True)), interval, timeout, user_agent, refresh)


@dataclass(frozen=True, slots=True)
class RadarConfig:
    enabled: bool = True
    interval_seconds: float = 120.0
    timeout_seconds: float = 8.0
    user_agent: str = "Personal-CIC/0.3.4 (local personal system)"
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
        if not data:
            return cls()
        interval = float(data.get("interval_seconds", 120.0))
        timeout = float(data.get("timeout_seconds", 8.0))
        user_agent = str(data.get("user_agent", "Personal-CIC/0.3.4 (local personal system)")).strip()
        range_miles = float(data.get("range_miles", 75.0))
        image_width = int(data.get("image_width", 900))
        image_height = int(data.get("image_height", 600))
        max_age = float(data.get("max_age_minutes", 15.0))
        cache_dir = Path(data.get("cache_dir", "state/radar"))
        loop_frame_capacity = int(data.get("loop_frame_capacity", 15))
        context_enabled = bool(data.get("context_enabled", True))
        context_interval = float(data.get("context_interval_seconds", 21600.0))
        context_timeout = float(data.get("context_timeout_seconds", 8.0))
        context_max_age_days = float(data.get("context_max_age_days", 30.0))
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
            enabled=bool(data.get("enabled", True)),
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

    @classmethod
    def from_mapping(cls, data: dict | None) -> "WorldAwarenessConfig":
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", False)),
            location=AwarenessLocationConfig.from_mapping(data.get("location")),
            weather=RemoteProviderConfig.from_mapping(
                data.get("weather"),
                default_interval_seconds=300.0,
            ),
            alerts=NWSAlertsConfig.from_mapping(data.get("alerts")),
            surface=AviationSurfaceConfig.from_mapping(data.get("surface")),
            forecast=NWSForecastConfig.from_mapping(data.get("forecast")),
            radar=RadarConfig.from_mapping(data.get("radar")),
        )


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    collection_interval_seconds: float
    snapshot_interval_seconds: float
    state_path: Path
    event_journal_path: Path
    presentation: PresentationConfig = field(default_factory=PresentationConfig)
    world_awareness: WorldAwarenessConfig = field(default_factory=WorldAwarenessConfig)

    @classmethod
    def load(cls, path: Path) -> "RuntimeConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            collection_interval_seconds=float(data["collection_interval_seconds"]),
            snapshot_interval_seconds=float(data["snapshot_interval_seconds"]),
            state_path=Path(data["state_path"]),
            event_journal_path=Path(data["event_journal_path"]),
            presentation=PresentationConfig.from_mapping(data.get("presentation")),
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
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            cpu_warning_percent=float(data["cpu_warning_percent"]),
            cpu_critical_percent=float(data["cpu_critical_percent"]),
            memory_warning_percent=float(data["memory_warning_percent"]),
            memory_critical_percent=float(data["memory_critical_percent"]),
            storage_warning_percent=float(data["storage_warning_percent"]),
            storage_critical_percent=float(data["storage_critical_percent"]),
            temperature_warning_c=float(data["temperature_warning_c"]),
            temperature_critical_c=float(data["temperature_critical_c"]),
            wifi_signal_warning_dbm=int(data["wifi_signal_warning_dbm"]),
        )
