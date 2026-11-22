"""Tests for MQTT observation admission before persistence."""

from __future__ import annotations

import json
import unittest

from mqtt_client import MqttObservationConsumer
from mqtt_config import MqttSettings
from mqtt_topics import observation_topic
from mqtt_validation import MAX_OBSERVATION_PAYLOAD_BYTES


class MqttObservationConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.persisted: list[dict[str, object]] = []
        self.consumer = MqttObservationConsumer(
            settings=MqttSettings(
                host="localhost",
                port=1883,
                client_id="test-consumer",
                keepalive_seconds=60,
                username=None,
                password=None,
                allowed_node_ids=frozenset({"node-01"}),
            ),
            persist_observation=self.persisted.append,
        )
        self.observation = {
            "node_id": "node-01",
            "timestamp": "2026-11-01T10:30:00Z",
            "signal_type": "spoofing",
            "confidence": 8.5,
            "coordinates": {"lat": 18.6298, "lon": 73.7997},
            "metadata": {"receiver": {"fix": True}},
        }

    def _payload(self, observation: dict[str, object] | None = None) -> bytes:
        return json.dumps(observation or self.observation).encode("utf-8")

    def test_valid_message_reaches_persistence(self) -> None:
        accepted = self.consumer.handle_message(
            observation_topic("node-01"), self._payload()
        )
        self.assertTrue(accepted)
        self.assertEqual(self.persisted, [self.observation])

    def test_malformed_json_does_not_reach_persistence(self) -> None:
        accepted = self.consumer.handle_message(observation_topic("node-01"), b"{bad")
        self.assertFalse(accepted)
        self.assertEqual(self.persisted, [])

    def test_schema_violation_does_not_reach_persistence(self) -> None:
        invalid = {**self.observation, "confidence": 0}
        accepted = self.consumer.handle_message(
            observation_topic("node-01"), self._payload(invalid)
        )
        self.assertFalse(accepted)
        self.assertEqual(self.persisted, [])

    def test_oversized_payload_does_not_reach_persistence(self) -> None:
        accepted = self.consumer.handle_message(
            observation_topic("node-01"), b"x" * (MAX_OBSERVATION_PAYLOAD_BYTES + 1)
        )
        self.assertFalse(accepted)
        self.assertEqual(self.persisted, [])

    def test_unknown_node_does_not_reach_persistence(self) -> None:
        unknown = {**self.observation, "node_id": "node-02"}
        accepted = self.consumer.handle_message(
            observation_topic("node-02"), self._payload(unknown)
        )
        self.assertFalse(accepted)
        self.assertEqual(self.persisted, [])


if __name__ == "__main__":
    unittest.main()
