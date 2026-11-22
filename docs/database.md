# PostgreSQL persistence

The `gnss_observations` table persists validated observations from the MQTT
consumer. The database accepts no replacement for MQTT/schema validation; it
adds constraints as a final integrity boundary.

## Storage decisions

- `id` is an application-generated UUID primary key. It does not add a field
  to the MQTT or API payload.
- `timestamp` uses PostgreSQL `TIMESTAMP WITH TIME ZONE` to preserve the
  contract's timezone-aware observation time.
- `confidence`, `lat`, and `lon` use PostgreSQL `NUMERIC` without a fixed
  scale, preserving approved decimal values without imposing an unapproved
  decimal-place limit.
- `metadata` uses PostgreSQL `JSONB`, preserving nested JSON values and
  enabling future metadata queries without denormalizing the payload.
- Database checks repeat the confidence, signal-type, latitude, and longitude
  limits in the approved observation contract.
- B-tree indexes support time-based queries, node filtering, and
  signal-classification filtering.

## Configuration and migrations

Set `HAZEGUARD_DATABASE_URL` to a PostgreSQL SQLAlchemy URL, for example a URL
using the `postgresql+psycopg` driver. The value is required and is never
logged by the database helpers.

Apply schema changes with:

```text
alembic upgrade head
```

Alembic reads `HAZEGUARD_DATABASE_URL`; the initial migration creates
`gnss_observations` and its indexes on an empty database. Migrations never
drop existing data during upgrade.

Integration tests require `HAZEGUARD_TEST_DATABASE_URL`, which must point to
an isolated PostgreSQL database. The test suite applies `alembic upgrade head`
before exercising the repository and removes only rows it created.
