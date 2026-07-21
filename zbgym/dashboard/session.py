"""Dashboard session management for ZBGym.

This module manages training sessions on the Dashboard server,
including session creation, updates, and lifecycle management.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from zbgym.dashboard.exceptions import DashboardSessionError
from zbgym.dashboard.models import ZBGYM_VERSION, TrainingSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages training sessions with Dashboard server.

    This class handles session lifecycle:
    - Creating sessions when training starts
    - Updating session progress
    - Finishing sessions when training completes

    Args:
        connection: DashboardConnection instance.
    """

    def __init__(self, connection: Any) -> None:
        """Initialize session manager.

        Args:
            connection: DashboardConnection instance.
        """
        self._connection = connection
        self._current_session: TrainingSession | None = None
        self._start_time: float | None = None

    @property
    def current_session(self) -> TrainingSession | None:
        """Get current active session.

        Returns:
            Current session or None if not in a session.
        """
        return self._current_session

    @property
    def is_active(self) -> bool:
        """Check if there is an active session.

        Returns:
            True if in a session, False otherwise.
        """
        return self._current_session is not None

    def create(
        self,
        project_name: str,
        trainer: str,
        env_id: str,
        total_timesteps: int = 0,
        **metadata: Any,
    ) -> TrainingSession:
        """Create a new training session.

        Creates a session on the Dashboard server and starts tracking.

        Args:
            project_name: Name of the project.
            trainer: Training algorithm name (e.g., "PPO").
            env_id: Environment ID (e.g., "BattleArena-v2").
            total_timesteps: Target total timesteps for training.
            **metadata: Additional metadata to store with session.

        Returns:
            Created TrainingSession instance.

        Raises:
            DashboardSessionError: If session creation fails.
            DashboardConnectionError: If not connected to server.

        Example:
            session = dashboard.session.create(
                project_name="ZoobaBot",
                trainer="PPO",
                env_id="BattleArena-v2",
                total_timesteps=1_000_000,
                learning_rate=3e-4,
            )
        """
        if self._current_session is not None:
            logger.warning(
                f"Session {self._current_session.session_id} is still active. Finishing it first."
            )
            self.finish()

        # Create local session object
        session = TrainingSession.create(
            project_name=project_name,
            trainer=trainer,
            env_id=env_id,
            total_timesteps=total_timesteps,
            framework_version=ZBGYM_VERSION,
            **metadata,
        )

        self._current_session = session
        self._start_time = time.time()

        # Send create packet
        self._connection.send_now(
            self._connection._packet_builder.session_create(
                session_id=session.session_id,
                project_name=project_name,
                trainer=trainer,
                env_id=env_id,
                total_timesteps=total_timesteps,
                metadata=metadata,
            )
        )

        logger.info(f"Created session {session.session_id}: {project_name}/{trainer}/{env_id}")

        return session

    def update(
        self,
        status: str | None = None,
        current_timestep: int | None = None,
        **metadata: Any,
    ) -> None:
        """Update current session.

        Sends session update to Dashboard with current progress.

        Args:
            status: New session status (e.g., "running", "paused").
            current_timestep: Current training timestep.
            **metadata: Updated metadata.

        Raises:
            DashboardSessionError: If no active session.

        Example:
            dashboard.session.update(
                current_timestep=50000,
                mean_reward=15.5
            )
        """
        if self._current_session is None:
            raise DashboardSessionError(
                "No active session to update",
                operation="update",
            )

        # Update local session
        if status is not None:
            self._current_session.status = status
        if current_timestep is not None:
            self._current_session.current_timestep = current_timestep

        self._current_session.updated_at = time.time()

        # Merge metadata
        if metadata:
            self._current_session.metadata.update(metadata)

        # Send update packet
        self._connection.send_now(
            self._connection._packet_builder.session_update(
                session=self._current_session.session_id,
                status=status,
                current_timestep=current_timestep,
                metadata=metadata if metadata else None,
            )
        )

    def finish(
        self,
        status: str = "finished",
        final_metrics: dict[str, float] | None = None,
    ) -> TrainingSession | None:
        """Finish current session.

        Stops tracking and sends final session update.

        Args:
            status: Final status ("finished", "interrupted", "failed").
            final_metrics: Optional final metrics summary.

        Returns:
            Finished session or None if no active session.

        Raises:
            DashboardSessionError: If no active session.

        Example:
            session = dashboard.session.finish(
                status="finished",
                final_metrics={"mean_reward": 25.0, "total_time": 3600}
            )
        """
        if self._current_session is None:
            return None

        session = self._current_session
        duration = time.time() - (self._start_time or session.created_at)

        # Update session
        session.status = status
        session.updated_at = time.time()

        # Send training finished packet
        self._connection.send_now(
            self._connection._packet_builder.training_finished(
                session=session.session_id,
                total_timesteps=session.current_timestep,
                duration=duration,
                final_metrics=final_metrics,
            )
        )

        logger.info(
            f"Finished session {session.session_id}: status={status}, duration={duration:.1f}s"
        )

        self._current_session = None
        self._start_time = None

        return session

    def get_progress(self) -> dict[str, Any]:
        """Get session progress information.

        Returns:
            Dictionary with progress details.

        Raises:
            DashboardSessionError: If no active session.
        """
        if self._current_session is None:
            raise DashboardSessionError(
                "No active session",
                operation="get_progress",
            )

        session = self._current_session
        elapsed = time.time() - (self._start_time or session.created_at)

        progress: dict[str, Any] = {
            "session_id": session.session_id,
            "status": session.status,
            "elapsed_time": elapsed,
        }

        if session.total_timesteps > 0:
            progress["progress_percent"] = session.current_timestep / session.total_timesteps * 100
            progress["remaining_timesteps"] = session.total_timesteps - session.current_timestep

            if elapsed > 0:
                tps = session.current_timestep / elapsed
                if tps > 0:
                    progress["eta"] = progress["remaining_timesteps"] / tps

        return progress

    def pause(self) -> None:
        """Pause current session.

        Raises:
            DashboardSessionError: If no active session.
        """
        self.update(status="paused")

    def resume(self) -> None:
        """Resume paused session.

        Raises:
            DashboardSessionError: If no active session.
        """
        self.update(status="running")

    def checkpoint_saved(
        self,
        timestep: int,
        is_best: bool = False,
        metrics: dict[str, float] | None = None,
    ) -> None:
        """Notify that a checkpoint was saved.

        Args:
            timestep: Training timestep at checkpoint.
            is_best: Whether this is the best model.
            metrics: Optional metrics snapshot.

        Raises:
            DashboardSessionError: If no active session.
        """
        if self._current_session is None:
            raise DashboardSessionError(
                "No active session",
                operation="checkpoint_saved",
            )

        # Update timestep
        self._current_session.current_timestep = max(
            self._current_session.current_timestep, timestep
        )

        # Event will be published separately via dashboard.publish_event()
        logger.debug(f"Checkpoint saved at timestep {timestep}, is_best={is_best}")

    def replay_saved(
        self,
        episode: int,
        duration: float,
    ) -> None:
        """Notify that a replay was saved.

        Args:
            episode: Episode number.
            duration: Replay duration in seconds.

        Raises:
            DashboardSessionError: If no active session.
        """
        if self._current_session is None:
            raise DashboardSessionError(
                "No active session",
                operation="replay_saved",
            )

        logger.debug(f"Replay saved for episode {episode}, duration={duration:.1f}s")

    def __repr__(self) -> str:
        """String representation."""
        if self._current_session:
            return (
                f"SessionManager(session={self._current_session.session_id}, "
                f"status={self._current_session.status})"
            )
        return "SessionManager(no active session)"
