"""Dashboard client for ZBGym.

This is the main client module that provides the DashboardClient class
for connecting to and publishing data to the Dashboard server.

Example:
    dashboard = DashboardClient()
    dashboard.connect(
        url="https://dashboard.zbgym.dev",
        api_key="zb_xxx"
    )

    with dashboard.session(
        project="Zooba",
        trainer="PPO",
        env="BattleArena-v2"
    ):
        for step in range(1000000):
            # Training loop
            dashboard.publish_metrics(reward=reward, loss=loss)

    dashboard.disconnect()
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from zbgym.dashboard.auth import AuthManager
from zbgym.dashboard.config import (
    DEFAULT_URL,
    DashboardConfig,
    configure,
    get_config,
)
from zbgym.dashboard.connection import DashboardConnection
from zbgym.dashboard.events import Event
from zbgym.dashboard.exceptions import (
    DashboardConnectionError,
)
from zbgym.dashboard.models import (
    EventData,
    LogLevel,
    TrainingSession,
)
from zbgym.dashboard.packet import PacketBuilder, PacketType
from zbgym.dashboard.session import SessionManager

logger = logging.getLogger(__name__)


class DashboardClient:
    """Main Dashboard client for ZBGym.

    This class provides a high-level interface for connecting to
    the Dashboard server and publishing training data.

    It is designed to be:
    - Thread-safe for use in multi-threaded training
    - Non-blocking via internal queue
    - Easy to use with context managers
    - Compatible with existing ZBGym trainers

    Example:
        # Basic usage
        dashboard = DashboardClient()
        dashboard.connect(url="https://dashboard.zbgym.dev", api_key="zb_xxx")

        session = dashboard.start_session(
            project="ZoobaBot",
            trainer="PPO",
            env="BattleArena-v2"
        )

        dashboard.publish_metrics(reward=10.5, loss=0.3)
        dashboard.publish_event("checkpoint_saved", {"step": 1000})

        dashboard.finish_session()
        dashboard.disconnect()

        # Or with context manager
        dashboard = DashboardClient()
        with dashboard.connect(url, api_key):
            with dashboard.session("Zooba", "PPO", "BattleArena-v2"):
                # Training
                pass
    """

    _instance: DashboardClient | None = None
    _instance_lock = threading.Lock()

    def __init__(
        self,
        config: DashboardConfig | None = None,
        auto_session: bool = False,
    ) -> None:
        """Initialize Dashboard client.

        Args:
            config: Dashboard configuration. If None, uses global config.
            auto_session: If True, automatically create session on connect.
        """
        self._config = config or get_config()
        self._auto_session = auto_session

        # Initialize components
        self._connection: DashboardConnection | None = None
        self._auth: AuthManager | None = None
        self._session_manager: SessionManager | None = None
        self._packet_builder: PacketBuilder | None = None

        # State
        self._connected = False
        self._lock = threading.Lock()

        # Logging
        self._logger = logging.getLogger(f"{__name__}.{id(self)}")

        # Set as singleton if not already set
        with DashboardClient._instance_lock:
            if DashboardClient._instance is None:
                DashboardClient._instance = self

    @classmethod
    def get_instance(cls) -> DashboardClient | None:
        """Get the singleton instance.

        Returns:
            Singleton DashboardClient instance or None.
        """
        with cls._instance_lock:
            return cls._instance

    def connect(
        self,
        url: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> DashboardClient:
        """Connect to Dashboard server.

        Args:
            url: Dashboard server URL.
            api_key: API key for authentication.
            **kwargs: Additional configuration options.

        Returns:
            Self for chaining.

        Raises:
            DashboardConnectionError: If connection fails.
            DashboardAuthError: If authentication fails.

        Example:
            dashboard.connect(
                url="https://dashboard.zbgym.dev",
                api_key="zb_xxx",
                reconnect=True
            )
        """
        with self._lock:
            if self._connected:
                self._logger.warning("Already connected")
                return self

            # Update config
            if url or api_key or kwargs:
                self._config = configure(
                    url=url or self._config.url,
                    api_key=api_key or self._config.api_key,
                    **kwargs,
                )

            if not self._config.enabled:
                self._logger.info("Dashboard disabled in config")
                return self

            # Initialize components
            self._connection = DashboardConnection(
                config=self._config,
                on_connect=self._handle_connect,
                on_disconnect=self._handle_disconnect,
                on_error=self._handle_error,
            )

            self._auth = AuthManager(self._config)
            self._session_manager = SessionManager(self._connection)

            # Connect
            try:
                self._connection.connect()

                # Authenticate
                if self._config.api_key:
                    self._auth.authenticate()

                self._connected = True

                # Create packet builder with session if active
                if self._session_manager.is_active:
                    self._packet_builder = PacketBuilder(
                        self._session_manager.current_session.session_id
                    )

            except Exception as e:
                self._logger.error(f"Connection failed: {e}")
                self._connection = None
                self._auth = None
                self._session_manager = None
                raise

        return self

    def disconnect(self) -> None:
        """Disconnect from Dashboard server.

        Finishes any active session and closes connection.
        """
        with self._lock:
            if not self._connected:
                return

            # Finish session if active
            if self._session_manager and self._session_manager.is_active:
                try:
                    self._session_manager.finish(status="interrupted")
                except Exception as e:
                    self._logger.warning(f"Error finishing session: {e}")

            # Disconnect
            if self._connection:
                self._connection.disconnect()

            self._connected = False
            self._logger.info("Disconnected from Dashboard")

    def reconnect(self) -> None:
        """Reconnect to Dashboard server.

        Raises:
            DashboardConnectionError: If reconnection fails.
        """
        with self._lock:
            if self._connection:
                self._connection.reconnect()
                self._connected = True

    @property
    def is_connected(self) -> bool:
        """Check if connected to server.

        Returns:
            True if connected, False otherwise.
        """
        with self._lock:
            return self._connected and self._connection is not None

    def _ensure_connected(self) -> None:
        """Ensure client is connected before operation.

        Raises:
            DashboardConnectionError: If not connected.
        """
        if not self.is_connected:
            raise DashboardConnectionError("Not connected to Dashboard. Call connect() first.")

    # Session management

    def start_session(
        self,
        project: str,
        trainer: str,
        env: str,
        total_timesteps: int = 0,
        **metadata: Any,
    ) -> TrainingSession:
        """Start a new training session.

        Args:
            project: Project name.
            trainer: Training algorithm name.
            env: Environment ID.
            total_timesteps: Target total timesteps.
            **metadata: Additional session metadata.

        Returns:
            Created TrainingSession.

        Raises:
            DashboardConnectionError: If not connected.
            DashboardSessionError: If session creation fails.

        Example:
            session = dashboard.start_session(
                project="ZoobaBot",
                trainer="PPO",
                env="BattleArena-v2",
                total_timesteps=1_000_000
            )
        """
        self._ensure_connected()

        if not self._session_manager:
            raise DashboardConnectionError("Session manager not initialized")

        session = self._session_manager.create(
            project_name=project,
            trainer=trainer,
            env_id=env,
            total_timesteps=total_timesteps,
            **metadata,
        )

        # Create packet builder for this session
        self._packet_builder = PacketBuilder(session.session_id)

        return session

    def finish_session(
        self,
        status: str = "finished",
        final_metrics: dict[str, float] | None = None,
    ) -> TrainingSession | None:
        """Finish current training session.

        Args:
            status: Final status.
            final_metrics: Final metrics summary.

        Returns:
            Finished session or None.

        Raises:
            DashboardSessionError: If no active session.
        """
        if not self._session_manager:
            return None

        session = self._session_manager.finish(status, final_metrics)
        self._packet_builder = None
        return session

    @contextmanager
    def session(
        self,
        project: str,
        trainer: str,
        env: str,
        total_timesteps: int = 0,
        **metadata: Any,
    ) -> Generator[TrainingSession, None, None]:
        """Context manager for training session.

        Automatically starts and finishes session.

        Args:
            project: Project name.
            trainer: Training algorithm name.
            env: Environment ID.
            total_timesteps: Target total timesteps.
            **metadata: Additional session metadata.

        Yields:
            TrainingSession instance.

        Example:
            with dashboard.session("Zooba", "PPO", "BattleArena-v2") as session:
                for step in range(1000000):
                    # Training
                    pass
        """
        session = self.start_session(
            project=project,
            trainer=trainer,
            env=env,
            total_timesteps=total_timesteps,
            **metadata,
        )

        try:
            yield session
        except Exception:
            self.finish_session(status="failed")
            raise
        else:
            self.finish_session(status="finished")

    @contextmanager
    def connect_session(
        self,
        url: str,
        api_key: str,
        **kwargs: Any,
    ) -> Generator[DashboardClient, None, None]:
        """Context manager for connect + session lifecycle.

        Args:
            url: Dashboard server URL.
            api_key: API key.
            **kwargs: Additional config options.

        Yields:
            Connected DashboardClient.

        Example:
            with dashboard.connect_session(
                "https://dashboard.zbgym.dev",
                api_key="zb_xxx"
            ) as dashboard:
                with dashboard.session("Zooba", "PPO", "BattleArena-v2"):
                    # Training
                    pass
        """
        self.connect(url=url, api_key=api_key, **kwargs)
        try:
            yield self
        finally:
            self.disconnect()

    # Publishing methods

    def publish(
        self,
        packet_type: PacketType,
        payload: dict[str, Any],
    ) -> None:
        """Publish generic packet.

        Args:
            packet_type: Type of packet.
            payload: Packet payload.
        """
        self._ensure_connected()

        if not self._packet_builder or not self._session_manager:
            return

        session_id = (
            self._session_manager.current_session.session_id
            if self._session_manager.current_session
            else ""
        )

        packet = Packet(
            type=packet_type,
            session=session_id,
            payload=payload,
        )

        self._connection.send(packet)

    def publish_metrics(
        self,
        episode: int | None = None,
        timestep: int | None = None,
        reward: float | None = None,
        loss: float | None = None,
        entropy: float | None = None,
        learning_rate: float | None = None,
        fps: float | None = None,
        **custom_metrics: float,
    ) -> None:
        """Publish training metrics.

        Args:
            episode: Current episode number.
            timestep: Current timestep.
            reward: Episode reward.
            loss: Training loss.
            entropy: Policy entropy.
            learning_rate: Learning rate.
            fps: Frames per second.
            **custom_metrics: Custom metric values.

        Example:
            dashboard.publish_metrics(
                episode=100,
                timestep=50000,
                reward=15.5,
                loss=0.3,
                fps=120
            )
        """
        self._ensure_connected()

        if not self._packet_builder or not self._session_manager:
            return

        # Build metrics dict
        metrics_dict: dict[str, float] = {}

        if reward is not None:
            metrics_dict["reward"] = reward
        if loss is not None:
            metrics_dict["loss"] = loss
        if entropy is not None:
            metrics_dict["entropy"] = entropy
        if learning_rate is not None:
            metrics_dict["learning_rate"] = learning_rate
        if fps is not None:
            metrics_dict["fps"] = fps

        metrics_dict.update(custom_metrics)

        if not metrics_dict:
            return

        # Create and send packet
        packet = self._packet_builder.metrics(metrics_dict)
        self._connection.send(packet)

        # Update session timestep if provided
        if timestep is not None and self._session_manager.is_active:
            if timestep > self._session_manager.current_session.current_timestep:
                self._session_manager.update(current_timestep=timestep)

    def publish_event(
        self,
        event_type: str | EventData,
        data: dict[str, Any] | None = None,
        actor: str | None = None,
    ) -> None:
        """Publish an event.

        Args:
            event_type: Type of event or EventData instance.
            data: Event data.
            actor: Actor that triggered the event.

        Example:
            dashboard.publish_event(
                "character_spawn",
                {"character_id": "player_1", "position": {"x": 100, "y": 200}}
            )
        """
        self._ensure_connected()

        if not self._packet_builder or not self._session_manager:
            return

        if isinstance(event_type, EventData):
            packet = self._packet_builder.event(
                event_type=event_type.event_type.value
                if hasattr(event_type.event_type, "value")
                else str(event_type.event_type),
                event_data=event_type.data,
                actor=event_type.actor,
            )
        else:
            packet = self._packet_builder.event(
                event_type=event_type,
                event_data=data or {},
                actor=actor,
            )

        self._connection.send(packet)

    def publish_log(
        self,
        level: str | LogLevel,
        message: str,
        source: str | None = None,
    ) -> None:
        """Publish a log message.

        Args:
            level: Log level (debug, info, warning, error, critical).
            message: Log message.
            source: Source of the log.

        Example:
            dashboard.publish_log("info", "Training started")
            dashboard.publish_log("warning", "High loss detected", source="trainer")
        """
        self._ensure_connected()

        if not self._packet_builder or not self._session_manager:
            return

        level_str = level.value if isinstance(level, LogLevel) else level

        packet = self._packet_builder.log(
            level=level_str,
            message=message,
            source=source,
        )

        self._connection.send(packet)

    def publish_checkpoint(
        self,
        file_path: str,
        timestep: int,
        is_best: bool = False,
        metrics: dict[str, float] | None = None,
    ) -> None:
        """Publish checkpoint metadata.

        Note: Actual file upload is handled separately.

        Args:
            file_path: Path to checkpoint file.
            timestep: Training timestep.
            is_best: Whether this is the best model.
            metrics: Optional metrics snapshot.

        Example:
            dashboard.publish_checkpoint(
                "/path/to/model.pt",
                timestep=100000,
                is_best=True,
                metrics={"mean_reward": 25.0}
            )
        """
        self._ensure_connected()

        if not self._packet_builder or not self._session_manager:
            return

        path = Path(file_path)
        file_size = path.stat().st_size if path.exists() else 0

        packet = self._packet_builder.checkpoint(
            file_path=file_path,
            file_size=file_size,
            file_type=path.suffix,
            timestep=timestep,
            is_best=is_best,
            metrics=metrics,
        )

        self._connection.send(packet)

        # Update session checkpoint info
        self._session_manager.checkpoint_saved(timestep, is_best, metrics)

    def publish_replay(
        self,
        file_path: str,
        episode: int,
        duration: float = 0.0,
    ) -> None:
        """Publish replay metadata.

        Note: Actual file upload is handled separately.

        Args:
            file_path: Path to replay file.
            episode: Episode number.
            duration: Replay duration in seconds.

        Example:
            dashboard.publish_replay(
                "/path/to/replay.json",
                episode=100,
                duration=180.5
            )
        """
        self._ensure_connected()

        if not self._packet_builder or not self._session_manager:
            return

        path = Path(file_path)
        file_size = path.stat().st_size if path.exists() else 0

        packet = self._packet_builder.replay(
            file_path=file_path,
            file_size=file_size,
            episode=episode,
            duration=duration,
        )

        self._connection.send(packet)

        # Update session
        self._session_manager.replay_saved(episode, duration)

    # Convenience methods using Event and Metrics classes

    def log_info(self, message: str, source: str | None = None) -> None:
        """Publish INFO log.

        Args:
            message: Log message.
            source: Source component.
        """
        self.publish_log(LogLevel.INFO, message, source)

    def log_warning(self, message: str, source: str | None = None) -> None:
        """Publish WARNING log.

        Args:
            message: Log message.
            source: Source component.
        """
        self.publish_log(LogLevel.WARNING, message, source)

    def log_error(self, message: str, source: str | None = None) -> None:
        """Publish ERROR log.

        Args:
            message: Log message.
            source: Source component.
        """
        self.publish_log(LogLevel.ERROR, message, source)

    def log_debug(self, message: str, source: str | None = None) -> None:
        """Publish DEBUG log.

        Args:
            message: Log message.
            source: Source component.
        """
        self.publish_log(LogLevel.DEBUG, message, source)

    # Event shortcuts

    def event_training_started(
        self,
        env_id: str,
        trainer: str,
        total_timesteps: int,
    ) -> None:
        """Publish training started event.

        Args:
            env_id: Environment ID.
            trainer: Training algorithm.
            total_timesteps: Target timesteps.
        """
        if not self._session_manager or not self._session_manager.is_active:
            return

        event = Event.training_started(
            session_id=self._session_manager.current_session.session_id,
            env_id=env_id,
            trainer=trainer,
            total_timesteps=total_timesteps,
        )
        self.publish_event(event)

    def event_training_finished(
        self,
        total_timesteps: int,
        duration: float,
        final_reward: float | None = None,
    ) -> None:
        """Publish training finished event.

        Args:
            total_timesteps: Total timesteps completed.
            duration: Training duration.
            final_reward: Final mean reward.
        """
        if not self._session_manager or not self._session_manager.is_active:
            return

        event = Event.training_finished(
            session_id=self._session_manager.current_session.session_id,
            total_timesteps=total_timesteps,
            duration=duration,
            final_reward=final_reward,
        )
        self.publish_event(event)

    def event_character_spawn(
        self,
        character_id: str,
        character_type: str,
        position: dict[str, float],
    ) -> None:
        """Publish character spawn event.

        Args:
            character_id: Character identifier.
            character_type: Character type/class.
            position: Spawn position.
        """
        if not self._session_manager or not self._session_manager.is_active:
            return

        event = Event.character_spawn(
            session_id=self._session_manager.current_session.session_id,
            character_id=character_id,
            character_type=character_type,
            position=position,
        )
        self.publish_event(event)

    def event_kill(
        self,
        killer_id: str,
        victim_id: str,
        weapon: str | None = None,
        position: dict[str, float] | None = None,
    ) -> None:
        """Publish kill event.

        Args:
            killer_id: Character that got the kill.
            victim_id: Character that was killed.
            weapon: Weapon used.
            position: Kill position.
        """
        if not self._session_manager or not self._session_manager.is_active:
            return

        event = Event.kill(
            session_id=self._session_manager.current_session.session_id,
            killer_id=killer_id,
            victim_id=victim_id,
            weapon=weapon,
            position=position,
        )
        self.publish_event(event)

    # Callbacks

    def _handle_connect(self) -> None:
        """Handle successful connection."""
        self._logger.info("Connected to Dashboard")
        self._connected = True

    def _handle_disconnect(self) -> None:
        """Handle disconnection."""
        self._logger.info("Disconnected from Dashboard")
        self._connected = False

    def _handle_error(self, error: Exception) -> None:
        """Handle connection error.

        Args:
            error: The error that occurred.
        """
        self._logger.error(f"Dashboard error: {error}")

    # Context manager support

    def __enter__(self) -> DashboardClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        session = (
            self._session_manager.current_session.session_id
            if self._session_manager and self._session_manager.is_active
            else "no session"
        )
        return f"DashboardClient({status}, {session})"


# Global client instance
_dashboard: DashboardClient | None = None


def get_dashboard() -> DashboardClient:
    """Get or create global Dashboard client.

    Returns:
        Global DashboardClient instance.
    """
    global _dashboard
    if _dashboard is None:
        _dashboard = DashboardClient()
    return _dashboard


def connect(
    url: str = DEFAULT_URL,
    api_key: str | None = None,
    **kwargs: Any,
) -> DashboardClient:
    """Connect global Dashboard client.

    Args:
        url: Dashboard server URL.
        api_key: API key.
        **kwargs: Additional config options.

    Returns:
        Connected DashboardClient.
    """
    dashboard = get_dashboard()
    dashboard.connect(url=url, api_key=api_key, **kwargs)
    return dashboard


def disconnect() -> None:
    """Disconnect global Dashboard client."""
    global _dashboard
    if _dashboard:
        _dashboard.disconnect()
        _dashboard = None
