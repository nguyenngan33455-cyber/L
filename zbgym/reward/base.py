"""Base classes for ZBGym reward system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class RewardConfig:
    """Base configuration for rewards."""

    enabled: bool = True
    scale: float = 1.0
    weight: float = 1.0
    normalize: bool = False
    clip_min: float = -float("inf")
    clip_max: float = float("inf")


@dataclass
class RewardResult:
    """Result from computing a reward."""

    total: float
    components: dict[str, float]
    info: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "components": self.components,
            "info": self.info,
        }


class Reward(ABC):
    """
    Base class for all rewards.

    Rewards are plugins that compute scalar rewards from the game state.
    Each reward type defines what events to track and how to compute rewards.
    """

    config: RewardConfig

    @abstractmethod
    def compute(
        self,
        state: BattleArenaState,
        prev_state: BattleArenaState | None = None,
    ) -> float:
        """
        Compute reward from game state.

        Args:
            state: Current game state
            prev_state: Previous game state (for computing deltas)

        Returns:
            Reward value
        """

    def process(self, raw_reward: float) -> float:
        """Process raw reward with scaling and clipping."""
        reward = raw_reward * self.config.scale * self.config.weight

        if self.config.normalize:
            reward = np.tanh(reward)

        reward = np.clip(reward, self.config.clip_min, self.config.clip_max)
        return float(reward)

    def validate(self) -> bool:
        """Validate reward configuration."""
        return self.config.scale >= 0 and self.config.weight >= 0


@dataclass
class RewardEvent:
    """Event data for reward computation."""

    event_type: str
    agent_id: str
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)


class RewardRegistry:
    """Registry for reward plugins."""

    def __init__(self) -> None:
        self._rewards: dict[str, type[Reward]] = {}

    def register(self, reward_id: str, reward_class: type[Reward]) -> type[Reward]:
        """Register a reward class."""
        self._rewards[reward_id] = reward_class
        return reward_class

    def get(self, reward_id: str) -> type[Reward] | None:
        """Get a reward class by ID."""
        return self._rewards.get(reward_id)

    def create(self, reward_id: str, **kwargs) -> Reward | None:
        """Create a reward instance."""
        reward_class = self.get(reward_id)
        if reward_class is None:
            return None
        return reward_class(**kwargs)

    def list_rewards(self) -> list[str]:
        """List all registered reward IDs."""
        return list(self._rewards.keys())

    def unregister(self, reward_id: str) -> bool:
        """Unregister a reward."""
        if reward_id in self._rewards:
            del self._rewards[reward_id]
            return True
        return False


# Global registry
reward_registry = RewardRegistry()
