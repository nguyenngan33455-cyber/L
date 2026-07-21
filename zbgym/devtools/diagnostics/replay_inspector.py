"""Replay file inspector for ZBGym."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from zbgym.replay.base import Replay


@dataclass
class ReplayInfo:
    """Information about a replay."""

    path: str
    size_bytes: int
    metadata: dict[str, Any]
    step_count: int
    tick_range: tuple[int, int]
    checksum: str
    hash_valid: bool = True
    errors: list[str] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


class ReplayInspector:
    """
    Inspect replay files.

    Displays detailed information about replays.
    """

    def __init__(self) -> None:
        """Initialize the inspector."""
        self._errors: list[str] = []

    def inspect(self, path: Path | str) -> ReplayInfo | None:
        """
        Inspect a replay file.

        Args:
            path: Path to replay file

        Returns:
            ReplayInfo if successful, None otherwise
        """
        path = Path(path)
        self._errors = []

        if not path.exists():
            self._errors.append(f"File not found: {path}")
            return None

        try:
            # Load replay
            if path.suffix == ".replay":
                data = path.read_bytes()
                replay = Replay.decompress(data)
            else:
                data = path.read_text()
                replay = Replay.from_dict(json.loads(data))

        except Exception as e:
            self._errors.append(f"Failed to load replay: {e}")
            return None

        # Calculate checksum
        checksum = self._calculate_checksum(data)

        # Get metadata
        metadata = {
            "env_id": replay.metadata.env_id,
            "seed": replay.metadata.seed,
            "algorithm": replay.metadata.algorithm,
            "total_ticks": replay.metadata.total_ticks,
            "episode_length": replay.metadata.episode_length,
            "episode_reward": replay.metadata.episode_reward,
            "num_agents": replay.metadata.num_agents,
            "created_at": replay.metadata.created_at.isoformat() if replay.metadata.created_at else None,
        }

        # Get tick range
        tick_range = (0, 0)
        if replay.steps:
            ticks = [step.tick for step in replay.steps]
            tick_range = (min(ticks), max(ticks))

        info = ReplayInfo(
            path=str(path),
            size_bytes=len(data),
            metadata=metadata,
            step_count=len(replay.steps),
            tick_range=tick_range,
            checksum=checksum,
            errors=self._errors,
        )

        return info

    def verify(self, path: Path | str) -> tuple[bool, list[str]]:
        """
        Verify a replay file.

        Args:
            path: Path to replay file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        path = Path(path)

        if not path.exists():
            return False, [f"File not found: {path}"]

        try:
            if path.suffix == ".replay":
                data = path.read_bytes()
                replay = Replay.decompress(data)
            else:
                data = path.read_text()
                replay = Replay.from_dict(json.loads(data))

        except Exception as e:
            return False, [f"Failed to load replay: {e}"]

        # Verify structure
        if not replay.steps:
            errors.append("Replay has no steps")

        # Verify tick sequence
        if replay.steps:
            ticks = [step.tick for step in replay.steps]
            expected = list(range(len(ticks)))
            if ticks != expected:
                errors.append("Tick sequence is not sequential")

        # Verify metadata
        if replay.metadata.env_id is None:
            errors.append("Missing env_id")

        if replay.metadata.seed is None:
            errors.append("Missing seed")

        return len(errors) == 0, errors

    def get_hash(self, path: Path | str) -> str | None:
        """
        Get the hash of a replay file.

        Args:
            path: Path to replay file

        Returns:
            SHA256 hash or None
        """
        path = Path(path)

        if not path.exists():
            return None

        try:
            data = path.read_bytes()
            return self._calculate_checksum(data)
        except Exception:
            return None

    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA256 checksum."""
        return hashlib.sha256(data).hexdigest()

    def print_info(self, info: ReplayInfo) -> None:
        """Print replay information."""
        print("\n" + "=" * 60)
        print("Replay Inspector")
        print("=" * 60)
        print(f"Path: {info.path}")
        print(f"Size: {info.size_bytes / 1024:.2f} KB")
        print("-" * 60)

        print("\nMetadata:")
        for key, value in info.metadata.items():
            print(f"  {key}: {value}")

        print(f"\nSteps: {info.step_count}")
        print(f"Tick Range: {info.tick_range[0]} - {info.tick_range[1]}")
        print(f"Checksum: {info.checksum[:32]}...")

        if info.errors:
            print("\nErrors:")
            for error in info.errors:
                print(f"  - {error}")

        print("=" * 60)

    def extract_statistics(self, path: Path | str) -> dict[str, Any]:
        """
        Extract statistics from a replay.

        Args:
            path: Path to replay file

        Returns:
            Statistics dictionary
        """
        path = Path(path)

        try:
            if path.suffix == ".replay":
                data = path.read_bytes()
                replay = Replay.decompress(data)
            else:
                data = path.read_text()
                replay = Replay.from_dict(json.loads(data))

        except Exception:
            return {}

        stats = {
            "step_count": len(replay.steps),
            "total_ticks": replay.metadata.total_ticks,
            "episode_reward": replay.metadata.episode_reward,
            "num_agents": replay.metadata.num_agents,
        }

        # Action statistics
        if replay.steps:
            all_actions = {}
            for step in replay.steps:
                for agent, action in step.actions.items():
                    if agent not in all_actions:
                        all_actions[agent] = {}
                    action_key = str(action)
                    all_actions[agent][action_key] = all_actions[agent].get(action_key, 0) + 1

            stats["actions"] = all_actions

        # Reward statistics
        if replay.steps:
            for agent in range(replay.metadata.num_agents or 0):
                agent_key = f"agent_{agent}"
                rewards = [
                    step.rewards.get(agent_key, 0)
                    for step in replay.steps
                    if agent_key in step.rewards
                ]
                if rewards:
                    stats[f"{agent_key}_total_reward"] = sum(rewards)
                    stats[f"{agent_key}_avg_reward"] = sum(rewards) / len(rewards)

        return stats


def inspect_replay(path: Path | str) -> ReplayInfo | None:
    """Quick replay inspection."""
    inspector = ReplayInspector()
    info = inspector.inspect(path)
    if info:
        inspector.print_info(info)
    return info


def verify_replay(path: Path | str) -> bool:
    """Quick replay verification."""
    inspector = ReplayInspector()
    valid, errors = inspector.verify(path)

    if valid:
        print(f"✅ Replay is valid: {path}")
    else:
        print(f"❌ Replay has issues: {path}")
        for error in errors:
            print(f"  - {error}")

    return valid
