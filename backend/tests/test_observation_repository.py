"""PostgreSQL integration tests for migrations and observation persistence."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import unittest

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database import create_session_factory
from models import GnssObservation
from repositories.observations import ObservationRepository

TEST_DATABASE_URL = os.getenv("HAZEGUARD_TEST_DATABASE_URL")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(TEST_DATABASE_URL, "HAZEGUARD_TEST_DATABASE_URL is not configured")
class ObservationRepositoryIntegrationTests(unittest.TestCase):
    """Run only against an explicitly configured isolated PostgreSQL database."""

    @classmethod
    def setUpClass(cls) -> None:
        alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
        alembic_config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
        previous_url = os.environ.get("HAZEGUARD_DATABASE_URL")
        os.environ["HAZEGUARD_DATABASE_URL"] = TEST_DATABASE_URL
        try:
            command.upgrade(alembic_config, "head")
        finally:
            if previous_url is None:
                os.environ.pop("HAZEGUARD_DATABASE_URL", None)
            else:
                os.environ["HAZEGUARD_DATABASE_URL"] = previous_url
        cls.session_factory = create_session_factory(TEST_DATABASE_URL)
        cls.node_id = f"integration-test-{uuid4()}"

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.session_factory() as session:
            session.query(GnssObservation).filter_by(node_id=cls.node_id).delete()
            session.commit()

    def setUp(self) -> None:
        self.session = self.session_factory()
        self.repository = ObservationRepository(self.session)

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.close()

    def _observation(self, **overrides: object) -> dict[str, object]:
        observation: dict[str, object] = {
            "node_id": self.node_id,
            "timestamp": "2026-11-01T10:30:00Z",
            "signal_type": "spoofing",
            "confidence": 8.5,
            "coordinates": {"lat": 18.6298, "lon": 73.7997},
            "metadata": {"receiver": {"fix": True}},
        }
        observation.update(overrides)
        return observation

    def test_migration_connectivity_and_repository_round_trip(self) -> None:
        self.assertEqual(self.session.scalar(text("SELECT 1")), 1)
        stored = self.repository.add(self._observation())
        self.session.commit()

        retrieved = self.repository.get_by_id(stored.id)
        self.assertIsNotNone(retrieved)
        assert retrieved is not None
        self.assertEqual(retrieved.node_id, self.node_id)
        self.assertEqual(retrieved.confidence, Decimal("8.5"))
        self.assertEqual(retrieved.metadata_json, {"receiver": {"fix": True}})
        self.assertEqual(retrieved.timestamp, datetime(2026, 11, 1, 10, 30, tzinfo=timezone.utc))

    def test_confidence_constraint(self) -> None:
        self.session.add(self._database_observation(confidence=Decimal("0")))
        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_signal_type_constraint(self) -> None:
        self.session.add(self._database_observation(signal_type="other"))
        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_coordinate_constraints(self) -> None:
        self.session.add(self._database_observation(lat=Decimal("90.1")))
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()
        self.session.add(self._database_observation(lon=Decimal("-180.1")))
        with self.assertRaises(IntegrityError):
            self.session.commit()

    def _database_observation(self, **overrides: object) -> GnssObservation:
        fields: dict[str, object] = {
            "node_id": self.node_id,
            "timestamp": datetime(2026, 11, 1, 10, 30, tzinfo=timezone.utc),
            "signal_type": "spoofing",
            "confidence": Decimal("8.5"),
            "lat": Decimal("18.6298"),
            "lon": Decimal("73.7997"),
            "metadata_json": {"receiver": {"fix": True}},
        }
        fields.update(overrides)
        return GnssObservation(**fields)


if __name__ == "__main__":
    unittest.main()
