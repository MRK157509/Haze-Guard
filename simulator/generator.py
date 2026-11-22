"""Reproducible software-only GNSS spoofing and jamming simulation."""

from __future__ import annotations

import random
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

Clock = Callable[[], datetime]


class SimulationGenerator:
    """Generate only contract-valid simulated detection observations.

    A normal scenario advances stable software positions but emits no detection.
    The approved contract has no ``normal`` signal type, so publishing one would
    violate the API and MQTT schema rather than represent normal operation.
    """

    def __init__(self, seed: int | None = None, clock: Clock | None = None) -> None:
        self._random = random.Random(seed)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._positions: dict[str, tuple[float, float]] = {}

    def generate(self, node_id: str, scenario: str) -> dict[str, Any] | None:
        """Advance a node simulation and return one valid detection, if any."""
        baseline_lat, baseline_lon = self._next_baseline_position(node_id)
        if scenario == "normal":
            return None
        if scenario == "mixed":
            scenario = self._random.choice(("spoofing", "jamming"))
        if scenario == "spoofing":
            return self._spoofing_observation(node_id, baseline_lat, baseline_lon)
        if scenario == "jamming":
            return self._jamming_observation(node_id, baseline_lat, baseline_lon)
        raise ValueError(f"unsupported simulation scenario: {scenario}")

    def _next_baseline_position(self, node_id: str) -> tuple[float, float]:
        if node_id not in self._positions:
            # Simulated WGS84 positions are deliberately software-generated.
            self._positions[node_id] = (
                round(self._random.uniform(-65, 65), 6),
                round(self._random.uniform(-170, 170), 6),
            )
        lat, lon = self._positions[node_id]
        lat = _bounded(lat + self._random.uniform(-0.00004, 0.00004), -89.999, 89.999)
        lon = _bounded(lon + self._random.uniform(-0.00004, 0.00004), -179.999, 179.999)
        self._positions[node_id] = (lat, lon)
        return lat, lon

    def _spoofing_observation(self, node_id: str, baseline_lat: float, baseline_lon: float) -> dict[str, Any]:
        offset_lat = self._random.uniform(-0.025, 0.025)
        offset_lon = self._random.uniform(-0.025, 0.025)
        reported_lat = _bounded(baseline_lat + offset_lat, -90, 90)
        reported_lon = _bounded(baseline_lon + offset_lon, -180, 180)
        return self._observation(
            node_id=node_id,
            signal_type="spoofing",
            confidence=round(self._random.uniform(6.8, 9.9), 1),
            coordinates=(reported_lat, reported_lon),
            baseline=(baseline_lat, baseline_lon),
            details={
                "anomaly": "simulated_position_shift",
                "position_offset_meters": round(((offset_lat**2 + offset_lon**2) ** 0.5) * 111_000, 1),
                "receiver_fix": "inconsistent",
            },
        )

    def _jamming_observation(self, node_id: str, baseline_lat: float, baseline_lon: float) -> dict[str, Any]:
        return self._observation(
            node_id=node_id,
            signal_type="jamming",
            confidence=round(self._random.uniform(5.5, 9.6), 1),
            coordinates=(baseline_lat, baseline_lon),
            baseline=(baseline_lat, baseline_lon),
            details={
                "anomaly": "simulated_signal_degradation",
                "receiver_fix": "degraded",
                "estimated_cn0_db_hz": round(self._random.uniform(15, 27), 1),
                "satellites_tracked": self._random.randint(0, 5),
            },
        )

    def _observation(
        self,
        *,
        node_id: str,
        signal_type: str,
        confidence: float,
        coordinates: tuple[float, float],
        baseline: tuple[float, float],
        details: dict[str, Any],
    ) -> dict[str, Any]:
        timestamp = self._clock()
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("simulation clock must return a timezone-aware timestamp")
        return {
            "node_id": node_id,
            "timestamp": timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "signal_type": signal_type,
            "confidence": confidence,
            "coordinates": {"lat": round(coordinates[0], 6), "lon": round(coordinates[1], 6)},
            "metadata": {
                "simulation": {
                    "is_simulated": True,
                    "scenario": signal_type,
                    "baseline_coordinates": {"lat": round(baseline[0], 6), "lon": round(baseline[1], 6)},
                    "normal_operation": "software baseline tracked before simulated detection",
                },
                "gnss": details,
            },
        }


def _bounded(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))
