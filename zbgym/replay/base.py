"""Base classes for ZBGym replay system."""

from __future__ import annotations

import gzip
import json
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class Step:
    """Single step in a replay."""

    tick: int
    state: dict[str, Any]
    observations: dict[str, np.ndarray]
    actions: dict[str, int | np.ndarray]
    rewards: dict[str, float]
    dones: dict[str, bool]
    infos: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tick": self.tick,
            "state": self.state,
            "observations": {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in self.observations.items()
            },
            "actions": {
                k: int(v)
                if isinstance(v, (np.int32, np.int64))
                else v.tolist()
                if isinstance(v, np.ndarray)
                else v
                for k, v in self.actions.items()
            },
            "rewards": self.rewards,
            "dones": self.dones,
            "infos": self.infos,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Step:
        """Create from dictionary."""
        return cls(
            tick=data["tick"],
            state=data["state"],
            observations={
                k: np.array(v) if isinstance(v, list) else v
                for k, v in data["observations"].items()
            },
            actions=data["actions"],
            rewards=data["rewards"],
            dones=data["dones"],
            infos=data["infos"],
        )


@dataclass
class ReplayMetadata:
    """Metadata for a replay."""

    env_id: str
    version: str = "1.0"
    created_at: float = field(default_factory=time.time)
    total_ticks: int = 0
    num_agents: int = 0
    episode_reward: float = 0.0
    episode_length: int = 0
    algorithm: str = "unknown"
    seed: int | None = None
    tags: list[str] = field(default_factory=list)
    compression: str = "gzip"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "env_id": self.env_id,
            "version": self.version,
            "created_at": self.created_at,
            "total_ticks": self.total_ticks,
            "num_agents": self.num_agents,
            "episode_reward": self.episode_reward,
            "episode_length": self.episode_length,
            "algorithm": self.algorithm,
            "seed": self.seed,
            "tags": self.tags,
            "compression": self.compression,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReplayMetadata:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Replay:
    """Complete replay of an episode."""

    metadata: ReplayMetadata
    steps: list[Step] = field(default_factory=list)

    def add_step(self, step: Step) -> None:
        """Add a step to the replay."""
        self.steps.append(step)
        self.metadata.total_ticks = len(self.steps)

    def get_step(self, tick: int) -> Step | None:
        """Get a step by tick."""
        if 0 <= tick < len(self.steps):
            return self.steps[tick]
        return None

    def __iter__(self) -> Iterator[Step]:
        """Iterate over steps."""
        return iter(self.steps)

    def __len__(self) -> int:
        """Get number of steps."""
        return len(self.steps)

    @property
    def total_reward(self) -> float:
        """Get total reward across all steps."""
        return sum(sum(s.rewards.values()) for s in self.steps)

    def get_stats(self) -> dict[str, Any]:
        """Get replay statistics."""
        if not self.steps:
            return {}

        return {
            "total_ticks": len(self.steps),
            "total_reward": self.total_reward,
            "metadata": self.metadata.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def compress(self, level: int = 6) -> bytes:
        """Compress replay to bytes."""
        json_data = self.to_json()
        return gzip.compress(json_data.encode(), compresslevel=level)

    @classmethod
    def decompress(cls, data: bytes) -> Replay:
        """Decompress replay from bytes."""
        json_data = gzip.decompress(data).decode()
        return cls.from_dict(json.loads(json_data))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Replay:
        """Create from dictionary."""
        metadata = ReplayMetadata.from_dict(data["metadata"])
        steps = [Step.from_dict(s) for s in data["steps"]]
        return cls(metadata=metadata, steps=steps)


class ReplayBuffer:
    """Buffer for storing multiple replays."""

    def __init__(self, max_size: int = 1000) -> None:
        """
        Initialize replay buffer.

        Args:
            max_size: Maximum number of replays to store
        """
        self.max_size = max_size
        self.replays: list[Replay] = []

    def add(self, replay: Replay) -> None:
        """Add a replay to the buffer."""
        self.replays.append(replay)
        if len(self.replays) > self.max_size:
            self.replays.pop(0)

    def get(self, index: int) -> Replay | None:
        """Get a replay by index."""
        if 0 <= index < len(self.replays):
            return self.replays[index]
        return None

    def get_best(self, n: int = 10) -> list[Replay]:
        """Get top N replays by reward."""
        sorted_replays = sorted(
            self.replays,
            key=lambda r: r.total_reward,
            reverse=True,
        )
        return sorted_replays[:n]

    def __len__(self) -> int:
        """Get number of replays."""
        return len(self.replays)

    def __iter__(self) -> Iterator[Replay]:
        """Iterate over replays."""
        return iter(self.replays)
