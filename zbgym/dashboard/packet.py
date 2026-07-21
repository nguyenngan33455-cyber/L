"""Dashboard packet protocol for ZBGym.

This module implements the packet protocol used for communication
between the ZBGym framework and the Dashboard server.

Packet Format:
{
    "type": "packet_type",
    "session": "session_id",
    "timestamp": 1234567890.123,
    "seq": 123,
    "payload": {...}
}
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from zbgym.dashboard.exceptions import DashboardProtocolError
from zbgym.dashboard.models import PacketType

# Protocol version
PROTOCOL_VERSION = "1.0"


@dataclass
class Packet:
    """Base packet class for Dashboard protocol.

    All packets follow a standard format with type, session,
    timestamp, sequence number, and payload.

    Attributes:
        type: Type of packet (PacketType enum).
        session: Session ID this packet belongs to.
        timestamp: Unix timestamp when packet was created.
        seq: Sequence number for ordering.
        payload: Packet-specific data.
        protocol_version: Protocol version being used.
    """

    type: PacketType
    session: str
    timestamp: float = field(default_factory=time.time)
    seq: int = 0
    payload: dict[str, Any] = field(default_factory=dict)
    protocol_version: str = PROTOCOL_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Convert packet to dictionary.

        Returns:
            Dictionary representation of the packet.
        """
        return {
            "type": self.type.value if hasattr(self.type, "value") else self.type,
            "session": self.session,
            "timestamp": self.timestamp,
            "seq": self.seq,
            "protocol_version": self.protocol_version,
            "payload": self.payload,
        }

    def to_json(self) -> str:
        """Convert packet to JSON string.

        Returns:
            JSON string representation.

        Raises:
            DashboardProtocolError: If packet cannot be serialized.
        """
        try:
            return json.dumps(self.to_dict())
        except (TypeError, ValueError) as e:
            raise DashboardProtocolError(
                f"Failed to serialize packet: {e}",
                packet_type=self.type.value if hasattr(self.type, "value") else self.type,
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Packet:
        """Create packet from dictionary.

        Args:
            data: Dictionary containing packet data.

        Returns:
            Packet instance.

        Raises:
            DashboardProtocolError: If required fields are missing.
        """
        # Validate required fields
        required = ["type", "session"]
        for field_name in required:
            if field_name not in data:
                raise DashboardProtocolError(
                    f"Missing required field: {field_name}",
                    field=field_name,
                )

        # Parse packet type
        packet_type = data["type"]
        if isinstance(packet_type, str):
            try:
                packet_type = PacketType(packet_type)
            except ValueError:
                raise DashboardProtocolError(
                    f"Invalid packet type: {packet_type}",
                    packet_type=packet_type,
                )

        return cls(
            type=packet_type,
            session=data["session"],
            timestamp=data.get("timestamp", time.time()),
            seq=data.get("seq", 0),
            payload=data.get("payload", {}),
            protocol_version=data.get("protocol_version", PROTOCOL_VERSION),
        )

    @classmethod
    def from_json(cls, json_str: str) -> Packet:
        """Create packet from JSON string.

        Args:
            json_str: JSON string containing packet data.

        Returns:
            Packet instance.

        Raises:
            DashboardProtocolError: If JSON is invalid or packet cannot be parsed.
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise DashboardProtocolError(
                f"Invalid JSON in packet: {e}",
            )


@dataclass
class AuthPacket(Packet):
    """Authentication packet.

    Used to authenticate with the Dashboard server.
    """

    def __init__(self, api_key: str, session: str = "") -> None:
        """Initialize authentication packet.

        Args:
            api_key: API key for authentication.
            session: Session ID (empty for auth packet).
        """
        super().__init__(
            type=PacketType.AUTH,
            session=session,
            payload={"api_key": api_key},
        )


@dataclass
class HeartbeatPacket(Packet):
    """Heartbeat packet.

    Sent periodically to keep connection alive and check server health.
    """

    def __init__(self, session: str) -> None:
        """Initialize heartbeat packet.

        Args:
            session: Session ID to keep alive.
        """
        super().__init__(
            type=PacketType.HEARTBEAT,
            session=session,
            payload={},
        )


@dataclass
class MetricsPacket(Packet):
    """Metrics packet.

    Contains training metrics to be published.
    """

    def __init__(self, session: str, metrics: dict[str, float]) -> None:
        """Initialize metrics packet.

        Args:
            session: Session ID.
            metrics: Dictionary of metric names to values.
        """
        super().__init__(
            type=PacketType.METRICS,
            session=session,
            payload={"metrics": metrics},
        )


@dataclass
class EventPacket(Packet):
    """Event packet.

    Contains an event to be logged.
    """

    def __init__(
        self,
        session: str,
        event_type: str,
        event_data: dict[str, Any],
        actor: str | None = None,
    ) -> None:
        """Initialize event packet.

        Args:
            session: Session ID.
            event_type: Type of event.
            event_data: Event-specific data.
            actor: Actor that triggered the event.
        """
        payload = {"event_type": event_type, "data": event_data}
        if actor:
            payload["actor"] = actor

        super().__init__(
            type=PacketType.EVENT,
            session=session,
            payload=payload,
        )


@dataclass
class LogPacket(Packet):
    """Log packet.

    Contains a log message to be recorded.
    """

    def __init__(
        self,
        session: str,
        level: str,
        message: str,
        source: str | None = None,
    ) -> None:
        """Initialize log packet.

        Args:
            session: Session ID.
            level: Log level (debug, info, warning, error, critical).
            message: Log message.
            source: Source of the log.
        """
        payload = {"level": level, "message": message}
        if source:
            payload["source"] = source

        super().__init__(
            type=PacketType.LOG,
            session=session,
            payload=payload,
        )


@dataclass
class CheckpointPacket(Packet):
    """Checkpoint packet.

    Contains metadata about a checkpoint to be uploaded.
    """

    def __init__(
        self,
        session: str,
        file_path: str,
        file_size: int,
        file_type: str,
        timestep: int,
        is_best: bool = False,
        metrics: dict[str, float] | None = None,
    ) -> None:
        """Initialize checkpoint packet.

        Args:
            session: Session ID.
            file_path: Path to checkpoint file.
            file_size: Size of file in bytes.
            file_type: File extension (e.g., ".pt").
            timestep: Training timestep.
            is_best: Whether this is the best model.
            metrics: Optional metrics snapshot.
        """
        payload = {
            "file_path": file_path,
            "file_size": file_size,
            "file_type": file_type,
            "timestep": timestep,
            "is_best": is_best,
        }
        if metrics:
            payload["metrics"] = metrics

        super().__init__(
            type=PacketType.CHECKPOINT,
            session=session,
            payload=payload,
        )


@dataclass
class ReplayPacket(Packet):
    """Replay packet.

    Contains metadata about a replay to be uploaded.
    """

    def __init__(
        self,
        session: str,
        file_path: str,
        file_size: int,
        episode: int,
        duration: float,
    ) -> None:
        """Initialize replay packet.

        Args:
            session: Session ID.
            file_path: Path to replay file.
            file_size: Size of file in bytes.
            episode: Episode number.
            duration: Duration in seconds.
        """
        super().__init__(
            type=PacketType.REPLAY,
            session=session,
            payload={
                "file_path": file_path,
                "file_size": file_size,
                "episode": episode,
                "duration": duration,
            },
        )


@dataclass
class SessionCreatePacket(Packet):
    """Session creation packet.

    Sent to create a new training session on the server.
    """

    def __init__(
        self,
        session_id: str,
        project_name: str,
        trainer: str,
        env_id: str,
        total_timesteps: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize session creation packet.

        Args:
            session_id: Unique session identifier.
            project_name: Name of the project.
            trainer: Training algorithm name.
            env_id: Environment ID.
            total_timesteps: Target total timesteps.
            metadata: Additional session metadata.
        """
        super().__init__(
            type=PacketType.SESSION_CREATE,
            session=session_id,
            payload={
                "project_name": project_name,
                "trainer": trainer,
                "env_id": env_id,
                "total_timesteps": total_timesteps,
                "metadata": metadata or {},
            },
        )


@dataclass
class SessionUpdatePacket(Packet):
    """Session update packet.

    Sent to update session status or progress.
    """

    def __init__(
        self,
        session: str,
        status: str | None = None,
        current_timestep: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize session update packet.

        Args:
            session: Session ID.
            status: New session status.
            current_timestep: Current training timestep.
            metadata: Updated metadata.
        """
        payload: dict[str, Any] = {}
        if status is not None:
            payload["status"] = status
        if current_timestep is not None:
            payload["current_timestep"] = current_timestep
        if metadata is not None:
            payload["metadata"] = metadata

        super().__init__(
            type=PacketType.SESSION_UPDATE,
            session=session,
            payload=payload,
        )


@dataclass
class TrainingStartedPacket(Packet):
    """Training started notification packet."""

    def __init__(self, session: str) -> None:
        """Initialize training started packet.

        Args:
            session: Session ID.
        """
        super().__init__(
            type=PacketType.TRAINING_STARTED,
            session=session,
        )


@dataclass
class TrainingFinishedPacket(Packet):
    """Training finished notification packet."""

    def __init__(
        self,
        session: str,
        total_timesteps: int,
        duration: float,
        final_metrics: dict[str, float] | None = None,
    ) -> None:
        """Initialize training finished packet.

        Args:
            session: Session ID.
            total_timesteps: Total timesteps completed.
            duration: Total training duration in seconds.
            final_metrics: Optional final metrics summary.
        """
        super().__init__(
            type=PacketType.TRAINING_FINISHED,
            session=session,
            payload={
                "total_timesteps": total_timesteps,
                "duration": duration,
                "final_metrics": final_metrics or {},
            },
        )


class PacketBuilder:
    """Builder class for creating packets with auto-incrementing sequence.

    This builder maintains a sequence counter and provides convenient
    methods for creating all packet types.

    Example:
        builder = PacketBuilder(session_id="abc123")
        packet = builder.metrics({"reward": 10.5, "loss": 0.5})
        builder.heartbeat()
    """

    def __init__(self, session: str) -> None:
        """Initialize packet builder.

        Args:
            session: Session ID for all packets.
        """
        self.session = session
        self._seq: int = 0

    def _next_seq(self) -> int:
        """Get next sequence number.

        Returns:
            Next sequence number.
        """
        self._seq += 1
        return self._seq

    def heartbeat(self) -> HeartbeatPacket:
        """Create heartbeat packet.

        Returns:
            HeartbeatPacket instance.
        """
        packet = HeartbeatPacket(session=self.session)
        packet.seq = self._next_seq()
        return packet

    def metrics(self, data: dict[str, float]) -> MetricsPacket:
        """Create metrics packet.

        Args:
            data: Dictionary of metric values.

        Returns:
            MetricsPacket instance.
        """
        packet = MetricsPacket(session=self.session, metrics=data)
        packet.seq = self._next_seq()
        return packet

    def event(
        self,
        event_type: str,
        event_data: dict[str, Any],
        actor: str | None = None,
    ) -> EventPacket:
        """Create event packet.

        Args:
            event_type: Type of event.
            event_data: Event data.
            actor: Actor that triggered event.

        Returns:
            EventPacket instance.
        """
        packet = EventPacket(
            session=self.session,
            event_type=event_type,
            event_data=event_data,
            actor=actor,
        )
        packet.seq = self._next_seq()
        return packet

    def log(
        self,
        level: str,
        message: str,
        source: str | None = None,
    ) -> LogPacket:
        """Create log packet.

        Args:
            level: Log level.
            message: Log message.
            source: Log source.

        Returns:
            LogPacket instance.
        """
        packet = LogPacket(
            session=self.session,
            level=level,
            message=message,
            source=source,
        )
        packet.seq = self._next_seq()
        return packet

    def checkpoint(
        self,
        file_path: str,
        file_size: int,
        file_type: str,
        timestep: int,
        is_best: bool = False,
        metrics: dict[str, float] | None = None,
    ) -> CheckpointPacket:
        """Create checkpoint packet.

        Args:
            file_path: Path to checkpoint file.
            file_size: File size in bytes.
            file_type: File extension.
            timestep: Training timestep.
            is_best: Whether this is the best model.
            metrics: Optional metrics.

        Returns:
            CheckpointPacket instance.
        """
        packet = CheckpointPacket(
            session=self.session,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            timestep=timestep,
            is_best=is_best,
            metrics=metrics,
        )
        packet.seq = self._next_seq()
        return packet

    def replay(
        self,
        file_path: str,
        file_size: int,
        episode: int,
        duration: float,
    ) -> ReplayPacket:
        """Create replay packet.

        Args:
            file_path: Path to replay file.
            file_size: File size in bytes.
            episode: Episode number.
            duration: Duration in seconds.

        Returns:
            ReplayPacket instance.
        """
        packet = ReplayPacket(
            session=self.session,
            file_path=file_path,
            file_size=file_size,
            episode=episode,
            duration=duration,
        )
        packet.seq = self._next_seq()
        return packet

    def training_started(self) -> TrainingStartedPacket:
        """Create training started packet.

        Returns:
            TrainingStartedPacket instance.
        """
        packet = TrainingStartedPacket(session=self.session)
        packet.seq = self._next_seq()
        return packet

    def training_finished(
        self,
        total_timesteps: int,
        duration: float,
        final_metrics: dict[str, float] | None = None,
    ) -> TrainingFinishedPacket:
        """Create training finished packet.

        Args:
            total_timesteps: Total timesteps completed.
            duration: Training duration.
            final_metrics: Optional final metrics.

        Returns:
            TrainingFinishedPacket instance.
        """
        packet = TrainingFinishedPacket(
            session=self.session,
            total_timesteps=total_timesteps,
            duration=duration,
            final_metrics=final_metrics,
        )
        packet.seq = self._next_seq()
        return packet
