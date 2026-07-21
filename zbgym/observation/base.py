"""Base classes for ZBGym observation system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


T = TypeVar("T")


@dataclass
class ObservationConfig:
    """Base configuration for observations."""

    enabled: bool = True
    normalize: bool = True
    scale: float = 1.0
    offset: float = 0.0


@dataclass
class ObservationResult:
    """Result from an observation builder."""

    data: NDArray[np.float32]
    dimension: int
    names: list[str]
    config: dict[str, Any]

    @property
    def shape(self) -> tuple[int, ...]:
        """Get observation shape."""
        return self.data.shape


class Observation(ABC):
    """
    Base class for all observations.

    Observations are plugins that extract information from the game state.
    Each observation type defines what data to extract and how to normalize it.
    """

    config: ObservationConfig

    @property
    def dimension(self) -> int:
        """Get observation dimension."""
        return self.get_dimension()

    @abstractmethod
    def compute(self, state: BattleArenaState) -> NDArray[np.float32]:
        """
        Compute observation from game state.

        Args:
            state: Current game state

        Returns:
            Observation array
        """

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of this observation."""

    def normalize(self, data: NDArray[np.float32]) -> NDArray[np.float32]:
        """Normalize observation data."""
        if not self.config.normalize:
            return data

        data = data * self.config.scale + self.config.offset

        # Clip to reasonable range
        return np.clip(data, -10.0, 10.0)

    def validate(self) -> bool:
        """Validate observation configuration."""
        return True


class ObservationRegistry:
    """Registry for observation plugins."""

    def __init__(self) -> None:
        self._observations: dict[str, type[Observation]] = {}

    def register(
        self,
        obs_id: str,
        obs_class: type[Observation],
    ) -> type[Observation]:
        """
        Register an observation class.

        Args:
            obs_id: Unique identifier for the observation
            obs_class: Observation class to register

        Returns:
            The registered class
        """
        self._observations[obs_id] = obs_class
        return obs_class

    def get(self, obs_id: str) -> type[Observation] | None:
        """Get an observation class by ID."""
        return self._observations.get(obs_id)

    def create(self, obs_id: str, **kwargs) -> Observation | None:
        """Create an observation instance."""
        obs_class = self.get(obs_id)
        if obs_class is None:
            return None
        return obs_class(**kwargs)

    def list_observations(self) -> list[str]:
        """List all registered observation IDs."""
        return list(self._observations.keys())

    def unregister(self, obs_id: str) -> bool:
        """Unregister an observation."""
        if obs_id in self._observations:
            del self._observations[obs_id]
            return True
        return False


# Global registry
observation_registry = ObservationRegistry()
