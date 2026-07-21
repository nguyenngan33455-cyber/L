"""Observation system for ZBGym."""

from zbgym.observation.base import (
    Observation,
    ObservationConfig,
    ObservationRegistry,
    ObservationResult,
    observation_registry,
)
from zbgym.observation.builder import (
    ObservationBuilder,
    ObservationBuilderConfig,
    get_default_registry,
)
from zbgym.observation.enemy import EnemyObservation, EnemyObservationConfig
from zbgym.observation.health import HealthObservation, HealthObservationConfig
from zbgym.observation.position import PositionObservation, PositionObservationConfig
from zbgym.observation.zone import ZoneObservation, ZoneObservationConfig

__all__ = [
    # Base
    "Observation",
    "ObservationConfig",
    "ObservationResult",
    "ObservationRegistry",
    "observation_registry",
    # Builder
    "ObservationBuilder",
    "ObservationBuilderConfig",
    "get_default_registry",
    # Specific observations
    "HealthObservation",
    "HealthObservationConfig",
    "PositionObservation",
    "PositionObservationConfig",
    "EnemyObservation",
    "EnemyObservationConfig",
    "ZoneObservation",
    "ZoneObservationConfig",
]
