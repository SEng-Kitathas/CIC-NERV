from personal_cic.core.config import HealthThresholds
from personal_cic.core.events import ComponentUpdated
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    ComputeState,
    HealthState,
    MemoryState,
    StorageState,
    TemperatureState,
    UsbDeviceState,
    WifiLinkState,
)


class HealthSystem:
    RELEVANT = {
        ComputeState.__name__,
        MemoryState.__name__,
        StorageState.__name__,
        TemperatureState.__name__,
        UsbDeviceState.__name__,
        WifiLinkState.__name__,
    }

    def __init__(self, world: WorldState, thresholds: HealthThresholds) -> None:
        self.world = world
        self.thresholds = thresholds

    def on_component_updated(self, event: ComponentUpdated) -> None:
        if event.component_name not in self.RELEVANT:
            return
        self.evaluate(event.entity_id)

    def evaluate(self, entity_id: str) -> None:
        entity = self.world.entities[entity_id]
        t = self.thresholds
        critical: list[str] = []
        warning: list[str] = []

        compute = entity.get(ComputeState)
        if compute:
            if compute.cpu_percent >= t.cpu_critical_percent:
                critical.append(f"CPU {compute.cpu_percent:.0f}%")
            elif compute.cpu_percent >= t.cpu_warning_percent:
                warning.append(f"CPU {compute.cpu_percent:.0f}%")

        memory = entity.get(MemoryState)
        if memory:
            if memory.used_percent >= t.memory_critical_percent:
                critical.append(f"memory {memory.used_percent:.0f}%")
            elif memory.used_percent >= t.memory_warning_percent:
                warning.append(f"memory {memory.used_percent:.0f}%")

        storage = entity.get(StorageState)
        if storage:
            if storage.used_percent >= t.storage_critical_percent:
                critical.append(f"storage {storage.used_percent:.0f}%")
            elif storage.used_percent >= t.storage_warning_percent:
                warning.append(f"storage {storage.used_percent:.0f}%")

        temperature = entity.get(TemperatureState)
        if temperature and temperature.celsius is not None:
            if temperature.celsius >= t.temperature_critical_c:
                critical.append(f"temperature {temperature.celsius:.0f} C")
            elif temperature.celsius >= t.temperature_warning_c:
                warning.append(f"temperature {temperature.celsius:.0f} C")

        usb = entity.get(UsbDeviceState)
        if usb:
            if not usb.present:
                critical.append("USB radio absent")
            elif usb.mode != "wifi":
                warning.append(f"USB radio mode={usb.mode}")

        wifi = entity.get(WifiLinkState)
        if wifi:
            if not wifi.connected:
                critical.append("Wi-Fi disconnected")
            elif (
                wifi.signal_dbm is not None
                and wifi.signal_dbm <= t.wifi_signal_warning_dbm
            ):
                warning.append(f"Wi-Fi signal {wifi.signal_dbm} dBm")

        if critical:
            status, reasons = "critical", tuple(critical + warning)
        elif warning:
            status, reasons = "warning", tuple(warning)
        elif any(
            entity.get(component_type) is not None
            for component_type in (
                ComputeState,
                MemoryState,
                StorageState,
                TemperatureState,
                UsbDeviceState,
                WifiLinkState,
            )
        ):
            status, reasons = "nominal", ()
        else:
            status, reasons = "unknown", ("no health-bearing telemetry",)

        current = entity.get(HealthState)
        proposed = HealthState(status=status, reasons=reasons)
        if current != proposed:
            self.world.upsert_component(entity_id, proposed)
