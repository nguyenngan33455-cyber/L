"""
Kernel Event Dispatcher Tests for Phase 26.5 Validation.

Tests event routing and priority ordering.
"""

import pytest
from zbgym.kernel import (
    EventDispatcher, Event
)


class TestEventDispatcher:
    """Test event dispatcher."""

    def test_subscribe_emit(self):
        """Test basic subscribe and emit."""
        dispatcher = EventDispatcher()
        received = []
        
        def callback(event):
            received.append(event)
        
        dispatcher.subscribe("test", callback)
        dispatcher.emit(Event(type="test"))
        
        assert len(received) == 1
        
        dispatcher.clear()

    def test_unsubscribe(self):
        """Test unsubscribe."""
        dispatcher = EventDispatcher()
        received = []
        
        def callback(event):
            received.append(event)
        
        sub_id = dispatcher.subscribe("test", callback)
        dispatcher.unsubscribe(sub_id)
        
        dispatcher.emit(Event(type="test"))
        assert len(received) == 0
        
        dispatcher.clear()

    def test_priority_ordering(self):
        """Test priority ordering."""
        dispatcher = EventDispatcher()
        order = []
        
        def low_priority(event):
            order.append("low")
        
        def high_priority(event):
            order.append("high")
        
        def medium_priority(event):
            order.append("medium")
        
        dispatcher.subscribe("test", low_priority, priority=0)
        dispatcher.subscribe("test", high_priority, priority=100)
        dispatcher.subscribe("test", medium_priority, priority=50)
        
        dispatcher.emit(Event(type="test"))
        
        # Should be ordered by priority (high first)
        assert order == ["high", "medium", "low"]
        
        dispatcher.clear()

    def test_filter_function(self):
        """Test event filtering."""
        dispatcher = EventDispatcher()
        received = []
        
        def callback(event):
            received.append(event)
        
        def filter_func(event):
            return event.data.get("allowed", False)
        
        dispatcher.subscribe("test", callback, filter_fn=filter_func)
        
        # Rejected
        dispatcher.emit(Event(type="test", data={"allowed": False}))
        assert len(received) == 0
        
        # Accepted
        dispatcher.emit(Event(type="test", data={"allowed": True}))
        assert len(received) == 1
        
        dispatcher.clear()

    def test_once_subscription(self):
        """Test one-time subscription."""
        dispatcher = EventDispatcher()
        received = []
        
        def callback(event):
            received.append(event)
        
        dispatcher.subscribe("test", callback, once=True)
        
        dispatcher.emit(Event(type="test"))
        assert len(received) == 1
        
        dispatcher.emit(Event(type="test"))
        assert len(received) == 1  # Should not receive again
        
        dispatcher.clear()

    def test_global_subscription(self):
        """Test subscription to all events."""
        dispatcher = EventDispatcher()
        received = []
        
        def callback(event):
            received.append(event)
        
        dispatcher.subscribe_all(callback)
        
        dispatcher.emit(Event(type="test1"))
        dispatcher.emit(Event(type="test2"))
        dispatcher.emit(Event(type="test3"))
        
        assert len(received) == 3
        
        dispatcher.clear()

    def test_event_data(self):
        """Test event data preservation."""
        dispatcher = EventDispatcher()
        received = []
        
        def callback(event):
            received.append(event.data)
        
        dispatcher.subscribe("test", callback)
        
        dispatcher.emit(Event(type="test", data={"key": "value", "num": 42}))
        
        assert received[0]["key"] == "value"
        assert received[0]["num"] == 42
        
        dispatcher.clear()

    def test_pending_events(self):
        """Test pending event queue."""
        dispatcher = EventDispatcher()
        
        received = []
        
        def callback(event):
            received.append(event)
        
        dispatcher.subscribe("test", callback)
        
        # Emit while dispatching would queue
        dispatcher.emit(Event(type="test"))
        
        # Dispatch pending
        count = dispatcher.dispatch_pending()
        
        assert len(received) == 1
        
        dispatcher.clear()

    def test_subscription_count(self):
        """Test subscription count."""
        dispatcher = EventDispatcher()
        
        dispatcher.subscribe("test1", lambda e: None)
        dispatcher.subscribe("test2", lambda e: None)
        dispatcher.subscribe_all(lambda e: None)
        
        assert dispatcher.get_subscription_count() == 3
        
        dispatcher.clear()

    def test_get_event_types(self):
        """Test getting registered event types."""
        dispatcher = EventDispatcher()
        
        dispatcher.subscribe("type1", lambda e: None)
        dispatcher.subscribe("type2", lambda e: None)
        
        types = dispatcher.get_event_types()
        assert set(types) == {"type1", "type2"}
        
        dispatcher.clear()


class TestEventOrdering:
    """Test event ordering determinism."""

    def test_multiple_events_order(self):
        """Test multiple events maintain order."""
        dispatcher = EventDispatcher()
        received = []
        
        def callback(event):
            received.append(event.data["order"])
        
        dispatcher.subscribe("test", callback)
        
        for i in range(100):
            dispatcher.emit(Event(type="test", data={"order": i}))
        
        # Should be in order
        assert received == list(range(100))
        
        dispatcher.clear()

    def test_multiple_subscribers_order(self):
        """Test multiple subscribers called in order."""
        dispatcher = EventDispatcher()
        call_order = []
        
        for i in range(10):
            def callback(e, idx=i):
                call_order.append(idx)
            dispatcher.subscribe("test", callback, priority=i)
        
        dispatcher.emit(Event(type="test"))
        
        # Should be called in priority order
        assert call_order == list(range(10))
        
        dispatcher.clear()


class TestEventPerformance:
    """Test event dispatcher performance."""

    def test_many_events(self):
        """Test handling many events."""
        dispatcher = EventDispatcher()
        count = 0
        
        def callback(event):
            nonlocal count
            count += 1
        
        dispatcher.subscribe("test", callback)
        
        for _ in range(1000):
            dispatcher.emit(Event(type="test"))
        
        assert count == 1000
        
        dispatcher.clear()

    def test_many_subscribers(self):
        """Test handling many subscribers."""
        dispatcher = EventDispatcher()
        received = []
        
        def callback(event):
            received.append(1)
        
        for i in range(100):
            dispatcher.subscribe("test", callback)
        
        dispatcher.emit(Event(type="test"))
        
        assert len(received) == 100
        
        dispatcher.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
