import os
import time

import psutil

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import (
    ComputeState,
    MemoryState,
    StorageState,
    TemperatureState,
    UptimeState,
)


class LinuxHostAdapter:
    """Translate Linux host telemetry into normalized CIC observations."""

    ADAPTER_ID = "linux.host"

    @staticmethod
    def _temperature() -> Observation[TemperatureState]:
        try:
            sensors = psutil.sensors_temperatures(fahrenheit=False) or {}
            preferred = ("coretemp", "k10temp", "acpitz")
            ordered = [name for name in preferred if name in sensors]
            ordered.extend(name for name in sensors if name not in ordered)

            candidates: list[tuple[float, str]] = []
            for group in ordered:
                for reading in sensors.get(group, ()):
                    if reading.current is not None:
                        label = reading.label or group
                        candidates.append((float(reading.current), f"{group}:{label}"))

            if candidates:
                current, source = max(candidates, key=lambda item: item[0])
                return Observation.observed(
                    "linux.temperature",
                    TemperatureState(round(current, 1), source),
                )

            # Successful sensor query with no exposed sensor is a valid observation.
            return Observation.observed(
                "linux.temperature",
                TemperatureState(None, None),
            )
        except (AttributeError, OSError) as exc:
            return Observation.unavailable("linux.temperature", str(exc))

    def collect(self) -> tuple[Observation[object], ...]:
        observations: list[Observation[object]] = []

        try:
            logical = psutil.cpu_count(logical=True) or 1
            load_1m = os.getloadavg()[0]
            observations.append(
                Observation.observed(
                    "linux.compute",
                    ComputeState(
                        cpu_percent=round(psutil.cpu_percent(interval=0.15), 1),
                        logical_cpus=logical,
                        load_1m=round(load_1m, 2),
                        load_per_cpu=round(load_1m / logical, 3),
                    ),
                )
            )
        except (OSError, ValueError) as exc:
            observations.append(Observation.unavailable("linux.compute", str(exc)))

        try:
            memory = psutil.virtual_memory()
            observations.append(
                Observation.observed(
                    "linux.memory",
                    MemoryState(
                        total_bytes=int(memory.total),
                        available_bytes=int(memory.available),
                        used_percent=round(float(memory.percent), 1),
                    ),
                )
            )
        except (OSError, ValueError) as exc:
            observations.append(Observation.unavailable("linux.memory", str(exc)))

        try:
            disk = psutil.disk_usage("/")
            observations.append(
                Observation.observed(
                    "linux.storage",
                    StorageState(
                        mountpoint="/",
                        total_bytes=int(disk.total),
                        free_bytes=int(disk.free),
                        used_percent=round(float(disk.percent), 1),
                    ),
                )
            )
        except (OSError, ValueError) as exc:
            observations.append(Observation.unavailable("linux.storage", str(exc)))

        try:
            observations.append(
                Observation.observed(
                    "linux.uptime",
                    UptimeState(uptime_seconds=max(0, int(time.time() - psutil.boot_time()))),
                )
            )
        except (OSError, ValueError) as exc:
            observations.append(Observation.unavailable("linux.uptime", str(exc)))

        observations.append(self._temperature())
        return tuple(observations)
