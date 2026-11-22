"""MQTT consumer wiring for validated GNSS observations."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from mqtt_config import MqttSettings
from mqtt_topics import OBSERVATION_TOPIC_FILTER, OBSERVATION_QOS
from mqtt_validation import ObservationRejected, validate_observation_message


class MqttObservationConsumer:
    """Subscribe to observations and persist only messages that validate."""

    def __init__(
        self,
        settings: MqttSettings,
        persist_observation: Callable[[Mapping[str, Any]], None],
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._persist_observation = persist_observation
        self._logger = logger or logging.getLogger(__name__)

    def handle_message(self, topic: str, payload: bytes) -> bool:
        """Validate a received MQTT message before handing it to persistence."""
        try:
            observation = validate_observation_message(
                topic=topic,
                payload=payload,
                allowed_node_ids=self._settings.allowed_node_ids,
            )
        except ObservationRejected as exc:
            self._logger.warning(
                "Rejected MQTT observation: reason=%s topic=%r payload_size_bytes=%d",
                exc.code,
                topic,
                len(payload),
            )
            return False

        try:
            self._persist_observation(observation)
        except Exception:
            self._logger.exception("Could not persist validated MQTT observation")
            return False
        return True

    def create_client(self) -> Any:
        """Create a configured Paho client without connecting to the broker."""
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:  # pragma: no cover - depends on deployment setup
            raise RuntimeError("paho-mqtt must be installed to run the MQTT consumer") from exc

        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=self._settings.client_id,
        )
        if self._settings.username is not None:
            client.username_pw_set(self._settings.username, self._settings.password)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        return client

    def start(self) -> Any:
        """Connect to Mosquitto and start its network loop."""
        client = self.create_client()
        client.connect(
            self._settings.host,
            self._settings.port,
            self._settings.keepalive_seconds,
        )
        client.loop_start()
        return client

    @staticmethod
    def stop(client: Any) -> None:
        """Stop an MQTT client created by this consumer."""
        client.loop_stop()
        client.disconnect()

    def _on_connect(self, client: Any, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any) -> None:
        if reason_code != 0:
            self._logger.error("MQTT connection rejected: reason_code=%s", reason_code)
            return
        client.subscribe(OBSERVATION_TOPIC_FILTER, qos=OBSERVATION_QOS)
        self._logger.info("Subscribed to MQTT observation topic filter")

    def _on_message(self, _client: Any, _userdata: Any, message: Any) -> None:
        self.handle_message(message.topic, bytes(message.payload))
