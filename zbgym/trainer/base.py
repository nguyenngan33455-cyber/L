"""Base trainer class for ZBGym."""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from zbgym.dashboard.manager import DashboardManager, DashboardManagerConfig

logger = logging.getLogger(__name__)


@dataclass
class TrainerConfig:
    """Configuration for trainer."""

    env_id: str = "BattleArena-v1"
    total_timesteps: int = 1_000_000
    num_envs: int = 4
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    ent_coef: float = 0.01
    n_steps: int = 2048
    batch_size: int = 64
    n_epochs: int = 10
    clip_range: float = 0.2
    clip_range_vf: float | None = None
    normalize_advantage: bool = True
    normalize_observations: bool = True
    use_sde: bool = False
    sde_sample_freq: int = -1
    max_grad_norm: float = 0.5
    target_kl: float | None = None
    verbose: int = 1
    seed: int | None = None
    device: str = "auto"


@dataclass
class TrainingStats:
    """Statistics from training."""

    episode_count: int = 0
    total_timesteps: int = 0
    fps: int = 0
    time_elapsed: float = 0.0
    episode_rewards: list[float] = field(default_factory=list)
    episode_lengths: list[int] = field(default_factory=list)
    losses: list[dict[str, float]] = field(default_factory=list)

    @property
    def mean_reward(self) -> float:
        """Get mean episode reward."""
        if not self.episode_rewards:
            return 0.0
        return float(np.mean(self.episode_rewards[-100:]))

    @property
    def mean_length(self) -> float:
        """Get mean episode length."""
        if not self.episode_lengths:
            return 0.0
        return float(np.mean(self.episode_lengths[-100:]))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "episode_count": self.episode_count,
            "total_timesteps": self.total_timesteps,
            "fps": self.fps,
            "time_elapsed": self.time_elapsed,
            "mean_reward": self.mean_reward,
            "mean_length": self.mean_length,
        }


class BaseTrainer(ABC):
    """
    Base trainer class for RL algorithms.

    Provides common functionality for training RL agents:
    - Checkpoint management
    - Progress tracking
    - Logging
    - Evaluation
    - Dashboard integration (optional)
    """

    def __init__(
        self,
        config: TrainerConfig | None = None,
        model_save_dir: str | Path = "./models",
        log_dir: str | Path = "./logs",
        dashboard: DashboardManagerConfig | DashboardManager | bool | None = None,
        dashboard_url: str | None = None,
        dashboard_api_key: str | None = None,
        dashboard_publish_interval: int = 100,
    ) -> None:
        """
        Initialize trainer.

        Args:
            config: Training configuration
            model_save_dir: Directory to save models
            log_dir: Directory for logs
            dashboard: Dashboard configuration (DashboardManagerConfig,
                     DashboardManager instance, bool, or None)
            dashboard_url: Dashboard server URL (if dashboard=True)
            dashboard_api_key: Dashboard API key (if dashboard=True)
            dashboard_publish_interval: Publish metrics every N timesteps
        """
        self.config = config or TrainerConfig()
        self.model_save_dir = Path(model_save_dir)
        self.log_dir = Path(log_dir)
        self.model_save_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.stats = TrainingStats()
        self.start_time: float = 0.0
        self.model: Any = None

        # Initialize dashboard manager
        self._init_dashboard(
            dashboard,
            dashboard_url,
            dashboard_api_key,
            dashboard_publish_interval,
        )

    def _init_dashboard(
        self,
        dashboard: DashboardManagerConfig | DashboardManager | bool | None,
        dashboard_url: str | None,
        dashboard_api_key: str | None,
        dashboard_publish_interval: int,
    ) -> None:
        """Initialize dashboard manager.

        Args:
            dashboard: Dashboard configuration.
            dashboard_url: Dashboard URL.
            dashboard_api_key: Dashboard API key.
            dashboard_publish_interval: Publish interval.
        """
        if dashboard is None or dashboard is False:
            self._dashboard: DashboardManager | None = None
            return

        if isinstance(dashboard, DashboardManager):
            self._dashboard = dashboard
            return

        if isinstance(dashboard, DashboardManagerConfig):
            self._dashboard = DashboardManager(dashboard)
            return

        # dashboard is True or a dict-like config
        if dashboard is True or isinstance(dashboard, dict):
            config = DashboardManagerConfig(
                enabled=True,
                url=dashboard_url or "http://localhost:8080",
                api_key=dashboard_api_key,
                publish_interval=dashboard_publish_interval,
            )
            self._dashboard = DashboardManager(config)
            return

        self._dashboard = None

    @property
    def dashboard(self) -> DashboardManager | None:
        """Get dashboard manager."""
        return self._dashboard

    @abstractmethod
    def setup(self) -> None:
        """Setup training environment and model."""
        pass

    @abstractmethod
    def train(self, callback: Callable | None = None) -> Any:
        """
        Train the model.

        Args:
            callback: Training callback

        Returns:
            Trained model
        """
        pass

    @abstractmethod
    def predict(self, observation: np.ndarray, deterministic: bool = True) -> tuple:
        """
        Make a prediction.

        Args:
            observation: Environment observation
            deterministic: Use deterministic policy

        Returns:
            Action and state
        """
        pass

    def save(self, path: str | Path | None = None) -> Path:
        """
        Save the model.

        Args:
            path: Path to save model (auto-generates if None)

        Returns:
            Path where model was saved
        """
        if path is None:
            timestamp = int(time.time())
            path = self.model_save_dir / f"model_{timestamp}.zip"

        path = Path(path)
        self.model.save(str(path.with_suffix(".zip")))
        return path

    def load(self, path: str | Path) -> Any:
        """
        Load a model.

        Args:
            path: Path to model

        Returns:
            Loaded model
        """
        path = Path(path)
        return self.model.load(str(path.with_suffix(".zip")))

    def get_stats(self) -> TrainingStats:
        """Get training statistics."""
        return self.stats

    def reset_stats(self) -> None:
        """Reset training statistics."""
        self.stats = TrainingStats()

    def export_model(self, path: str | Path, format: str = "onnx") -> Path:
        """
        Export model to different format.

        Args:
            path: Path to export to
            format: Export format (onnx, tflite, etc.)

        Returns:
            Path where model was exported
        """
        # This is a placeholder - actual implementation depends on SB3 version
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # For now, just save the zip model
        return self.save(path)

    def get_best_checkpoint(self) -> Path | None:
        """Get path to best checkpoint based on mean reward."""
        checkpoints = list(self.model_save_dir.glob("*.zip"))
        if not checkpoints:
            return None

        best_reward = float("-inf")
        best_path = None

        for ckpt in checkpoints:
            stats_file = ckpt.with_suffix(".stats.json")
            if stats_file.exists():
                with open(stats_file) as f:
                    stats = json.load(f)
                    reward = stats.get("mean_reward", 0)
                    if reward > best_reward:
                        best_reward = reward
                        best_path = ckpt

        return best_path
