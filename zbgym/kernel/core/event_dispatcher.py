"""
EventDispatcher implementation for ZBGym Kernel.

Central event routing with priority and deterministic ordering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable
import time
from uuid import uuid4


@dataclass
class Event:
    """Event object."""
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    source: str | None = None
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class Subscription:
    """Event subscription."""
    id: str
    event_type: str | None
    callback: Callable[[Event], None]
    priority: int = 0
    filter_fn: Callable[[Event], bool] | None = None
    once: bool = False


class EventDispatcher:
    """
    Central event dispatcher.
    
    Routes events to subscribers with priority ordering.
    Thread-safe and deterministic.
    """

    def __init__(self) -> None:
        """Initialize the event dispatcher."""
        self._subscriptions: dict[str, list[Subscription]] = {}
        self._global_subscriptions: list[Subscription] = []
        self._pending_events: list[Event] = []
        self._lock = Lock()
        self._dispatching: bool = False
        self._dispatch_count: int = 0

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], None],
        priority: int = 0,
        filter_fn: Callable[[Event], bool] | None = None,
        once: bool = False
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            event_type: Event type to subscribe to
            callback: Callback function
            priority: Higher priority called first
            filter_fn: Optional filter function
            once: If True, unsubscribe after first call
            
        Returns:
            Subscription ID
        """
        subscription = Subscription(
            id=str(uuid4()),
            event_type=event_type,
            callback=callback,
            priority=priority,
            filter_fn=filter_fn,
            once=once
        )

        with self._lock:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
            self._subscriptions[event_type].append(subscription)
            # Sort by priority (descending)
            self._subscriptions[event_type].sort(key=lambda s: s.priority, reverse=True)

        return subscription.id

    def subscribe_all(
        self,
        callback: Callable[[Event], None],
        priority: int = 0,
        filter_fn: Callable[[Event], bool] | None = None
    ) -> str:
        """
        Subscribe to all events.
        
        Args:
            callback: Callback function
            priority: Higher priority called first
            filter_fn: Optional filter function
            
        Returns:
            Subscription ID
        """
        subscription = Subscription(
            id=str(uuid4()),
            event_type=None,
            callback=callback,
            priority=priority,
            filter_fn=filter_fn,
            once=False
        )

        with self._lock:
            self._global_subscriptions.append(subscription)
            self._global_subscriptions.sort(key=lambda s: s.priority, reverse=True)

        return subscription.id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            True if unsubscribed
        """
        with self._lock:
            # Check specific subscriptions
            for event_type, subs in self._subscriptions.items():
                for i, sub in enumerate(subs):
                    if sub.id == subscription_id:
                        subs.pop(i)
                        return True

            # Check global subscriptions
            for i, sub in enumerate(self._global_subscriptions):
                if sub.id == subscription_id:
                    self._global_subscriptions.pop(i)
                    return True

        return False

    def emit(self, event: Event) -> Event:
        """
        Emit an event.
        
        Args:
            event: Event to emit
            
        Returns:
            The emitted event
        """
        with self._lock:
            if self._dispatching:
                self._pending_events.append(event)
            else:
                self._dispatch_event(event)
        return event

    def emit_now(self, event: Event) -> Event:
        """
        Emit an event immediately (not deferred).
        
        Args:
            event: Event to emit
            
        Returns:
            The emitted event
        """
        self._dispatch_event(event)
        return event

    def _dispatch_event(self, event: Event) -> None:
        """
        Dispatch event to subscribers.
        
        Args:
            event: Event to dispatch
        """
        self._dispatching = True
        self._dispatch_count += 1

        try:
            to_remove: list[tuple[str, Subscription]] = []

            # Dispatch to specific subscriptions
            subs = self._subscriptions.get(event.type, [])
            for subscription in subs:
                if subscription.filter_fn and not subscription.filter_fn(event):
                    continue

                try:
                    subscription.callback(event)
                except Exception as e:
                    # Log but don't stop dispatch
                    import logging
                    logging.getLogger(__name__).error(f"Event callback error: {e}")

                if subscription.once:
                    to_remove.append((event.type, subscription))

            # Dispatch to global subscriptions
            for subscription in self._global_subscriptions:
                if subscription.filter_fn and not subscription.filter_fn(event):
                    continue

                try:
                    subscription.callback(event)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Event callback error: {e}")

            # Remove one-time subscriptions
            for event_type, subscription in to_remove:
                if event_type in self._subscriptions:
                    try:
                        self._subscriptions[event_type].remove(subscription)
                    except ValueError:
                        pass

        finally:
            self._dispatching = False

    def dispatch_pending(self) -> int:
        """
        Dispatch all pending events.
        
        Returns:
            Number of events dispatched
        """
        count = 0
        with self._lock:
            events = self._pending_events
            self._pending_events = []

        for event in events:
            self._dispatch_event(event)
            count += 1

        return count

    def clear(self) -> None:
        """Clear all subscriptions and pending events."""
        with self._lock:
            self._subscriptions.clear()
            self._global_subscriptions.clear()
            self._pending_events.clear()

    def get_subscription_count(self) -> int:
        """Get total number of subscriptions."""
        with self._lock:
            return (
                sum(len(subs) for subs in self._subscriptions.values())
                + len(self._global_subscriptions)
            )

    def get_event_types(self) -> list[str]:
        """Get all registered event types."""
        with self._lock:
            return list(self._subscriptions.keys())
