from personal_cic.core.config import HealthThresholds
from personal_cic.core.events import ObservationCycleCompleted
from personal_cic.core.world import WorldState
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world.components import (
    ComputeState,
    HealthState,
    HealthStatus,
    MemoryState,
    ObservationState,
    StorageState,
    TemperatureState,
    UsbDeviceState,
    WifiLinkState,
)


class HealthSystem:
    def __init__(self, world: WorldState, thresholds: HealthThresholds) -> None:
        self.world = world
        self.thresholds = thresholds

    def on_observation_cycle_completed(self, event: ObservationCycleCompleted) -> None:
        self.evaluate(event.entity_id)

    def evaluate(self, entity_id: str) -> None:
        entity = self.world.entities[entity_id]
        t = self.thresholds
        critical: list[str] = []
        warning: list[str] = []

        observation = entity.get(ObservationState)
        if observation and observation.availability is ObservationAvailability.UNAVAILABLE:
            reason = "telemetry unavailable"
            if observation.reasons:
                reason += ": " + "; ".join(observation.reasons)
            if observation.last_success_at:
                reason += f"; last success {observation.last_success_at}"
            self._set_health(entity_id, HealthState(HealthStatus.UNKNOWN, (reason,)))
            return

        if observation and observation.availability is ObservationAvailability.DEGRADED:
            detail = "; ".join(observation.reasons) or "partial telemetry"
            warning.append(f"telemetry degraded: {detail}")

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
            proposed = HealthState(HealthStatus.CRITICAL, tuple(critical + warning))
        elif warning:
            proposed = HealthState(HealthStatus.WARNING, tuple(warning))
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
            proposed = HealthState(HealthStatus.NOMINAL, ())
        else:
            proposed = HealthState(
                HealthStatus.UNKNOWN,
                ("no health-bearing telemetry",),
            )

        self._set_health(entity_id, proposed)

    def _set_health(self, entity_id: str, proposed: HealthState) -> None:
        entity = self.world.entities[entity_id]
        if entity.get(HealthState) != proposed:
            self.world.upsert_component(entity_id, proposed)
