"""Dashboard data models for ZBGym.

This module defines all data models used by the Dashboard Connector,
including training sessions, metrics, events, and checkpoints.
"""

from __future__ import annotations

import socket
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar


# Framework version
ZBGYM_VERSION = "0.1.0"


class PacketType(str, Enum):
    """Types of packets that can be sent to Dashboard.

    Each packet type represents a different kind of data or event
    that can be transmitted to the Dashboard server.
    """

    # Connection packets
    HEARTBEAT = "heartbeat"
    AUTH = "auth"
    AUTH_RESPONSE = "auth_response"

    # Session packets
    TRAINING_STARTED = "training_started"
    TRAINING_FINISHED = "training_finished"
    SESSION_CREATE = "session_create"
    SESSION_UPDATE = "session_update"

    # Data packets
    METRICS = "metrics"
    EVENT = "event"
    LOG = "log"
    CHECKPOINT = "checkpoint"
    REPLAY = "replay"

    # Response packets
    ACK = "ack"
    ERROR = "error"


class MetricType(str, Enum):
    """Types of metrics that can be published to Dashboard.

    These are standard RL training metrics that are commonly
    tracked during training sessions.
    """

    # Training metrics
    EPISODE = "episode"
    EPISODE_REWARD = "episode_reward"
    EPISODE_LENGTH = "episode_length"
    STEP = "step"
    TIMESTEP = "timestep"

    # Learning metrics
    LEARNING_RATE = "learning_rate"
    LOSS = "loss"
    VALUE_LOSS = "value_loss"
    POLICY_LOSS = "policy_loss"
    ENTROPY = "entropy"
    KL_DIVERGENCE = "kl_divergence"
    ADVANTAGE = "advantage"
    RETURN = "return"

    # Performance metrics
    FPS = "fps"
    TPS = "tps"  # Training steps per second
    ENV_STEPS_PER_SECOND = "env_steps_per_second"

    # System metrics
    CPU_PERCENT = "cpu_percent"
    MEMORY_MB = "memory_mb"
    GPU_PERCENT = "gpu_percent"
    GPU_MEMORY_MB = "gpu_memory_mb"

    # Environment metrics
    REWARD_MEAN = "reward_mean"
    REWARD_STD = "reward_std"
    REWARD_MIN = "reward_min"
    REWARD_MAX = "reward_max"

    # Time metrics
    ELAPSED_TIME = "elapsed_time"
    ETA = "eta"  # Estimated time of arrival (completion)


class EventType(str, Enum):
    """Types of events that can be published to Dashboard.

    These events represent significant occurrences during
    training that should be logged and tracked.
    """

    # Character events
    CHARACTER_SPAWN = "character_spawn"
    CHARACTER_DEATH = "character_death"
    CHARACTER_DAMAGE = "character_damage"
    CHARACTER_HEAL = "character_heal"

    # Combat events
    KILL = "kill"
    ASSIST = "assist"
    PROJECTILE_FIRED = "projectile_fired"
    PROJECTILE_HIT = "projectile_hit"
    MELEE_ATTACK = "melee_attack"

    # World events
    COLLISION = "collision"
    SAFE_ZONE_SHRINK = "safe_zone_shrink"
    SAFE_ZONE_EXPAND = "safe_zone_expand"
    ZONE_ENTER = "zone_enter"
    ZONE_EXIT = "zone_exit"

    # System events
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    ENVIRONMENT_RESET = "environment_reset"
    CHECKPOINT_SAVED = "checkpoint_saved"
    REPLAY_SAVED = "replay_saved"

    # Training events
    TRAINING_STARTED = "training_started"
    TRAINING_PAUSED = "training_paused"
    TRAINING_RESUMED = "training_resumed"
    TRAINING_FINISHED = "training_finished"
    TRAINING_INTERRUPTED = "training_interrupted"

    # Model events
    MODEL_LOADED = "model_loaded"
    MODEL_SAVED = "model_saved"
    BEST_MODEL_UPDATE = "best_model_update"

    # Custom events
    CUSTOM = "custom"


class LogLevel(str, Enum):
    """Logging levels for Dashboard logs.

    Standard logging levels following Python's logging module.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class TrainingSession:
    """Training session data model.

    Represents a single training run with all its metadata.
    A session is created when training starts and finished when it ends.

    Attributes:
        session_id: Unique identifier for this session.
        project_name: Name of the project this training belongs to.
        trainer: Training algorithm used (e.g., "PPO", "SAC").
        env_id: Environment ID (e.g., "BattleArena-v2").
        framework_version: ZBGym framework version.
        hostname: Host machine name.
        status: Current session status.
        created_at: Timestamp when session was created.
        updated_at: Timestamp when session was last updated.
        total_timesteps: Target total timesteps for training.
        current_timestep: Current training timestep.
        metadata: Additional session metadata.
    """

    # Default values
    DEFAULT_FRAMEWORK_VERSION: ClassVar[str] = ZBGYM_VERSION

    session_id: str
    project_name: str
    trainer: str
    env_id: str
    framework_version: str = DEFAULT_FRAMEWORK_VERSION
    hostname: str = field(default_factory=socket.gethostname)
    status: str = "running"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    total_timesteps: int = 0
    current_timestep: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        project_name: str,
        trainer: str,
        env_id: str,
        total_timesteps: int = 0,
        **metadata,
    ) -> TrainingSession:
        """Create a new training session.

        Args:
            project_name: Name of the project.
            trainer: Training algorithm name.
            env_id: Environment ID.
            total_timesteps: Target total timesteps.
            **metadata: Additional metadata to store with session.

        Returns:
            New TrainingSession instance.

        Example:
            session = TrainingSession.create(
                project_name="ZoobaBot",
                trainer="PPO",
                env_id="BattleArena-v2",
                total_timesteps=1_000_000,
                config={"learning_rate": 3e-4}
            )
        """
        return cls(
            session_id=str(uuid.uuid4())[:8],
            project_name=project_name,
            trainer=trainer,
            env_id=env_id,
            total_timesteps=total_timesteps,
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary.

        Returns:
            Dictionary representation of the session.
        """
        return {
            "session_id": self.session_id,
            "project_name": self.project_name,
            "trainer": self.trainer,
            "env_id": self.env_id,
            "framework_version": self.framework_version,
            "hostname": self.hostname,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_timesteps": self.total_timesteps,
            "current_timestep": self.current_timestep,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrainingSession:
        """Create session from dictionary.

        Args:
            data: Dictionary containing session data.

        Returns:
            TrainingSession instance.
        """
        return cls(
            session_id=data["session_id"],
            project_name=data["project_name"],
            trainer=data["trainer"],
            env_id=data["env_id"],
            framework_version=data.get("framework_version", cls.DEFAULT_FRAMEWORK_VERSION),
            hostname=data.get("hostname", socket.gethostname()),
            status=data.get("status", "running"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            total_timesteps=data.get("total_timesteps", 0),
            current_timestep=data.get("current_timestep", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MetricsData:
    """Training metrics data model.

    Contains a collection of metrics to be published together.
    Metrics are typically published in batches for efficiency.

    Attributes:
        session_id: Associated session ID.
        timestamp: When these metrics were recorded.
        values: Dictionary of metric name to value.
        episode: Current episode number (if applicable).
        timestep: Current global timestep.
    """

    session_id: str
    timestamp: float = field(default_factory=time.time)
    values: dict[str, float] = field(default_factory=dict)
    episode: int | None = None
    timestep: int | None = None

    def add(self, metric_type: MetricType | str, value: float) -> None:
        """Add a metric value.

        Args:
            metric_type: Type of metric.
            value: Metric value.
        """
        if isinstance(metric_type, MetricType):
            self.values[metric_type.value] = value
        else:
            self.values[metric_type] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "values": self.values,
            "episode": self.episode,
            "timestep": self.timestep,
        }


@dataclass
class EventData:
    """Event data model.

    Represents a single event that occurred during training.
    Events are used to track significant occurrences.

    Attributes:
        session_id: Associated session ID.
        event_type: Type of event.
        timestamp: When the event occurred.
        data: Event-specific data.
        actor: Actor that triggered the event (if applicable).
    """

    session_id: str
    event_type: EventType | str
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)
    actor: str | None = None

    @classmethod
    def create(
        cls,
        session_id: str,
        event_type: EventType | str,
        data: dict[str, Any] | None = None,
        actor: str | None = None,
    ) -> EventData:
        """Create a new event.

        Args:
            session_id: Associated session ID.
            event_type: Type of event.
            data: Event-specific data.
            actor: Actor that triggered the event.

        Returns:
            New EventData instance.
        """
        return cls(
            session_id=session_id,
            event_type=event_type,
            data=data or {},
            actor=actor,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "event_type": self.event_type.value
            if isinstance(self.event_type, EventType)
            else self.event_type,
            "timestamp": self.timestamp,
            "data": self.data,
            "actor": self.actor,
        }


@dataclass
class LogData:
    """Log data model.

    Represents a single log entry to be sent to Dashboard.

    Attributes:
        session_id: Associated session ID.
        level: Log level.
        message: Log message.
        timestamp: When the log was created.
        source: Source of the log (e.g., module name).
    """

    session_id: str
    level: LogLevel | str
    message: str
    timestamp: float = field(default_factory=time.time)
    source: str | None = None

    @classmethod
    def create(
        cls,
        session_id: str,
        level: LogLevel | str,
        message: str,
        source: str | None = None,
    ) -> LogData:
        """Create a new log entry.

        Args:
            session_id: Associated session ID.
            level: Log level.
            message: Log message.
            source: Source module or component.

        Returns:
            New LogData instance.
        """
        return cls(
            session_id=session_id,
            level=level,
            message=message,
            source=source,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert log to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "level": self.level.value if isinstance(self.level, LogLevel) else self.level,
            "message": self.message,
            "timestamp": self.timestamp,
            "source": self.source,
        }


@dataclass
class CheckpointData:
    """Checkpoint data model.

    Represents a model checkpoint to be uploaded.

    Attributes:
        session_id: Associated session ID.
        file_path: Path to the checkpoint file.
        file_size: Size of the checkpoint file in bytes.
        file_type: Type of checkpoint (e.g., ".pt", ".pth").
        timestep: Training timestep when checkpoint was saved.
        is_best: Whether this is the best model so far.
        metrics: Optional metrics snapshot at this checkpoint.
    """

    session_id: str
    file_path: str
    file_size: int = 0
    file_type: str = ""
    timestep: int = 0
    is_best: bool = False
    metrics: dict[str, float] | None = None

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if not self.file_size and self.file_path:
            path = Path(self.file_path)
            if path.exists():
                self.file_size = path.stat().st_size

        if not self.file_type and self.file_path:
            self.file_type = Path(self.file_path).suffix

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "timestep": self.timestep,
            "is_best": self.is_best,
            "metrics": self.metrics,
        }


@dataclass
class ReplayData:
    """Replay data model.

    Represents a training replay to be uploaded.

    Attributes:
        session_id: Associated session ID.
        file_path: Path to the replay file.
        file_size: Size of the replay file in bytes.
        episode: Episode number this replay is from.
        duration: Duration of the replay in seconds.
    """

    session_id: str
    file_path: str
    file_size: int = 0
    episode: int = 0
    duration: float = 0.0

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if not self.file_size and self.file_path:
            path = Path(self.file_path)
            if path.exists():
                self.file_size = path.stat().st_size

    def to_dict(self) -> dict[str, Any]:
        """Convert replay to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "episode": self.episode,
            "duration": self.duration,
        }
