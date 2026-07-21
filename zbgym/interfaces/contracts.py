"""
Common Data Contracts for ZBGym Interfaces.

This module defines reusable data contracts (dataclasses) that represent
common game entities and values. These contracts provide a standardized
way to represent game data across different game types.

Example:
    >>> from zbgym.interfaces.contracts import Vector2D, Position, Health
    >>> 
    >>> pos = Vector2D(x=100.0, y=200.0)
    >>> health = Health(current=100.0, max=100.0, regen=0.1)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, TYPE_CHECKING
import numpy as np


# =============================================================================
# Value Objects - Immutable data types
# =============================================================================

@dataclass(frozen=True, slots=True)
class Vector2D:
    """
    Immutable 2D vector for positions and velocities.
    
    Attributes:
        x: X coordinate or X component
        y: Y coordinate or Y component
    
    Example:
        >>> velocity = Vector2D(x=10.0, y=-5.0)
        >>> position = Vector2D(x=100.0, y=200.0)
        >>> distance = velocity.distance_to(position)
    """
    x: float = 0.0
    y: float = 0.0
    
    @classmethod
    def zero(cls) -> Vector2D:
        """Create a zero vector."""
        return cls(0.0, 0.0)
    
    @classmethod
    def from_angle(cls, angle: float, magnitude: float = 1.0) -> Vector2D:
        """Create a vector from angle (radians) and magnitude."""
        return cls(
            x=magnitude * np.cos(angle),
            y=magnitude * np.sin(angle)
        )
    
    def distance_to(self, other: Vector2D) -> float:
        """Calculate Euclidean distance to another vector."""
        dx = self.x - other.x
        dy = self.y - other.y
        return np.sqrt(dx * dx + dy * dy)
    
    def magnitude(self) -> float:
        """Calculate vector magnitude (length)."""
        return np.sqrt(self.x * self.x + self.y * self.y)
    
    def normalized(self) -> Vector2D:
        """Return unit vector in same direction."""
        mag = self.magnitude()
        if mag == 0:
            return Vector2D.zero()
        return Vector2D(x=self.x / mag, y=self.y / mag)
    
    def dot(self, other: Vector2D) -> float:
        """Calculate dot product with another vector."""
        return self.x * other.x + self.y * other.y
    
    def angle_to(self, other: Vector2D) -> float:
        """Calculate angle to another vector in radians."""
        return np.arctan2(other.y - self.y, other.x - self.x)
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y])
    
    @classmethod
    def from_array(cls, arr: np.ndarray) -> Vector2D:
        """Create from numpy array."""
        return cls(x=float(arr[0]), y=float(arr[1]))


@dataclass(frozen=True, slots=True)
class Position:
    """
    Immutable position in game world.
    
    Attributes:
        x: X coordinate
        y: Y coordinate
        z: Z coordinate (optional, default 0)
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def to_vector2d(self) -> Vector2D:
        """Convert to 2D vector (ignores Z)."""
        return Vector2D(x=self.x, y=self.y)
    
    def distance_to(self, other: Position) -> float:
        """Calculate 3D Euclidean distance."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return np.sqrt(dx * dx + dy * dy + dz * dz)
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.z])


@dataclass(frozen=True, slots=True)
class Velocity:
    """
    Immutable velocity vector.
    
    Attributes:
        dx: X component (velocity in X direction)
        dy: Y component (velocity in Y direction)
        dz: Z component (velocity in Z direction, optional)
    """
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    
    def speed(self) -> float:
        """Calculate speed (magnitude of velocity)."""
        return np.sqrt(self.dx * self.dx + self.dy * self.dy + self.dz * self.dz)
    
    def to_vector2d(self) -> Vector2D:
        """Convert to 2D vector."""
        return Vector2D(x=self.dx, y=self.dy)
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.dx, self.dy, self.dz])


@dataclass(frozen=True, slots=True)
class Rotation:
    """
    Immutable rotation in 2D or 3D space.
    
    Attributes:
        yaw: Rotation around Z axis (radians)
        pitch: Rotation around X axis (radians, optional)
        roll: Rotation around Y axis (radians, optional)
    """
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    
    @classmethod
    def from_degrees(cls, yaw: float, pitch: float = 0.0, roll: float = 0.0) -> Rotation:
        """Create from degrees instead of radians."""
        return cls(
            yaw=np.radians(yaw),
            pitch=np.radians(pitch),
            roll=np.radians(roll)
        )
    
    def to_degrees(self) -> tuple[float, float, float]:
        """Convert to degrees."""
        return (
            np.degrees(self.yaw),
            np.degrees(self.pitch),
            np.degrees(self.roll)
        )
    
    def forward_vector(self) -> Vector2D:
        """Get forward direction as 2D vector."""
        return Vector2D(
            x=np.cos(self.yaw),
            y=np.sin(self.yaw)
        )


# =============================================================================
# State Value Objects
# =============================================================================

@dataclass(frozen=True, slots=True)
class Health:
    """
    Health state value object.
    
    Attributes:
        current: Current health value
        max: Maximum health value
        regen: Health regeneration per second (optional)
    """
    current: float = 100.0
    max: float = 100.0
    regen: float = 0.0
    
    @property
    def ratio(self) -> float:
        """Get health as ratio of max (0.0 to 1.0)."""
        if self.max <= 0:
            return 0.0
        return max(0.0, min(1.0, self.current / self.max))
    
    @property
    def is_dead(self) -> bool:
        """Check if health is depleted."""
        return self.current <= 0
    
    @property
    def is_full(self) -> bool:
        """Check if health is at maximum."""
        return self.current >= self.max


@dataclass(frozen=True, slots=True)
class Mana:
    """
    Mana/Energy state value object.
    
    Attributes:
        current: Current mana value
        max: Maximum mana value
        regen: Mana regeneration per second (optional)
    """
    current: float = 100.0
    max: float = 100.0
    regen: float = 0.0
    
    @property
    def ratio(self) -> float:
        """Get mana as ratio of max (0.0 to 1.0)."""
        if self.max <= 0:
            return 0.0
        return max(0.0, min(1.0, self.current / self.max))
    
    @property
    def is_empty(self) -> bool:
        """Check if mana is depleted."""
        return self.current <= 0
    
    @property
    def can_cast(self) -> bool:
        """Check if can cast ability (has mana)."""
        return self.current > 0


@dataclass(frozen=True, slots=True)
class Score:
    """
    Score value object.
    
    Attributes:
        value: Current score value
        kills: Number of kills
        deaths: Number of deaths
        assists: Number of assists
        other: Additional score components
    """
    value: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    other: dict[str, int] = field(default_factory=dict)
    
    @property
    def kda(self) -> float:
        """Calculate KDA (Kills + Assists) / Deaths."""
        if self.deaths == 0:
            return float(self.kills + self.assists)
        return (self.kills + self.assists) / self.deaths


@dataclass(frozen=True, slots=True)
class Experience:
    """
    Experience/Level value object.
    
    Attributes:
        level: Current level
        current: Current XP in current level
        required: XP required for next level
        total: Total XP earned
    """
    level: int = 1
    current: float = 0.0
    required: float = 100.0
    total: float = 0.0
    
    @property
    def ratio(self) -> float:
        """Get progress to next level (0.0 to 1.0)."""
        if self.required <= 0:
            return 0.0
        return max(0.0, min(1.0, self.current / self.required))


@dataclass(frozen=True, slots=True)
class GameTime:
    """
    Game time value object.
    
    Attributes:
        tick: Current game tick (integer)
        elapsed: Elapsed time in seconds
        duration: Match duration in seconds (0 = unlimited)
    """
    tick: int = 0
    elapsed: float = 0.0
    duration: float = 0.0
    
    @property
    def is_match_active(self) -> bool:
        """Check if match is still active."""
        if self.duration <= 0:
            return True
        return self.elapsed < self.duration
    
    @property
    def remaining(self) -> float:
        """Get remaining time in seconds."""
        if self.duration <= 0:
            return float('inf')
        return max(0.0, self.duration - self.elapsed)
    
    @property
    def progress(self) -> float:
        """Get match progress (0.0 to 1.0)."""
        if self.duration <= 0:
            return 0.0
        return min(1.0, self.elapsed / self.duration)


# =============================================================================
# ID Types
# =============================================================================

@dataclass(frozen=True, slots=True)
class TeamID:
    """
    Team identifier value object.
    
    Provides type safety for team IDs.
    
    Attributes:
        value: The team identifier string
    """
    value: str
    
    def __str__(self) -> str:
        return self.value
    
    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True, slots=True)
class EntityID:
    """
    Entity identifier value object.
    
    Provides type safety for entity IDs.
    
    Attributes:
        value: The entity identifier string
    """
    value: str
    
    def __str__(self) -> str:
        return self.value
    
    def __hash__(self) -> int:
        return hash(self.value)


# =============================================================================
# Collection Types
# =============================================================================

@dataclass
class Inventory:
    """
    Mutable inventory container.
    
    Attributes:
        items: Dictionary of item_id to quantity
        capacity: Maximum number of slots (0 = unlimited)
    """
    items: dict[str, int] = field(default_factory=dict)
    capacity: int = 0
    
    def add(self, item_id: str, quantity: int = 1) -> bool:
        """Add item to inventory."""
        if self.capacity > 0 and len(self.items) >= self.capacity:
            if item_id not in self.items:
                return False
        self.items[item_id] = self.items.get(item_id, 0) + quantity
        return True
    
    def remove(self, item_id: str, quantity: int = 1) -> bool:
        """Remove item from inventory."""
        if item_id not in self.items:
            return False
        if self.items[item_id] < quantity:
            return False
        self.items[item_id] -= quantity
        if self.items[item_id] <= 0:
            del self.items[item_id]
        return True
    
    def has(self, item_id: str, quantity: int = 1) -> bool:
        """Check if inventory has item."""
        return self.items.get(item_id, 0) >= quantity
    
    def count(self, item_id: str) -> int:
        """Get quantity of item in inventory."""
        return self.items.get(item_id, 0)


@dataclass
class GameConfig:
    """
    Generic game configuration.
    
    Attributes:
        name: Game/environment name
        max_players: Maximum number of players
        max_teams: Maximum number of teams
        match_duration: Match duration in seconds (0 = unlimited)
        allow_respawn: Whether players can respawn
        respawn_time: Respawn delay in seconds
    """
    name: str = "Game-v0"
    max_players: int = 10
    max_teams: int = 2
    match_duration: float = 600.0
    allow_respawn: bool = False
    respawn_time: float = 5.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "max_players": self.max_players,
            "max_teams": self.max_teams,
            "match_duration": self.match_duration,
            "allow_respawn": self.allow_respawn,
            "respawn_time": self.respawn_time,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", "Game-v0"),
            max_players=data.get("max_players", 10),
            max_teams=data.get("max_teams", 2),
            match_duration=data.get("match_duration", 600.0),
            allow_respawn=data.get("allow_respawn", False),
            respawn_time=data.get("respawn_time", 5.0),
        )
