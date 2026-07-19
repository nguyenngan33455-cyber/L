"""Replay recorder for ZBGym."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from zbgym.replay.base import Replay, ReplayMetadata, Step


class ReplayRecorder:
    """
    Records episodes to replay files.

    Usage:
        recorder = ReplayRecorder("BattleArena-v1")
        recorder.start()

        # In training loop:
        recorder.record_step(state, obs, actions, rewards, dones, infos)

        # End of episode:
        replay = recorder.stop()
        recorder.save(replay, "episode_1.replay")
    """

    def __init__(
        self,
        env_id: str = "BattleArena-v1",
        algorithm: str = "unknown",
        compress: bool = True,
    ) -> None:
        """
        Initialize replay recorder.

        Args:
            env_id: Environment ID
            algorithm: Algorithm name
            compress: Whether to compress replays
        """
        self.env_id = env_id
        self.algorithm = algorithm
        self.compress = compress

        self._current_replay: Replay | None = None
        self._current_tick: int = 0
        self._recording: bool = False

    def start(
        self,
        seed: int | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """
        Start recording a new episode.

        Args:
            seed: Random seed
            tags: Tags for this episode
        """
        self._current_replay = Replay(
            metadata=ReplayMetadata(
                env_id=self.env_id,
                algorithm=self.algorithm,
                seed=seed,
                tags=tags or [],
                compression="gzip" if self.compress else "none",
            )
        )
        self._current_tick = 0
        self._recording = True

    def record_step(
        self,
        state: dict[str, Any],
        observations: dict[str, np.ndarray],
        actions: dict[str, int | np.ndarray],
        rewards: dict[str, float],
        dones: dict[str, bool],
        infos: dict[str, Any],
    ) -> None:
        """
        Record a single step.

        Args:
            state: Current game state
            observations: Agent observations
            actions: Agent actions
            rewards: Agent rewards
            dones: Agent done flags
            infos: Additional info
        """
        if not self._recording or self._current_replay is None:
            return

        step = Step(
            tick=self._current_tick,
            state=state,
            observations=observations,
            actions=actions,
            rewards=rewards,
            dones=dones,
            infos=infos,
        )

        self._current_replay.add_step(step)
        self._current_tick += 1

        # Update metadata
        self._current_replay.metadata.episode_length = len(self._current_replay)

    def stop(self) -> Replay | None:
        """
        Stop recording and return the replay.

        Returns:
            Recorded replay or None if not recording
        """
        if not self._recording or self._current_replay is None:
            return None

        self._recording = False
        self._current_replay.metadata.total_ticks = len(self._current_replay)
        self._current_replay.metadata.episode_reward = self._current_replay.total_reward
        self._current_replay.metadata.num_agents = len(self._current_replay.steps[0].rewards) if self._current_replay.steps else 0

        replay = self._current_replay
        self._current_replay = None
        return replay

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    def save(self, replay: Replay, path: str | None = None) -> str:
        """
        Save replay to file.

        Args:
            replay: Replay to save
            path: Path to save to (auto-generates if None)

        Returns:
            Path where replay was saved
        """
        from pathlib import Path
        import time

        if path is None:
            timestamp = int(time.time())
            path = f"replay_{timestamp}.replay"

        path = Path(path)

        if self.compress:
            data = replay.compress()
            path.write_bytes(data)
        else:
            path.write_text(replay.to_json())

        return str(path)

    def load(self, path: str | Path) -> Replay:
        """
        Load replay from file.

        Args:
            path: Path to replay file

        Returns:
            Loaded replay
        """
        path = Path(path)

        if path.suffix == ".replay":
            data = path.read_bytes()
            return Replay.decompress(data)
        else:
            import json
            return Replay.from_dict(json.loads(path.read_text()))


class ReplayCallback:
    """Callback to record replays during training."""

    def __init__(
        self,
        recorder: ReplayRecorder,
        save_freq: int = 1,
        save_dir: str = "./replays",
    ) -> None:
        """
        Initialize replay callback.

        Args:
            recorder: Replay recorder
            save_freq: Save replay every N episodes
            save_dir: Directory to save replays
        """
        self.recorder = recorder
        self.save_freq = save_freq
        self.save_dir = Path(save_dir)
        self.episode_count: int = 0

    def __call__(
        self,
        locals: dict,
        globals: dict,
    ) -> bool:
        """Called at each step."""
        # Get step data from SB3 locals
        if "infos" in locals:
            infos = locals.get("infos", [{}])
            for info in infos:
                if info.get("episode"):
                    self._on_episode_end(locals, info)
        return True

    def _on_episode_end(self, locals: dict, info: dict) -> None:
        """Handle episode end."""
        self.episode_count += 1

        if self.episode_count % self.save_freq == 0:
            replay = self.recorder.stop()
            if replay:
                self.save_dir.mkdir(parents=True, exist_ok=True)
                path = self.save_dir / f"episode_{self.episode_count}.replay"
                self.recorder.save(replay, str(path))

        # Start new recording
        self.recorder.start()
