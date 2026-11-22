# HazeGuard GNSS software simulator

All data emitted by this component is **simulated**. It represents neither a
physical GNSS receiver nor a real-world attack or detection.

## Architecture

```text
simulator/ (Python) -> Mosquitto MQTT -> FastAPI validation/persistence -> PostgreSQL -> React dashboard
```

`simulator/` is independent from `backend/` and `frontend/`. It reuses the
approved topic and JSON contract but has no direct database access and no HTTP
observation-create capability.

## Simulator structure

- `config.py` parses command-line and environment configuration.
- `generator.py` creates seeded, timezone-aware spoofing and jamming events.
- `validation.py` validates and serializes each message against
  `docs/schema.json` before publishing.
- `publisher.py` sends UTF-8 JSON on the approved QoS 1, non-retained topic
  and lets Paho reconnect after a temporary broker disconnect.
- `main.py` runs the publishing loop and shuts down cleanly on Ctrl+C.

The existing contract has only `spoofing` and `jamming` signal types. The
`normal` scenario therefore advances a stable simulated baseline but emits no
observation, rather than publishing an unapproved `normal` event. Spoofing
and jamming metadata include `simulation.is_simulated: true` and baseline
context.

## Prerequisites

Install the Python dependencies already declared for the backend; the
simulator reuses `paho-mqtt` and `jsonschema` and adds no new package.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
docker compose up -d mosquitto postgres

# Use the password configured in your local Docker Compose environment.
$env:HAZEGUARD_DATABASE_URL = 'postgresql+psycopg://hazeguard:<local-password>@localhost:5432/hazeguard'
$env:HAZEGUARD_MQTT_ALLOWED_NODE_IDS = 'sim-node-01,sim-node-02,sim-node-03'
$env:HAZEGUARD_CORS_ORIGINS = 'http://localhost:5173'

Push-Location backend
alembic upgrade head
uvicorn main:app --reload
Pop-Location
```

In a second PowerShell window, with the virtual environment activated:

```powershell
python -m simulator --node-ids sim-node-01,sim-node-02,sim-node-03 --scenario mixed --interval-seconds 3 --seed 42
```

In a third window:

```powershell
Push-Location frontend
npm install
Copy-Item .env.example .env.local
npm run dev
Pop-Location
```

Set `VITE_API_BASE_URL` in `frontend/.env.local` if FastAPI is not on
`http://localhost:8000`. The dashboard polls the existing `GET /observations`
endpoint every five seconds, so MQTT-ingested observations appear without a
browser reload.

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
docker compose up -d mosquitto postgres
export HAZEGUARD_DATABASE_URL='postgresql+psycopg://hazeguard:<local-password>@localhost:5432/hazeguard'
export HAZEGUARD_MQTT_ALLOWED_NODE_IDS='sim-node-01,sim-node-02,sim-node-03'
export HAZEGUARD_CORS_ORIGINS='http://localhost:5173'
(cd backend && alembic upgrade head && uvicorn main:app --reload)
python -m simulator --scenario mixed --seed 42
```

## Configuration

CLI options override defaults/environment values. The MQTT host defaults to
`localhost`, port to `1883`, interval to `3` seconds, and node IDs to
`sim-node-01`.

```text
--mqtt-host HOST          HAZEGUARD_MQTT_HOST
--mqtt-port PORT          HAZEGUARD_MQTT_PORT
--node-ids IDS            HAZEGUARD_SIMULATOR_NODE_IDS (comma separated)
--interval-seconds VALUE  HAZEGUARD_SIMULATOR_INTERVAL_SECONDS
--scenario NAME           HAZEGUARD_SIMULATOR_SCENARIO (mixed|normal|spoofing|jamming)
--seed INTEGER            HAZEGUARD_SIMULATOR_SEED
--duration-seconds VALUE  HAZEGUARD_SIMULATOR_DURATION_SECONDS
--max-observations VALUE  HAZEGUARD_SIMULATOR_MAX_OBSERVATIONS
--mqtt-username VALUE     HAZEGUARD_MQTT_USERNAME
--mqtt-password VALUE     HAZEGUARD_MQTT_PASSWORD
```

For a finite reproducible jamming run:

```powershell
python -m simulator --scenario jamming --node-ids sim-node-01,sim-node-02 --seed 42 --max-observations 10
```

The `normal` scenario should be run with `--duration-seconds`, because it
publishes no detection observations by design.

## Tests and troubleshooting

```powershell
python -m unittest discover -s simulator\tests -v
Push-Location backend; python -m unittest discover -s tests -v; Pop-Location
Push-Location frontend; npm test; npm run lint; npm run build; Pop-Location
```

- If the simulator cannot connect, confirm `docker compose ps`, host/port,
  and broker credentials. It retries transient disconnects after connecting.
- If the backend logs `unknown_node`, add every simulator node to
  `HAZEGUARD_MQTT_ALLOWED_NODE_IDS` and restart FastAPI.
- If the dashboard has an API error, confirm FastAPI is running and its CORS
  allowlist includes the Vite origin.
- If no records appear, inspect FastAPI logs first: the backend deliberately
  rejects invalid topics, payloads, node mismatches, and contract violations.
