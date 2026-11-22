"""Non-secret application configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiSettings:
    """HTTP settings that are safe to load while constructing the app."""

    cors_origins: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "ApiSettings":
        origins = tuple(
            origin.strip()
            for origin in os.getenv("HAZEGUARD_CORS_ORIGINS", "").split(",")
            if origin.strip()
        )
        return cls(cors_origins=origins)
