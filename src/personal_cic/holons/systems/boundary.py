from personal_cic.core.holons import HolonSpec


SYSTEMS_HOLON = HolonSpec(
    name="systems",
    purpose="Maintain operational awareness of CIC compute and network substrate.",
    owns=(
        "local host telemetry",
        "network-interface telemetry",
        "device health derivation",
    ),
    interfaces=(
        "normalized components into WorldState",
        "typed ComponentUpdated events",
        "HealthState for presentation and alert consumers",
    ),
    invariants=(
        "adapters do not own operational truth",
        "presentation does not query hardware directly",
        "experimental RF behavior cannot redefine systems health semantics",
    ),
    hazards=(
        "vendor-specific logic leaking into core",
        "health thresholds becoming hidden constants across multiple modules",
        "telemetry failure being mistaken for device failure",
    ),
)
