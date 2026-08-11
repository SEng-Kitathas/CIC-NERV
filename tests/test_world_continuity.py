import tempfile
import unittest
from pathlib import Path

from personal_cic.core.events import EventBus
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    CICNode,
    HealthState,
    MemoryState,
)


class WorldContinuityTests(unittest.TestCase):
    def test_snapshot_round_trip_restores_typed_components_without_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "world.json"

            first_events = EventBus()
            first = WorldState(first_events)
            first.ensure_entity("engage", "Engage")
            first.upsert_component("engage", CICNode())
            first.upsert_component("engage", MemoryState(16_000, 12_000, 25.0))
            first.upsert_component("engage", HealthState("nominal", ()))
            first.write_json(state_path)

            second_events = EventBus()
            second = WorldState(second_events)
            restored = second.hydrate_json(state_path)

            self.assertEqual(restored, 1)
            self.assertEqual(second_events.published_count, 0)
            entity = second.entities["engage"]
            self.assertIsInstance(entity.get(CICNode), CICNode)
            self.assertEqual(entity.get(MemoryState), MemoryState(16_000, 12_000, 25.0))
            self.assertEqual(entity.get(HealthState), HealthState("nominal", ()))


if __name__ == "__main__":
    unittest.main()
