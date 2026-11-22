"""Resilient MQTT publisher for validated simulated observations."""

from __future__ import annotations

import logging
import threading
from typing import Any, Mapping

from .config import SimulatorSettings
from .topics import OBSERVATION_QOS, observation_topic
from .validation import InvalidSimulatedObservation, serialize_observation


class MqttObservationPublisher:
    """Publish valid simulator observations with QoS 1 and reconnect support."""

    def __init__(self, settings: SimulatorSettings, client: Any | None = None, logger: logging.Logger | None = None) -> None:
        self._settings = settings
        self._client = client
        self._logger = logger or logging.getLogger(__name__)
        self._connected = threading.Event()

    def connect(self, timeout_seconds: float = 10) -> None:
        """Start Paho's reconnecting network loop and await the first connection."""
        client = self._client or self._create_client()
        self._client = client
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.reconnect_delay_set(min_delay=1, max_delay=30)
        client.connect_async(self._settings.host, self._settings.port, keepalive=60)
        client.loop_start()
        if not self._connected.wait(timeout_seconds):
            self.close()
            raise ConnectionError(f"Could not connect to MQTT broker at {self._settings.host}:{self._settings.port}")

    def publish(self, observation: Mapping[str, Any]) -> bool:
        """Publish one contract-valid observation, returning false if unavailable."""
        if self._client is None or not self._connected.is_set():
            self._logger.warning("Simulator is not connected to MQTT; observation was not published")
            return False
        try:
            payload = serialize_observation(observation)
            topic = observation_topic(str(observation["node_id"]))
        except (InvalidSimulatedObservation, KeyError, ValueError) as exc:
            self._logger.error("Refusing invalid simulated observation: %s", exc)
            return False
        message = self._client.publish(topic, payload, qos=OBSERVATION_QOS, retain=False)
        if getattr(message, "rc", 0) != 0:
            self._logger.warning("MQTT publish was rejected: result_code=%s", message.rc)
            return False
        try:
            message.wait_for_publish(timeout=10)
        except (RuntimeError, ValueError) as exc:
            self._logger.warning("MQTT publish did not complete: %s", exc)
            return False
        self._logger.info("Published simulated %s observation from %s", observation["signal_type"], observation["node_id"])
        return True

    def close(self) -> None:
        """Stop the network loop cleanly, including after Ctrl+C."""
        if self._client is None:
            return
        self._connected.clear()
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:  # pragma: no cover - broker/client shutdown is environment-dependent
            self._logger.exception("Error while disconnecting MQTT simulator client")

    def _create_client(self) -> Any:
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:  # pragma: no cover - deployment dependency
            raise RuntimeError("paho-mqtt must be installed; install backend/requirements.txt") from exc
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="hazeguard-simulator")
        if self._settings.username is not None:
            client.username_pw_set(self._settings.username, self._settings.password)
        return client

    def _on_connect(self, _client: Any, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any) -> None:
        if reason_code == 0:
            self._connected.set()
            self._logger.info("Connected to MQTT broker at %s:%d", self._settings.host, self._settings.port)
        else:
            self._logger.error("MQTT connection rejected: reason_code=%s", reason_code)

    def _on_disconnect(self, _client: Any, _userdata: Any, _disconnect_flags: Any, reason_code: Any, _properties: Any) -> None:
        self._connected.clear()
        self._logger.warning("MQTT disconnected: reason_code=%s; Paho will retry connection", reason_code)
