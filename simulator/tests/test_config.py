"""Regression tests for simulator CLI argument parsing and validation."""

from __future__ import annotations

import unittest

from simulator.config import parse_settings


class SimulatorConfigurationTests(unittest.TestCase):
    def test_reported_multi_node_cli_arguments_are_parsed(self) -> None:
        settings = parse_settings(
            [
                "--node-ids",
                "sim-node-01,sim-node-02,sim-node-03",
                "--scenario",
                "mixed",
                "--interval-seconds",
                "3",
                "--seed",
                "42",
            ]
        )
        self.assertEqual(settings.host, "localhost")
        self.assertEqual(settings.port, 1883)
        self.assertEqual(settings.node_ids, ("sim-node-01", "sim-node-02", "sim-node-03"))
        self.assertEqual(settings.interval_seconds, 3)
        self.assertEqual(settings.scenario, "mixed")
        self.assertEqual(settings.seed, 42)
        self.assertIsNone(settings.duration_seconds)
        self.assertIsNone(settings.max_observations)

    def test_mqtt_host_port_duration_and_count_are_parsed(self) -> None:
        settings = parse_settings(
            [
                "--mqtt-host",
                "broker.internal",
                "--mqtt-port",
                "2883",
                "--duration-seconds",
                "12.5",
                "--max-observations",
                "10",
            ]
        )
        self.assertEqual(settings.host, "broker.internal")
        self.assertEqual(settings.port, 2883)
        self.assertEqual(settings.duration_seconds, 12.5)
        self.assertEqual(settings.max_observations, 10)

    def test_invalid_mqtt_ports_are_rejected(self) -> None:
        for port in ("0", "-1", "65536"):
            with self.subTest(port=port), self.assertRaises(SystemExit):
                parse_settings(["--mqtt-port", port])

    def test_invalid_publish_intervals_are_rejected(self) -> None:
        for interval in ("0", "-0.5", "nan", "inf"):
            with self.subTest(interval=interval), self.assertRaises(SystemExit):
                parse_settings(["--interval-seconds", interval])


if __name__ == "__main__":
    unittest.main()
