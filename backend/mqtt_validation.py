"""Safe parsing and schema validation for MQTT GNSS observation payloads."""

from __future__ import annotations

import json
from collections.abc import Mapping, Set
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from mqtt_topics import node_id_from_observation_topic

MAX_OBSERVATION_PAYLOAD_BYTES = 64 * 1024
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "docs" / "schema.json"


class ObservationRejected(ValueError):
    """A message failed topic, size, JSON, or observation-schema validation."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@lru_cache(maxsize=1)
def _observation_validator() -> Draft202012Validator:
    with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_observation_message(
    topic: str,
    payload: bytes,
    allowed_node_ids: Set[str] | frozenset[str],
) -> Mapping[str, Any]:
    """Return an approved observation or raise ``ObservationRejected``.

    The raw payload is intentionally never returned or logged by this module.
    """
    topic_node_id = node_id_from_observation_topic(topic)
    if topic_node_id is None:
        raise ObservationRejected("invalid_topic")
    if topic_node_id not in allowed_node_ids:
        raise ObservationRejected("unknown_node")
    if len(payload) > MAX_OBSERVATION_PAYLOAD_BYTES:
        raise ObservationRejected("payload_too_large")

    try:
        decoded_payload = payload.decode("utf-8")
        observation = json.loads(decoded_payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ObservationRejected("malformed_json") from exc

    if not isinstance(observation, dict):
        raise ObservationRejected("schema_validation_failed")
    if observation.get("node_id") != topic_node_id:
        raise ObservationRejected("node_id_topic_mismatch")

    if not _observation_validator().is_valid(observation):
        raise ObservationRejected("schema_validation_failed")
    return observation
