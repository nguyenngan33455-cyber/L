"""Health observation for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from zbgym.constants import MAX_ENERGY, MAX_HEALTH, MAX_SHIELD
from zbgym.observation.base import (
    Observation,
    ObservationConfig,
    observation_registry,
)

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class HealthObservationConfig(ObservationConfig):
    """Configuration for health observation."""

    include_health: bool = True
    include_shield: bool = True
    include_energy: bool = True


class HealthObservation(Observation):
    """
    Observation for character health, shield, and energy.

    Output dimensions:
    - health (normalized 0-1)
    - shield (normalized 0-1)
    - energy (normalized 0-1)
    - health_percent (health / max_health)
    """

    config: HealthObservationConfig

    def __init__(self, config: HealthObservationConfig | None = None) -> None:
        self.config = config or HealthObservationConfig()
        self._names = ["health", "shield", "energy", "health_percent"]

    @property
    def names(self) -> list[str]:
        return self._names

    def get_dimension(self) -> int:
        """Get observation dimension."""
        dim = 0
        if self.config.include_health:
            dim += 1
        if self.config.include_shield:
            dim += 1
        if self.config.include_energy:
            dim += 1
        if self.config.include_health:  # health_percent
            dim += 1
        return dim

    def compute(self, state: BattleArenaState) -> NDArray[np.float32]:
        """Compute health observation."""
        # Get first alive character as "self"
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        if self_char is None:
            return np.zeros(self.get_dimension(), dtype=np.float32)

        values = []

        if self.config.include_health:
            values.append(self_char.health / MAX_HEALTH)

        if self.config.include_shield:
            values.append(self_char.shield / MAX_SHIELD)

        if self.config.include_energy:
            values.append(self_char.energy / MAX_ENERGY)

        if self.config.include_health:
            values.append(self_char.health / MAX_HEALTH)  # health_percent

        data = np.array(values, dtype=np.float32)
        return self.normalize(data)


# Register observation
observation_registry.register("health", HealthObservation)
