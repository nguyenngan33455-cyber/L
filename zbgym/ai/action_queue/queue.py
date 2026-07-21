"""
AI Action Queue

Provides a queue for AI actions with:
- Priority ordering
- Deduplication
- Validation
- Cancellation
- Deterministic replay

Example:
    >>> queue = ActionQueue()
    >>> 
    >>> # Enqueue actions
    >>> queue.enqueue(agent_id="player_1", action=request)
    >>> queue.enqueue(agent_id="player_2", action=request2, priority=10)
    >>> 
    >>> # Get next action
    >>> next_action = queue.dequeue()
    >>> 
    >>> # Clear for tick
    >>> queue.clear_tick()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import TYPE_CHECKING
import hashlib

from zbgym.ai.core.types import ActionRequest, ActionType

if TYPE_CHECKING:
    from zbgym.interfaces import GameState


@dataclass
class QueuedAction:
    """
    An action in the queue.
    
    Attributes:
        agent_id: Agent that produced this action
        action: The action request
        priority: Action priority (higher first)
        tick: Tick when action was queued
        hash: Deterministic hash for replay
        cancelled: Whether action is cancelled
    """
    
    agent_id: str
    action: ActionRequest
    priority: float
    tick: int
    hash: str = ""
    cancelled: bool = False
    
    def __post_init__(self) -> None:
        """Generate deterministic hash."""
        if not self.hash:
            self.hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate deterministic hash for replay."""
        data = f"{self.agent_id}:{self.action.action_type.value}:{self.tick}:{self.priority}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def cancel(self) -> None:
        """Cancel this action."""
        self.cancelled = True


class ActionQueue:
    """
    Queue for AI actions with validation and ordering.
    
    Features:
    - Priority-based ordering
    - Deduplication by agent+action type
    - Validation against GameState
    - Deterministic hash for replay
    - Cancellation support
    
    Thread Safety:
        Uses RLock for thread-safe operations.
    """
    
    def __init__(
        self,
        deduplicate: bool = True,
        allow_idle: bool = True,
    ) -> None:
        """
        Initialize action queue.
        
        Args:
            deduplicate: Whether to deduplicate actions by agent+type
            allow_idle: Whether to allow IDLE actions
        """
        self._lock = RLock()
        self._queue: list[QueuedAction] = []
        self._tick: int = 0
        self._deduplicate = deduplicate
        self._allow_idle = allow_idle
        
        # Stats
        self._total_enqueued: int = 0
        self._total_dequeued: int = 0
        self._total_cancelled: int = 0
        self._total_dropped: int = 0
    
    @property
    def tick(self) -> int:
        """Current queue tick."""
        return self._tick
    
    @property
    def size(self) -> int:
        """Number of actions in queue."""
        with self._lock:
            return len(self._queue)
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        with self._lock:
            return len(self._queue) == 0
    
    def enqueue(
        self,
        agent_id: str,
        action: ActionRequest,
        priority: float | None = None,
        tick: int | None = None,
    ) -> bool:
        """
        Enqueue an action.
        
        Args:
            agent_id: Agent ID
            action: Action to enqueue
            priority: Override priority (default: use action.priority)
            tick: Override tick (default: use current)
            
        Returns:
            True if enqueued
        """
        with self._lock:
            # Check if should allow
            if not self._allow_idle and action.action_type == ActionType.IDLE:
                self._total_dropped += 1
                return False
            
            # Use action priority if not specified
            if priority is None:
                priority = action.priority
            
            # Use current tick if not specified
            if tick is None:
                tick = self._tick
            
            # Deduplication check - find and remove existing
            if self._deduplicate:
                for i, existing in enumerate(self._queue):
                    if (existing.agent_id == agent_id and 
                        existing.action.action_type == action.action_type):
                        # Replace if higher priority, else drop new
                        if priority > existing.priority:
                            self._queue.pop(i)
                            self._total_cancelled += 1
                        else:
                            self._total_dropped += 1
                            return False
                        break
            
            # Create queued action
            queued = QueuedAction(
                agent_id=agent_id,
                action=action,
                priority=priority,
                tick=tick,
            )
            
            self._queue.append(queued)
            self._queue.sort(key=lambda q: (-q.priority, q.tick, q.hash))
            self._total_enqueued += 1
            
            return True
    
    def dequeue(self) -> QueuedAction | None:
        """
        Get the next action from the queue.
        
        Returns:
            Next QueuedAction or None if empty
        """
        with self._lock:
            # Find first non-cancelled action
            for i, queued in enumerate(self._queue):
                if not queued.cancelled:
                    self._queue.pop(i)
                    self._total_dequeued += 1
                    return queued
            
            return None
    
    def peek(self) -> QueuedAction | None:
        """
        Peek at next action without removing.
        
        Returns:
            Next QueuedAction or None
        """
        with self._lock:
            for queued in self._queue:
                if not queued.cancelled:
                    return queued
            return None
    
    def cancel_agent(self, agent_id: str) -> int:
        """
        Cancel all actions for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Number of actions cancelled
        """
        with self._lock:
            count = 0
            # Mark as cancelled (filter during operations)
            for queued in self._queue:
                if queued.agent_id == agent_id and not queued.cancelled:
                    queued.cancelled = True
                    count += 1
            self._total_cancelled += count
            # Remove cancelled items
            self._queue = [q for q in self._queue if not q.cancelled]
            return count
    
    def cancel_action_type(self, action_type: ActionType) -> int:
        """
        Cancel all actions of a specific type.
        
        Args:
            action_type: Action type to cancel
            
        Returns:
            Number of actions cancelled
        """
        with self._lock:
            count = 0
            for queued in self._queue:
                if queued.action.action_type == action_type and not queued.cancelled:
                    queued.cancelled = True
                    count += 1
            self._total_cancelled += count
            # Remove cancelled items
            self._queue = [q for q in self._queue if not q.cancelled]
            return count
    
    def validate_action(
        self,
        action: ActionRequest,
        game_state: GameState,
        agent_id: str,
    ) -> tuple[bool, str | None]:
        """
        Validate an action against game state.
        
        Args:
            action: Action to validate
            game_state: Current game state
            agent_id: Agent ID
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check agent exists
        agent = game_state.get_player(agent_id)
        if agent is None:
            return False, f"Agent '{agent_id}' not found"
        
        # Check agent is alive
        if not agent.is_alive:
            return False, f"Agent '{agent_id}' is not alive"
        
        # Check target exists if specified
        if action.target_id is not None:
            target = game_state.get_player(action.target_id)
            if target is None:
                return False, f"Target '{action.target_id}' not found"
        
        return True, None
    
    def clear_tick(self) -> int:
        """
        Clear all actions for the current tick.
        
        Returns:
            Number of actions cleared
        """
        with self._lock:
            # Remove actions with tick < current tick (expired)
            before = len(self._queue)
            current_tick = self._tick
            self._tick += 1
            self._queue = [
                q for q in self._queue
                if not q.cancelled and q.tick >= self._tick
            ]
            return before - len(self._queue)
    
    def clear_all(self) -> int:
        """
        Clear all actions.
        
        Returns:
            Number of actions cleared
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            return count
    
    def get_for_replay(self) -> list[dict]:
        """
        Get all actions for replay serialization.
        
        Returns:
            List of action data for replay
        """
        with self._lock:
            return [
                {
                    "agent_id": q.agent_id,
                    "action_type": q.action.action_type.value,
                    "target_id": q.action.target_id,
                    "priority": q.priority,
                    "tick": q.tick,
                    "hash": q.hash,
                }
                for q in self._queue
                if not q.cancelled
            ]
    
    def get_stats(self) -> dict:
        """Get queue statistics."""
        with self._lock:
            return {
                "size": len(self._queue),
                "tick": self._tick,
                "total_enqueued": self._total_enqueued,
                "total_dequeued": self._total_dequeued,
                "total_cancelled": self._total_cancelled,
                "total_dropped": self._total_dropped,
                "deduplicate": self._deduplicate,
                "allow_idle": self._allow_idle,
            }
