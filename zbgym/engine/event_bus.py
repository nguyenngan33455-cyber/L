"""Event bus system for ZBGym engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, TypeVar
from uuid import uuid4

from zbgym.constants import EventType


T = TypeVar("T")


@dataclass
class Event:
    """Base event class for the event bus."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: EventType | str = ""
    timestamp: float = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)
    source: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.type, str):
            try:
                self.type = EventType(self.type)
            except ValueError:
                pass


@dataclass
class Subscription:
    """Represents an event subscription."""

    id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType | str | None = None
    callback: Callable[[Event], None] = field(default_factory=lambda: lambda e: None)
    filter_fn: Callable[[Event], bool] | None = None
    once: bool = False
    priority: int = 0


class EventBus:
    """
    Central event bus for decoupled communication between engine components.

    Supports:
    - Subscribe to specific event types
    - Filter events before delivery
    - Priority-based event handling
    - One-time subscriptions
    - Async event dispatch
    """

    def __init__(self) -> None:
        self._subscriptions: dict[str, list[Subscription]] = {}
        self._global_subscriptions: list[Subscription] = []
        self._event_queue: list[Event] = []
        self._processing: bool = False
        self._history: list[Event] = []
        self._max_history: int = 1000

    def subscribe(
        self,
        event_type: EventType | str | None = None,
        callback: Callable[[Event], None] | None = None,
        filter_fn: Callable[[Event], bool] | None = None,
        once: bool = False,
        priority: int = 0,
    ) -> str:
        """
        Subscribe to events.

        Args:
            event_type: Type of event to subscribe to (None for all events)
            callback: Function to call when event is received
            filter_fn: Additional filter function for events
            once: If True, unsubscribe after first event
            priority: Higher priority handlers are called first

        Returns:
            Subscription ID for later unsubscription
        """
        if callback is None:
            callback = lambda e: None

        sub = Subscription(
            event_type=event_type,
            callback=callback,
            filter_fn=filter_fn,
            once=once,
            priority=priority,
        )

        if event_type is None:
            self._global_subscriptions.append(sub)
            self._global_subscriptions.sort(key=lambda s: -s.priority)
        else:
            type_str = event_type.value if isinstance(event_type, EventType) else event_type
            if type_str not in self._subscriptions:
                self._subscriptions[type_str] = []
            self._subscriptions[type_str].append(sub)
            self._subscriptions[type_str].sort(key=lambda s: -s.priority)

        return sub.id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription_id: ID returned from subscribe()

        Returns:
            True if subscription was found and removed
        """
        # Check global subscriptions
        for i, sub in enumerate(self._global_subscriptions):
            if sub.id == subscription_id:
                self._global_subscriptions.pop(i)
                return True

        # Check typed subscriptions
        for subs in self._subscriptions.values():
            for i, sub in enumerate(subs):
                if sub.id == subscription_id:
                    subs.pop(i)
                    return True

        return False

    def emit(self, event: Event | EventType | str, **data: Any) -> Event:
        """
        Emit an event to all subscribers.

        Args:
            event: Event object or event type
            **data: Additional data to include in event

        Returns:
            The emitted event
        """
        if isinstance(event, str):
            event = Event(type=event, data=data)
        elif isinstance(event, EventType):
            event = Event(type=event, data=data)
        elif data:
            event.data.update(data)

        # Store in history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Queue for processing
        self._event_queue.append(event)

        # Process immediately
        self._process_event(event)

        return event

    def _process_event(self, event: Event) -> None:
        """Process a single event."""
        event_type = event.type
        type_str = event_type.value if isinstance(event_type, EventType) else event_type

        # Process global subscriptions
        to_remove: list[Subscription] = []
        for sub in self._global_subscriptions:
            if sub.filter_fn is None or sub.filter_fn(event):
                sub.callback(event)
                if sub.once:
                    to_remove.append(sub)

        for sub in to_remove:
            self._global_subscriptions.remove(sub)

        # Process type-specific subscriptions
        if type_str in self._subscriptions:
            to_remove.clear()
            for sub in self._subscriptions[type_str]:
                if sub.filter_fn is None or sub.filter_fn(event):
                    sub.callback(event)
                    if sub.once:
                        to_remove.append(sub)

            for sub in to_remove:
                self._subscriptions[type_str].remove(sub)

    def get_history(
        self,
        event_type: EventType | str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """
        Get recent event history.

        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        events = self._history
        if event_type is not None:
            type_str = event_type.value if isinstance(event_type, EventType) else event_type
            events = [e for e in events if str(e.type) == type_str]

        return events[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()

    def on(
        self,
        event_type: EventType | str,
        filter_fn: Callable[[Event], bool] | None = None,
        priority: int = 0,
    ) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:
        """
        Decorator for subscribing to events.

        Usage:
            @event_bus.on(EventType.CHARACTER_DEATH)
            def handle_death(event: Event) -> None:
                print(f"Character died: {event.data}")

        Args:
            event_type: Type of event to subscribe to
            filter_fn: Optional filter function
            priority: Handler priority

        Returns:
            Decorator function
        """

        def decorator(callback: Callable[[Event], None]) -> Callable[[Event], None]:
            self.subscribe(event_type, callback, filter_fn, priority=priority)
            return callback

        return decorator

    def once(
        self,
        event_type: EventType | str,
        callback: Callable[[Event], None] | None = None,
    ) -> str | Callable[[Callable[[Event], None]], Callable[[Event], None]]:
        """
        Subscribe to an event once.

        Can be used as decorator or direct call.
        """
        if callback is None:
            return self._once_decorator(event_type)

        return self.subscribe(event_type, callback, once=True)

    def _once_decorator(
        self, event_type: EventType | str
    ) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:
        def decorator(callback: Callable[[Event], None]) -> Callable[[Event], None]:
            self.subscribe(event_type, callback, once=True)
            return callback

        return decorator

    def create_filter(
        self,
        **criteria: Any,
    ) -> Callable[[Event], bool]:
        """
        Create a filter function for event subscriptions.

        Args:
            **criteria: Event attributes to filter on

        Returns:
            Filter function
        """

        def filter_fn(event: Event) -> bool:
            for key, value in criteria.items():
                if key == "type":
                    if isinstance(value, str):
                        if str(event.type) != value:
                            return False
                    elif event.type != value:
                        return False
                elif key == "source":
                    if event.source != value:
                        return False
                elif key == "data_key":
                    # Filter by data key existence
                    if value not in event.data:
                        return False
                elif event.data.get(key) != value:
                    return False
            return True

        return filter_fn

    def wait_for(
        self,
        event_type: EventType | str,
        timeout: float = 10.0,
    ) -> Event | None:
        """
        Wait for a specific event (blocking).

        Note: This is for synchronous usage. For async, use async_wait_for.

        Args:
            event_type: Type of event to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            The event if received, None if timeout
        """
        import threading
        import time

        result: list[Event] = []
        event_received = threading.Event()

        def capture(event: Event) -> None:
            result.append(event)
            event_received.set()

        sub_id = self.subscribe(event_type, capture)

        # Wait with timeout
        event_received.wait(timeout=timeout)

        self.unsubscribe(sub_id)
        return result[0] if result else None
