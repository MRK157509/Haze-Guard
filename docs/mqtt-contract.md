# MQTT observation contract

HazeGuard nodes publish GNSS observations to Mosquitto. The FastAPI backend
subscribes, validates each message, and passes only valid observations to its
persistence layer. The flow remains:

`GNSS detection node → Mosquitto → FastAPI backend → PostgreSQL → React dashboard`

## Topic

The only topic defined by this contract is the versioned observation topic:

```text
hazeguard/v1/nodes/{node_id}/observations
```

`{node_id}` must be the same value as the payload's `node_id`, and must not
contain `/`, `+`, or `#`. For example, `node-01` publishes to:

```text
hazeguard/v1/nodes/node-01/observations
```

The backend subscribes to `hazeguard/v1/nodes/+/observations`. No heartbeat,
command, control, or additional telemetry topics are defined because this
contract only covers observation ingestion.

## Delivery and retention

Nodes publish observations with QoS 1. This provides at-least-once delivery,
so downstream persistence must remain prepared for duplicate delivery when it
is implemented. Nodes must publish with `retain=false`: an observation is an
event, and a retained event could be replayed as a current observation to a
new subscriber.

Mosquitto persistence is enabled by the existing broker configuration. This
does not change the requirement that publishers disable MQTT retained messages.

## Payload

Payloads must be UTF-8 encoded JSON and validate against
[`schema.json`](schema.json). The serialized payload may be at most 64 KiB
(65,536 bytes). The backend checks that byte limit before decoding JSON.

The topic node ID and payload `node_id` must match. The backend also accepts
messages only from the configured `HAZEGUARD_MQTT_ALLOWED_NODE_IDS` allowlist.
With no node registry yet, a node absent from that setting is treated as
unknown and its message is rejected.

## Rejection handling

The backend rejects invalid-topic, unknown-node, oversized, non-UTF-8,
malformed-JSON, topic/payload-node-mismatch, and schema-invalid messages.
Rejected messages are never passed to persistence. It logs the rejection
reason, MQTT topic, and payload byte count; it does not log the raw payload or
credentials.

## Backend configuration

Configure the backend through environment variables. Do not put credentials in
source code or frontend settings.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HAZEGUARD_MQTT_HOST` | `localhost` | Mosquitto host. |
| `HAZEGUARD_MQTT_PORT` | `1883` | MQTT TCP listener port. |
| `HAZEGUARD_MQTT_CLIENT_ID` | `hazeguard-backend` | Backend MQTT client ID. |
| `HAZEGUARD_MQTT_KEEPALIVE_SECONDS` | `60` | MQTT keepalive interval. |
| `HAZEGUARD_MQTT_ALLOWED_NODE_IDS` | none; required | Comma-separated authorized node IDs. |
| `HAZEGUARD_MQTT_USERNAME` | unset | MQTT username when broker authentication is configured. |
| `HAZEGUARD_MQTT_PASSWORD` | unset | MQTT password paired with the username. |

The existing `infra/mosquitto/mosquitto.conf` exposes TCP port 1883 and a
WebSocket listener on 9001, permits anonymous connections, and enables broker
persistence. This contract does not change those settings. Anonymous access is
only the repository's current development configuration and is not a
production security claim.

The backend currently contains no persistence implementation. Its MQTT
consumer therefore receives a persistence callback from the future service
layer; this keeps MQTT connection handling separate from validation and
database access.
