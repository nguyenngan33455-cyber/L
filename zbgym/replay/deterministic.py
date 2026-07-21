"""Deterministic Replay System for ZBGym."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class Action:
    """An action taken by an agent."""

    agent_id: str
    action_type: str
    action_data: dict[str, Any]
    tick: int = 0
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "action_data": self.action_data,
            "tick": self.tick,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Action:
        return cls(**data)


@dataclass
class StateSnapshot:
    """A snapshot of environment state."""

    tick: int
    state_hash: str
    positions: dict[str, tuple[float, float]]
    velocities: dict[str, tuple[float, float]]
    healths: dict[str, float]
    shields: dict[str, float]
    energies: dict[str, float]
    is_alive: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "state_hash": self.state_hash,
            "positions": self.positions,
            "velocities": self.velocities,
            "healths": self.healths,
            "shields": self.shields,
            "energies": self.energies,
            "is_alive": self.is_alive,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateSnapshot:
        return cls(**data)


@dataclass
class Event:
    """An event in the replay."""

    tick: int
    event_type: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "event_type": self.event_type,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        return cls(**data)


@dataclass
class ReplayStep:
    """A single step in the replay."""

    tick: int

    # Observations (for verification)
    observation: list[float]

    # Actions taken
    actions: list[Action]

    # Rewards received
    rewards: dict[str, float]

    # Events that occurred
    events: list[Event]

    # Projectile states
    projectiles: list[dict[str, Any]] = field(default_factory=list)

    # Damage events
    damages: list[dict[str, Any]] = field(default_factory=list)

    # Cooldown states
    cooldowns: dict[str, dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "observation": self.observation,
            "actions": [a.to_dict() for a in self.actions],
            "rewards": self.rewards,
            "events": [e.to_dict() for e in self.events],
            "projectiles": self.projectiles,
            "damages": self.damages,
            "cooldowns": self.cooldowns,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReplayStep:
        return cls(
            tick=data["tick"],
            observation=data["observation"],
            actions=[Action.from_dict(a) for a in data["actions"]],
            rewards=data["rewards"],
            events=[Event.from_dict(e) for e in data["events"]],
            projectiles=data.get("projectiles", []),
            damages=data.get("damages", []),
            cooldowns=data.get("cooldowns", {}),
        )


@dataclass
class DeterministicReplay:
    """
    Deterministic replay system for ZBGym.

    Records and replays game episodes with full determinism guarantees.
    """

    metadata: dict[str, Any]
    initial_seed: int
    steps: list[ReplayStep] = field(default_factory=list)
    state_snapshots: list[StateSnapshot] = field(default_factory=list)

    def add_step(self, step: ReplayStep) -> None:
        """Add a step to the replay."""
        self.steps.append(step)

    def add_snapshot(self, snapshot: StateSnapshot) -> None:
        """Add a state snapshot."""
        self.state_snapshots.append(snapshot)

    def verify_determinism(self) -> bool:
        """
        Verify that the replay is deterministic.

        Returns:
            True if replay is deterministic
        """
        if not self.state_snapshots:
            return True

        # Check that snapshots are in order
        for i in range(1, len(self.state_snapshots)):
            if self.state_snapshots[i].tick <= self.state_snapshots[i - 1].tick:
                return False

        # Verify state hashes
        for snapshot in self.state_snapshots:
            computed_hash = self._compute_state_hash(snapshot)
            if computed_hash != snapshot.state_hash:
                return False

        return True

    def _compute_state_hash(self, snapshot: StateSnapshot) -> str:
        """Compute hash of a state snapshot."""
        # Create deterministic string representation
        state_str = json.dumps(
            {
                "positions": snapshot.positions,
                "healths": snapshot.healths,
                "shields": snapshot.shields,
                "is_alive": snapshot.is_alive,
            },
            sort_keys=True,
        )
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]

    def save(self, path: Path) -> None:
        """
        Save replay to file.

        Args:
            path: Path to save the replay
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": self.metadata,
            "initial_seed": self.initial_seed,
            "steps": [s.to_dict() for s in self.steps],
            "state_snapshots": [s.to_dict() for s in self.state_snapshots],
        }

        # Compress the data
        json_str = json.dumps(data, ensure_ascii=False)
        compressed = zlib.compress(json_str.encode())

        # Write with header
        with open(path, "wb") as f:
            # Write header
            f.write(b"ZBGR")  # Magic number
            f.write(struct.pack("<I", 1))  # Version
            f.write(struct.pack("<Q", len(compressed)))  # Compressed size
            f.write(compressed)

    @classmethod
    def load(cls, path: Path) -> DeterministicReplay:
        """
        Load replay from file.

        Args:
            path: Path to the replay file

        Returns:
            DeterministicReplay instance
        """
        with open(path, "rb") as f:
            # Read header
            magic = f.read(4)
            if magic != b"ZBGR":
                raise ValueError("Invalid replay file format")

            version = struct.unpack("<I", f.read(4))[0]
            if version != 1:
                raise ValueError(f"Unsupported replay version: {version}")

            compressed_size = struct.unpack("<Q", f.read(8))[0]
            compressed = f.read(compressed_size)

        # Decompress
        json_str = zlib.decompress(compressed).decode()
        data = json.loads(json_str)

        return cls(
            metadata=data["metadata"],
            initial_seed=data["initial_seed"],
            steps=[ReplayStep.from_dict(s) for s in data["steps"]],
            state_snapshots=[StateSnapshot.from_dict(s) for s in data["state_snapshots"]],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata,
            "initial_seed": self.initial_seed,
            "steps": [s.to_dict() for s in self.steps],
            "state_snapshots": [s.to_dict() for s in self.state_snapshots],
        }


class ReplayRecorder:
    """Records episodes for replay."""

    def __init__(self, initial_seed: int, metadata: dict[str, Any] | None = None) -> None:
        """
        Initialize recorder.

        Args:
            initial_seed: Initial random seed
            metadata: Additional metadata
        """
        self.initial_seed = initial_seed
        self.metadata = metadata or {}
        self.steps: list[ReplayStep] = []
        self.snapshots: list[StateSnapshot] = []
        self._current_tick = 0

    def record_step(
        self,
        observation: np.ndarray,
        actions: list[Action],
        rewards: dict[str, float],
        events: list[Event],
        state_snapshot: StateSnapshot | None = None,
        **kwargs,
    ) -> None:
        """
        Record a step.

        Args:
            observation: Current observation
            actions: Actions taken
            rewards: Rewards received
            events: Events that occurred
            state_snapshot: Optional state snapshot
            **kwargs: Additional data (projectiles, damages, cooldowns)
        """
        step = ReplayStep(
            tick=self._current_tick,
            observation=observation.tolist()
            if isinstance(observation, np.ndarray)
            else observation,
            actions=actions,
            rewards=rewards,
            events=events,
            projectiles=kwargs.get("projectiles", []),
            damages=kwargs.get("damages", []),
            cooldowns=kwargs.get("cooldowns", {}),
        )
        self.steps.append(step)

        if state_snapshot:
            self.snapshots.append(state_snapshot)

        self._current_tick += 1

    def finalize(self) -> DeterministicReplay:
        """
        Finalize and return the replay.

        Returns:
            DeterministicReplay instance
        """
        replay = DeterministicReplay(
            metadata=self.metadata,
            initial_seed=self.initial_seed,
            steps=self.steps,
            state_snapshots=self.snapshots,
        )

        # Verify determinism
        if not replay.verify_determinism():
            raise RuntimeWarning("Replay may not be deterministic!")

        return replay

    def save(self, path: Path) -> None:
        """
        Save replay to file.

        Args:
            path: Path to save the replay
        """
        replay = self.finalize()
        replay.save(path)


class ReplayPlayer:
    """Plays back recorded replays."""

    def __init__(self, replay: DeterministicReplay) -> None:
        """
        Initialize player.

        Args:
            replay: The replay to play back
        """
        self.replay = replay
        self.current_step = 0
        self.initial_seed = replay.initial_seed

    def __iter__(self) -> ReplayPlayer:
        """Return iterator."""
        self.current_step = 0
        return self

    def __next__(self) -> ReplayStep:
        """Get next step."""
        if self.current_step >= len(self.replay.steps):
            raise StopIteration
        step = self.replay.steps[self.current_step]
        self.current_step += 1
        return step

    def get_step(self, step_index: int) -> ReplayStep | None:
        """Get a specific step."""
        if 0 <= step_index < len(self.replay.steps):
            return self.replay.steps[step_index]
        return None

    def get_snapshot(self, tick: int) -> StateSnapshot | None:
        """Get snapshot for a specific tick."""
        for snapshot in self.replay.state_snapshots:
            if snapshot.tick == tick:
                return snapshot
        return None

    def get_events_of_type(self, event_type: str) -> list[Event]:
        """Get all events of a specific type."""
        events = []
        for step in self.replay.steps:
            for event in step.events:
                if event.event_type == event_type:
                    events.append(event)
        return events

    def replay_info(self) -> dict[str, Any]:
        """Get replay information."""
        total_damage = 0
        total_kills = 0

        for step in self.replay.steps:
            for damage in step.damages:
                total_damage += damage.get("damage", 0)
            for event in step.events:
                if event.event_type == "character_death":
                    total_kills += 1

        return {
            "duration_ticks": len(self.replay.steps),
            "total_events": sum(len(s.events) for s in self.replay.steps),
            "total_damage": total_damage,
            "total_kills": total_kills,
            "unique_agents": len(set(a.agent_id for s in self.replay.steps for a in s.actions)),
        }


# Aliases for backward compatibility
DeterministicRecorder = ReplayRecorder
DeterministicPlayer = ReplayPlayer
