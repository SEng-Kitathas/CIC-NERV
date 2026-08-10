from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HolonSpec:
    name: str
    purpose: str
    owns: tuple[str, ...]
    interfaces: tuple[str, ...]
    invariants: tuple[str, ...]
    hazards: tuple[str, ...]
