"""Enemy observation for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from zbgym.constants import MAX_HEALTH
from zbgym.observation.base import (
    Observation,
    ObservationConfig,
    observation_registry,
)

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class EnemyObservationConfig(ObservationConfig):
    """Configuration for enemy observation."""

    max_enemies: int = 8
    include_health: bool = True
    include_distance: bool = True
    include_relative_position: bool = True
    vision_range: float = 500.0


class EnemyObservation(Observation):
    """
    Observation for nearby enemies.

    Output dimensions (per enemy):
    - relative_x
    - relative_y
    - distance
    - health

    Plus:
    - num_visible_enemies
    - nearest_enemy_distance
    """

    config: EnemyObservationConfig

    def __init__(self, config: EnemyObservationConfig | None = None) -> None:
        self.config = config or EnemyObservationConfig()
        self._names: list[str] = []
        self._update_names()

    @property
    def names(self) -> list[str]:
        return self._names

    def _update_names(self) -> None:
        """Update names based on config."""
        self._names = ["num_visible_enemies", "nearest_distance"]
        for i in range(self.config.max_enemies):
            prefix = f"enemy_{i}"
            self._names.append(f"{prefix}_rel_x")
            self._names.append(f"{prefix}_rel_y")
            if self.config.include_distance:
                self._names.append(f"{prefix}_dist")
            if self.config.include_health:
                self._names.append(f"{prefix}_health")

    def get_dimension(self) -> int:
        """Get observation dimension."""
        base = 2  # num_visible_enemies, nearest_distance
        per_enemy = 0
        if self.config.include_relative_position:
            per_enemy += 2
        if self.config.include_distance:
            per_enemy += 1
        if self.config.include_health:
            per_enemy += 1
        return base + self.config.max_enemies * per_enemy

    def compute(self, state: BattleArenaState) -> NDArray[np.float32]:
        """Compute enemy observation."""
        # Get self character
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        if self_char is None:
            return np.zeros(self.get_dimension(), dtype=np.float32)

        # Find all enemies
        enemies = []
        for char in state.characters.values():
            if char.id != self_char.id and char.is_alive:
                distance = self_char.position.distance_to(char.position)
                if distance <= self.config.vision_range:
                    enemies.append((char, distance))

        # Sort by distance
        enemies.sort(key=lambda x: x[1])

        # Build observation
        values = []
        values.append(len(enemies))  # num_visible_enemies
        nearest_dist = enemies[0][1] / self.config.vision_range if len(enemies) > 0 else 1.0
        values.append(nearest_dist)  # nearest_distance

        # Add enemy data
        for i in range(self.config.max_enemies):
            if i < len(enemies):
                char, distance = enemies[i]
                rel_x = (char.position.x - self_char.position.x) / self.config.vision_range
                rel_y = (char.position.y - self_char.position.y) / self.config.vision_range

                if self.config.include_relative_position:
                    values.append(np.clip(rel_x, -1.0, 1.0))
                    values.append(np.clip(rel_y, -1.0, 1.0))
                if self.config.include_distance:
                    values.append(distance / self.config.vision_range)
                if self.config.include_health:
                    values.append(char.health / MAX_HEALTH)
            else:
                # Padding
                if self.config.include_relative_position:
                    values.extend([0.0, 0.0])
                if self.config.include_distance:
                    values.append(0.0)
                if self.config.include_health:
                    values.append(0.0)

        data = np.array(values, dtype=np.float32)
        return self.normalize(data)


# Register observation
observation_registry.register("enemies", EnemyObservation)
