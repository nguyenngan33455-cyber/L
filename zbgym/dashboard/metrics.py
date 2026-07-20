"""Dashboard metrics definitions for ZBGym.

This module defines all metrics that can be published
to the Dashboard during training.
"""

from __future__ import annotations

import psutil
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.dashboard.models import MetricsData


class Metrics:
    """Metrics factory for creating standardized metrics.

    This class provides methods to create properly formatted
    metrics data for common training and system metrics.

    Example:
        metrics = Metrics.collect(session_id="abc123")
        # or
        metrics = Metrics.training(reward=10.5, loss=0.5)
    """

    @staticmethod
    def training(
        session_id: str,
        episode: int | None = None,
        timestep: int | None = None,
        reward: float | None = None,
        loss: float | None = None,
        entropy: float | None = None,
        learning_rate: float | None = None,
        episode_length: int | None = None,
        **custom_metrics: float,
    ) -> MetricsData:
        """Create training metrics.

        Args:
            session_id: Session ID.
            episode: Current episode number.
            timestep: Current global timestep.
            reward: Episode reward.
            loss: Training loss.
            entropy: Policy entropy.
            learning_rate: Current learning rate.
            episode_length: Length of episode.
            **custom_metrics: Additional custom metrics.

        Returns:
            MetricsData instance.
        """
        from zbgym.dashboard.models import MetricsData, MetricType

        metrics = MetricsData(session_id=session_id)
        metrics.episode = episode
        metrics.timestep = timestep

        if reward is not None:
            metrics.add(MetricType.EPISODE_REWARD, reward)
        if loss is not None:
            metrics.add(MetricType.LOSS, loss)
        if entropy is not None:
            metrics.add(MetricType.ENTROPY, entropy)
        if learning_rate is not None:
            metrics.add(MetricType.LEARNING_RATE, learning_rate)
        if episode_length is not None:
            metrics.add(MetricType.EPISODE_LENGTH, episode_length)

        # Add custom metrics
        for name, value in custom_metrics.items():
            metrics.add(name, value)

        return metrics

    @staticmethod
    def ppo(
        session_id: str,
        timestep: int | None = None,
        policy_loss: float | None = None,
        value_loss: float | None = None,
        entropy: float | None = None,
        kl_divergence: float | None = None,
        advantage: float | None = None,
        **custom_metrics: float,
    ) -> MetricsData:
        """Create PPO-specific metrics.

        Args:
            session_id: Session ID.
            timestep: Current global timestep.
            policy_loss: Policy loss value.
            value_loss: Value function loss.
            entropy: Policy entropy.
            kl_divergence: KL divergence between old and new policy.
            advantage: Advantage estimate.
            **custom_metrics: Additional custom metrics.

        Returns:
            MetricsData instance.
        """
        from zbgym.dashboard.models import MetricsData, MetricType

        metrics = MetricsData(session_id=session_id)
        metrics.timestep = timestep

        if policy_loss is not None:
            metrics.add(MetricType.POLICY_LOSS, policy_loss)
        if value_loss is not None:
            metrics.add(MetricType.VALUE_LOSS, value_loss)
        if entropy is not None:
            metrics.add(MetricType.ENTROPY, entropy)
        if kl_divergence is not None:
            metrics.add(MetricType.KL_DIVERGENCE, kl_divergence)
        if advantage is not None:
            metrics.add(MetricType.ADVANTAGE, advantage)

        for name, value in custom_metrics.items():
            metrics.add(name, value)

        return metrics

    @staticmethod
    def system(
        session_id: str,
        cpu_percent: float | None = None,
        memory_mb: float | None = None,
        gpu_percent: float | None = None,
        gpu_memory_mb: float | None = None,
    ) -> MetricsData:
        """Create system metrics.

        Args:
            session_id: Session ID.
            cpu_percent: CPU usage percentage.
            memory_mb: Memory usage in MB.
            gpu_percent: GPU usage percentage.
            gpu_memory_mb: GPU memory usage in MB.

        Returns:
            MetricsData instance.
        """
        from zbgym.dashboard.models import MetricsData, MetricType

        metrics = MetricsData(session_id=session_id)

        # Auto-collect if not provided
        if cpu_percent is None:
            cpu_percent = psutil.cpu_percent()
        if memory_mb is None:
            memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)

        metrics.add(MetricType.CPU_PERCENT, cpu_percent)
        metrics.add(MetricType.MEMORY_MB, memory_mb)

        if gpu_percent is not None:
            metrics.add(MetricType.GPU_PERCENT, gpu_percent)
        if gpu_memory_mb is not None:
            metrics.add(MetricType.GPU_MEMORY_MB, gpu_memory_mb)

        return metrics

    @staticmethod
    def performance(
        session_id: str,
        fps: float | None = None,
        tps: float | None = None,
        env_steps_per_second: float | None = None,
    ) -> MetricsData:
        """Create performance metrics.

        Args:
            session_id: Session ID.
            fps: Frames per second (if rendering).
            tps: Training steps per second.
            env_steps_per_second: Environment steps per second.

        Returns:
            MetricsData instance.
        """
        from zbgym.dashboard.models import MetricsData, MetricType

        metrics = MetricsData(session_id=session_id)

        if fps is not None:
            metrics.add(MetricType.FPS, fps)
        if tps is not None:
            metrics.add(MetricType.TPS, tps)
        if env_steps_per_second is not None:
            metrics.add(MetricType.ENV_STEPS_PER_SECOND, env_steps_per_second)

        return metrics

    @staticmethod
    def reward_stats(
        session_id: str,
        mean: float | None = None,
        std: float | None = None,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> MetricsData:
        """Create reward statistics metrics.

        Args:
            session_id: Session ID.
            mean: Mean reward.
            std: Standard deviation of rewards.
            min_val: Minimum reward.
            max_val: Maximum reward.

        Returns:
            MetricsData instance.
        """
        from zbgym.dashboard.models import MetricsData, MetricType

        metrics = MetricsData(session_id=session_id)

        if mean is not None:
            metrics.add(MetricType.REWARD_MEAN, mean)
        if std is not None:
            metrics.add(MetricType.REWARD_STD, std)
        if min_val is not None:
            metrics.add(MetricType.REWARD_MIN, min_val)
        if max_val is not None:
            metrics.add(MetricType.REWARD_MAX, max_val)

        return metrics

    @staticmethod
    def timing(
        session_id: str,
        elapsed_time: float | None = None,
        eta: float | None = None,
    ) -> MetricsData:
        """Create timing metrics.

        Args:
            session_id: Session ID.
            elapsed_time: Elapsed training time in seconds.
            eta: Estimated time to completion in seconds.

        Returns:
            MetricsData instance.
        """
        from zbgym.dashboard.models import MetricsData, MetricType

        metrics = MetricsData(session_id=session_id)

        if elapsed_time is None:
            elapsed_time = time.time()

        metrics.add(MetricType.ELAPSED_TIME, elapsed_time)
        if eta is not None:
            metrics.add(MetricType.ETA, eta)

        return metrics

    @staticmethod
    def collect(
        session_id: str,
        episode: int | None = None,
        timestep: int | None = None,
        reward: float | None = None,
        loss: float | None = None,
        fps: float | None = None,
        **custom_metrics: float,
    ) -> MetricsData:
        """Collect common metrics in one call.

        This is a convenience method that collects training,
        system, and performance metrics together.

        Args:
            session_id: Session ID.
            episode: Current episode number.
            timestep: Current global timestep.
            reward: Episode reward.
            loss: Training loss.
            fps: Frames per second.
            **custom_metrics: Additional custom metrics.

        Returns:
            MetricsData instance with all collected metrics.
        """
        from zbgym.dashboard.models import MetricsData, MetricType

        metrics = MetricsData(session_id=session_id)
        metrics.episode = episode
        metrics.timestep = timestep

        if reward is not None:
            metrics.add(MetricType.EPISODE_REWARD, reward)
        if loss is not None:
            metrics.add(MetricType.LOSS, loss)
        if fps is not None:
            metrics.add(MetricType.FPS, fps)

        # Auto-collect system metrics
        metrics.add(MetricType.CPU_PERCENT, psutil.cpu_percent())
        metrics.add(
            MetricType.MEMORY_MB, psutil.Process().memory_info().rss / (1024 * 1024)
        )

        # Add elapsed time
        metrics.add(MetricType.ELAPSED_TIME, time.time())

        # Add custom metrics
        for name, value in custom_metrics.items():
            metrics.add(name, value)

        return metrics


class MetricsAggregator:
    """Aggregates metrics over multiple samples.

    Useful for computing running averages and other
    aggregated statistics.

    Example:
        aggregator = MetricsAggregator(window_size=100)
        aggregator.add({"reward": 10.0, "loss": 0.5})
        aggregator.add({"reward": 11.0, "loss": 0.4})
        stats = aggregator.get()
    """

    def __init__(self, window_size: int = 100) -> None:
        """Initialize aggregator.

        Args:
            window_size: Number of samples to keep for rolling window.
        """
        self.window_size = window_size
        self._samples: list[dict[str, float]] = []
        self._totals: dict[str, float] = {}

    def add(self, metrics: dict[str, float]) -> None:
        """Add a metrics sample.

        Args:
            metrics: Dictionary of metric values.
        """
        self._samples.append(metrics)

        # Update totals
        for key, value in metrics.items():
            self._totals[key] = self._totals.get(key, 0.0) + value

        # Maintain window size
        if len(self._samples) > self.window_size:
            removed = self._samples.pop(0)
            for key, value in removed.items():
                self._totals[key] -= value

    def get(self) -> dict[str, float]:
        """Get aggregated statistics.

        Returns:
            Dictionary with mean values for each metric.
        """
        if not self._samples:
            return {}

        count = len(self._samples)
        return {key: total / count for key, total in self._totals.items()}

    def reset(self) -> None:
        """Reset the aggregator."""
        self._samples.clear()
        self._totals.clear()

    @property
    def count(self) -> int:
        """Get number of samples in window."""
        return len(self._samples)
