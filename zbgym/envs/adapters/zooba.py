"""Zooba game adapter for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import gymnasium as gym
import numpy as np
from numpy.typing import NDArray

from zbgym.config import EnvironmentConfig, ZBGymConfig
from zbgym.env.battle_arena import BattleArena, BattleArenaState
from zbgym.envs.base.environment import BaseEnvironment


@dataclass
class GameState:
    """Zooba game state."""

    tick: int = 0
    elapsed_time: float = 0.0
    match_active: bool = True

    # Character states
    characters: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Zone state
    safe_zone_center: tuple[float, float] = (1000.0, 750.0)
    safe_zone_radius: float = 1000.0
    danger_zone_radius: float = 1200.0

    # Map data
    map_id: str = "default"
    map_width: int = 2000
    map_height: int = 1500

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "elapsed_time": self.elapsed_time,
            "match_active": self.match_active,
            "characters": self.characters,
            "safe_zone_center": self.safe_zone_center,
            "safe_zone_radius": self.safe_zone_radius,
            "danger_zone_radius": self.danger_zone_radius,
            "map_id": self.map_id,
            "map_width": self.map_width,
            "map_height": self.map_height,
        }


@dataclass
class ZoobaConfig:
    """Configuration for Zooba environment."""

    # Core settings
    name: str = "Zooba-v1"
    num_agents: int = 2
    max_episode_steps: int = 10000

    # Arena settings
    arena_width: int = 2000
    arena_height: int = 1500

    # Game-specific settings
    game_mode: str = "battle_royale"
    respawn_enabled: bool = False
    zone_shrink_enabled: bool = True

    # Character settings
    auto_equip_weapons: bool = True
    auto_use_skills: bool = False

    # Map settings
    map_name: str = "default"
    spawn_mode: str = "random"  # "random", "balanced", "fixed"

    # Observation settings
    obs_include_health: bool = True
    obs_include_position: bool = True
    obs_include_velocity: bool = True
    obs_include_vision: bool = True

    # Zooba-specific rewards
    kill_reward: float = 10.0
    death_penalty: float = -5.0
    damage_reward_ratio: float = 0.1
    zone_damage_per_second: float = 1.0


class ZoobaAdapter(BaseEnvironment):
    """
    Zooba game adapter.

    Wraps the existing BattleArena environment with a game-specific interface.
    """

    metadata = {
        "render_modes": ["human", "rgb_array", "state_pixels"],
        "render_fps": 30,
    }

    def __init__(
        self,
        config: ZoobaConfig | None = None,
        render_mode: str | None = None,
    ) -> None:
        """
        Initialize Zooba adapter.

        Args:
            config: Zooba configuration
            render_mode: Rendering mode
        """
        super().__init__(render_mode=render_mode)

        self.config = config or ZoobaConfig()

        # Create internal environment
        zbgym_config = ZBGymConfig(
            arena_width=self.config.arena_width,
            arena_height=self.config.arena_height,
            game_mode=self.config.game_mode,
            respawn_time=5.0 if self.config.respawn_enabled else 0.0,
        )

        env_config = EnvironmentConfig(
            name=self.config.name,
            num_agents=self.config.num_agents,
            config=zbgym_config,
        )

        self._env = BattleArena(config=env_config, render_mode=render_mode)

        # Define observation space
        obs_size = self._calculate_obs_size()
        self.observation_space = self._env.observation_space
        self.action_space = self._env.action_space

        # Rewards
        self.kill_reward = self.config.kill_reward
        self.death_penalty = self.config.death_penalty
        self.damage_reward_ratio = self.config.damage_reward_ratio

    def _calculate_obs_size(self) -> int:
        """Calculate observation size based on config."""
        size = 0

        if self.config.obs_include_health:
            size += 1
        if self.config.obs_include_position:
            size += 2
        if self.config.obs_include_velocity:
            size += 2

        # Enemy observations
        size += self.config.num_agents * 3

        # Zone info
        size += 1

        return size

    def reset(
        self,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[NDArray[np.float32], dict]:
        """Reset the environment."""
        obs, info = self._env.reset(seed=seed, options=options)
        self._current_step = 0
        self._episode_reward = 0.0
        return obs, info

    def step(
        self,
        action: NDArray[np.float32] | int,
    ) -> tuple[NDArray[np.float32], float, bool, bool, dict]:
        """Execute one step."""
        obs, reward, terminated, truncated, info = self._env.step(action)

        # Apply game-specific reward modifications
        reward = self._modify_reward(reward, info)

        self._current_step += 1
        self._episode_reward += reward

        return obs, reward, terminated, truncated, info

    def _modify_reward(self, base_reward: float, info: dict) -> float:
        """Apply game-specific reward modifications."""
        reward = base_reward

        # Apply zone damage penalty
        if not info.get("in_safe_zone", True):
            reward += self.config.zone_damage_per_second * -0.1

        return reward

    def get_state(self) -> GameState:
        """Get current game state."""
        arena_state = self._env.get_state()

        characters = {}
        for char_id, char in arena_state.characters.items():
            characters[char_id] = {
                "position": (char.position.x, char.position.y),
                "velocity": (char.velocity.x, char.velocity.y),
                "health": char.health,
                "shield": char.shield,
                "energy": char.energy,
                "is_alive": char.is_alive,
                "team": char.team,
                "kills": char.kills,
                "deaths": char.deaths,
                "damage_dealt": char.damage_dealt,
            }

        return GameState(
            tick=arena_state.tick,
            elapsed_time=arena_state.elapsed_time,
            match_active=arena_state.match_active,
            characters=characters,
            safe_zone_center=(arena_state.safe_zone_center.x, arena_state.safe_zone_center.y),
            safe_zone_radius=arena_state.safe_zone_radius,
            danger_zone_radius=arena_state.danger_zone_radius,
            map_width=self.config.arena_width,
            map_height=self.config.arena_height,
        )

    def set_state(self, state: GameState) -> None:
        """Set game state."""
        from zbgym.physics.vector import Vector2D

        arena_state = BattleArenaState(
            tick=state.tick,
            elapsed_time=state.elapsed_time,
            match_active=state.match_active,
            safe_zone_center=Vector2D(*state.safe_zone_center),
            safe_zone_radius=state.safe_zone_radius,
            danger_zone_radius=state.danger_zone_radius,
        )

        for char_id, char_data in state.characters.items():
            from zbgym.env.battle_arena import CharacterState

            pos = char_data["position"]
            vel = char_data["velocity"]

            arena_state.characters[char_id] = CharacterState(
                id=char_id,
                position=Vector2D(pos[0], pos[1]),
                velocity=Vector2D(vel[0], vel[1]),
                health=char_data["health"],
                shield=char_data["shield"],
                energy=char_data["energy"],
                is_alive=char_data["is_alive"],
                team=char_data.get("team", "none"),
                kills=char_data.get("kills", 0),
                deaths=char_data.get("deaths", 0),
                damage_dealt=char_data.get("damage_dealt", 0.0),
            )

        self._env.set_state(arena_state)

    def render(self) -> NDArray[np.uint8] | None:
        """Render the environment."""
        return self._env.render()

    def close(self) -> None:
        """Close the environment."""
        self._env.close()


# Register with gymnasium
gym.register(
    id="Zooba-v1",
    entry_point="zbgym.envs.adapters.zooba:ZoobaAdapter",
)
