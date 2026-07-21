"""
PanicManager implementation for ZBGym Kernel.

Emergency handling and graceful shutdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Callable
import time
import traceback


class PanicLevel(Enum):
    """Panic level enumeration."""
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3
    PANIC = 4


@dataclass
class PanicEvent:
    """Panic event data."""
    level: PanicLevel
    message: str
    timestamp: float
    source: str | None = None
    exception: Exception | None = None
    traceback: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


class PanicManager:
    """
    Emergency handling system.
    
    Handles different panic levels from INFO to PANIC.
    PANIC level triggers graceful shutdown.
    """

    def __init__(self) -> None:
        """Initialize the panic manager."""
        self._level: PanicLevel = PanicLevel.INFO
        self._lock = Lock()
        self._handlers: dict[PanicLevel, list[Callable[[PanicEvent], None]]] = {
            level: [] for level in PanicLevel
        }
        self._events: list[PanicEvent] = []
        self._max_events: int = 100
        self._on_shutdown: Callable[[], None] | None = None
        self._state_snapshot: dict[str, Any] = {}

    def info(self, message: str, source: str | None = None, **context: Any) -> None:
        """
        Log an info message.
        
        Args:
            message: Info message
            source: Optional source
            **context: Additional context
        """
        self._handle(PanicLevel.INFO, message, source=source, context=context)

    def warning(self, message: str, source: str | None = None, **context: Any) -> None:
        """
        Log a warning.
        
        Args:
            message: Warning message
            source: Optional source
            **context: Additional context
        """
        self._handle(PanicLevel.WARNING, message, source=source, context=context)

    def error(self, message: str, source: str | None = None, **context: Any) -> None:
        """
        Log an error.
        
        Args:
            message: Error message
            source: Optional source
            **context: Additional context
        """
        self._handle(PanicLevel.ERROR, message, source=source, context=context)

    def critical(
        self,
        message: str,
        exception: Exception | None = None,
        source: str | None = None,
        **context: Any
    ) -> None:
        """
        Log a critical error.
        
        Args:
            message: Critical message
            exception: Optional exception
            source: Optional source
            **context: Additional context
        """
        self._handle(
            PanicLevel.CRITICAL,
            message,
            exception=exception,
            source=source,
            context=context
        )

    def panic(
        self,
        message: str,
        exception: Exception | None = None,
        source: str | None = None,
        **context: Any
    ) -> None:
        """
        Trigger panic shutdown.
        
        This will:
        1. Stop tick loop
        2. Freeze RuntimeContext
        3. Save snapshot
        4. Emit panic event
        5. Call shutdown handler
        
        Args:
            message: Panic message
            exception: Optional exception
            source: Optional source
            **context: Additional context
        """
        with self._lock:
            self._level = PanicLevel.PANIC

        self._handle(
            PanicLevel.PANIC,
            message,
            exception=exception,
            source=source,
            context=context
        )

        # Trigger shutdown
        if self._on_shutdown:
            self._on_shutdown()

    def _handle(
        self,
        level: PanicLevel,
        message: str,
        exception: Exception | None = None,
        source: str | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        """
        Handle a panic event.
        
        Args:
            level: Panic level
            message: Message
            exception: Optional exception
            source: Optional source
            context: Optional context
        """
        tb = None
        if exception:
            tb = traceback.format_exc()

        event = PanicEvent(
            level=level,
            message=message,
            timestamp=time.time(),
            source=source,
            exception=exception,
            traceback=tb,
            context=context or {}
        )

        with self._lock:
            self._events.append(event)
            # Keep only last max_events
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]

            # Update max level
            if level.value > self._level.value:
                self._level = level

        # Notify handlers
        for handler_level in PanicLevel:
            if handler_level.value <= level.value:
                for handler in self._handlers.get(handler_level, []):
                    try:
                        handler(event)
                    except Exception:
                        pass  # Don't let handler errors stop processing

    def subscribe(
        self,
        level: PanicLevel,
        handler: Callable[[PanicEvent], None]
    ) -> None:
        """
        Subscribe to panic events.
        
        Args:
            level: Minimum level to receive
            handler: Handler function
        """
        with self._lock:
            if level not in self._handlers:
                self._handlers[level] = []
            self._handlers[level].append(handler)

    def unsubscribe(
        self,
        level: PanicLevel,
        handler: Callable[[PanicEvent], None]
    ) -> None:
        """
        Unsubscribe from panic events.
        
        Args:
            level: Level
            handler: Handler to remove
        """
        with self._lock:
            if handler in self._handlers.get(level, []):
                self._handlers[level].remove(handler)

    def set_shutdown_handler(self, handler: Callable[[], None]) -> None:
        """
        Set shutdown handler.
        
        Called when PANIC is triggered.
        
        Args:
            handler: Shutdown function
        """
        self._on_shutdown = handler

    def save_snapshot(self, state: dict[str, Any]) -> None:
        """
        Save state snapshot.
        
        Args:
            state: State to save
        """
        with self._lock:
            self._state_snapshot = state.copy()

    def get_snapshot(self) -> dict[str, Any]:
        """
        Get saved state snapshot.
        
        Returns:
            State snapshot
        """
        with self._lock:
            return self._state_snapshot.copy()

    @property
    def level(self) -> PanicLevel:
        """Get current panic level."""
        with self._lock:
            return self._level

    @property
    def is_panic(self) -> bool:
        """Check if in panic state."""
        with self._lock:
            return self._level == PanicLevel.PANIC

    def get_events(self, since: float | None = None) -> list[PanicEvent]:
        """
        Get panic events.
        
        Args:
            since: Optional timestamp filter
            
        Returns:
            List of events
        """
        with self._lock:
            if since is None:
                return list(self._events)
            return [e for e in self._events if e.timestamp >= since]

    def reset(self) -> None:
        """Reset panic manager."""
        with self._lock:
            self._level = PanicLevel.INFO
            self._events.clear()
            self._state_snapshot.clear()
