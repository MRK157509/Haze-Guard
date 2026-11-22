"""FastAPI application composition and lifecycle management."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from api.observations import router as observations_router
from config import ApiSettings
from database import create_session_factory
from mqtt_client import MqttObservationConsumer
from mqtt_config import MqttSettings
from mqtt_validation import MAX_OBSERVATION_PAYLOAD_BYTES
from schemas import HealthResponse
from services.observations import DatabaseUnavailable, ObservationNotFound, ObservationService

logger = logging.getLogger(__name__)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": {"code": code, "message": message}})


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject HTTP request bodies above the approved observation payload limit."""

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Any:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > MAX_OBSERVATION_PAYLOAD_BYTES:
                    return _error_response(413, "payload_too_large", "Request body exceeds 64 KiB")
            except ValueError:
                return _error_response(400, "invalid_content_length", "Content-Length must be an integer")

        if len(await request.body()) > MAX_OBSERVATION_PAYLOAD_BYTES:
            return _error_response(413, "payload_too_large", "Request body exceeds 64 KiB")
        return await call_next(request)


def create_app(
    *,
    observation_service: ObservationService | None = None,
    enable_mqtt: bool = True,
) -> FastAPI:
    """Build the HazeGuard API without connecting until application startup."""
    settings = ApiSettings.from_environment()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        service = observation_service or ObservationService(create_session_factory())
        app.state.observation_service = service
        mqtt_consumer: MqttObservationConsumer | None = None
        mqtt_client: Any | None = None
        if enable_mqtt:
            mqtt_consumer = MqttObservationConsumer(MqttSettings.from_environment(), service.persist_from_mqtt)
            mqtt_client = mqtt_consumer.start()
        try:
            yield
        finally:
            if mqtt_consumer is not None and mqtt_client is not None:
                mqtt_consumer.stop(mqtt_client)

    app = FastAPI(title="HazeGuard API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(PayloadSizeLimitMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=False,
            allow_methods=["GET"],
            allow_headers=["Accept", "Content-Type"],
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return _error_response(422, "validation_error", "Request validation failed")

    @app.exception_handler(ObservationNotFound)
    async def observation_not_found_handler(_request: Request, _exc: ObservationNotFound) -> JSONResponse:
        return _error_response(404, "observation_not_found", "Observation was not found")

    @app.exception_handler(DatabaseUnavailable)
    async def database_unavailable_handler(_request: Request, _exc: DatabaseUnavailable) -> JSONResponse:
        return _error_response(503, "database_unavailable", "Observation data is temporarily unavailable")

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health(request: Request) -> HealthResponse:
        """Return success only when the configured database is reachable."""
        request.app.state.observation_service.check_health()
        return HealthResponse(status="ok")

    app.include_router(observations_router)
    return app


app = create_app()
