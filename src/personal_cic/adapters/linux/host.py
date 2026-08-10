import os
import time
import psutil

from personal_cic.core.world.components import (
    ComputeState,
    MemoryState,
    StorageState,
    TemperatureState,
    UptimeState,
)


class LinuxHostAdapter:
    """Translate Linux host telemetry into normalized CIC components."""

    @staticmethod
    def _temperature() -> TemperatureState:
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
                return TemperatureState(round(current, 1), source)
        except (AttributeError, OSError):
            pass

        return TemperatureState(None, None)

    def collect(self) -> tuple[object, ...]:
        logical = psutil.cpu_count(logical=True) or 1
        load_1m = os.getloadavg()[0]
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime = max(0, int(time.time() - psutil.boot_time()))

        return (
            ComputeState(
                cpu_percent=round(psutil.cpu_percent(interval=0.15), 1),
                logical_cpus=logical,
                load_1m=round(load_1m, 2),
                load_per_cpu=round(load_1m / logical, 3),
            ),
            MemoryState(
                total_bytes=int(memory.total),
                available_bytes=int(memory.available),
                used_percent=round(float(memory.percent), 1),
            ),
            StorageState(
                mountpoint="/",
                total_bytes=int(disk.total),
                free_bytes=int(disk.free),
                used_percent=round(float(disk.percent), 1),
            ),
            UptimeState(uptime_seconds=uptime),
            self._temperature(),
        )
