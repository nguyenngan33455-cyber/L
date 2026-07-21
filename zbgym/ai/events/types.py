"""
AI Event Types

Defines events for AI lifecycle management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import hashlib


class AIAgentEventType(Enum):
    """
    Types of AI agent events.
    
    Lifecycle Events:
    - AGENT_CREATED: Agent instance created
    - AGENT_INITIALIZED: Agent initialized
    - AGENT_DESTROYED: Agent shutdown/destroyed
    
    Decision Events:
    - DECISION_STARTED: Agent started thinking
    - DECISION_FINISHED: Agent finished thinking
    - ACTION_SUBMITTED: Action added to queue
    - ACTION_EXECUTED: Action executed in environment
    
    Control Events:
    - AGENT_PAUSED: Agent paused
    - AGENT_RESUMED: Agent resumed
    - AGENT_RESET: Agent state reset
    
    Team Events:
    - TEAM_JOINED: Agent joined a team
    - TEAM_LEFT: Agent left a team
    
    Error Events:
    - DECISION_ERROR: Decision failed
    - ACTION_ERROR: Action failed
    """
    
    # Lifecycle
    AGENT_CREATED = "agent_created"
    AGENT_INITIALIZED = "agent_initialized"
    AGENT_DESTROYED = "agent_destroyed"
    
    # Decisions
    DECISION_STARTED = "decision_started"
    DECISION_FINISHED = "decision_finished"
    ACTION_SUBMITTED = "action_submitted"
    ACTION_EXECUTED = "action_executed"
    
    # Control
    AGENT_PAUSED = "agent_paused"
    AGENT_RESUMED = "agent_resumed"
    AGENT_RESET = "agent_reset"
    
    # Team
    TEAM_JOINED = "team_joined"
    TEAM_LEFT = "team_left"
    
    # Errors
    DECISION_ERROR = "decision_error"
    ACTION_ERROR = "action_error"


@dataclass
class AIAgentEvent:
    """
    Event emitted during AI agent lifecycle.
    
    Attributes:
        event_type: Type of event
        agent_id: Agent identifier
        tick: Game tick when event occurred
        timestamp: Wall clock timestamp
        data: Additional event data
        hash: Deterministic hash for replay
    """
    
    event_type: AIAgentEventType
    agent_id: str
    tick: int
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    data: dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    
    def __post_init__(self) -> None:
        """Generate deterministic hash."""
        if not self.hash:
            self.hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate deterministic hash."""
        data = f"{self.event_type.value}:{self.agent_id}:{self.tick}"
        if self.data:
            # Sort keys for determinism
            sorted_data = sorted(self.data.items())
            data += f":{sorted_data}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "tick": self.tick,
            "timestamp": self.timestamp,
            "data": self.data,
            "hash": self.hash,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> AIAgentEvent:
        """Create from dictionary."""
        return cls(
            event_type=AIAgentEventType(data["event_type"]),
            agent_id=data["agent_id"],
            tick=data["tick"],
            timestamp=data.get("timestamp", 0.0),
            data=data.get("data", {}),
            hash=data.get("hash", ""),
        )


class AIAgentEventLogger:
    """
    Logs AI agent events for replay and debugging.
    
    Thread-safe event logging with deterministic hashing.
    """
    
    def __init__(self, max_events: int = 10000) -> None:
        """
        Initialize event logger.
        
        Args:
            max_events: Maximum events to store
        """
        from collections import deque
        from threading import RLock
        
        self._events: deque[AIAgentEvent] = deque(maxlen=max_events)
        self._lock = RLock()
        self._max_events = max_events
        self._event_counts: dict[AIAgentEventType, int] = {}
    
    def log(self, event: AIAgentEvent) -> None:
        """
        Log an event.
        
        Args:
            event: Event to log
        """
        with self._lock:
            self._events.append(event)
            self._event_counts[event.event_type] = (
                self._event_counts.get(event.event_type, 0) + 1
            )
    
    def log_event(
        self,
        event_type: AIAgentEventType,
        agent_id: str,
        tick: int,
        **data: Any,
    ) -> AIAgentEvent:
        """
        Create and log an event.
        
        Args:
            event_type: Type of event
            agent_id: Agent ID
            tick: Game tick
            **data: Additional event data
            
        Returns:
            Created event
        """
        event = AIAgentEvent(
            event_type=event_type,
            agent_id=agent_id,
            tick=tick,
            data=data,
        )
        self.log(event)
        return event
    
    def get_events(
        self,
        agent_id: str | None = None,
        event_type: AIAgentEventType | None = None,
        tick_range: tuple[int, int] | None = None,
    ) -> list[AIAgentEvent]:
        """
        Get events with optional filtering.
        
        Args:
            agent_id: Filter by agent ID
            event_type: Filter by event type
            tick_range: Filter by tick range (start, end)
            
        Returns:
            List of matching events
        """
        with self._lock:
            events = list(self._events)
        
        if agent_id is not None:
            events = [e for e in events if e.agent_id == agent_id]
        
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        
        if tick_range is not None:
            start, end = tick_range
            events = [e for e in events if start <= e.tick <= end]
        
        return events
    
    def clear(self) -> int:
        """
        Clear all events.
        
        Returns:
            Number of events cleared
        """
        with self._lock:
            count = len(self._events)
            self._events.clear()
            self._event_counts.clear()
            return count
    
    def get_stats(self) -> dict:
        """Get event statistics."""
        with self._lock:
            return {
                "total_events": len(self._events),
                "max_events": self._max_events,
                "event_counts": dict(self._event_counts),
            }


# Convenience functions for common events

def log_agent_created(
    logger: AIAgentEventLogger,
    agent_id: str,
    tick: int,
    agent_type: str,
    **kwargs: Any,
) -> AIAgentEvent:
    """Log agent creation event."""
    return logger.log_event(
        AIAgentEventType.AGENT_CREATED,
        agent_id,
        tick,
        agent_type=agent_type,
        **kwargs,
    )


def log_decision_started(
    logger: AIAgentEventLogger,
    agent_id: str,
    tick: int,
    **kwargs: Any,
) -> AIAgentEvent:
    """Log decision started event."""
    return logger.log_event(
        AIAgentEventType.DECISION_STARTED,
        agent_id,
        tick,
        **kwargs,
    )


def log_decision_finished(
    logger: AIAgentEventLogger,
    agent_id: str,
    tick: int,
    action_type: str,
    duration: float,
    **kwargs: Any,
) -> AIAgentEvent:
    """Log decision finished event."""
    return logger.log_event(
        AIAgentEventType.DECISION_FINISHED,
        agent_id,
        tick,
        action_type=action_type,
        duration=duration,
        **kwargs,
    )


def log_action_submitted(
    logger: AIAgentEventLogger,
    agent_id: str,
    tick: int,
    action_type: str,
    **kwargs: Any,
) -> AIAgentEvent:
    """Log action submitted event."""
    return logger.log_event(
        AIAgentEventType.ACTION_SUBMITTED,
        agent_id,
        tick,
        action_type=action_type,
        **kwargs,
    )


def log_agent_paused(
    logger: AIAgentEventLogger,
    agent_id: str,
    tick: int,
) -> AIAgentEvent:
    """Log agent paused event."""
    return logger.log_event(
        AIAgentEventType.AGENT_PAUSED,
        agent_id,
        tick,
    )


def log_agent_resumed(
    logger: AIAgentEventLogger,
    agent_id: str,
    tick: int,
) -> AIAgentEvent:
    """Log agent resumed event."""
    return logger.log_event(
        AIAgentEventType.AGENT_RESUMED,
        agent_id,
        tick,
    )


def log_decision_error(
    logger: AIAgentEventLogger,
    agent_id: str,
    tick: int,
    error: str,
    **kwargs: Any,
) -> AIAgentEvent:
    """Log decision error event."""
    return logger.log_event(
        AIAgentEventType.DECISION_ERROR,
        agent_id,
        tick,
        error=error,
        **kwargs,
    )
