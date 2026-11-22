"""API tests using an isolated service double instead of PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
import unittest

from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import create_app
from schemas import ObservationInput
from services.observations import DatabaseUnavailable, ObservationNotFound


class FakeObservationService:
    def __init__(self) -> None:
        self.observation = SimpleNamespace(
            id=uuid4(),
            node_id="node-01",
            timestamp=datetime(2026, 11, 1, 10, 30, tzinfo=timezone.utc),
            signal_type="spoofing",
            confidence=Decimal("8.5"),
            lat=Decimal("18.6298"),
            lon=Decimal("73.7997"),
            metadata_json={"receiver": {"fix": True}},
        )
        self.last_query = None
        self.fail_database = False

    def check_health(self) -> None:
        if self.fail_database:
            raise DatabaseUnavailable("unavailable")

    def list_observations(self, query: object) -> list[SimpleNamespace]:
        if self.fail_database:
            raise DatabaseUnavailable("unavailable")
        self.last_query = query
        return [self.observation]

    def get_observation(self, observation_id: object) -> SimpleNamespace:
        if self.fail_database:
            raise DatabaseUnavailable("unavailable")
        if observation_id != self.observation.id:
            raise ObservationNotFound(str(observation_id))
        return self.observation


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FakeObservationService()
        self.client = TestClient(create_app(observation_service=self.service, enable_mqtt=False))

    def test_health(self) -> None:
        with self.client:
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_list_uses_pagination_and_filters(self) -> None:
        with self.client:
            response = self.client.get(
                "/observations",
                params={
                    "node_id": "node-01",
                    "signal_type": "spoofing",
                    "start_time": "2026-11-01T00:00:00Z",
                    "end_time": "2026-11-02T00:00:00Z",
                    "limit": 10,
                    "offset": 5,
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["limit"], 10)
        self.assertEqual(response.json()["offset"], 5)
        self.assertEqual(response.json()["items"][0]["confidence"], 8.5)
        assert self.service.last_query is not None
        self.assertEqual(self.service.last_query.node_id, "node-01")
        self.assertEqual(self.service.last_query.signal_type, "spoofing")

    def test_missing_observation_returns_consistent_404(self) -> None:
        with self.client:
            response = self.client.get(f"/observations/{uuid4()}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"]["code"], "observation_not_found")

    def test_get_observation_returns_stored_contract_fields(self) -> None:
        with self.client:
            response = self.client.get(f"/observations/{self.service.observation.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], str(self.service.observation.id))
        self.assertEqual(response.json()["metadata"], {"receiver": {"fix": True}})

    def test_database_failure_returns_consistent_503(self) -> None:
        self.service.fail_database = True
        with self.client:
            response = self.client.get("/observations")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "database_unavailable")

    def test_oversized_request_body_is_rejected(self) -> None:
        with self.client:
            response = self.client.request("GET", "/observations", content=b"x" * (64 * 1024 + 1))
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["detail"]["code"], "payload_too_large")

    def test_pydantic_observation_validation(self) -> None:
        valid = {
            "node_id": "node-01",
            "timestamp": "2026-11-01T10:30:00Z",
            "signal_type": "spoofing",
            "confidence": 8.5,
            "coordinates": {"lat": 18.6298, "lon": 73.7997},
            "metadata": {"receiver": {"fix": True}},
        }
        self.assertEqual(ObservationInput.model_validate(valid).confidence, 8.5)
        for invalid in (
            {**valid, "confidence": 0},
            {**valid, "coordinates": {"lat": 90.1, "lon": 73.7997}},
            {**valid, "signal_type": "other"},
            {**valid, "timestamp": "2026-11-01T10:30:00"},
            {**valid, "unexpected": True},
        ):
            with self.assertRaises(ValidationError):
                ObservationInput.model_validate(invalid)


if __name__ == "__main__":
    unittest.main()
