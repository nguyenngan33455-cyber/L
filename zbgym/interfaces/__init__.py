"""
ZBGym Interfaces Package

Generic interfaces for multi-game reinforcement learning framework.

This package provides abstract interfaces that allow ZBGym to support
multiple game types through a common abstraction layer.

Example:
    >>> from zbgym.interfaces import GameState, GameEngine, ObservationProvider
    >>> 
    >>> class MyGameAdapter:
    ...     def get_game_state(self) -> GameState:
    ...         ...
"""

from zbgym.interfaces.protocol import (
    GameState,
    GameEngine,
    GameAdapter,
    Entity,
    Player,
    Team,
    GameMap,
    Zone,
    Action,
    ObservationProvider,
    RewardProvider,
    ReplayProvider,
    DashboardProvider,
    CheckpointProvider,
)
from zbgym.interfaces.contracts import (
    Vector2D,
    Position,
    Velocity,
    Rotation,
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
from zbgym.interfaces.exceptions import (
    InterfaceError,
    StateError,
    EntityError,
    ActionError,
    ProviderError,
)

__all__ = [
    # Protocols
    "GameState",
    "GameEngine",
    "GameAdapter",
    "Entity",
    "Player",
    "Team",
    "GameMap",
    "Zone",
    "Action",
    "ObservationProvider",
    "RewardProvider",
    "ReplayProvider",
    "DashboardProvider",
    "CheckpointProvider",
    # Contracts
    "Vector2D",
    "Position",
    "Velocity",
    "Rotation",
    "Health",
    "Mana",
    "Score",
    "Experience",
    "GameTime",
    "TeamID",
    "EntityID",
    "Inventory",
    "GameConfig",
    # Exceptions
    "InterfaceError",
    "StateError",
    "EntityError",
    "ActionError",
    "ProviderError",
]

__version__ = "0.1.0"
