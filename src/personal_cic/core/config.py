from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    collection_interval_seconds: float
    snapshot_interval_seconds: float
    state_path: Path
    event_journal_path: Path

    @classmethod
    def load(cls, path: Path) -> "RuntimeConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            collection_interval_seconds=float(data["collection_interval_seconds"]),
            snapshot_interval_seconds=float(data["snapshot_interval_seconds"]),
            state_path=Path(data["state_path"]),
            event_journal_path=Path(data["event_journal_path"]),
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
