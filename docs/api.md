# HazeGuard REST API

The FastAPI backend exposes read-only observation data for the dashboard. MQTT
is the only ingestion path; there is no HTTP observation-create endpoint.

All successful observation responses use the approved fields plus the
database-generated `id` required to retrieve a stored observation. Timestamps
are RFC3339 date-times with an explicit timezone.

## `GET /health`

Checks PostgreSQL connectivity and returns:

```json
{"status":"ok"}
```

It returns a `503` error with code `database_unavailable` when the database
cannot be reached.

## `GET /observations`

Lists observations in descending observation-time order. Accepted query
parameters are:

| Parameter | Meaning |
| --- | --- |
| `node_id` | Exact node identifier. |
| `signal_type` | `spoofing` or `jamming`. |
| `start_time` | RFC3339 inclusive lower timestamp bound with timezone. |
| `end_time` | RFC3339 inclusive upper timestamp bound with timezone. |
| `limit` | Page size from 1 to 100; defaults to 50. |
| `offset` | Zero-based page offset; defaults to 0. |

The response contains `items`, `limit`, and `offset`. Each item contains
`id`, `node_id`, `timestamp`, `signal_type`, `confidence`, `coordinates`, and
`metadata`.

## `GET /observations/{id}`

Returns one observation using its database UUID. A missing record returns
`404` with error code `observation_not_found`.

## Errors and CORS

Errors use `{"detail":{"code":"...","message":"..."}}` and do not
include credentials, payload contents, or stack traces. Request bodies larger
than 64 KiB receive `413`.

Cross-origin access is disabled unless `HAZEGUARD_CORS_ORIGINS` is configured
as a comma-separated allowlist. When enabled, it permits `GET` requests only.

## Runtime configuration

The application requires the database and MQTT settings documented in
[`database.md`](database.md) and [`mqtt-contract.md`](mqtt-contract.md):
`HAZEGUARD_DATABASE_URL` and `HAZEGUARD_MQTT_ALLOWED_NODE_IDS` are required at
startup. Use `uvicorn main:app` from `backend/` after applying migrations.

MQTT uses QoS 1, which can redeliver a message. The approved payload has no
stable event identifier, so reliable deduplication cannot be implemented
without changing the contract; the backend intentionally does not infer one.
