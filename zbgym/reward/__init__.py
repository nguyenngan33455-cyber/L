"""Reward system for ZBGym."""

from zbgym.reward.base import (
    Reward,
    RewardConfig,
    RewardEvent,
    RewardRegistry,
    RewardResult,
    reward_registry,
)
from zbgym.reward.builder import (
    RewardBuilder,
    RewardBuilderConfig,
)
from zbgym.reward.combat import DamageReward, DamageRewardConfig, KillReward, KillRewardConfig
from zbgym.reward.survival import SurvivalReward, SurvivalRewardConfig
from zbgym.reward.utility import DeathPenalty, DeathPenaltyConfig, IdlePenalty, IdlePenaltyConfig

__all__ = [
    # Base
    "Reward",
    "RewardConfig",
    "RewardResult",
    "RewardEvent",
    "RewardRegistry",
    "reward_registry",
    # Builder
    "RewardBuilder",
    "RewardBuilderConfig",
    # Specific rewards
    "SurvivalReward",
    "SurvivalRewardConfig",
    "KillReward",
    "KillRewardConfig",
    "DamageReward",
    "DamageRewardConfig",
    "DeathPenalty",
    "DeathPenaltyConfig",
    "IdlePenalty",
    "IdlePenaltyConfig",
]
