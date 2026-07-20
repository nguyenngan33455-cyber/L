"""Dashboard callback for ZBGym trainers.

This module provides a callback that integrates DashboardManager
with the Stable-Baselines3 training loop.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import numpy as np

from zbgym.dashboard.manager import DashboardManager, DashboardManagerConfig

if TYPE_CHECKING:
    from zbgym.trainer.callbacks import BaseCallback


class DashboardCallback:
    """Callback to publish training metrics to Dashboard.

    This callback automatically publishes training metrics to the
    Dashboard at configured intervals without blocking training.

    It integrates with Stable-Baselines3's callback system and
    publishes:
    - Training metrics (reward, loss, entropy, etc.)
    - System metrics (CPU, memory, GPU)
    - Training progress events

    Example:
        dashboard = DashboardManager(DashboardManagerConfig(
            enabled=True,
            url="https://dashboard.zbgym.dev",
            api_key="zb_xxx"
        ))

        callback = DashboardCallback(dashboard)

        model.learn(
            total_timesteps=1000000,
            callback=callback
        )
    """

    def __init__(
        self,
        dashboard_manager: DashboardManager,
        publish_system_metrics: bool = False,
        publish_freq: int = 100,
    ) -> None:
        """Initialize Dashboard callback.

        Args:
            dashboard_manager: DashboardManager instance.
            publish_system_metrics: Whether to publish system metrics.
            publish_freq: Frequency of metric publishing.
        """
        self._dashboard = dashboard_manager
        self._publish_system_metrics = publish_system_metrics
        self._publish_freq = publish_freq
        self._last_episode_reward: float = 0
        self._episode_count: int = 0
        self._training_start_time: float = 0
        self._num_timesteps: int = 0
        self._model: Any = None
        self._locals: dict = {}
        self._globals: dict = {}

    @property
    def num_timesteps(self) -> int:
        """Get current number of timesteps."""
        return self._num_timesteps

    @num_timesteps.setter
    def num_timesteps(self, value: int) -> None:
        """Set number of timesteps."""
        self._num_timesteps = value

    @property
    def model(self) -> Any:
        """Get the model."""
        return self._model

    @model.setter
    def model(self, value: Any) -> None:
        """Set the model."""
        self._model = value

    def __call__(
        self,
        locals: dict | None = None,
        globals: dict | None = None,
    ) -> bool:
        """Call the callback (for SB3 integration).

        Args:
            locals: Local variables from training loop.
            globals: Global variables from training loop.

        Returns:
            True to continue training.
        """
        if locals is not None:
            self._locals = locals
        if globals is not None:
            self._globals = globals
            self._num_timesteps = globals.get("n_callbacks", 0)

        return self._on_step()

    def _on_step(self) -> bool:
        """Called at each training step.

        Returns:
            True to continue training.
        """
        # Publish episode rewards if available
        if "infos" in self._locals:
            for info in self._locals.get("infos", []):
                if "episode" in info:
                    episode_info = info["episode"]
                    self._episode_count += 1

                    self._dashboard.publish_metrics(
                        episode=self._episode_count,
                        reward=float(episode_info.get("r", 0)),
                    )

                    self._last_episode_reward = float(episode_info.get("r", 0))

        # Publish at intervals or when timestep crosses threshold
        timestep = self._num_timesteps

        if timestep % self._publish_freq == 0:
            # Get metrics from SB3 logger if available
            if self._model is not None:
                self._publish_sb3_metrics()

            # Publish system metrics
            if self._publish_system_metrics:
                self._publish_system_info()

        return True

    def on_training_start(self, locals: dict | None = None, globals: dict | None = None) -> None:
        """Called at training start.

        Args:
            locals: Local variables from training loop.
            globals: Global variables from training loop.
        """
        self._training_start_time = time.time()
        if locals is not None:
            self._locals = locals
        if globals is not None:
            self._globals = globals

        # Start dashboard session if enabled
        if self._dashboard.is_enabled:
            self._dashboard.start_session()

    def on_training_end(self, locals: dict | None = None, globals: dict | None = None) -> None:
        """Called at training end.

        Args:
            locals: Local variables from training loop.
            globals: Global variables from training loop.
        """
        if locals is not None:
            self._locals = locals
        if globals is not None:
            self._globals = globals

        if self._dashboard.is_enabled:
            duration = time.time() - self._training_start_time

            self._dashboard.publish_event(
                "training_finished",
                {
                    "duration": duration,
                    "total_timesteps": self._num_timesteps,
                    "total_episodes": self._episode_count,
                    "final_reward": self._last_episode_reward,
                },
            )

            self._dashboard.finish_session(
                status="finished",
                final_metrics={
                    "total_timesteps": self._num_timesteps,
                    "total_episodes": self._episode_count,
                    "final_reward": self._last_episode_reward,
                    "duration": duration,
                },
            )

    def _publish_sb3_metrics(self) -> None:
        """Publish metrics from Stable-Baselines3 model."""
        try:
            # Access SB3's loggerRollout ep_rew_mean, ep_len_mean, etc
            if hasattr(self._model, "logger"):
                logger = self._model.logger

                # Try to get metrics from logger
                if hasattr(logger, "name_to_value"):
                    metrics = logger.name_to_value

                    kwargs = {}

                    # Map common SB3 metrics
                    if "rollout/ep_rew_mean" in metrics:
                        kwargs["reward_mean"] = metrics["rollout/ep_rew_mean"]
                    if "rollout/ep_len_mean" in metrics:
                        kwargs["episode_length"] = metrics["rollout/ep_len_mean"]
                    if "train/loss" in metrics:
                        kwargs["loss"] = metrics["train/loss"]
                    if "train/ent_coef" in metrics:
                        kwargs["entropy_coef"] = metrics["train/ent_coef"]
                    if "train/lr" in metrics:
                        kwargs["learning_rate"] = metrics["train/lr"]

                    if kwargs:
                        self._dashboard.publish_metrics(
                            timestep=self._num_timesteps,
                            episode=self._episode_count,
                            **kwargs,
                        )

        except Exception:
            pass

    def _publish_system_info(self) -> None:
        """Publish system metrics."""
        try:
            import psutil

            process = psutil.Process()

            kwargs = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_mb": process.memory_info().rss / (1024 * 1024),
            }

            # Try to get GPU metrics if available
            try:
                import torch

                if torch.cuda.is_available():
                    kwargs["gpu_memory_mb"] = torch.cuda.memory_allocated() / (1024 * 1024)
                    kwargs["gpu_percent"] = (
                        torch.cuda.memory_allocated() / torch.cuda.get_device_properties(0).total_memory * 100
                        if torch.cuda.is_available()
                        else 0
                    )
            except ImportError:
                pass

            self._dashboard.publish_system_metrics(**kwargs)

        except Exception:
            pass


class DashboardMetricsCallback:
    """Simplified callback for just publishing metrics.

    Use this when you only need basic metrics publishing without
    the overhead of the full DashboardCallback.
    """

    def __init__(
        self,
        dashboard_manager: DashboardManager,
    ) -> None:
        """Initialize.

        Args:
            dashboard_manager: DashboardManager instance.
        """
        self._dashboard = dashboard_manager
        self._episode_count = 0
        self._num_timesteps: int = 0
        self._locals: dict = {}

    @property
    def num_timesteps(self) -> int:
        return self._num_timesteps

    def __call__(self, locals: dict | None = None, globals: dict | None = None) -> bool:
        """Call the callback."""
        if locals is not None:
            self._locals = locals
        if globals is not None:
            self._num_timesteps = globals.get("n_callbacks", 0)
        return self._on_step()

    def _on_step(self) -> bool:
        """Called at each step."""
        # Check for new episodes
        if "infos" in self._locals:
            for info in self._locals.get("infos", []):
                if "episode" in info:
                    episode_info = info["episode"]
                    self._episode_count += 1

                    self._dashboard.publish_metrics(
                        episode=self._episode_count,
                        reward=float(episode_info.get("r", 0)),
                        timestep=self._num_timesteps,
                    )

        return True


class DashboardCheckpointCallback:
    """Callback to notify dashboard when checkpoints are saved.

    This callback wraps CheckpointCallback and notifies the
    Dashboard when a checkpoint is saved.
    """

    def __init__(
        self,
        dashboard_manager: DashboardManager,
        wrapped_callback: Any | None = None,
    ) -> None:
        """Initialize.

        Args:
            dashboard_manager: DashboardManager instance.
            wrapped_callback: Optional callback to wrap (e.g., CheckpointCallback).
        """
        self._dashboard = dashboard_manager
        self._wrapped = wrapped_callback
        self._num_timesteps: int = 0
        self._locals: dict = {}
        self._globals: dict = {}

    @property
    def num_timesteps(self) -> int:
        return self._num_timesteps

    def __call__(self, locals: dict | None = None, globals: dict | None = None) -> bool:
        """Call the callback."""
        if locals is not None:
            self._locals = locals
        if globals is not None:
            self._num_timesteps = globals.get("n_callbacks", 0)
        return self._on_step()

    def _on_step(self) -> bool:
        """Called at each step."""
        # Check if wrapped callback would save
        if self._wrapped is not None and hasattr(self._wrapped, "_on_step"):
            result = self._wrapped._on_step()

            # Check if checkpoint was saved (timestep divisible by save_freq)
            if (
                hasattr(self._wrapped, "save_freq")
                and self._num_timesteps % self._wrapped.save_freq == 0
            ):
                self._dashboard.publish_event(
                    "checkpoint_saved",
                    {
                        "timestep": self._num_timesteps,
                        "path": str(self._wrapped.save_path / f"{self._wrapped.name_prefix}_{self._num_timesteps}"),
                    },
                )

            return result

        return True

    def on_training_start(self, locals: dict | None = None, globals: dict | None = None) -> None:
        """Forward to wrapped callback."""
        if self._wrapped is not None and hasattr(self._wrapped, "on_training_start"):
            self._wrapped.on_training_start(locals, globals)

    def on_training_end(self, locals: dict | None = None, globals: dict | None = None) -> None:
        """Forward to wrapped callback."""
        if self._wrapped is not None and hasattr(self._wrapped, "on_training_end"):
            self._wrapped.on_training_end(locals, globals)
