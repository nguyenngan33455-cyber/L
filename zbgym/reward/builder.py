"""Reward builder for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from zbgym.reward.base import (
    Reward,
    RewardConfig,
    RewardResult,
    RewardRegistry,
    reward_registry,
)

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class RewardBuilderConfig:
    """Configuration for the reward builder."""

    reward_types: list[str] = field(
        default_factory=lambda: ["survival", "kill", "death_penalty"]
    )
    default_weights: dict[str, float] = field(default_factory=lambda: {
        "survival": 1.0,
        "kill": 1.0,
        "damage": 1.0,
        "death_penalty": 1.0,
        "idle_penalty": 0.5,
    })
    normalize_total: bool = False


class RewardBuilder:
    """
    Builds complete rewards from game state.

    Combines multiple reward plugins into a single reward value.
    Supports weighted composition and normalization.
    """

    def __init__(
        self,
        config: RewardBuilderConfig | None = None,
        registry: RewardRegistry | None = None,
    ) -> None:
        """
        Initialize reward builder.

        Args:
            config: Builder configuration
            registry: Reward registry to use
        """
        self.config = config or RewardBuilderConfig()
        self.registry = registry
        if self.registry is None:
            self.registry = reward_registry
            self._register_default_rewards()
        self._rewards: list[Reward] = []
        self._build_rewards()

    def _register_default_rewards(self) -> None:
        """Register default rewards."""
        from zbgym.reward.survival import SurvivalReward
        from zbgym.reward.combat import KillReward, DamageReward
        from zbgym.reward.utility import DeathPenalty, IdlePenalty

        self.registry.register("survival", SurvivalReward)
        self.registry.register("kill", KillReward)
        self.registry.register("damage", DamageReward)
        self.registry.register("death_penalty", DeathPenalty)
        self.registry.register("idle_penalty", IdlePenalty)

    def _build_rewards(self) -> None:
        """Build reward list from configuration."""
        self._rewards.clear()

        for reward_id in self.config.reward_types:
            reward = self.registry.create(reward_id)
            if reward is not None:
                # Apply weight from config
                if reward_id in self.config.default_weights:
                    reward.config.weight = self.config.default_weights[reward_id]
                self._rewards.append(reward)

    @property
    def reward_types(self) -> list[str]:
        """List of reward types being used."""
        return [type(r).__name__.replace("Reward", "").lower() for r in self._rewards]

    def build(
        self,
        state: "BattleArenaState",
        prev_state: "BattleArenaState | None" = None,
    ) -> RewardResult:
        """
        Build complete reward from game state.

        Args:
            state: Current game state
            prev_state: Previous game state

        Returns:
            Reward result with components
        """
        components = {}
        total = 0.0

        for reward in self._rewards:
            reward_value = reward.compute(state, prev_state)
            reward_name = type(reward).__name__.replace("Reward", "").lower()
            components[reward_name] = reward_value
            total += reward_value

        # Normalize if requested
        if self.config.normalize_total:
            total = float(__import__("numpy").tanh(total))

        return RewardResult(
            total=total,
            components=components,
            info=self._get_info(),
        )

    def _get_info(self) -> dict[str, Any]:
        """Get reward info."""
        return {
            "reward_types": self.reward_types,
            "weights": {type(r).__name__: r.config.weight for r in self._rewards},
        }

    def reset(self) -> None:
        """Reset all rewards."""
        self._build_rewards()

    def get_weights(self) -> dict[str, float]:
        """Get current reward weights."""
        return {type(r).__name__: r.config.weight for r in self._rewards}

    def set_weight(self, reward_id: str, weight: float) -> bool:
        """Set weight for a reward type."""
        for reward in self._rewards:
            reward_name = type(reward).__name__.lower()
            if reward_id in reward_name or reward_name in reward_id:
                reward.config.weight = weight
                return True
        return False

    def add_reward(self, reward_id: str) -> bool:
        """Add a reward type."""
        reward = self.registry.create(reward_id)
        if reward is None:
            return False

        # Check if already added
        for existing in self._rewards:
            if type(existing).__name__ == type(reward).__name__:
                return False

        if reward_id in self.config.default_weights:
            reward.config.weight = self.config.default_weights[reward_id]
        self._rewards.append(reward)
        return True

    def remove_reward(self, reward_id: str) -> bool:
        """Remove a reward type."""
        for i, reward in enumerate(self._rewards):
            reward_name = type(reward).__name__.lower()
            if reward_id in reward_name or reward_name in reward_id:
                self._rewards.pop(i)
                return True
        return False
