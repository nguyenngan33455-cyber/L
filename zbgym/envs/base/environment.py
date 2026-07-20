"""Base environment interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import gymnasium as gym
import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from zbgym.envs.adapters.zooba import GameState


@dataclass
class EnvironmentConfig:
    """Base configuration for all environments."""

    name: str = "Base-v0"
    num_agents: int = 2
    max_episode_steps: int = 10000

    # Arena settings
    arena_width: int = 2000
    arena_height: int = 1500

    # Observation
    obs_include_health: bool = True
    obs_include_position: bool = True
    obs_include_velocity: bool = True
    obs_include_vision: bool = True

    # Reward
    reward_config: dict[str, Any] = field(default_factory=dict)


class BaseEnvironment(ABC, gym.Env):
    """
    Abstract base class for all game environments.

    Provides a unified interface for RL training across different games.
    """

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "render_fps": 30,
    }

    def __init__(
        self,
        config: EnvironmentConfig | None = None,
        render_mode: str | None = None,
    ) -> None:
        """
        Initialize base environment.

        Args:
            config: Environment configuration
            render_mode: Rendering mode
        """
        super().__init__()

        self.config = config or EnvironmentConfig()
        self.render_mode = render_mode

        # State
        self._current_step = 0
        self._episode_reward = 0.0

        # Spaces (to be defined by subclasses)
        self.observation_space: gym.Space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(50,),
            dtype=np.float32,
        )
        self.action_space: gym.Space = gym.spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(4,),
            dtype=np.float32,
        )

    @abstractmethod
    def reset(
        self,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[NDArray[np.float32], dict]:
        """
        Reset the environment.

        Args:
            seed: Random seed
            options: Additional reset options

        Returns:
            Initial observation and info dict
        """

    @abstractmethod
    def step(
        self,
        action: NDArray[np.float32] | int,
    ) -> tuple[NDArray[np.float32], float, bool, bool, dict]:
        """
        Execute one step.

        Args:
            action: Action to take

        Returns:
            observation, reward, terminated, truncated, info
        """

    @abstractmethod
    def get_state(self) -> "GameState":
        """Get current game state."""

    @abstractmethod
    def set_state(self, state: "GameState") -> None:
        """Set game state."""

    def render(self) -> NDArray[np.uint8] | None:
        """
        Render the environment.

        Returns:
            RGB array or None
        """
        if self.render_mode is None:
            return None

        # Default: return black image
        width = self.config.arena_width // 4
        height = self.config.arena_height // 4
        return np.zeros((height, width, 3), dtype=np.uint8)

    def close(self) -> None:
        """Clean up environment."""
        pass

    @property
    def spec(self) -> gym.envs.env_spec.EnvSpec | None:
        """Get environment spec."""
        return None

    @property
    def unwrapped(self) -> BaseEnvironment:
        """Get unwrapped environment."""
        return self

    def _get_info(self) -> dict:
        """Get info dictionary."""
        return {
            "step": self._current_step,
            "episode_reward": self._episode_reward,
        }


class VectorizedBase(ABC):
    """
    Base class for vectorized environments.

    Supports batched execution for parallel RL training.
    """

    def __init__(self, num_envs: int = 32) -> None:
        """
        Initialize vectorized environment.

        Args:
            num_envs: Number of parallel environments
        """
        self.num_envs = num_envs

    @abstractmethod
    def reset(self, seeds: list[int] | None = None) -> tuple[NDArray[np.float32], list[dict]]:
        """Reset all environments."""

    @abstractmethod
    def step(
        self, actions: NDArray[np.float32]
    ) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.bool_], NDArray[np.bool_], list[dict]]:
        """Step all environments."""

    @abstractmethod
    def close(self) -> None:
        """Close all environments."""
