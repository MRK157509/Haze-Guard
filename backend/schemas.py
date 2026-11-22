"""Pydantic schemas for HazeGuard observation and API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SignalType = Literal["spoofing", "jamming"]


class Coordinates(BaseModel):
    """WGS84 decimal-degree coordinates from the approved observation contract."""

    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)


class ObservationInput(BaseModel):
    """A GNSS observation accepted from the MQTT validation boundary."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1)
    timestamp: datetime
    signal_type: SignalType
    confidence: float = Field(ge=1, le=10, allow_inf_nan=False)
    coordinates: Coordinates
    metadata: dict[str, Any]

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_have_timezone(cls, value: datetime) -> datetime:
        """Require a timezone-aware RFC3339 date-time."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value

    def repository_payload(self) -> dict[str, Any]:
        """Return values in the shape expected by the repository layer."""
        return self.model_dump(mode="json")


class ObservationResponse(BaseModel):
    """Public representation of a stored observation."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    node_id: str
    timestamp: datetime
    signal_type: SignalType
    confidence: float
    coordinates: Coordinates
    metadata: dict[str, Any]


class ObservationPage(BaseModel):
    """Offset-paginated collection of stored observations."""

    items: list[ObservationResponse]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class ObservationListQuery(BaseModel):
    """Supported filters for the observation list endpoint."""

    node_id: str | None = Field(default=None, min_length=1)
    signal_type: SignalType | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("start_time", "end_time")
    @classmethod
    def filter_timestamps_must_have_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def start_time_must_not_follow_end_time(self) -> "ObservationListQuery":
        if self.start_time is not None and self.end_time is not None and self.start_time > self.end_time:
            raise ValueError("start_time must be before or equal to end_time")
        return self


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: Literal["ok"]
