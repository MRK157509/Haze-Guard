"""Unit tests for contract-valid, reproducible simulated GNSS detections."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from simulator.generator import SimulationGenerator
from simulator.topics import observation_topic
from simulator.validation import InvalidSimulatedObservation, serialize_observation

FIXED_TIME = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)


class SimulationGeneratorTests(unittest.TestCase):
    def _generator(self, seed: int = 42) -> SimulationGenerator:
        return SimulationGenerator(seed=seed, clock=lambda: FIXED_TIME)

    def test_spoofing_observation_has_required_contract_fields(self) -> None:
        observation = self._generator().generate("sim-node-01", "spoofing")
        assert observation is not None
        self.assertEqual(set(observation), {"node_id", "timestamp", "signal_type", "confidence", "coordinates", "metadata"})
        self.assertEqual(observation["signal_type"], "spoofing")
        self.assertTrue(observation["metadata"]["simulation"]["is_simulated"])
        self.assertEqual(observation["timestamp"], "2026-11-22T12:00:00Z")
        self.assertGreaterEqual(observation["confidence"], 1)
        self.assertLessEqual(observation["confidence"], 10)
        self.assertGreaterEqual(observation["coordinates"]["lat"], -90)
        self.assertLessEqual(observation["coordinates"]["lat"], 90)
        self.assertGreaterEqual(observation["coordinates"]["lon"], -180)
        self.assertLessEqual(observation["coordinates"]["lon"], 180)
        self.assertEqual(json.loads(serialize_observation(observation)), observation)

    def test_jamming_and_mixed_scenarios_emit_valid_events(self) -> None:
        jamming = self._generator().generate("sim-node-02", "jamming")
        mixed = self._generator().generate("sim-node-03", "mixed")
        assert jamming is not None and mixed is not None
        self.assertEqual(jamming["signal_type"], "jamming")
        self.assertIn(mixed["signal_type"], {"spoofing", "jamming"})
        serialize_observation(jamming)
        serialize_observation(mixed)

    def test_normal_scenario_emits_no_invalid_normal_signal_type(self) -> None:
        self.assertIsNone(self._generator().generate("sim-node-01", "normal"))

    def test_fixed_seed_and_clock_are_reproducible(self) -> None:
        self.assertEqual(
            self._generator(123).generate("sim-node-01", "spoofing"),
            self._generator(123).generate("sim-node-01", "spoofing"),
        )

    def test_invalid_observation_is_rejected_before_publish(self) -> None:
        invalid = {"node_id": "sim-node-01", "timestamp": "not-a-timestamp"}
        with self.assertRaises(InvalidSimulatedObservation):
            serialize_observation(invalid)

    def test_unknown_top_level_and_coordinate_fields_are_rejected(self) -> None:
        observation = self._generator().generate("sim-node-01", "spoofing")
        assert observation is not None
        with self.assertRaises(InvalidSimulatedObservation):
            serialize_observation({**observation, "unapproved": True})
        with self.assertRaises(InvalidSimulatedObservation):
            serialize_observation({**observation, "coordinates": {**observation["coordinates"], "alt": 1}})

    def test_topic_matches_payload_node_id(self) -> None:
        observation = self._generator().generate("sim-node-01", "jamming")
        assert observation is not None
        self.assertEqual(observation_topic(observation["node_id"]), "hazeguard/v1/nodes/sim-node-01/observations")


if __name__ == "__main__":
    unittest.main()
