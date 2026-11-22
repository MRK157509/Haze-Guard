"""Local contract validation before a simulator message reaches MQTT."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

MAX_OBSERVATION_PAYLOAD_BYTES = 64 * 1024
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "docs" / "schema.json"


class InvalidSimulatedObservation(ValueError):
    """Raised when data would violate the approved observation contract."""


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def serialize_observation(observation: Mapping[str, Any]) -> bytes:
    """Validate and serialize an observation as an MQTT-safe UTF-8 payload."""
    errors = list(_validator().iter_errors(dict(observation)))
    if errors:
        raise InvalidSimulatedObservation(errors[0].message)
    try:
        payload = json.dumps(observation, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InvalidSimulatedObservation("observation cannot be JSON serialized") from exc
    if len(payload) > MAX_OBSERVATION_PAYLOAD_BYTES:
        raise InvalidSimulatedObservation("serialized observation exceeds 64 KiB")
    return payload
