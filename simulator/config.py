"""Configuration parsing for the HazeGuard software simulator."""

from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass

from .topics import observation_topic

SCENARIOS = ("mixed", "normal", "spoofing", "jamming")


@dataclass(frozen=True)
class SimulatorSettings:
    """Non-secret simulator settings loaded from CLI arguments and environment."""

    host: str
    port: int
    node_ids: tuple[str, ...]
    interval_seconds: float
    scenario: str
    seed: int | None
    duration_seconds: float | None
    max_observations: int | None
    username: str | None
    password: str | None


def parse_settings(arguments: list[str] | None = None) -> SimulatorSettings:
    """Parse user configuration without printing or persisting credentials."""
    parser = argparse.ArgumentParser(description="Publish simulated HazeGuard GNSS detections over MQTT.")
    # Keep the public option names while explicitly aligning argparse destinations
    # with the settings fields used below.  argparse would otherwise derive
    # ``mqtt_host`` and ``mqtt_port`` from these option names.
    parser.add_argument("--mqtt-host", dest="host", default=os.getenv("HAZEGUARD_MQTT_HOST", "localhost"))
    parser.add_argument("--mqtt-port", dest="port", type=int, default=_integer_env("HAZEGUARD_MQTT_PORT", 1883))
    parser.add_argument(
        "--node-ids",
        default=os.getenv("HAZEGUARD_SIMULATOR_NODE_IDS", "sim-node-01"),
        help="Comma-separated software node identities.",
    )
    parser.add_argument("--interval-seconds", type=float, default=_float_env("HAZEGUARD_SIMULATOR_INTERVAL_SECONDS", 3.0))
    parser.add_argument("--scenario", choices=SCENARIOS, default=os.getenv("HAZEGUARD_SIMULATOR_SCENARIO", "mixed"))
    parser.add_argument("--seed", type=int, default=_optional_integer_env("HAZEGUARD_SIMULATOR_SEED"))
    parser.add_argument("--duration-seconds", type=float, default=_optional_float_env("HAZEGUARD_SIMULATOR_DURATION_SECONDS"))
    parser.add_argument("--max-observations", type=int, default=_optional_integer_env("HAZEGUARD_SIMULATOR_MAX_OBSERVATIONS"))
    parser.add_argument("--mqtt-username", default=os.getenv("HAZEGUARD_MQTT_USERNAME"))
    parser.add_argument("--mqtt-password", default=os.getenv("HAZEGUARD_MQTT_PASSWORD"))
    parsed = parser.parse_args(arguments)
    node_ids = tuple(node.strip() for node in parsed.node_ids.split(",") if node.strip())
    if not node_ids:
        parser.error("--node-ids must include at least one node ID")
    for node_id in node_ids:
        try:
            observation_topic(node_id)
        except ValueError as exc:
            parser.error(str(exc))
    if not parsed.host.strip():
        parser.error("MQTT host must not be empty")
    if not 1 <= parsed.port <= 65535:
        parser.error("MQTT port must be between 1 and 65535")
    if not math.isfinite(parsed.interval_seconds) or parsed.interval_seconds <= 0:
        parser.error("publishing interval must be finite and greater than zero")
    if parsed.duration_seconds is not None and (
        not math.isfinite(parsed.duration_seconds) or parsed.duration_seconds <= 0
    ):
        parser.error("duration must be greater than zero")
    if parsed.max_observations is not None and parsed.max_observations <= 0:
        parser.error("max observations must be greater than zero")
    if parsed.mqtt_password and not parsed.mqtt_username:
        parser.error("--mqtt-username is required when an MQTT password is configured")
    return SimulatorSettings(
        host=parsed.host,
        port=parsed.port,
        node_ids=node_ids,
        interval_seconds=parsed.interval_seconds,
        scenario=parsed.scenario,
        seed=parsed.seed,
        duration_seconds=parsed.duration_seconds,
        max_observations=parsed.max_observations,
        username=parsed.mqtt_username,
        password=parsed.mqtt_password,
    )


def _integer_env(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _float_env(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _optional_integer_env(name: str) -> int | None:
    value = os.getenv(name)
    return int(value) if value else None


def _optional_float_env(name: str) -> float | None:
    value = os.getenv(name)
    return float(value) if value else None
