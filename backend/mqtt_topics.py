"""MQTT topic constants and parsing for HazeGuard observations."""

from __future__ import annotations

OBSERVATION_TOPIC_TEMPLATE = "hazeguard/v1/nodes/{node_id}/observations"
OBSERVATION_TOPIC_FILTER = "hazeguard/v1/nodes/+/observations"
OBSERVATION_QOS = 1


def observation_topic(node_id: str) -> str:
    """Return the observation publishing topic for one valid node identifier."""
    if not node_id or any(character in node_id for character in ("/", "+", "#")):
        raise ValueError("node_id cannot be empty or contain MQTT topic separators or wildcards")
    return OBSERVATION_TOPIC_TEMPLATE.format(node_id=node_id)


def node_id_from_observation_topic(topic: str) -> str | None:
    """Return the node ID only when *topic* is an exact observation topic."""
    prefix = "hazeguard/v1/nodes/"
    suffix = "/observations"
    if not topic.startswith(prefix) or not topic.endswith(suffix):
        return None
    node_id = topic[len(prefix) : -len(suffix)]
    if not node_id or "/" in node_id or "+" in node_id or "#" in node_id:
        return None
    return node_id
