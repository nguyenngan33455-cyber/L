"""Position and movement observations for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from zbgym.observation.base import (
    Observation,
    ObservationConfig,
    observation_registry,
)
from zbgym.constants import DEFAULT_ARENA_WIDTH, DEFAULT_ARENA_HEIGHT

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class PositionObservationConfig(ObservationConfig):
    """Configuration for position observation."""

    include_position: bool = True
    include_velocity: bool = True
    include_rotation: bool = False
    include_speed: bool = True


class PositionObservation(Observation):
    """
    Observation for position and movement.

    Output dimensions:
    - position_x (normalized)
    - position_y (normalized)
    - velocity_x (normalized)
    - velocity_y (normalized)
    - speed (normalized)
    """

    config: PositionObservationConfig

    def __init__(self, config: PositionObservationConfig | None = None) -> None:
        self.config = config or PositionObservationConfig()
        self._names = ["pos_x", "pos_y", "vel_x", "vel_y", "speed"]
        self._update_names()

    @property
    def names(self) -> list[str]:
        return self._names

    def _update_names(self) -> None:
        """Update names based on config."""
        self._names = []
        if self.config.include_position:
            self._names.extend(["pos_x", "pos_y"])
        if self.config.include_velocity:
            self._names.extend(["vel_x", "vel_y"])
        if self.config.include_speed:
            self._names.append("speed")

    def get_dimension(self) -> int:
        """Get observation dimension."""
        dim = 0
        if self.config.include_position:
            dim += 2
        if self.config.include_velocity:
            dim += 2
        if self.config.include_speed:
            dim += 1
        return dim

    def compute(self, state: "BattleArenaState") -> NDArray[np.float32]:
        """Compute position observation."""
        # Get first alive character
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        if self_char is None:
            return np.zeros(self.get_dimension(), dtype=np.float32)

        values = []
        arena_width = DEFAULT_ARENA_WIDTH
        arena_height = DEFAULT_ARENA_HEIGHT

        if self.config.include_position:
            values.append(self_char.position.x / arena_width)
            values.append(self_char.position.y / arena_height)

        if self.config.include_velocity:
            values.append(self_char.velocity.x / 1000.0)  # normalize by max speed
            values.append(self_char.velocity.y / 1000.0)

        if self.config.include_speed:
            speed = self_char.velocity.length
            values.append(speed / 1000.0)

        data = np.array(values, dtype=np.float32)
        return self.normalize(data)


# Register observation
observation_registry.register("position", PositionObservation)
