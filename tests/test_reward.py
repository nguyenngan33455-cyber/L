"""Tests for ZBGym reward system."""

import pytest
import numpy as np
from zbgym.reward import (
    RewardBuilder,
    RewardBuilderConfig,
    SurvivalReward,
    KillReward,
    DeathPenalty,
    IdlePenalty,
)
from zbgym.env.battle_arena import BattleArenaState, CharacterState
from zbgym.physics.vector import Vector2D


@pytest.fixture
def mock_state():
    """Create a mock game state."""
    state = BattleArenaState(
        tick=100,
        match_active=True,
        safe_zone_center=Vector2D(1000, 750),
        safe_zone_radius=800.0,
        danger_zone_radius=1000.0,
    )

    state.characters["player_1"] = CharacterState(
        id="player_1",
        position=Vector2D(900, 700),
        velocity=Vector2D(100, 50),
        health=80.0,
        shield=30.0,
        energy=60.0,
        is_alive=True,
        team="red",
    )
    state.characters["enemy_1"] = CharacterState(
        id="enemy_1",
        position=Vector2D(1200, 800),
        health=100.0,
        is_alive=True,
        team="blue",
    )

    return state


class TestSurvivalReward:
    """Tests for SurvivalReward."""

    def test_reward_creation(self):
        """Test creating a survival reward."""
        reward = SurvivalReward()
        assert reward is not None

    def test_compute_survival(self, mock_state):
        """Test computing survival reward."""
        reward = SurvivalReward()
        value = reward.compute(mock_state)

        assert isinstance(value, float)
        assert value > 0  # Should get positive reward for being alive


class TestKillReward:
    """Tests for KillReward."""

    def test_reward_creation(self):
        """Test creating a kill reward."""
        reward = KillReward()
        assert reward is not None

    def test_compute_no_kill(self, mock_state):
        """Test computing reward with no kill."""
        reward = KillReward()
        value = reward.compute(mock_state, mock_state)  # Same state = no kill

        assert value == 0.0


class TestDeathPenalty:
    """Tests for DeathPenalty."""

    def test_reward_creation(self):
        """Test creating a death penalty."""
        reward = DeathPenalty()
        assert reward is not None

    def test_compute_alive(self, mock_state):
        """Test computing penalty when alive."""
        reward = DeathPenalty()
        value = reward.compute(mock_state)

        assert value == 0.0  # No penalty when alive


class TestIdlePenalty:
    """Tests for IdlePenalty."""

    def test_reward_creation(self):
        """Test creating an idle penalty."""
        reward = IdlePenalty()
        assert reward is not None

    def test_compute_no_idle(self, mock_state):
        """Test computing penalty when moving."""
        reward = IdlePenalty()
        value = reward.compute(mock_state)

        # Character has velocity > threshold, should not be idle
        assert value == 0.0


class TestRewardBuilder:
    """Tests for RewardBuilder."""

    def test_builder_creation(self):
        """Test creating a reward builder."""
        config = RewardBuilderConfig(
            reward_types=["survival"]
        )
        builder = RewardBuilder(config=config)

        assert builder is not None
        assert len(builder.reward_types) > 0

    def test_build_reward(self, mock_state):
        """Test building complete reward."""
        config = RewardBuilderConfig(
            reward_types=["survival", "death_penalty"]
        )
        builder = RewardBuilder(config=config)

        result = builder.build(mock_state)

        assert result.total is not None
        assert isinstance(result.components, dict)

    def test_add_reward(self):
        """Test adding reward to builder."""
        config = RewardBuilderConfig(reward_types=[])
        builder = RewardBuilder(config=config)

        initial_count = len(builder.reward_types)
        builder.add_reward("survival")
        assert len(builder.reward_types) > initial_count

    def test_remove_reward(self):
        """Test removing reward from builder."""
        config = RewardBuilderConfig(reward_types=["survival"])
        builder = RewardBuilder(config=config)

        initial_count = len(builder.reward_types)
        builder.remove_reward("survival")
        assert len(builder.reward_types) < initial_count

    def test_set_weight(self):
        """Test setting reward weight."""
        config = RewardBuilderConfig(reward_types=["survival"])
        builder = RewardBuilder(config=config)

        builder.set_weight("survival", 2.0)
        weights = builder.get_weights()
        assert "SurvivalReward" in weights
        assert weights["SurvivalReward"] == 2.0

    def test_reset(self):
        """Test resetting builder."""
        config = RewardBuilderConfig(reward_types=["survival"])
        builder = RewardBuilder(config=config)

        builder.add_reward("kill")
        builder.reset()
        assert len(builder.reward_types) == 1

    def test_build_with_previous_state(self, mock_state):
        """Test building reward with previous state."""
        config = RewardBuilderConfig(reward_types=["survival", "death_penalty"])
        builder = RewardBuilder(config=config)

        result = builder.build(mock_state, mock_state)
        assert result.total is not None
