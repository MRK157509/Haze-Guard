"""MQTT topic helpers shared by the HazeGuard software simulator."""

OBSERVATION_TOPIC_TEMPLATE = "hazeguard/v1/nodes/{node_id}/observations"
OBSERVATION_QOS = 1


def observation_topic(node_id: str) -> str:
    """Return the approved observation topic for a simulated node."""
    if not node_id or any(character in node_id for character in ("/", "+", "#")):
        raise ValueError("node_id cannot be empty or contain MQTT separators or wildcards")
    return OBSERVATION_TOPIC_TEMPLATE.format(node_id=node_id)
