"""Application service for observation persistence and retrieval."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import session_scope
from models import GnssObservation
from repositories.observations import ObservationRepository
from schemas import ObservationInput, ObservationListQuery


class ObservationNotFound(LookupError):
    """Raised when no observation exists for a requested primary key."""


class DatabaseUnavailable(RuntimeError):
    """Raised when a database operation cannot be completed safely."""


class ObservationService:
    """Coordinate observation validation and database repository work."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._logger = logging.getLogger(__name__)

    def persist_from_mqtt(self, observation: Mapping[str, Any]) -> GnssObservation:
        """Apply Pydantic validation before persisting an MQTT observation."""
        validated = ObservationInput.model_validate(observation)
        try:
            with session_scope(self._session_factory) as session:
                return ObservationRepository(session).add(validated.repository_payload())
        except SQLAlchemyError as exc:
            self._logger.error("Database failure while persisting a validated observation")
            raise DatabaseUnavailable("observation persistence is unavailable") from exc

    def list_observations(self, query: ObservationListQuery) -> list[GnssObservation]:
        """Return one filtered, paginated page of observations."""
        try:
            with session_scope(self._session_factory) as session:
                return ObservationRepository(session).list(
                    node_id=query.node_id,
                    signal_type=query.signal_type,
                    start_time=query.start_time,
                    end_time=query.end_time,
                    limit=query.limit,
                    offset=query.offset,
                )
        except SQLAlchemyError as exc:
            self._logger.error("Database failure while listing observations")
            raise DatabaseUnavailable("observation retrieval is unavailable") from exc

    def get_observation(self, observation_id: UUID) -> GnssObservation:
        """Return one stored observation or raise ``ObservationNotFound``."""
        try:
            with session_scope(self._session_factory) as session:
                observation = ObservationRepository(session).get_by_id(observation_id)
        except SQLAlchemyError as exc:
            self._logger.error("Database failure while retrieving an observation")
            raise DatabaseUnavailable("observation retrieval is unavailable") from exc
        if observation is None:
            raise ObservationNotFound(str(observation_id))
        return observation

    def check_health(self) -> None:
        """Verify the configured database is reachable without exposing details."""
        try:
            with session_scope(self._session_factory) as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            self._logger.error("Database health check failed")
            raise DatabaseUnavailable("database is unavailable") from exc
