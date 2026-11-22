"""Environment-based configuration for the MQTT observation consumer."""

from __future__ import annotations

import os
from dataclasses import dataclass


class MqttConfigurationError(ValueError):
    """Raised when MQTT environment configuration is incomplete or invalid."""


@dataclass(frozen=True)
class MqttSettings:
    """Settings required to connect the backend MQTT consumer to Mosquitto."""

    host: str
    port: int
    client_id: str
    keepalive_seconds: int
    username: str | None
    password: str | None
    allowed_node_ids: frozenset[str]

    @classmethod
    def from_environment(cls) -> "MqttSettings":
        """Load settings without logging credential values."""
        allowed_node_ids = frozenset(
            node_id.strip()
            for node_id in os.getenv("HAZEGUARD_MQTT_ALLOWED_NODE_IDS", "").split(",")
            if node_id.strip()
        )
        if not allowed_node_ids:
            raise MqttConfigurationError(
                "HAZEGUARD_MQTT_ALLOWED_NODE_IDS must list one or more authorized node IDs"
            )

        username = os.getenv("HAZEGUARD_MQTT_USERNAME")
        password = os.getenv("HAZEGUARD_MQTT_PASSWORD")
        if password is not None and username is None:
            raise MqttConfigurationError(
                "HAZEGUARD_MQTT_USERNAME is required when HAZEGUARD_MQTT_PASSWORD is set"
            )

        return cls(
            host=os.getenv("HAZEGUARD_MQTT_HOST", "localhost"),
            port=_positive_integer("HAZEGUARD_MQTT_PORT", 1883),
            client_id=os.getenv("HAZEGUARD_MQTT_CLIENT_ID", "hazeguard-backend"),
            keepalive_seconds=_positive_integer("HAZEGUARD_MQTT_KEEPALIVE_SECONDS", 60),
            username=username,
            password=password,
            allowed_node_ids=allowed_node_ids,
        )


def _positive_integer(variable_name: str, default: int) -> int:
    value = os.getenv(variable_name)
    if value is None:
        return default
    try:
        number = int(value)
    except ValueError as exc:
        raise MqttConfigurationError(f"{variable_name} must be an integer") from exc
    if number <= 0:
        raise MqttConfigurationError(f"{variable_name} must be greater than zero")
    return number
