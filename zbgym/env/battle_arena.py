"""Battle Arena environment for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, SupportsFloat

import gymnasium as gym
import numpy as np
from numpy.typing import NDArray

from zbgym.config import ZBGymConfig, EnvironmentConfig
from zbgym.constants import (
    DEFAULT_ARENA_WIDTH,
    DEFAULT_ARENA_HEIGHT,
    MAX_HEALTH,
    MAX_SHIELD,
    MAX_ENERGY,
    DEFAULT_TICK_RATE,
)
from zbgym.engine.event_bus import EventBus, Event
from zbgym.engine.tick_system import TickSystem
from zbgym.physics.vector import Vector2D
from zbgym.physics.movement import MovementSystem, MovementConfig


@dataclass
class CharacterState:
    """State of a character in the arena."""

    id: str
    position: Vector2D = field(default_factory=Vector2D.zero)
    velocity: Vector2D = field(default_factory=Vector2D.zero)
    health: float = MAX_HEALTH
    shield: float = MAX_SHIELD
    energy: float = MAX_ENERGY
    is_alive: bool = True
    team: str = "none"

    # Stats
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    damage_dealt: float = 0.0
    damage_taken: float = 0.0
    healing: float = 0.0

    # Cooldowns
    ability_cooldowns: dict[str, float] = field(default_factory=dict)


@dataclass
class BattleArenaState:
    """Complete state of the battle arena."""

    tick: int = 0
    elapsed_time: float = 0.0
    match_active: bool = False
    match_duration: float = 600.0

    characters: dict[str, CharacterState] = field(default_factory=dict)

    # Zone
    safe_zone_center: Vector2D = field(default_factory=Vector2D.zero)
    safe_zone_radius: float = 1000.0
    danger_zone_radius: float = 1200.0

    # Scores
    scores: dict[str, int] = field(default_factory=dict)


class BattleArena(gym.Env):
    """
    Battle Arena environment for Reinforcement Learning.

    A competitive combat environment where agents fight in an arena.
    Fully compatible with Gymnasium API.

    Observation Space:
        Dict containing:
        - self: Agent's own state (health, position, velocity, etc.)
        - enemies: List of enemy states
        - zone: Safe zone information
        - items: Nearby items (optional)

    Action Space:
        Box(-1, 1, shape=(4,)) for [move_x, move_y, aim_x, aim_y]
        Or Discrete for discrete action mode
    """

    metadata = {
        "render_modes": ["human", "rgb_array", "state_pixels"],
        "render_fps": 30,
    }

    def __init__(
        self,
        config: EnvironmentConfig | None = None,
        render_mode: str | None = None,
        obs_config: dict | None = None,
        reward_config: dict | None = None,
    ) -> None:
        """
        Initialize Battle Arena environment.

        Args:
            config: Environment configuration
            render_mode: Rendering mode
            obs_config: Observation configuration
            reward_config: Reward configuration
        """
        super().__init__()

        self.config = config or EnvironmentConfig()
        self.render_mode = render_mode or self.config.render_mode

        # Engine components
        self.event_bus = EventBus()
        self.tick_system = TickSystem(
            tick_rate=self.config.config.tick_rate,
            event_bus=self.event_bus,
        )
        self.movement_system = MovementSystem(
            config=MovementConfig(),
            event_bus=self.event_bus,
        )

        # State
        self._state = BattleArenaState()
        self._action_history: list[dict] = []
        self._episode_reward = 0.0
        self._max_episode_steps = 10000
        self._current_step = 0

        # Spaces
        self.observation_space = self._create_observation_space()
        self.action_space = self._create_action_space()

        # Configuration
        self.obs_config = obs_config or self._default_obs_config()
        self.reward_config = reward_config or self._default_reward_config()

        # Rendering
        self._renderer = None

    @staticmethod
    def _default_obs_config() -> dict:
        """Default observation configuration."""
        return {
            "include_health": True,
            "include_position": True,
            "include_velocity": True,
            "include_energy": True,
            "include_shield": True,
            "include_enemies": True,
            "include_zone": True,
            "include_items": True,
            "max_enemies": 8,
            "vision_range": 500.0,
        }

    @staticmethod
    def _default_reward_config() -> dict:
        """Default reward configuration."""
        return {
            "kill_reward": 10.0,
            "death_penalty": -5.0,
            "damage_reward_ratio": 0.1,
            "healing_reward_ratio": 0.2,
            "survival_reward": 0.1,
            "idle_penalty": -0.01,
        }

    def _create_observation_space(self) -> gym.Space:
        """Create observation space."""
        obs_size = 50  # Base observation size
        return gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_size,),
            dtype=np.float32,
        )

    def _create_action_space(self) -> gym.Space:
        """Create action space."""
        return gym.spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(4,),  # move_x, move_y, aim_x, aim_y
            dtype=np.float32,
        )

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
        super().reset(seed=seed)

        # Initialize RNG
        if seed is not None:
            self._np_random = np.random.default_rng(seed)
        elif not hasattr(self, "_np_random") or self._np_random is None:
            self._np_random = np.random.default_rng()

        # Reset state
        self._state = BattleArenaState(
            match_active=True,
            match_duration=self.config.config.match_duration,
            safe_zone_center=Vector2D(
                self.config.config.arena_width / 2,
                self.config.config.arena_height / 2,
            ),
            safe_zone_radius=min(
                self.config.config.arena_width,
                self.config.config.arena_height,
            ) / 2,
            danger_zone_radius=min(
                self.config.config.arena_width,
                self.config.config.arena_height,
            ) / 2 + 200,
        )

        # Initialize characters
        self._init_characters()

        # Reset systems
        self.tick_system.reset()
        self.movement_system.reset_all()
        self._action_history.clear()
        self._episode_reward = 0.0
        self._current_step = 0

        # Emit match start event
        self.event_bus.emit(
            Event(type="match_start", data={"state": self._state})
        )

        return self._get_obs(), self._get_info()

    def _init_characters(self) -> None:
        """Initialize characters in the arena."""
        num_agents = self.config.num_agents
        arena_width = self.config.config.arena_width
        arena_height = self.config.config.arena_height

        # Spawn positions
        spawn_positions = [
            Vector2D(arena_width * 0.2, arena_height * 0.5),
            Vector2D(arena_width * 0.8, arena_height * 0.5),
            Vector2D(arena_width * 0.5, arena_height * 0.2),
            Vector2D(arena_width * 0.5, arena_height * 0.8),
        ]

        for i in range(num_agents):
            char_id = f"agent_{i}"
            spawn_pos = spawn_positions[i % len(spawn_positions)]

            # Add some randomness to spawn
            spawn_pos = Vector2D(
                spawn_pos.x + self._np_random.uniform(-50, 50),
                spawn_pos.y + self._np_random.uniform(-50, 50),
            )

            self._state.characters[char_id] = CharacterState(
                id=char_id,
                position=spawn_pos,
                team="red" if i < num_agents // 2 else "blue",
            )

    def step(
        self,
        action: NDArray[np.float32] | int,
    ) -> tuple[NDArray[np.float32], float, bool, bool, dict]:
        """
        Execute one step in the environment.

        Args:
            action: Action to take

        Returns:
            observation, reward, terminated, truncated, info
        """
        self._current_step += 1

        # Process action
        reward = self._process_action(action)

        # Update game state
        self._update()

        # Get observation
        obs = self._get_obs()

        # Check termination
        terminated = self._is_terminated()
        truncated = self._current_step >= self._max_episode_steps

        # Update info
        info = self._get_info()

        # Track episode reward
        self._episode_reward += reward

        return obs, reward, terminated, truncated, info

    def _process_action(self, action: NDArray[np.float32] | int) -> float:
        """Process action and calculate reward."""
        reward = 0.0

        # Parse action
        if isinstance(action, np.ndarray):
            move_x = float(action[0])
            move_y = float(action[1])
            aim_x = float(action[2]) if len(action) > 2 else 0.0
            aim_y = float(action[3]) if len(action) > 3 else 0.0
        else:
            move_x, move_y, aim_x, aim_y = 0.0, 0.0, 0.0, 0.0

        # Check if agent is moving
        is_moving = abs(move_x) > 0.1 or abs(move_y) > 0.1

        # Idle penalty
        if not is_moving:
            reward += self.reward_config.get("idle_penalty", -0.01)

        # Survival reward
        reward += self.reward_config.get("survival_reward", 0.1)

        # Store action
        self._action_history.append({
            "step": self._current_step,
            "move": (move_x, move_y),
            "aim": (aim_x, aim_y),
        })

        return reward

    def _update(self) -> None:
        """Update game state by one tick."""
        # Advance tick
        dt = self.tick_system.tick()
        self._state.tick = self.tick_system.current_tick
        self._state.elapsed_time = self.tick_system.elapsed_time

        # Update characters
        for char_id, char in self._state.characters.items():
            if not char.is_alive:
                continue

            # Update position based on last action
            if self._action_history:
                last_action = self._action_history[-1]
                move = last_action.get("move", (0.0, 0.0))
                if move:
                    move_dir = Vector2D(move[0], move[1])
                    if move_dir.length_squared > 0:
                        move_dir = move_dir.normalized
                        speed = 200.0  # pixels per second
                        char.position += move_dir * speed * dt

            # Keep in bounds
            char.position.x = max(16, min(self.config.config.arena_width - 16, char.position.x))
            char.position.y = max(16, min(self.config.config.arena_height - 16, char.position.y))

            # Regenerate energy
            char.energy = min(MAX_ENERGY, char.energy + 5.0 * dt)

        # Check zone damage
        self._update_zone()

    def _update_zone(self) -> None:
        """Update safe/danger zone."""
        center = self._state.safe_zone_center
        safe_radius = self._state.safe_zone_radius

        for char in self._state.characters.values():
            if not char.is_alive:
                continue

            distance = char.position.distance_to(center)
            if distance > safe_radius:
                # Zone damage
                damage = (distance - safe_radius) * 0.1
                char.health -= damage

                if char.health <= 0:
                    char.health = 0
                    char.is_alive = False
                    char.deaths += 1

                    # Emit death event
                    self.event_bus.emit(
                        Event(
                            type="character_death",
                            data={"character_id": char.id, "position": char.position.to_dict()},
                        )
                    )

    def _get_obs(self) -> NDArray[np.float32]:
        """Get current observation."""
        obs = np.zeros(50, dtype=np.float32)
        idx = 0

        # Get first alive character as "self"
        self_char = None
        for char in self._state.characters.values():
            if char.is_alive:
                self_char = char
                break

        if self_char is None:
            return obs

        # Self observations
        if self.obs_config.get("include_health", True):
            obs[idx] = self_char.health / MAX_HEALTH
            idx += 1

        if self.obs_config.get("include_position", True):
            obs[idx] = self_char.position.x / self.config.config.arena_width
            obs[idx + 1] = self_char.position.y / self.config.config.arena_height
            idx += 2

        if self.obs_config.get("include_velocity", True):
            obs[idx] = self_char.velocity.x / 1000.0
            obs[idx + 1] = self_char.velocity.y / 1000.0
            idx += 2

        if self.obs_config.get("include_energy", True):
            obs[idx] = self_char.energy / MAX_ENERGY
            idx += 1

        if self.obs_config.get("include_shield", True):
            obs[idx] = self_char.shield / MAX_SHIELD
            idx += 1

        # Zone info
        if self.obs_config.get("include_zone", True):
            obs[idx] = self_char.position.distance_to(self._state.safe_zone_center) / self._state.safe_zone_radius
            idx += 1

        # Enemy observations
        if self.obs_config.get("include_enemies", True):
            enemy_idx = 0
            max_enemies = self.obs_config.get("max_enemies", 8)
            for char in self._state.characters.values():
                if char.id == self_char.id or not char.is_alive:
                    continue
                if enemy_idx >= max_enemies:
                    break

                # Relative position
                rel_x = (char.position.x - self_char.position.x) / self.obs_config.get("vision_range", 500.0)
                rel_y = (char.position.y - self_char.position.y) / self.obs_config.get("vision_range", 500.0)

                obs[idx] = np.clip(rel_x, -1, 1)
                obs[idx + 1] = np.clip(rel_y, -1, 1)
                obs[idx + 2] = char.health / MAX_HEALTH
                idx += 3
                enemy_idx += 1

        return obs

    def _get_info(self) -> dict:
        """Get info dictionary."""
        alive_agents = sum(1 for c in self._state.characters.values() if c.is_alive)

        return {
            "tick": self._state.tick,
            "elapsed_time": self._state.elapsed_time,
            "episode_reward": self._episode_reward,
            "alive_agents": alive_agents,
            "total_agents": len(self._state.characters),
            "match_active": self._state.match_active,
            "zone_radius": self._state.safe_zone_radius,
        }

    def _is_terminated(self) -> bool:
        """Check if episode is terminated."""
        # Check if only one team/agent remains
        alive_by_team: dict[str, int] = {}
        for char in self._state.characters.values():
            if char.is_alive:
                alive_by_team[char.team] = alive_by_team.get(char.team, 0) + 1

        if len(alive_by_team) == 1:
            return True

        # Check time limit
        if self._state.elapsed_time >= self._state.match_duration:
            return True

        # Check if all agents dead
        if all(not c.is_alive for c in self._state.characters.values()):
            return True

        return False

    def render(self) -> NDArray[np.uint8] | None:
        """Render the environment."""
        if self.render_mode is None:
            return None

        # Simple text rendering
        if self.render_mode == "human":
            print(f"Step {self._current_step}: {len(self._state.characters)} characters, {sum(1 for c in self._state.characters.values() if c.is_alive)} alive")
            return None

        # RGB array
        width = self.config.config.arena_width // 4
        height = self.config.config.arena_height // 4
        img = np.zeros((height, width, 3), dtype=np.uint8)

        # Draw characters
        for char in self._state.characters.values():
            if not char.is_alive:
                continue

            x = int(char.position.x / 4)
            y = int(char.position.y / 4)
            if 0 <= x < width and 0 <= y < height:
                img[y, x] = [100, 200, 100] if char.team == "red" else [200, 100, 100]

        # Draw zone
        cx = int(self._state.safe_zone_center.x / 4)
        cy = int(self._state.safe_zone_center.y / 4)
        r = int(self._state.safe_zone_radius / 4)
        for angle in range(360):
            x = int(cx + r * np.cos(np.radians(angle)))
            y = int(cy + r * np.sin(np.radians(angle)))
            if 0 <= x < width and 0 <= y < height:
                img[y, x] = [50, 150, 50]

        return img

    def close(self) -> None:
        """Clean up environment."""
        self.event_bus.emit(Event(type="match_end", data={}))
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None

    @property
    def spec(self) -> gym.envs.env_spec.EnvSpec | None:
        """Get environment spec."""
        return None

    @property
    def unwrapped(self) -> "BattleArena":
        """Get unwrapped environment."""
        return self

    def get_state(self) -> BattleArenaState:
        """Get current arena state."""
        return self._state

    def set_state(self, state: BattleArenaState) -> None:
        """Set arena state."""
        self._state = state
