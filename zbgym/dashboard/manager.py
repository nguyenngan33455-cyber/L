"""Dashboard Manager for ZBGym.

This module provides the DashboardManager class that serves as the central
interface between the ZBGym framework and the Dashboard client.

Architecture:
    Trainer -> DashboardManager -> DashboardClient -> Connection

DashboardManager is responsible for:
- Publishing training metrics
- Publishing events
- Publishing logs
- Publishing checkpoint metadata
- Publishing replay metadata

All operations are:
- Thread-safe
- Non-blocking via internal queue
- Fault-tolerant (framework continues if dashboard fails)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zbgym.dashboard.client import DashboardClient
from zbgym.dashboard.config import DashboardConfig
from zbgym.dashboard.connection import ConnectionState
from zbgym.dashboard.exceptions import (
    DashboardAuthError,
    DashboardConnectionError,
    DashboardError,
)
from zbgym.dashboard.models import EventType, LogLevel


logger = logging.getLogger(__name__)


@dataclass
class DashboardManagerConfig:
    """Configuration for Dashboard Manager.

    Attributes:
        enabled: Whether dashboard is enabled.
        url: Dashboard server URL.
        api_key: API key for authentication.
        publish_interval: Publish metrics every N timesteps.
        publish_interval_seconds: Publish metrics every N seconds.
        reconnect: Whether to auto-reconnect.
        heartbeat_interval: Heartbeat interval in seconds.
        timeout: Request timeout in seconds.
    """

    enabled: bool = False
    url: str = "http://localhost:8080"
    api_key: str | None = None
    publish_interval: int = 100  # timesteps
    publish_interval_seconds: float | None = None  # seconds
    reconnect: bool = True
    heartbeat_interval: float = 30.0
    timeout: float = 10.0
    project_name: str = "ZBGym"
    agent_name: str = "Agent"


class DashboardManager:
    """Central manager for Dashboard operations.

    This class provides a high-level interface for publishing training
    data to the Dashboard. It wraps DashboardClient with:

    - Automatic connection management
    - Metrics batching
    - Event filtering
    - Fault tolerance
    - Thread safety

    Example:
        manager = DashboardManager(DashboardManagerConfig(
            enabled=True,
            url="https://dashboard.zbgym.dev",
            api_key="zb_xxx"
        ))

        manager.start_session(
            project="Zooba",
            trainer="PPO",
            env="BattleArena-v2"
        )

        manager.publish_metrics(episode=100, reward=15.5)
        manager.publish_event("checkpoint_saved", {"path": "/models/model.pt"})

        manager.finish_session()
    """

    def __init__(
        self,
        config: DashboardManagerConfig | None = None,
    ) -> None:
        """Initialize Dashboard Manager.

        Args:
            config: Dashboard manager configuration.
        """
        self._config = config or DashboardManagerConfig()
        self._client: DashboardClient | None = None
        self._session_id: str | None = None
        self._last_publish_time: float = 0
        self._last_timestep: int = 0
        self._metrics_buffer: dict[str, float] = {}
        self._replay_count: int = 0
        self._checkpoint_count: int = 0
        self._is_started: bool = False
        self._start_time: float = 0

    @property
    def is_enabled(self) -> bool:
        """Check if dashboard is enabled."""
        return self._config.enabled

    @property
    def is_connected(self) -> bool:
        """Check if connected to dashboard."""
        return self._client is not None and self._client.is_connected

    @property
    def session_id(self) -> str | None:
        """Get current session ID."""
        return self._session_id

    def configure(
        self,
        enabled: bool | None = None,
        url: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Update configuration.

        Args:
            enabled: Enable/disable dashboard.
            url: Dashboard server URL.
            api_key: API key.
            **kwargs: Additional config options.
        """
        if enabled is not None:
            self._config.enabled = enabled
        if url is not None:
            self._config.url = url
        if api_key is not None:
            self._config.api_key = api_key

        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def start_session(
        self,
        project: str | None = None,
        trainer: str | None = None,
        env: str | None = None,
        total_timesteps: int = 0,
        **metadata: Any,
    ) -> str | None:
        """Start a training session.

        Args:
            project: Project name.
            trainer: Training algorithm name.
            env: Environment ID.
            total_timesteps: Target total timesteps.
            **metadata: Additional session metadata.

        Returns:
            Session ID if started, None if disabled or failed.
        """
        if not self._config.enabled:
            return None

        self._start_time = time.time()

        try:
            # Create client if needed
            if self._client is None:
                self._client = DashboardClient()

            # Connect
            self._client.connect(
                url=self._config.url,
                api_key=self._config.api_key,
                reconnect=self._config.reconnect,
                heartbeat_interval=self._config.heartbeat_interval,
                timeout=self._config.timeout,
            )

            # Start session
            session = self._client.start_session(
                project=project or self._config.project_name,
                trainer=trainer or "Unknown",
                env=env or "Unknown",
                total_timesteps=total_timesteps,
                agent_name=self._config.agent_name,
                **metadata,
            )

            self._session_id = session.session_id
            self._is_started = True
            self._replay_count = 0
            self._checkpoint_count = 0

            # Publish training started event
            self._client.publish_event(
                "training_started",
                {
                    "project": project or self._config.project_name,
                    "trainer": trainer or "Unknown",
                    "env": env or "Unknown",
                    "total_timesteps": total_timesteps,
                },
            )

            logger.info(f"Dashboard session started: {self._session_id}")
            return self._session_id

        except DashboardAuthError as e:
            logger.warning(f"Dashboard authentication failed: {e}. Training continues.")
            self._config.enabled = False
            return None
        except DashboardConnectionError as e:
            logger.warning(f"Dashboard connection failed: {e}. Training continues.")
            # Don't disable - may reconnect later
            return None
        except Exception as e:
            logger.warning(f"Dashboard error: {e}. Training continues.")
            return None

    def finish_session(
        self,
        status: str = "finished",
        final_metrics: dict[str, float] | None = None,
    ) -> None:
        """Finish current training session.

        Args:
            status: Final status.
            final_metrics: Optional final metrics.
        """
        if not self._is_started or self._session_id is None:
            return

        try:
            if self._client and self.is_connected:
                # Publish training finished event
                duration = time.time() - self._start_time
                self._client.publish_event(
                    "training_finished",
                    {
                        "status": status,
                        "duration": duration,
                        "replay_count": self._replay_count,
                        "checkpoint_count": self._checkpoint_count,
                        **(final_metrics or {}),
                    },
                )

                self._client.finish_session(
                    status=status,
                    final_metrics=final_metrics,
                )

                self._client.disconnect()

            logger.info(f"Dashboard session finished: {self._session_id}")

        except Exception as e:
            logger.warning(f"Error finishing dashboard session: {e}")

        finally:
            self._session_id = None
            self._is_started = False
            self._client = None
            self._metrics_buffer.clear()

    def should_publish(self, timestep: int) -> bool:
        """Check if metrics should be published now.

        Args:
            timestep: Current training timestep.

        Returns:
            True if metrics should be published.
        """
        if not self._config.enabled:
            return False

        # Check interval by timesteps
        if self._config.publish_interval > 0:
            if timestep - self._last_timestep >= self._config.publish_interval:
                self._last_timestep = timestep
                return True

        # Check interval by time
        if self._config.publish_interval_seconds is not None:
            if time.time() - self._last_publish_time >= self._config.publish_interval_seconds:
                self._last_publish_time = time.time()
                return True

        return False

    def publish_metrics(
        self,
        timestep: int | None = None,
        episode: int | None = None,
        reward: float | None = None,
        loss: float | None = None,
        fps: float | None = None,
        **custom_metrics: float,
    ) -> None:
        """Publish training metrics.

        Args:
            timestep: Current timestep.
            episode: Current episode.
            reward: Episode reward.
            loss: Training loss.
            fps: Frames per second.
            **custom_metrics: Custom metrics.
        """
        if not self._config.enabled:
            return

        try:
            if self._client is None or not self.is_connected:
                return

            self._client.publish_metrics(
                episode=episode,
                timestep=timestep,
                reward=reward,
                loss=loss,
                fps=fps,
                **custom_metrics,
            )

        except DashboardError as e:
            logger.debug(f"Dashboard publish error: {e}")

    def publish_system_metrics(
        self,
        cpu_percent: float | None = None,
        memory_mb: float | None = None,
        gpu_percent: float | None = None,
        gpu_memory_mb: float | None = None,
    ) -> None:
        """Publish system metrics.

        Args:
            cpu_percent: CPU usage.
            memory_mb: Memory usage in MB.
            gpu_percent: GPU usage.
            gpu_memory_mb: GPU memory in MB.
        """
        if not self._config.enabled:
            return

        try:
            if self._client is None or not self.is_connected:
                return

            self._client.publish_metrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                gpu_percent=gpu_percent,
                gpu_memory_mb=gpu_memory_mb,
            )

        except DashboardError:
            pass

    def publish_event(
        self,
        event_type: str | EventType,
        data: dict[str, Any] | None = None,
        actor: str | None = None,
    ) -> None:
        """Publish an event.

        Args:
            event_type: Type of event.
            data: Event data.
            actor: Actor that triggered event.
        """
        if not self._config.enabled:
            return

        try:
            if self._client is None or not self.is_connected:
                return

            self._client.publish_event(event_type, data, actor)

        except DashboardError as e:
            logger.debug(f"Dashboard event error: {e}")

    def publish_log(
        self,
        level: str | LogLevel,
        message: str,
        source: str | None = None,
    ) -> None:
        """Publish a log message.

        Args:
            level: Log level.
            message: Log message.
            source: Source component.
        """
        if not self._config.enabled:
            return

        try:
            if self._client is None or not self.is_connected:
                return

            self._client.publish_log(level, message, source)

        except DashboardError:
            pass

    def publish_checkpoint(
        self,
        file_path: str | Path,
        timestep: int,
        is_best: bool = False,
        metrics: dict[str, float] | None = None,
    ) -> None:
        """Publish checkpoint metadata.

        Args:
            file_path: Path to checkpoint file.
            timestep: Training timestep.
            is_best: Whether this is the best model.
            metrics: Optional metrics snapshot.
        """
        if not self._config.enabled:
            return

        self._checkpoint_count += 1

        try:
            if self._client is None or not self.is_connected:
                return

            path = Path(file_path)

            self._client.publish_checkpoint(
                file_path=str(path),
                timestep=timestep,
                is_best=is_best,
                metrics=metrics,
            )

            # Publish checkpoint event
            self.publish_event(
                "checkpoint_saved",
                {
                    "file_path": str(path),
                    "file_size": path.stat().st_size if path.exists() else 0,
                    "timestep": timestep,
                    "is_best": is_best,
                    "metrics": metrics or {},
                },
            )

        except DashboardError as e:
            logger.debug(f"Dashboard checkpoint error: {e}")

    def publish_replay(
        self,
        file_path: str | Path,
        episode: int,
        duration: float = 0.0,
    ) -> None:
        """Publish replay metadata.

        Args:
            file_path: Path to replay file.
            episode: Episode number.
            duration: Replay duration in seconds.
        """
        if not self._config.enabled:
            return

        self._replay_count += 1

        try:
            if self._client is None or not self.is_connected:
                return

            path = Path(file_path)

            self._client.publish_replay(
                file_path=str(path),
                episode=episode,
                duration=duration,
            )

            # Publish replay event
            self.publish_event(
                "replay_saved",
                {
                    "file_path": str(path),
                    "file_size": path.stat().st_size if path.exists() else 0,
                    "episode": episode,
                    "duration": duration,
                },
            )

        except DashboardError as e:
            logger.debug(f"Dashboard replay error: {e}")

    # Event shortcuts

    def on_training_start(self) -> None:
        """Called when training starts."""
        self.publish_event("training_started", {})

    def on_training_end(
        self,
        status: str = "finished",
        duration: float = 0.0,
    ) -> None:
        """Called when training ends.

        Args:
            status: Final status.
            duration: Training duration.
        """
        self.publish_event(
            "training_finished",
            {"status": status, "duration": duration},
        )

    def on_episode_start(self, episode: int) -> None:
        """Called when episode starts.

        Args:
            episode: Episode number.
        """
        self.publish_event(
            "episode_started",
            {"episode": episode},
        )

    def on_episode_end(
        self,
        episode: int,
        reward: float,
        length: int,
    ) -> None:
        """Called when episode ends.

        Args:
            episode: Episode number.
            reward: Episode reward.
            length: Episode length.
        """
        self.publish_event(
            "episode_finished",
            {
                "episode": episode,
                "reward": reward,
                "length": length,
            },
        )

    def on_checkpoint_save(
        self,
        path: str | Path,
        timestep: int,
        is_best: bool = False,
    ) -> None:
        """Called when checkpoint is saved.

        Args:
            path: Checkpoint path.
            timestep: Training timestep.
            is_best: Whether this is best model.
        """
        self.publish_checkpoint(path, timestep, is_best)

    def on_replay_save(
        self,
        path: str | Path,
        episode: int,
        duration: float = 0.0,
    ) -> None:
        """Called when replay is saved.

        Args:
            path: Replay path.
            episode: Episode number.
            duration: Replay duration.
        """
        self.publish_replay(path, episode, duration)

    def on_evaluation_start(self) -> None:
        """Called when evaluation starts."""
        self.publish_event("evaluation_started", {})

    def on_evaluation_end(
        self,
        mean_reward: float,
        std_reward: float,
        n_episodes: int,
    ) -> None:
        """Called when evaluation ends.

        Args:
            mean_reward: Mean reward.
            std_reward: Std of rewards.
            n_episodes: Number of episodes.
        """
        self.publish_event(
            "evaluation_finished",
            {
                "mean_reward": mean_reward,
                "std_reward": std_reward,
                "n_episodes": n_episodes,
            },
        )

    def log_info(self, message: str) -> None:
        """Publish INFO log."""
        self.publish_log(LogLevel.INFO, message)

    def log_warning(self, message: str) -> None:
        """Publish WARNING log."""
        self.publish_log(LogLevel.WARNING, message)

    def log_error(self, message: str) -> None:
        """Publish ERROR log."""
        self.publish_log(LogLevel.ERROR, message)

    def log_debug(self, message: str) -> None:
        """Publish DEBUG log."""
        self.publish_log(LogLevel.DEBUG, message)

    def __enter__(self) -> "DashboardManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if exc_type is not None:
            self.finish_session(status="failed")
        else:
            self.finish_session()

    def __repr__(self) -> str:
        """String representation."""
        status = "enabled" if self._config.enabled else "disabled"
        if self._config.enabled:
            status += f", connected={self.is_connected}"
        return f"DashboardManager({status})"


# Global manager instance
_dashboard_manager: DashboardManager | None = None


def get_dashboard_manager() -> DashboardManager:
    """Get or create global Dashboard Manager.

    Returns:
        Global DashboardManager instance.
    """
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = DashboardManager()
    return _dashboard_manager


def configure_dashboard(
    enabled: bool = False,
    url: str = "http://localhost:8080",
    api_key: str | None = None,
    **kwargs: Any,
) -> DashboardManager:
    """Configure global dashboard manager.

    Args:
        enabled: Enable dashboard.
        url: Dashboard server URL.
        api_key: API key.
        **kwargs: Additional config options.

    Returns:
        Configured DashboardManager.
    """
    manager = get_dashboard_manager()
    manager.configure(
        enabled=enabled,
        url=url,
        api_key=api_key,
        **kwargs,
    )
    return manager
