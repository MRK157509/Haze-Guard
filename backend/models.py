"""SQLAlchemy database models for HazeGuard."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for PostgreSQL persistence models."""


class GnssObservation(Base):
    """A validated GNSS spoofing or jamming observation."""

    __tablename__ = "gnss_observations"
    __table_args__ = (
        CheckConstraint("confidence >= 1 AND confidence <= 10", name="ck_gnss_observations_confidence_range"),
        CheckConstraint(
            "signal_type IN ('spoofing', 'jamming')",
            name="ck_gnss_observations_signal_type",
        ),
        CheckConstraint("lat >= -90 AND lat <= 90", name="ck_gnss_observations_lat_range"),
        CheckConstraint("lon >= -180 AND lon <= 180", name="ck_gnss_observations_lon_range"),
        Index("ix_gnss_observations_timestamp", "timestamp"),
        Index("ix_gnss_observations_node_id", "node_id"),
        Index("ix_gnss_observations_signal_type", "signal_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    node_id: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    lat: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    lon: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False)
