"""
StateStore implementation for ZBGym Kernel.

Thread-safe state storage for modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


class StateStore:
    """
    Thread-safe state storage.
    
    Modules store and retrieve state through this interface.
    No global state. No singletons.
    """

    def __init__(self) -> None:
        """Initialize the state store."""
        self._state: dict[str, Any] = {}
        self._lock = Lock()
        self._snapshots: list[dict[str, Any]] = []

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get state value.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        with self._lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set state value.
        
        Args:
            key: State key
            value: State value
        """
        with self._lock:
            self._state[key] = value

    def delete(self, key: str) -> bool:
        """
        Delete state value.
        
        Args:
            key: State key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._state:
                del self._state[key]
                return True
            return False

    def has(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: State key
            
        Returns:
            True if key exists
        """
        with self._lock:
            return key in self._state

    def snapshot(self) -> dict[str, Any]:
        """
        Create a state snapshot.
        
        Returns:
            Dictionary copy of current state
        """
        with self._lock:
            snapshot = dict(self._state)
            self._snapshots.append(snapshot)
            return snapshot

    def restore(self, snapshot: dict[str, Any]) -> None:
        """
        Restore from snapshot.
        
        Args:
            snapshot: State snapshot to restore
        """
        with self._lock:
            self._state.clear()
            self._state.update(snapshot)

    def clear(self) -> None:
        """Clear all state."""
        with self._lock:
            self._state.clear()

    def keys(self) -> list[str]:
        """Get all state keys."""
        with self._lock:
            return list(self._state.keys())

    def values(self) -> list[Any]:
        """Get all state values."""
        with self._lock:
            return list(self._state.values())

    def items(self) -> list[tuple[str, Any]]:
        """Get all state items."""
        with self._lock:
            return list(self._state.items())

    def get_snapshot_count(self) -> int:
        """Get number of stored snapshots."""
        with self._lock:
            return len(self._snapshots)

    def get_snapshots(self) -> list[dict[str, Any]]:
        """Get all stored snapshots."""
        with self._lock:
            return list(self._snapshots)

    def shutdown(self) -> None:
        """Shutdown the state store."""
        with self._lock:
            self._state.clear()
            self._snapshots.clear()


@dataclass
class StateSnapshot:
    """Represents a state snapshot for serialization."""
    
    timestamp: float
    tick: int
    state: dict[str, Any]
    metadata: dict[str, Any] = None
    
    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}
