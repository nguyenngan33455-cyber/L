"""
AI Memory System

Provides memory capabilities for AI agents.
Supports short-term, long-term, and temporal memory.

Memory Types:
- Short-term: Recent observations, immediate context
- Long-term: Learned patterns, persistent knowledge
- Temporal: Time-based facts with expiration

Example:
    >>> memory = Memory(capacity=100)
    >>> 
    >>> # Store observation
    >>> memory.remember("saw_enemy", {"id": "enemy_1", "pos": (100, 200)})
    >>> 
    >>> # Recall recent
    >>> recent = memory.get_recent(count=5)
    >>> 
    >>> # Get history
    >>> history = memory.get_history("saw_enemy")
    >>> 
    >>> # Clear old entries
    >>> memory.forget_old(max_age=60.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from threading import RLock
from time import time
from collections import deque


@dataclass
class MemoryEntry:
    """
    Single memory entry.
    
    Attributes:
        key: Memory key
        value: Memory value
        timestamp: Creation time
        ttl: Time to live (None for permanent)
        importance: Memory importance (0-1)
        memory_type: Type of memory (short_term, long_term, temporal)
    """
    
    key: str
    value: Any
    timestamp: float = field(default_factory=time)
    ttl: float | None = None
    importance: float = 0.5
    memory_type: str = "short_term"
    
    def is_expired(self) -> bool:
        """Check if temporal memory has expired."""
        if self.ttl is None:
            return False
        return time() - self.timestamp > self.ttl
    
    def age(self) -> float:
        """Get age in seconds."""
        return time() - self.timestamp


class Memory:
    """
    Memory system for AI agents.
    
    Provides structured memory storage with different types:
    - Short-term: Recent observations (default)
    - Long-term: Important persistent memories
    - Temporal: Time-based facts
    
    Thread Safety:
        Uses RLock for thread-safe operations.
        
    Determinism:
        Operations are deterministic when seed is provided.
    """
    
    def __init__(
        self,
        capacity: int = 100,
        seed: int | None = None,
        forget_threshold: float = 0.3,
    ) -> None:
        """
        Initialize memory.
        
        Args:
            capacity: Maximum number of entries
            seed: Random seed
            forget_threshold: Importance threshold for auto-forgetting
        """
        self._lock = RLock()
        self._capacity = capacity
        self._seed = seed
        self._forget_threshold = forget_threshold
        
        # Main memory storage
        self._entries: deque[MemoryEntry] = deque(maxlen=capacity)
        
        # Index by key for fast lookup
        self._key_index: dict[str, list[int]] = {}
        
        # Long-term memory (never expires unless explicitly)
        self._long_term: dict[str, MemoryEntry] = {}
        
        # Cooldown tracking
        self._cooldowns: dict[str, float] = {}
    
    def remember(
        self,
        key: str,
        value: Any,
        importance: float = 0.5,
        memory_type: str = "short_term",
        ttl: float | None = None,
    ) -> None:
        """
        Store a memory.
        
        Args:
            key: Memory key
            value: Value to remember
            importance: Importance (0-1)
            memory_type: Type of memory
            ttl: Time to live
        """
        with self._lock:
            entry = MemoryEntry(
                key=key,
                value=value,
                importance=importance,
                memory_type=memory_type,
                ttl=ttl,
            )
            
            if memory_type == "long_term":
                self._long_term[key] = entry
            else:
                self._entries.append(entry)
                
                # Update key index
                if key not in self._key_index:
                    self._key_index[key] = []
                self._key_index[key].append(len(self._entries) - 1)
    
    def recall(self, key: str, default: Any = None) -> Any:
        """
        Recall a memory by key.
        
        Searches both short-term and long-term memory.
        
        Args:
            key: Memory key
            default: Default if not found
            
        Returns:
            Memory value or default
        """
        with self._lock:
            # Check long-term first
            if key in self._long_term:
                entry = self._long_term[key]
                if not entry.is_expired():
                    return entry.value
            
            # Check short-term
            if key in self._key_index:
                for idx in reversed(self._key_index[key]):
                    if idx < len(self._entries):
                        entry = self._entries[idx]
                        if entry.key == key and not entry.is_expired():
                            return entry.value
            
            return default
    
    def get_recent(self, count: int = 10) -> list[MemoryEntry]:
        """
        Get most recent memories.
        
        Args:
            count: Number of entries
            
        Returns:
            List of recent entries
        """
        with self._lock:
            result = []
            seen = set()
            for entry in reversed(self._entries):
                if entry.key not in seen and not entry.is_expired():
                    result.append(entry)
                    seen.add(entry.key)
                    if len(result) >= count:
                        break
            return result
    
    def get_history(self, key: str) -> list[MemoryEntry]:
        """
        Get all memories with a key.
        
        Args:
            key: Memory key
            
        Returns:
            List of entries (oldest first)
        """
        with self._lock:
            result = []
            if key in self._key_index:
                for idx in self._key_index[key]:
                    if idx < len(self._entries):
                        entry = self._entries[idx]
                        if entry.key == key and not entry.is_expired():
                            result.append(entry)
            return result
    
    def forget_old(self, max_age: float) -> int:
        """
        Remove old memories.
        
        Args:
            max_age: Maximum age in seconds
            
        Returns:
            Number of entries removed
        """
        with self._lock:
            count = 0
            cutoff = time() - max_age
            
            # Remove from short-term
            new_entries = deque(maxlen=self._capacity)
            for entry in self._entries:
                if entry.age() < max_age or entry.importance > self._forget_threshold:
                    new_entries.append(entry)
                else:
                    count += 1
            
            self._entries = new_entries
            
            # Rebuild key index
            self._key_index.clear()
            for idx, entry in enumerate(self._entries):
                if entry.key not in self._key_index:
                    self._key_index[entry.key] = []
                self._key_index[entry.key].append(idx)
            
            return count
    
    def update_cooldown(self, key: str, duration: float) -> None:
        """
        Set a cooldown for a key.
        
        Args:
            key: Cooldown key
            duration: Cooldown duration in seconds
        """
        with self._lock:
            # Store absolute end time
            self._cooldowns[key] = time() + duration
    
    def is_on_cooldown(self, key: str) -> bool:
        """Check if key is on cooldown."""
        with self._lock:
            if key not in self._cooldowns:
                return False
            # _cooldowns[key] is now absolute end time
            remaining = self._cooldowns[key] - time()
            if remaining <= 0:
                del self._cooldowns[key]
                return False
            return True
    
    def get_cooldown_remaining(self, key: str) -> float:
        """Get remaining cooldown time."""
        with self._lock:
            if key not in self._cooldowns:
                return 0.0
            remaining = self._cooldowns[key] - time()
            return max(0.0, remaining)
    
    def clear(self) -> None:
        """Clear all short-term memory."""
        with self._lock:
            self._entries.clear()
            self._key_index.clear()
            self._cooldowns.clear()
    
    def clear_all(self) -> None:
        """Clear all memory including long-term."""
        with self._lock:
            self.clear()
            self._long_term.clear()
    
    def __len__(self) -> int:
        """Get number of short-term entries."""
        with self._lock:
            return len(self._entries)
    
    def get_state_dict(self) -> dict:
        """Get memory state for serialization."""
        with self._lock:
            return {
                "capacity": self._capacity,
                "seed": self._seed,
                "forget_threshold": self._forget_threshold,
                "entries": [
                    {
                        "key": e.key,
                        "value": e.value,
                        "timestamp": e.timestamp,
                        "ttl": e.ttl,
                        "importance": e.importance,
                        "memory_type": e.memory_type,
                    }
                    for e in self._entries
                    if not e.is_expired()
                ],
                "long_term": {
                    k: {
                        "value": v.value,
                        "importance": v.importance,
                    }
                    for k, v in self._long_term.items()
                    if not v.is_expired()
                },
            }
