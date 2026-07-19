"""Combat rewards for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from zbgym.reward.base import (
    Reward,
    RewardConfig,
    RewardEvent,
    reward_registry,
)
from zbgym.constants import MAX_HEALTH

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState


@dataclass
class KillRewardConfig(RewardConfig):
    """Configuration for kill reward."""

    kill_reward: float = 10.0
    kill_streak_bonus: float = 2.0
    max_streak_bonus: float = 5.0


class KillReward(Reward):
    """
    Reward for eliminating enemies.

    Components:
    - kill_reward: Base reward for a kill
    - kill_streak_bonus: Additional reward for consecutive kills
    """

    config: KillRewardConfig
    _kill_streak: int = 0

    def __init__(self, config: KillRewardConfig | None = None) -> None:
        self.config = config or KillRewardConfig()
        self._kill_streak = 0

    def compute(
        self,
        state: "BattleArenaState",
        prev_state: "BattleArenaState" | None = None,
    ) -> float:
        """Compute kill reward."""
        if prev_state is None:
            return self.process(0.0)

        total = 0.0

        # Find self character
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        if self_char is None:
            return self.process(0.0)

        # Check for kills (enemies that died this step)
        for char_id, char in state.characters.items():
            if char_id in prev_state.characters:
                was_alive = prev_state.characters[char_id].is_alive
                is_dead = not char.is_alive
                was_enemy = char.team != self_char.team

                if was_alive and is_dead and was_enemy:
                    self._kill_streak += 1
                    total += self.config.kill_reward

                    # Kill streak bonus
                    streak = min(self._kill_streak, int(self.config.max_streak_bonus))
                    total += self.config.kill_streak_bonus * streak

        # Reset streak if agent died
        if not self_char.is_alive:
            self._kill_streak = 0

        return self.process(total)


@dataclass
class DamageRewardConfig(RewardConfig):
    """Configuration for damage reward."""

    damage_scale: float = 0.01
    headshot_bonus: float = 0.05
    consecutive_hit_bonus: float = 0.01


class DamageReward(Reward):
    """
    Reward for dealing damage.

    Components:
    - damage_scale: Reward proportional to damage dealt
    - headshot_bonus: Additional reward for headshots
    """

    config: DamageRewardConfig

    def __init__(self, config: DamageRewardConfig | None = None) -> None:
        self.config = config or DamageRewardConfig()
        self._total_damage_dealt: float = 0.0

    def compute(
        self,
        state: "BattleArenaState",
        prev_state: "BattleArenaState" | None = None,
    ) -> float:
        """Compute damage reward."""
        if prev_state is None:
            return self.process(0.0)

        # Find self character
        self_char = None
        for char in state.characters.values():
            if char.is_alive:
                self_char = char
                break

        if self_char is None:
            return self.process(0.0)

        total = 0.0

        # Track damage from damage events in state
        if hasattr(state, 'damage_events') and state.damage_events:
            for event in state.damage_events:
                if event.agent_id == self_char.id:
                    damage = event.value
                    total += damage * self.config.damage_scale

                    if event.metadata.get('headshot', False):
                        total += self.config.headshot_bonus

        return self.process(total)


# Register rewards
reward_registry.register("kill", KillReward)
reward_registry.register("damage", DamageReward)
