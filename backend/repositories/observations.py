"""Repository operations for persisted GNSS observations."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from models import GnssObservation


class ObservationRepository:
    """Store and retrieve validated observations within a caller-managed session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, observation: Mapping[str, Any]) -> GnssObservation:
        """Stage a schema-validated observation for insertion and return its model."""
        timestamp = _parse_timestamp(observation["timestamp"])
        stored_observation = GnssObservation(
            node_id=observation["node_id"],
            timestamp=timestamp,
            signal_type=observation["signal_type"],
            confidence=Decimal(str(observation["confidence"])),
            lat=Decimal(str(observation["coordinates"]["lat"])),
            lon=Decimal(str(observation["coordinates"]["lon"])),
            metadata_json=observation["metadata"],
        )
        self._session.add(stored_observation)
        self._session.flush()
        return stored_observation

    def get_by_id(self, observation_id: UUID) -> GnssObservation | None:
        """Return one persisted observation by its primary key."""
        return self._session.scalar(
            select(GnssObservation).where(GnssObservation.id == observation_id)
        )

    def list(
        self,
        *,
        node_id: str | None = None,
        signal_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[GnssObservation]:
        """List observations with supported filters and stable pagination order."""
        statement = select(GnssObservation)
        if node_id is not None:
            statement = statement.where(GnssObservation.node_id == node_id)
        if signal_type is not None:
            statement = statement.where(GnssObservation.signal_type == signal_type)
        if start_time is not None:
            statement = statement.where(GnssObservation.timestamp >= start_time)
        if end_time is not None:
            statement = statement.where(GnssObservation.timestamp <= end_time)
        statement = statement.order_by(desc(GnssObservation.timestamp), desc(GnssObservation.id))
        statement = statement.limit(limit).offset(offset)
        return list(self._session.scalars(statement))


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an RFC3339 date-time string")
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return timestamp
