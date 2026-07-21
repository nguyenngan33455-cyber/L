"""Survival reward for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from zbgym.constants import MAX_HEALTH
from zbgym.reward.base import (
    Reward,
    RewardConfig,
    reward_registry,
)

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class SurvivalRewardConfig(RewardConfig):
    """Configuration for survival reward."""

    alive_reward: float = 0.1
    health_bonus: float = 0.01
    low_health_penalty: float = -0.5
    low_health_threshold: float = 0.25


class SurvivalReward(Reward):
    """
    Reward for staying alive.

    Components:
    - alive_reward: Small positive reward for being alive
    - health_bonus: Reward proportional to health percentage
    - low_health_penalty: Penalty when health is low
    """

    config: SurvivalRewardConfig

    def __init__(self, config: SurvivalRewardConfig | None = None) -> None:
        self.config = config or SurvivalRewardConfig()

    def compute(
        self,
        state: BattleArenaState,
        prev_state: BattleArenaState | None = None,
    ) -> float:
        """Compute survival reward."""
        # Find self character
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        if self_char is None:
            return self.process(0.0)

        total = self.config.alive_reward

        # Health bonus
        health_ratio = self_char.health / MAX_HEALTH
        total += self.config.health_bonus * health_ratio

        # Low health penalty
        if health_ratio < self.config.low_health_threshold:
            total += self.config.low_health_penalty * (
                1.0 - health_ratio / self.config.low_health_threshold
            )

        return self.process(total)


# Register reward
reward_registry.register("survival", SurvivalReward)
