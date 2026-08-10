import unittest

from personal_cic.core.events import ComponentUpdated, EventBus
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import ComputeState, HealthState, MemoryState, StorageState, WifiLinkState
from personal_cic.holons.systems.health import HealthSystem


class VerticalSliceTests(unittest.TestCase):
    def setUp(self):
        self.events = EventBus()
        self.world = WorldState(self.events)
        self.world.ensure_entity("node", "Test Node")
        self.health = HealthSystem(self.world)
        self.events.subscribe(ComponentUpdated, self.health.on_component_updated)

    def test_nominal_health_is_derived_from_components(self):
        self.world.upsert_component("node", ComputeState(12.0, 4, 0.3, 0.075))
        self.world.upsert_component("node", MemoryState(16_000, 10_000, 37.5))
        self.world.upsert_component("node", StorageState("/", 100_000, 60_000, 40.0))
        health = self.world.entities["node"].get(HealthState)
        self.assertEqual(health.status, "nominal")

    def test_bad_wifi_drives_critical_health(self):
        self.world.upsert_component(
            "node",
            WifiLinkState("wlan0", False, None, None, None, None, None, None),
        )
        health = self.world.entities["node"].get(HealthState)
        self.assertEqual(health.status, "critical")
        self.assertIn("Wi-Fi disconnected", health.reasons)

    def test_query_is_component_based(self):
        self.world.upsert_component("node", ComputeState(12.0, 4, 0.3, 0.075))
        matches = self.world.query(ComputeState)
        self.assertEqual([e.entity_id for e in matches], ["node"])


if __name__ == "__main__":
    unittest.main()
