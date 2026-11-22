"""REST controllers for stored GNSS observations."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from models import GnssObservation
from schemas import ObservationListQuery, ObservationPage, ObservationResponse
from services.observations import ObservationService

router = APIRouter(prefix="/observations", tags=["observations"])


def get_observation_service(request: Request) -> ObservationService:
    """Retrieve the application service initialized during app lifespan."""
    return request.app.state.observation_service


def _response_from_model(observation: GnssObservation) -> ObservationResponse:
    return ObservationResponse(
        id=observation.id,
        node_id=observation.node_id,
        timestamp=observation.timestamp,
        signal_type=observation.signal_type,
        confidence=float(observation.confidence),
        coordinates={"lat": float(observation.lat), "lon": float(observation.lon)},
        metadata=observation.metadata_json,
    )


@router.get("", response_model=ObservationPage)
def list_observations(
    query: Annotated[ObservationListQuery, Depends()],
    service: Annotated[ObservationService, Depends(get_observation_service)],
) -> ObservationPage:
    """List observations by optional node, signal type, and observation time."""
    observations = service.list_observations(query)
    return ObservationPage(
        items=[_response_from_model(observation) for observation in observations],
        limit=query.limit,
        offset=query.offset,
    )


@router.get("/{observation_id}", response_model=ObservationResponse)
def get_observation(
    observation_id: UUID,
    service: Annotated[ObservationService, Depends(get_observation_service)],
) -> ObservationResponse:
    """Retrieve a single stored observation by its database identifier."""
    return _response_from_model(service.get_observation(observation_id))
