"""Tests for ZBGym trainer."""

import pytest
from zbgym.trainer import (
    TrainerConfig,
    TrainingStats,
    PPOTrainer,
    CheckpointCallback,
    EvaluationCallback,
    ProgressCallback,
    EarlyStoppingCallback,
    BaseCallback,
)


class TestTrainerConfig:
    """Tests for TrainerConfig."""

    def test_config_creation(self):
        """Test creating trainer config."""
        config = TrainerConfig()
        assert config.env_id == "BattleArena-v1"
        assert config.total_timesteps == 1_000_000

    def test_config_custom(self):
        """Test custom config."""
        config = TrainerConfig(
            env_id="TestEnv-v1",
            total_timesteps=50000,
            learning_rate=1e-3,
        )
        assert config.env_id == "TestEnv-v1"
        assert config.total_timesteps == 50000
        assert config.learning_rate == 1e-3


class TestTrainingStats:
    """Tests for TrainingStats."""

    def test_stats_creation(self):
        """Test creating training stats."""
        stats = TrainingStats()
        assert stats.episode_count == 0
        assert stats.total_timesteps == 0

    def test_mean_reward(self):
        """Test mean reward calculation."""
        stats = TrainingStats()
        stats.episode_rewards = [1.0, 2.0, 3.0]
        assert stats.mean_reward == 2.0

    def test_mean_length(self):
        """Test mean length calculation."""
        stats = TrainingStats()
        stats.episode_lengths = [100, 200, 300]
        assert stats.mean_length == 200.0

    def test_to_dict(self):
        """Test converting to dictionary."""
        stats = TrainingStats()
        d = stats.to_dict()
        assert "episode_count" in d
        assert "mean_reward" in d


class TestPPOTrainer:
    """Tests for PPOTrainer."""

    def test_trainer_creation(self):
        """Test creating PPO trainer."""
        trainer = PPOTrainer()
        assert trainer is not None
        assert trainer.config is not None

    def test_trainer_with_config(self):
        """Test creating trainer with config."""
        config = TrainerConfig(total_timesteps=10000)
        trainer = PPOTrainer(config=config)
        assert trainer.config.total_timesteps == 10000

    def test_trainer_directories(self):
        """Test trainer directories."""
        trainer = PPOTrainer(
            model_save_dir="./test_models",
            log_dir="./test_logs",
        )
        assert trainer.model_save_dir.name == "test_models"
        assert trainer.log_dir.name == "test_logs"


class TestCallbacks:
    """Tests for callbacks."""

    def test_checkpoint_callback(self):
        """Test checkpoint callback."""
        callback = CheckpointCallback(save_freq=5000)
        assert callback.save_freq == 5000

    def test_progress_callback(self):
        """Test progress callback."""
        callback = ProgressCallback(total_timesteps=10000)
        assert callback.total_timesteps == 10000

    def test_early_stopping_callback(self):
        """Test early stopping callback."""
        callback = EarlyStoppingCallback(patience=5, target_reward=100.0)
        assert callback.patience == 5
        assert callback.target_reward == 100.0

    def test_base_callback(self):
        """Test base callback."""
        callback = BaseCallback()
        assert callback.num_timesteps == 0
        assert callback._on_step() is True
