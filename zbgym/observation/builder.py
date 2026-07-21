"""Observation builder for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from zbgym.observation.base import (
    Observation,
    ObservationRegistry,
    ObservationResult,
)

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class ObservationBuilderConfig:
    """Configuration for the observation builder."""

    observation_types: list[str] = field(
        default_factory=lambda: ["health", "position", "enemies", "zone"]
    )
    include_items: bool = False
    include_projectiles: bool = False
    normalize_all: bool = True


class ObservationBuilder:
    """
    Builds complete observations from game state.

    Combines multiple observation plugins into a single observation vector.
    Automatically computes total dimension and names.
    """

    def __init__(
        self,
        config: ObservationBuilderConfig | None = None,
        registry: ObservationRegistry | None = None,
    ) -> None:
        """
        Initialize observation builder.

        Args:
            config: Builder configuration
            registry: Observation registry to use
        """
        self.config = config or ObservationBuilderConfig()
        self.registry = registry
        if self.registry is None:
            # Create new registry and register default observations
            self.registry = ObservationRegistry()
            self._register_default_observations()
        self._observations: list[Observation] = []
        self._build_observations()

    def _register_default_observations(self) -> None:
        """Register default observations."""
        from zbgym.observation.enemy import EnemyObservation
        from zbgym.observation.health import HealthObservation
        from zbgym.observation.position import PositionObservation
        from zbgym.observation.zone import ZoneObservation

        self.registry.register("health", HealthObservation)
        self.registry.register("position", PositionObservation)
        self.registry.register("enemies", EnemyObservation)
        self.registry.register("zone", ZoneObservation)

    def _build_observations(self) -> None:
        """Build observation list from configuration."""
        self._observations.clear()

        for obs_id in self.config.observation_types:
            obs = self.registry.create(obs_id)
            if obs is not None:
                obs.config.normalize = self.config.normalize_all
                self._observations.append(obs)

    @property
    def dimension(self) -> int:
        """Total dimension of the observation."""
        return sum(obs.get_dimension() for obs in self._observations)

    @property
    def names(self) -> list[str]:
        """All observation names."""
        names = []
        for obs in self._observations:
            names.extend(obs.names)
        return names

    @property
    def observation_shapes(self) -> dict[str, int]:
        """Shapes of each observation component."""
        shapes = {}
        for obs in self._observations:
            obs_name = obs.__class__.__name__.replace("Observation", "").lower()
            shapes[obs_name] = obs.get_dimension()
        return shapes

    def build(self, state: BattleArenaState) -> ObservationResult:
        """
        Build complete observation from game state.

        Args:
            state: Current game state

        Returns:
            Observation result with data and metadata
        """
        all_data = []
        all_names = []

        for obs in self._observations:
            data = obs.compute(state)
            all_data.append(data)
            all_names.extend(obs.names)

        # Concatenate all observations
        if all_data:
            combined = np.concatenate(all_data)
        else:
            combined = np.zeros(self.dimension, dtype=np.float32)

        # Ensure correct dimension
        if len(combined) < self.dimension:
            combined = np.pad(combined, (0, self.dimension - len(combined)))
        elif len(combined) > self.dimension:
            combined = combined[: self.dimension]

        return ObservationResult(
            data=combined,
            dimension=self.dimension,
            names=all_names,
            config=self._get_config_dict(),
        )

    def build_dict(self, state: BattleArenaState) -> dict[str, float]:
        """
        Build observation as dictionary.

        Args:
            state: Current game state

        Returns:
            Dictionary mapping names to values
        """
        result = self.build(state)
        return dict(zip(result.names, result.data.tolist()))

    def _get_config_dict(self) -> dict[str, Any]:
        """Get configuration as dictionary."""
        return {
            "observation_types": self.config.observation_types,
            "include_items": self.config.include_items,
            "include_projectiles": self.config.include_projectiles,
            "normalize_all": self.config.normalize_all,
            "total_dimension": self.dimension,
            "observation_shapes": self.observation_shapes,
        }

    def add_observation(self, obs_id: str) -> bool:
        """
        Add an observation type.

        Args:
            obs_id: ID of observation to add

        Returns:
            True if observation was added
        """
        obs = self.registry.create(obs_id)
        if obs is None:
            return False

        # Check if already added
        for existing in self._observations:
            if type(existing).__name__ == type(obs).__name__:
                return False

        obs.config.normalize = self.config.normalize_all
        self._observations.append(obs)
        return True

    def remove_observation(self, obs_id: str) -> bool:
        """
        Remove an observation type.

        Args:
            obs_id: ID of observation to remove

        Returns:
            True if observation was removed
        """
        for i, obs in enumerate(self._observations):
            if type(obs).__name__.lower().replace("observation", "") == obs_id:
                self._observations.pop(i)
                return True
        return False

    def reset(self) -> None:
        """Reset and rebuild observations."""
        self._build_observations()

    def get_space(self) -> dict[str, Any]:
        """
        Get observation space information.

        Returns:
            Dictionary with space information
        """
        return {
            "shape": (self.dimension,),
            "dtype": np.float32,
            "low": -np.inf,
            "high": np.inf,
            "names": self.names,
            "shapes": self.observation_shapes,
        }


# Create default registry
_default_registry: ObservationRegistry | None = None


def get_default_registry() -> ObservationRegistry:
    """Get or create default observation registry."""
    global _default_registry
    if _default_registry is None:
        # Import and register default observations
        _default_registry = ObservationRegistry()
    return _default_registry
