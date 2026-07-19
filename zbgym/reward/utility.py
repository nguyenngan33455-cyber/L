"""Utility rewards for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from zbgym.reward.base import (
    Reward,
    RewardConfig,
    reward_registry,
)
from zbgym.constants import DEFAULT_ARENA_WIDTH, DEFAULT_ARENA_HEIGHT

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class DeathPenaltyConfig(RewardConfig):
    """Configuration for death penalty."""

    death_penalty: float = -10.0
    death_multiplier: float = 1.0


class DeathPenalty(Reward):
    """
    Penalty for dying.

    Components:
    - death_penalty: Large negative reward when dying
    """

    config: DeathPenaltyConfig
    _was_alive: bool = True

    def __init__(self, config: DeathPenaltyConfig | None = None) -> None:
        self.config = config or DeathPenaltyConfig()
        self._was_alive = True

    def compute(
        self,
        state: "BattleArenaState",
        prev_state: "BattleArenaState" | None = None,
    ) -> float:
        """Compute death penalty."""
        if prev_state is None:
            return self.process(0.0)

        # Find self character
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        total = 0.0

        if self_char is None:
            # Agent is dead
            if self._was_alive:
                # Died this step
                total = self.config.death_penalty
            self._was_alive = False
        else:
            self._was_alive = True

        return self.process(total)


@dataclass
class IdlePenaltyConfig(RewardConfig):
    """Configuration for idle penalty."""

    idle_penalty: float = -0.01
    movement_threshold: float = 10.0
    combat_threshold: float = 50.0


class IdlePenalty(Reward):
    """
    Penalty for being idle.

    Components:
    - idle_penalty: Small negative reward for not moving or fighting
    """

    config: IdlePenaltyConfig
    _idle_steps: int = 0

    def __init__(self, config: IdlePenaltyConfig | None = None) -> None:
        self.config = config or IdlePenaltyConfig()
        self._idle_steps = 0

    def compute(
        self,
        state: "BattleArenaState",
        prev_state: "BattleArenaState" | None = None,
    ) -> float:
        """Compute idle penalty."""
        # Find self character
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        if self_char is None:
            self._idle_steps = 0
            return self.process(0.0)

        is_idle = True

        # Check if moving
        if self_char.velocity.length > self.config.movement_threshold:
            is_idle = False

        # Check if in combat (dealt/received damage recently)
        if hasattr(state, 'damage_events') and state.damage_events:
            for event in state.damage_events:
                if abs(event.value) > self.config.combat_threshold:
                    is_idle = False
                    break

        if is_idle:
            self._idle_steps += 1
            return self.process(self.config.idle_penalty * self._idle_steps)
        else:
            self._idle_steps = 0
            return self.process(0.0)


# Register rewards
reward_registry.register("death_penalty", DeathPenalty)
reward_registry.register("idle_penalty", IdlePenalty)
