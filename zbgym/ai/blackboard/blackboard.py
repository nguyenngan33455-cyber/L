"""
Blackboard System

Provides a shared knowledge system for AI agents.
The blackboard stores targets, threats, objectives, and other shared information.

The blackboard supports:
- Shared knowledge across agents
- Team-based information
- Temporal facts with expiration
- Thread-safe access

Example:
    >>> blackboard = Blackboard()
    >>> 
    >>> # Store knowledge
    >>> blackboard.set("target_1", {"health": 50, "position": (100, 200)})
    >>> blackboard.set("threat_north", {"entity_id": "enemy_1", "danger": 0.8})
    >>> 
    >>> # Read knowledge
    >>> target = blackboard.get("target_1")
    >>> 
    >>> # Team-specific knowledge
    >>> blackboard.set_for_team("red", "objective", {"type": "capture"})
    >>> 
    >>> # Temporal facts
    >>> blackboard.set_temporary("last_seen_enemy", enemy_id, ttl=5.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from threading import RLock
from time import time


@dataclass
class BlackboardEntry:
    """
    Single entry in the blackboard.
    
    Attributes:
        key: Entry key
        value: Entry value
        owner: Agent ID that created this entry (None for shared)
        team_id: Team ID if team-specific
        timestamp: Creation timestamp
        ttl: Time to live (None for permanent)
        tags: Optional tags for categorization
    """
    
    key: str
    value: Any
    owner: str | None = None
    team_id: str | None = None
    timestamp: float = field(default_factory=time)
    ttl: float | None = None
    tags: set[str] = field(default_factory=set)
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time() - self.timestamp > self.ttl
    
    def age(self) -> float:
        """Get age of entry in seconds."""
        return time() - self.timestamp


class Blackboard:
    """
    Shared knowledge blackboard for AI agents.
    
    Provides thread-safe storage and retrieval of shared knowledge.
    Supports team-based access control and temporal facts.
    
    Thread Safety:
        Uses RLock for thread-safe operations.
        
    Determinism:
        Operations are deterministic when seed is provided.
    """
    
    def __init__(self, seed: int | None = None) -> None:
        """
        Initialize blackboard.
        
        Args:
            seed: Random seed (for future determinism)
        """
        self._lock = RLock()
        self._entries: dict[str, BlackboardEntry] = {}
        self._team_entries: dict[str, dict[str, BlackboardEntry]] = {}
        self._seed = seed
    
    def set(
        self,
        key: str,
        value: Any,
        owner: str | None = None,
        ttl: float | None = None,
        tags: set[str] | None = None,
    ) -> None:
        """
        Set a blackboard entry.
        
        Args:
            key: Entry key
            value: Entry value
            owner: Agent ID that owns this entry
            ttl: Time to live in seconds (None for permanent)
            tags: Optional tags
        """
        with self._lock:
            self._entries[key] = BlackboardEntry(
                key=key,
                value=value,
                owner=owner,
                ttl=ttl,
                tags=tags or set(),
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a blackboard entry.
        
        Args:
            key: Entry key
            default: Default value if not found
            
        Returns:
            Entry value or default
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return default
            if entry.is_expired():
                del self._entries[key]
                return default
            return entry.value
    
    def has(self, key: str) -> bool:
        """
        Check if key exists and is not expired.
        
        Args:
            key: Entry key
            
        Returns:
            True if exists and not expired
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                del self._entries[key]
                return False
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a blackboard entry.
        
        Args:
            key: Entry key
            
        Returns:
            True if deleted
        """
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False
    
    def set_for_team(
        self,
        team_id: str,
        key: str,
        value: Any,
        ttl: float | None = None,
        tags: set[str] | None = None,
    ) -> None:
        """
        Set a team-specific blackboard entry.
        
        Args:
            team_id: Team ID
            key: Entry key
            value: Entry value
            ttl: Time to live
            tags: Optional tags
        """
        with self._lock:
            if team_id not in self._team_entries:
                self._team_entries[team_id] = {}
            self._team_entries[team_id][key] = BlackboardEntry(
                key=key,
                value=value,
                team_id=team_id,
                ttl=ttl,
                tags=tags or set(),
            )
    
    def get_for_team(self, team_id: str, key: str, default: Any = None) -> Any:
        """
        Get a team-specific entry.
        
        Args:
            team_id: Team ID
            key: Entry key
            default: Default value
            
        Returns:
            Entry value or default
        """
        with self._lock:
            team_entries = self._team_entries.get(team_id, {})
            entry = team_entries.get(key)
            if entry is None:
                return default
            if entry.is_expired():
                del team_entries[key]
                return default
            return entry.value
    
    def get_team_keys(self, team_id: str) -> list[str]:
        """Get all keys for a team."""
        with self._lock:
            team_entries = self._team_entries.get(team_id, {})
            return list(team_entries.keys())
    
    def get_by_tag(self, tag: str) -> dict[str, Any]:
        """
        Get all entries with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            Dict of key -> value
        """
        with self._lock:
            result = {}
            for key, entry in self._entries.items():
                if tag in entry.tags and not entry.is_expired():
                    result[key] = entry.value
            return result
    
    def clear_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            count = 0
            expired = [k for k, e in self._entries.items() if e.is_expired()]
            for key in expired:
                del self._entries[key]
                count += 1
            
            for team_id in list(self._team_entries.keys()):
                team_entries = self._team_entries[team_id]
                team_expired = [k for k, e in team_entries.items() if e.is_expired()]
                for key in team_expired:
                    del team_entries[key]
                    count += 1
            
            return count
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._entries.clear()
            self._team_entries.clear()
    
    def keys(self) -> list[str]:
        """Get all non-expired keys."""
        with self._lock:
            self.clear_expired()
            return list(self._entries.keys())
    
    def __len__(self) -> int:
        """Get number of entries."""
        with self._lock:
            self.clear_expired()
            return len(self._entries)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return self.has(key)


# Convenience functions for common blackboard patterns

def create_target_entry(
    entity_id: str,
    position: tuple[float, float],
    health: float,
    threat_level: float = 0.5,
) -> dict:
    """Create a standard target entry."""
    return {
        "entity_id": entity_id,
        "position": position,
        "health": health,
        "threat_level": threat_level,
    }


def create_objective_entry(
    objective_type: str,
    position: tuple[float, float],
    priority: float = 1.0,
) -> dict:
    """Create a standard objective entry."""
    return {
        "type": objective_type,
        "position": position,
        "priority": priority,
    }


def create_navigation_goal(
    position: tuple[float, float],
    speed: float = 1.0,
) -> dict:
    """Create a navigation goal entry."""
    return {
        "position": position,
        "speed": speed,
    }
