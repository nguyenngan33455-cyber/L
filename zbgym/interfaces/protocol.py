"""
Core Protocol Interfaces for ZBGym.

This module defines the abstract interfaces that form the foundation
of the multi-game ZBGym framework. These protocols define how game
engines, adapters, and providers interact.

Example:
    >>> from zbgym.interfaces import GameState, GameEngine, ObservationProvider
    >>> 
    >>> class MyGameState(GameState):
    ...     @property
    ...     def tick(self) -> int: ...
    ...     
    ...     def get_players(self) -> list[Player]: ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, TYPE_CHECKING, runtime_checkable
import numpy as np

# Re-export contracts for convenience
from zbgym.interfaces.contracts import (
    Vector2D,
    Position,
    Velocity,
    Health,
    Mana,
    Score,
    Experience,
    GameTime,
    TeamID,
    EntityID,
    Inventory,
    GameConfig,
)


# =============================================================================
# Core Entity Protocols
# =============================================================================

@runtime_checkable
class Entity(Protocol):
    """
    Protocol for all game entities.
    
    An entity is any object that exists in the game world with
    a position and unique identifier.
    
    Example:
        >>> class MyEntity:
        ...     @property
        ...     def id(self) -> str: ...
        ...     
        ...     @property
        ...     def position(self) -> Vector2D: ...
    """
    
    @property
    def id(self) -> str:
        """Unique identifier for this entity."""
        ...
    
    @property
    def position(self) -> Vector2D:
        """Current position in world."""
        ...
    
    @property
    def is_active(self) -> bool:
        """Whether entity is currently active in the game."""
        ...


@runtime_checkable
class Player(Entity, Protocol):
    """
    Protocol for players/controllable entities.
    
    A player is an entity that can be controlled by an agent
    and has health, team membership, and game stats.
    
    Example:
        >>> class MyPlayer:
        ...     @property
        ...     def team_id(self) -> str | None: ...
        ...     
        ...     @property
        ...     def health(self) -> Health: ...
    """
    
    @property
    def team_id(self) -> str | None:
        """Team identifier (None if no team)."""
        ...
    
    @property
    def health(self) -> Health:
        """Current health state."""
        ...
    
    @property
    def is_alive(self) -> bool:
        """Whether player is alive."""
        ...
    
    @property
    def velocity(self) -> Vector2D:
        """Current velocity."""
        ...


@runtime_checkable
class Team(Protocol):
    """
    Protocol for teams/factions.
    
    A team is a collection of players with a shared identity
    and score.
    
    Example:
        >>> class MyTeam:
        ...     @property
        ...     def id(self) -> str: ...
        ...     
        ...     @property
        ...     def score(self) -> int: ...
    """
    
    @property
    def id(self) -> str:
        """Unique team identifier."""
        ...
    
    @property
    def name(self) -> str:
        """Display name for team."""
        ...
    
    @property
    def score(self) -> int:
        """Current team score."""
        ...
    
    @property
    def player_ids(self) -> list[str]:
        """List of player IDs in team."""
        ...


@runtime_checkable
class GameMap(Protocol):
    """
    Protocol for game maps/levels.
    
    A map defines the spatial boundaries and zones of the game world.
    
    Example:
        >>> class MyMap:
        ...     @property
        ...     def width(self) -> float: ...
        ...     
        ...     @property
        ...     def height(self) -> float: ...
    """
    
    @property
    def width(self) -> float:
        """Map width in world units."""
        ...
    
    @property
    def height(self) -> float:
        """Map height in world units."""
        ...
    
    def is_valid_position(self, x: float, y: float) -> bool:
        """Check if position is within map bounds."""
        ...
    
    def get_zone_at(self, x: float, y: float) -> Zone | None:
        """Get zone at given position (if zones exist)."""
        ...


@runtime_checkable
class Zone(Protocol):
    """
    Protocol for map zones.
    
    A zone is an area of the map with specific properties,
    such as safe zones, danger zones, or capture points.
    
    Example:
        >>> class MyZone:
        ...     @property
        ...     def center(self) -> Vector2D: ...
        ...     
        ...     @property
        ...     def radius(self) -> float: ...
    """
    
    @property
    def id(self) -> str:
        """Unique zone identifier."""
        ...
    
    @property
    def center(self) -> Vector2D:
        """Center position of zone."""
        ...
    
    @property
    def radius(self) -> float:
        """Zone radius (for circular zones)."""
        ...
    
    @property
    def danger_level(self) -> float:
        """Danger level of zone (0.0 = safe, 1.0 = lethal)."""
        ...
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within zone."""
        ...


@runtime_checkable
class Action(Protocol):
    """
    Protocol for game actions.
    
    An action represents a player input or command that
    affects the game state.
    
    Example:
        >>> class MyAction:
        ...     def to_array(self) -> np.ndarray: ...
    """
    
    def to_array(self) -> np.ndarray:
        """Convert action to numpy array for neural network."""
        ...
    
    @property
    def action_type(self) -> str:
        """Type of action (e.g., 'movement', 'ability', 'item')."""
        ...


# =============================================================================
# Game State Interface
# =============================================================================

class GameState(ABC):
    """
    Abstract base class for game states.
    
    GameState represents a complete snapshot of the game at a
    given moment. It provides access to all entities, teams,
    and game metadata.
    
    Example:
        >>> class MyGameState(GameState):
        ...     def get_players(self) -> list[Player]:
        ...         ...
        ...     
        ...     def get_teams(self) -> list[Team]:
        ...         ...
    """
    
    @property
    @abstractmethod
    def tick(self) -> int:
        """Current game tick."""
        ...
    
    @property
    @abstractmethod
    def elapsed_time(self) -> float:
        """Elapsed time in seconds since game start."""
        ...
    
    @property
    @abstractmethod
    def is_match_active(self) -> bool:
        """Whether match is currently active."""
        ...
    
    @property
    @abstractmethod
    def match_duration(self) -> float:
        """Total match duration in seconds (0 = unlimited)."""
        ...
    
    @abstractmethod
    def get_players(self) -> list[Player]:
        """Get all players in the game."""
        ...
    
    @abstractmethod
    def get_player(self, player_id: str) -> Player | None:
        """Get specific player by ID."""
        ...
    
    @abstractmethod
    def get_teams(self) -> list[Team]:
        """Get all teams in the game."""
        ...
    
    @abstractmethod
    def get_team(self, team_id: str) -> Team | None:
        """Get specific team by ID."""
        ...
    
    @abstractmethod
    def get_map(self) -> GameMap:
        """Get the game map."""
        ...
    
    @abstractmethod
    def get_zones(self) -> list[Zone]:
        """Get all zones in the game."""
        ...
    
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dictionary."""
        ...
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> GameState:
        """Deserialize state from dictionary."""
        ...


# =============================================================================
# Game Engine Interface
# =============================================================================

class GameEngine(ABC):
    """
    Abstract base class for game engines.
    
    GameEngine is the core interface for game simulation.
    It provides reset, step, and state access following the
    Gymnasium environment interface.
    
    Example:
        >>> class MyEngine(GameEngine):
        ...     def reset(self, seed=None) -> tuple[np.ndarray, dict]:
        ...         ...
        ...     
        ...     def step(self, action) -> tuple[np.ndarray, float, bool, bool, dict]:
        ...         ...
    """
    
    @property
    @abstractmethod
    def observation_space(self) -> Any:
        """Gymnasium observation space."""
        ...
    
    @property
    @abstractmethod
    def action_space(self) -> Any:
        """Gymnasium action space."""
        ...
    
    @property
    @abstractmethod
    def spec(self) -> Any | None:
        """Gymnasium environment spec."""
        ...
    
    @abstractmethod
    def reset(
        self,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[np.ndarray, dict]:
        """
        Reset the environment.
        
        Args:
            seed: Random seed for reproducibility
            options: Additional reset options
            
        Returns:
            Initial observation and info dict
        """
        ...
    
    @abstractmethod
    def step(
        self,
        action: Any,
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        """
        Execute one environment step.
        
        Args:
            action: Action to execute
            
        Returns:
            observation, reward, terminated, truncated, info
        """
        ...
    
    @abstractmethod
    def close(self) -> None:
        """Clean up environment resources."""
        ...
    
    def render(self) -> np.ndarray | None:
        """
        Render the environment.
        
        Returns:
            RGB array or None
        """
        return None


# =============================================================================
# Game Adapter Interface
# =============================================================================

class GameAdapter(ABC):
    """
    Abstract base class for game adapters.
    
    GameAdapter wraps a game-specific engine and provides
    a unified interface through generic protocols.
    
    Adapters translate between game-specific implementations
    and the generic ZBGym interface layer.
    
    Example:
        >>> class MyAdapter(GameAdapter):
        ...     def get_game_state(self) -> GameState:
        ...         ...
    """
    
    @property
    @abstractmethod
    def engine(self) -> GameEngine:
        """Get the underlying game engine."""
        ...
    
    @abstractmethod
    def get_game_state(self) -> GameState:
        """Get current game state as generic GameState."""
        ...
    
    @abstractmethod
    def set_game_state(self, state: GameState) -> None:
        """
        Set game state from generic GameState.
        
        Args:
            state: GameState to restore
            
        Raises:
            TypeError: If state type is incompatible
        """
        ...
    
    @abstractmethod
    def get_observation_provider(self) -> ObservationProvider:
        """Get the observation provider for this adapter."""
        ...
    
    @abstractmethod
    def get_reward_provider(self) -> RewardProvider:
        """Get the reward provider for this adapter."""
        ...


# =============================================================================
# Provider Interfaces
# =============================================================================

class ObservationProvider(ABC):
    """
    Abstract base class for observation providers.
    
    ObservationProvider computes observations from game states
    for agent consumption.
    
    Example:
        >>> class MyObsProvider(ObservationProvider):
        ...     def compute(self, state: GameState, agent_id: str) -> np.ndarray:
        ...         ...
    """
    
    @abstractmethod
    def compute(self, state: GameState, agent_id: str) -> np.ndarray:
        """
        Compute observation for agent.
        
        Args:
            state: Current game state
            agent_id: ID of agent to compute observation for
            
        Returns:
            Observation as numpy array
        """
        ...
    
    @abstractmethod
    def get_space(self) -> Any:
        """Get the observation space."""
        ...


class RewardProvider(ABC):
    """
    Abstract base class for reward providers.
    
    RewardProvider computes rewards based on state transitions.
    
    Example:
        >>> class MyRewardProvider(RewardProvider):
        ...     def compute(self, prev: GameState, curr: GameState, agent_id: str) -> float:
        ...         ...
    """
    
    @abstractmethod
    def compute(
        self,
        prev_state: GameState,
        current_state: GameState,
        agent_id: str,
    ) -> float:
        """
        Compute reward for state transition.
        
        Args:
            prev_state: Previous game state
            current_state: Current game state
            agent_id: ID of agent to compute reward for
            
        Returns:
            Reward value
        """
        ...
    
    @abstractmethod
    def reset(self) -> None:
        """Reset provider state (e.g., at episode start)."""
        ...


class ReplayProvider(ABC):
    """
    Abstract base class for replay providers.
    
    ReplayProvider handles recording and playback of game sessions.
    
    Example:
        >>> class MyReplayProvider(ReplayProvider):
        ...     def record_step(self, state: GameState, action: Any, reward: float) -> None:
        ...         ...
    """
    
    @abstractmethod
    def record_step(
        self,
        state: GameState,
        action: Any,
        reward: float,
    ) -> None:
        """
        Record a single step.
        
        Args:
            state: Current game state
            action: Action taken
            reward: Reward received
        """
        ...
    
    @abstractmethod
    def save(self, path: str) -> None:
        """
        Save replay to file.
        
        Args:
            path: File path to save replay
        """
        ...
    
    @abstractmethod
    def load(self, path: str) -> None:
        """
        Load replay from file.
        
        Args:
            path: File path to load replay from
        """
        ...
    
    @abstractmethod
    def get_replay_data(self) -> dict[str, Any]:
        """Get replay data as dictionary."""
        ...


class DashboardProvider(ABC):
    """
    Abstract base class for dashboard providers.
    
    DashboardProvider handles integration with training dashboards
    and metrics collection.
    
    Example:
        >>> class MyDashboardProvider(DashboardProvider):
        ...     def publish_metrics(self, metrics: dict) -> None:
        ...         ...
    """
    
    @abstractmethod
    def publish_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Publish training metrics.
        
        Args:
            metrics: Dictionary of metric names to values
        """
        ...
    
    @abstractmethod
    def publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Publish a game event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        ...
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if dashboard integration is enabled."""
        ...


class CheckpointProvider(ABC):
    """
    Abstract base class for checkpoint providers.
    
    CheckpointProvider handles saving and loading of training
    checkpoints and model states.
    
    Example:
        >>> class MyCheckpointProvider(CheckpointProvider):
        ...     def save_checkpoint(self, path: str, data: dict) -> None:
        ...         ...
    """
    
    @abstractmethod
    def save_checkpoint(self, path: str, data: dict[str, Any]) -> None:
        """
        Save a checkpoint.
        
        Args:
            path: File path for checkpoint
            data: Checkpoint data dictionary
        """
        ...
    
    @abstractmethod
    def load_checkpoint(self, path: str) -> dict[str, Any]:
        """
        Load a checkpoint.
        
        Args:
            path: File path to checkpoint
            
        Returns:
            Checkpoint data dictionary
        """
        ...
    
    @abstractmethod
    def list_checkpoints(self, directory: str) -> list[str]:
        """
        List available checkpoints.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of checkpoint file paths
        """
        ...
