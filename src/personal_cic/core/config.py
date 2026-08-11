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
    user_agent: str = "Personal-CIC/0.3.1 (local personal system)"

    @classmethod
    def from_mapping(cls, data: dict | None) -> "NWSAlertsConfig":
        if not data:
            return cls()
        interval = float(data.get("interval_seconds", 60.0))
        timeout = float(data.get("timeout_seconds", 8.0))
        user_agent = str(data.get("user_agent", "Personal-CIC/0.3.1 (local personal system)")).strip()
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
class WorldAwarenessConfig:
    enabled: bool = False
    location: AwarenessLocationConfig = field(default_factory=AwarenessLocationConfig)
    weather: RemoteProviderConfig = field(
        default_factory=lambda: RemoteProviderConfig(interval_seconds=300.0)
    )
    alerts: NWSAlertsConfig = field(default_factory=NWSAlertsConfig)

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
