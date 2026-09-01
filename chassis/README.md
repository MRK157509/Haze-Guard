# Chassis (Jonathan)

Backend, MQTT pipeline, triangulation logic, and React dashboard.
Consumes classification output from the engine via MQTT, following
the schema in `/docs/schema.json`.

## Structure
- `backend/` — FastAPI + PostgreSQL
- `dashboard/` — React + Mapbox/Leaflet
