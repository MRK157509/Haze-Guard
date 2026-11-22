"""Command-line entry point for the HazeGuard GNSS software simulator."""

from __future__ import annotations

import itertools
import logging
import time

from .config import SimulatorSettings, parse_settings
from .generator import SimulationGenerator
from .publisher import MqttObservationPublisher


def run(settings: SimulatorSettings) -> int:
    """Run until interrupted, duration expires, or the requested count is published."""
    generator = SimulationGenerator(seed=settings.seed)
    publisher = MqttObservationPublisher(settings)
    started_at = time.monotonic()
    published_count = 0
    nodes = itertools.cycle(settings.node_ids)
    try:
        publisher.connect()
        logging.info("Simulator started: nodes=%s scenario=%s", ",".join(settings.node_ids), settings.scenario)
        while True:
            if settings.duration_seconds is not None and time.monotonic() - started_at >= settings.duration_seconds:
                logging.info("Simulator duration reached")
                break
            if settings.max_observations is not None and published_count >= settings.max_observations:
                logging.info("Simulator published requested observation count")
                break
            node_id = next(nodes)
            observation = generator.generate(node_id, settings.scenario)
            if observation is None:
                logging.info("Normal operation for %s: no detection observation emitted", node_id)
            elif publisher.publish(observation):
                published_count += 1
            time.sleep(settings.interval_seconds)
    except KeyboardInterrupt:
        logging.info("Simulator stopped by Ctrl+C")
    except ConnectionError as exc:
        logging.error("Simulator could not start: %s", exc)
        return 1
    finally:
        publisher.close()
    return 0


def main() -> int:
    """Parse configuration and configure concise console diagnostics."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return run(parse_settings())


if __name__ == "__main__":
    raise SystemExit(main())
