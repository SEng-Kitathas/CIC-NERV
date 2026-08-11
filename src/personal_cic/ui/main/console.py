from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    ComputeState,
    HealthState,
    MemoryState,
    ObservationState,
    StorageState,
    TemperatureState,
    UptimeState,
    UsbDeviceState,
    WifiLinkState,
)


def _gib(value: int) -> float:
    return value / (1024 ** 3)


def _uptime(seconds: int) -> str:
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


def render(world: WorldState, event_count: int) -> None:
    print()
    print("PERSONAL CIC // SYSTEMS")
    print("=" * 72)

    for entity in world.entities.values():
        health = entity.get(HealthState)
        status = health.status.value.upper() if health else "UNKNOWN"
        print(f"{entity.label} [{entity.entity_id}] :: {status}")

        compute = entity.get(ComputeState)
        memory = entity.get(MemoryState)
        storage = entity.get(StorageState)
        uptime = entity.get(UptimeState)
        temp = entity.get(TemperatureState)
        usb = entity.get(UsbDeviceState)
        wifi = entity.get(WifiLinkState)
        observation = entity.get(ObservationState)

        if observation:
            obs = observation.availability.value.upper()
            print(f"  OBS  {obs} via {observation.adapter_id}")
            if observation.reasons:
                print("       " + "; ".join(observation.reasons))

        if compute:
            print(f"  CPU  {compute.cpu_percent:5.1f}% | load {compute.load_1m:.2f} | {compute.logical_cpus} logical CPUs")
        if memory:
            print(f"  MEM  {memory.used_percent:5.1f}% | {_gib(memory.available_bytes):.1f} GiB available")
        if storage:
            print(f"  DISK {storage.used_percent:5.1f}% | {_gib(storage.free_bytes):.1f} GiB free")
        if temp and temp.celsius is not None:
            print(f"  TEMP {temp.celsius:.1f} °C | {temp.source}")
        if uptime:
            print(f"  UP   {_uptime(uptime.uptime_seconds)}")
        if usb:
            print(f"  USB  {usb.usb_id or '--'} | mode={usb.mode}")
        if wifi:
            link = wifi.ssid if wifi.connected else "DISCONNECTED"
            signal = f"{wifi.signal_dbm} dBm" if wifi.signal_dbm is not None else "--"
            freq = f"{wifi.frequency_mhz} MHz" if wifi.frequency_mhz else "--"
            tx = f"{wifi.tx_mbps:.1f}" if wifi.tx_mbps is not None else "--"
            rx = f"{wifi.rx_mbps:.1f}" if wifi.rx_mbps is not None else "--"
            print(f"  WIFI {wifi.interface or '--'} | {link} | {signal} | {freq}")
            print(f"       IPv4 {wifi.ipv4 or '--'} | TX {tx} Mbps | RX {rx} Mbps")

        if health and health.reasons:
            print("  WHY  " + "; ".join(health.reasons))
        print()

    print(f"Typed events emitted this run: {event_count}")
    print("=" * 72)
