"""Tests for MQTT publication details without a live broker."""

from __future__ import annotations

import json
import unittest

from simulator.config import SimulatorSettings
from simulator.generator import SimulationGenerator
from simulator.publisher import MqttObservationPublisher


class FakeMessage:
    rc = 0

    def wait_for_publish(self, timeout: int) -> None:
        self.timeout = timeout


class FakeClient:
    def __init__(self) -> None:
        self.published: list[tuple[str, bytes, int, bool]] = []
        self.loop_stopped = False
        self.disconnected = False

    def publish(self, topic: str, payload: bytes, qos: int, retain: bool) -> FakeMessage:
        self.published.append((topic, payload, qos, retain))
        return FakeMessage()

    def loop_stop(self) -> None:
        self.loop_stopped = True

    def disconnect(self) -> None:
        self.disconnected = True


class PublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeClient()
        self.settings = SimulatorSettings("localhost", 1883, ("sim-node-01",), 1, "spoofing", 1, None, 1, None, None)
        self.publisher = MqttObservationPublisher(self.settings, client=self.client)
        self.publisher._connected.set()  # Establish a fake connected broker for this isolated unit test.

    def test_publishes_utf8_json_with_qos_one_and_no_retain(self) -> None:
        observation = SimulationGenerator(seed=1).generate("sim-node-01", "spoofing")
        assert observation is not None
        self.assertTrue(self.publisher.publish(observation))
        topic, payload, qos, retain = self.client.published[0]
        self.assertEqual(topic, "hazeguard/v1/nodes/sim-node-01/observations")
        self.assertEqual(qos, 1)
        self.assertFalse(retain)
        self.assertEqual(json.loads(payload.decode("utf-8"))["node_id"], "sim-node-01")

    def test_invalid_observation_is_not_published(self) -> None:
        self.assertFalse(self.publisher.publish({"node_id": "sim-node-01"}))
        self.assertEqual(self.client.published, [])

    def test_close_stops_network_loop_and_disconnects(self) -> None:
        self.publisher.close()
        self.assertTrue(self.client.loop_stopped)
        self.assertTrue(self.client.disconnected)


if __name__ == "__main__":
    unittest.main()
