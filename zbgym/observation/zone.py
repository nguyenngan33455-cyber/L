"""Zone observation for ZBGym."""

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

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class ZoneObservationConfig(ObservationConfig):
    """Configuration for zone observation."""

    include_distance: bool = True
    include_direction: bool = True
    include_in_zone: bool = True
    include_danger_level: bool = True


class ZoneObservation(Observation):
    """
    Observation for safe zone status.

    Output dimensions:
    - distance_to_center
    - direction_x
    - direction_y
    - in_safe_zone (0 or 1)
    - danger_level (0-1)
    - zone_radius
    """

    config: ZoneObservationConfig

    def __init__(self, config: ZoneObservationConfig | None = None) -> None:
        self.config = config or ZoneObservationConfig()
        self._names = ["zone_dist", "zone_dir_x", "zone_dir_y", "in_zone", "danger_level", "zone_radius"]
        self._update_names()

    @property
    def names(self) -> list[str]:
        return self._names

    def _update_names(self) -> None:
        """Update names based on config."""
        self._names = []
        if self.config.include_distance:
            self._names.append("zone_dist")
        if self.config.include_direction:
            self._names.extend(["zone_dir_x", "zone_dir_y"])
        if self.config.include_in_zone:
            self._names.append("in_zone")
        if self.config.include_danger_level:
            self._names.append("danger_level")
        self._names.append("zone_radius")

    def get_dimension(self) -> int:
        """Get observation dimension."""
        dim = 1  # zone_radius always included
        if self.config.include_distance:
            dim += 1
        if self.config.include_direction:
            dim += 2
        if self.config.include_in_zone:
            dim += 1
        if self.config.include_danger_level:
            dim += 1
        return dim

    def compute(self, state: "BattleArenaState") -> NDArray[np.float32]:
        """Compute zone observation."""
        # Get self character
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        values = []

        # Zone radius (always included)
        zone_radius = state.safe_zone_radius if state.safe_zone_radius > 0 else 1000.0
        values.append(zone_radius / 1000.0)

        if self_char is None:
            # Return zeros with correct shape
            return np.zeros(self.get_dimension(), dtype=np.float32)

        # Distance to zone center
        distance = self_char.position.distance_to(state.safe_zone_center)
        direction = (state.safe_zone_center - self_char.position).normalized

        if self.config.include_distance:
            values.append(distance / zone_radius)

        if self.config.include_direction:
            values.append(direction.x)
            values.append(direction.y)

        if self.config.include_in_zone:
            in_zone = 1.0 if distance <= state.safe_zone_radius else 0.0
            values.append(in_zone)

        if self.config.include_danger_level:
            # Danger increases as you move away from center
            danger = min(1.0, distance / state.danger_zone_radius) if state.danger_zone_radius > 0 else 0.0
            values.append(danger)

        data = np.array(values, dtype=np.float32)
        return self.normalize(data)


# Register observation
observation_registry.register("zone", ZoneObservation)
