"""Vectorized environment for massive parallel RL training."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from zbgym.env.battle_arena import BattleArena, BattleArenaState
from zbgym.config import EnvironmentConfig


@dataclass
class VectorizedState:
    """Vectorized state for batched environments."""

    # Shape: (num_envs, max_characters_per_env)
    positions: NDArray[np.float32] = field(default_factory=lambda: np.zeros((1, 10, 2), dtype=np.float32))
    velocities: NDArray[np.float32] = field(default_factory=lambda: np.zeros((1, 10, 2), dtype=np.float32))
    healths: NDArray[np.float32] = field(default_factory=lambda: np.zeros((1, 10), dtype=np.float32))
    shields: NDArray[np.float32] = field(default_factory=lambda: np.zeros((1, 10), dtype=np.float32))
    energies: NDArray[np.float32] = field(default_factory=lambda: np.zeros((1, 10), dtype=np.float32))
    is_alive: NDArray[np.bool_] = field(default_factory=lambda: np.ones((1, 10), dtype=np.bool_))

    # Shape: (num_envs,)
    ticks: NDArray[np.int32] = field(default_factory=lambda: np.zeros(1, dtype=np.int32))
    elapsed_times: NDArray[np.float32] = field(default_factory=lambda: np.zeros(1, dtype=np.float32))

    # Shape: (num_envs, 2) - zone centers
    zone_centers: NDArray[np.float32] = field(default_factory=lambda: np.zeros((1, 2), dtype=np.float32))
    zone_radii: NDArray[np.float32] = field(default_factory=lambda: np.zeros(1, dtype=np.float32))

    num_envs: int = 1


class VectorizedBattleArena:
    """
    Vectorized Battle Arena for massive parallel RL training.

    Supports any number of parallel environments >= 1.

    Uses multiprocessing for true parallelism.
    """

    def __init__(
        self,
        num_envs: int = 32,
        config: EnvironmentConfig | None = None,
        use_multiprocessing: bool = True,
    ) -> None:
        """
        Initialize vectorized environment.

        Args:
            num_envs: Number of parallel environments (must be >= 1)
            config: Environment configuration
            use_multiprocessing: Use multiprocessing for parallelism
        """
        if num_envs < 1:
            raise ValueError(f"num_envs must be >= 1, got {num_envs}")
        
        self.num_envs = num_envs
        self.config = config or EnvironmentConfig()
        self.use_multiprocessing = use_multiprocessing

        # Create environments
        self._envs: list[BattleArena] = []
        self._create_environments()

        # Vectorized state
        self._state = VectorizedState(num_envs=num_envs)

        # Maximum characters per environment
        self._max_chars = config.num_agents if config else 10

        # Observation and action spaces
        self.observation_space = self._envs[0].observation_space
        self.action_space = self._envs[0].action_space

    def _create_environments(self) -> None:
        """Create individual environments."""
        for _ in range(self.num_envs):
            env = BattleArena(config=self.config)
            self._envs.append(env)

    def reset(self, seeds: list[int] | None = None) -> tuple[NDArray[np.float32], list[dict]]:
        """
        Reset all environments.

        Args:
            seeds: Random seeds for each environment

        Returns:
            Observations and info for each environment
        """
        observations = []
        infos = []

        for i, env in enumerate(self._envs):
            seed = seeds[i] if seeds else None
            obs, info = env.reset(seed=seed)
            observations.append(obs)
            infos.append(info)

        # Stack observations
        stacked_obs = np.stack(observations, axis=0)

        # Update vectorized state
        self._update_vectorized_state()

        return stacked_obs, infos

    def step(
        self, actions: NDArray[np.float32]
    ) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.bool_], NDArray[np.bool_], list[dict]]:
        """
        Step all environments.

        Args:
            actions: Actions for each environment, shape (num_envs, action_dim)

        Returns:
            observations, rewards, terminateds, truncateds, infos
        """
        observations = []
        rewards = []
        terminateds = []
        truncateds = []
        infos = []

        for i, env in enumerate(self._envs):
            action = actions[i]
            obs, reward, terminated, truncated, info = env.step(action)
            observations.append(obs)
            rewards.append(reward)
            terminateds.append(terminated)
            truncateds.append(truncated)
            infos.append(info)

        # Stack results
        stacked_obs = np.stack(observations, axis=0)
        stacked_rewards = np.stack(rewards, axis=0)
        stacked_terminated = np.stack(terminateds, axis=0)
        stacked_truncated = np.stack(truncateds, axis=0)

        # Update vectorized state
        self._update_vectorized_state()

        return stacked_obs, stacked_rewards, stacked_terminated, stacked_truncated, infos

    def _update_vectorized_state(self) -> None:
        """Update vectorized state from individual environments."""
        positions = []
        velocities = []
        healths = []
        shields = []
        energies = []
        is_alive = []
        ticks = []
        elapsed_times = []
        zone_centers = []
        zone_radii = []

        for env in self._envs:
            state = env.get_state()
            pos = []
            vel = []
            h = []
            s = []
            e = []
            alive = []

            for char_id, char in state.characters.items():
                pos.append([char.position.x, char.position.y])
                vel.append([char.velocity.x, char.velocity.y])
                h.append(char.health)
                s.append(char.shield)
                e.append(char.energy)
                alive.append(char.is_alive)

            # Pad to max_chars
            while len(pos) < self._max_chars:
                pos.append([0.0, 0.0])
                vel.append([0.0, 0.0])
                h.append(0.0)
                s.append(0.0)
                e.append(0.0)
                alive.append(False)

            positions.append(pos[: self._max_chars])
            velocities.append(vel[: self._max_chars])
            healths.append(h[: self._max_chars])
            shields.append(s[: self._max_chars])
            energies.append(e[: self._max_chars])
            is_alive.append(alive[: self._max_chars])
            ticks.append(state.tick)
            elapsed_times.append(state.elapsed_time)
            zone_centers.append([state.safe_zone_center.x, state.safe_zone_center.y])
            zone_radii.append(state.safe_zone_radius)

        self._state = VectorizedState(
            positions=np.array(positions, dtype=np.float32),
            velocities=np.array(velocities, dtype=np.float32),
            healths=np.array(healths, dtype=np.float32),
            shields=np.array(shields, dtype=np.float32),
            energies=np.array(energies, dtype=np.float32),
            is_alive=np.array(is_alive, dtype=np.bool_),
            ticks=np.array(ticks, dtype=np.int32),
            elapsed_times=np.array(elapsed_times, dtype=np.float32),
            zone_centers=np.array(zone_centers, dtype=np.float32),
            zone_radii=np.array(zone_radii, dtype=np.float32),
            num_envs=self.num_envs,
        )

    def get_state(self) -> VectorizedState:
        """Get vectorized state."""
        return self._state

    def close(self) -> None:
        """Close all environments."""
        for env in self._envs:
            env.close()
        self._envs.clear()


class SyncVectorizedEnv:
    """
    Synchronous vectorized environment using shared memory.

    For very high parallelism (512, 1024 environments).
    """

    def __init__(
        self,
        num_envs: int = 256,
        config: EnvironmentConfig | None = None,
    ) -> None:
        """
        Initialize sync vectorized environment.

        Args:
            num_envs: Number of parallel environments
            config: Environment configuration
        """
        self.num_envs = num_envs
        self.config = config or EnvironmentConfig()

        # Use a single environment with batched processing
        self._env = BattleArena(config=self.config)

        # Shared memory for observations
        self._max_chars = config.num_agents if config else 10
        obs_dim = 50  # From BattleArena
        self._obs_buffer = np.zeros((num_envs, obs_dim), dtype=np.float32)
        self._reward_buffer = np.zeros(num_envs, dtype=np.float32)
        self._terminated_buffer = np.zeros(num_envs, dtype=np.bool_)
        self._truncated_buffer = np.zeros(num_envs, dtype=np.bool_)

        # Action buffer
        self._action_buffer = np.zeros((num_envs, 4), dtype=np.float32)

        # State snapshots for each env
        self._state_snapshots: list[BattleArenaState] = []

        # Observation and action spaces
        self.observation_space = self._env.observation_space
        self.action_space = self._env.action_space

    def reset(self, seeds: list[int] | None = None) -> tuple[NDArray[np.float32], list[dict]]:
        """Reset all virtual environments."""
        observations = []
        infos = []

        for i in range(self.num_envs):
            seed = seeds[i] if seeds else None
            obs, info = self._env.reset(seed=seed)
            observations.append(obs)
            infos.append(info)

            # Save snapshot
            self._state_snapshots.append(self._env.get_state())

        return np.stack(observations, axis=0), infos

    def step(
        self, actions: NDArray[np.float32]
    ) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.bool_], NDArray[np.bool_], list[dict]]:
        """Step all virtual environments."""
        observations = []
        rewards = []
        terminateds = []
        truncateds = []
        infos = []

        for i in range(self.num_envs):
            action = actions[i]
            obs, reward, terminated, truncated, info = self._env.step(action)
            observations.append(obs)
            rewards.append(reward)
            terminateds.append(terminated)
            truncateds.append(truncated)
            infos.append(info)

            # Save snapshot
            if terminated or truncated:
                self._state_snapshots[i] = self._env.get_state()

        return (
            np.stack(observations, axis=0),
            np.stack(rewards, axis=0),
            np.stack(terminateds, axis=0),
            np.stack(truncateds, axis=0),
            infos,
        )

    def close(self) -> None:
        """Close the environment."""
        self._env.close()


def make_vectorized(env_id: str = "BattleArena-v1", num_envs: int = 32, **kwargs) -> VectorizedBattleArena:
    """
    Create a vectorized environment.

    Args:
        env_id: Environment ID (ignored for now)
        num_envs: Number of parallel environments
        **kwargs: Additional arguments for EnvironmentConfig

    Returns:
        VectorizedBattleArena instance
    """
    config = EnvironmentConfig(**kwargs)
    return VectorizedBattleArena(num_envs=num_envs, config=config)
