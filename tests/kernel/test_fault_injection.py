"""
Kernel Fault Injection Tests for Phase 26.5 Validation.

Tests fault isolation and recovery mechanisms.
"""

import pytest
from zbgym.kernel import (
    Kernel, KernelState, KernelConfig,
    EventDispatcher, Event,
    PanicManager, PanicLevel
)


class TestFaultIsolation:
    """Test fault isolation."""

    def test_event_callback_error_isolated(self):
        """Test errors in event callbacks don't crash dispatcher."""
        dispatcher = EventDispatcher()
        
        errors = []
        
        def failing_callback(event):
            raise RuntimeError("Simulated failure")
        
        def good_callback(event):
            errors.append(event)
        
        dispatcher.subscribe("test", failing_callback)
        dispatcher.subscribe("test", good_callback)
        
        # Should not raise
        dispatcher.emit(Event(type="test"))
        
        # Good callback should still be called
        assert len(errors) == 1
        
        dispatcher.clear()

    def test_multiple_callback_errors(self):
        """Test multiple callback errors are isolated."""
        dispatcher = EventDispatcher()
        
        call_count = []
        
        def failing1(event):
            raise RuntimeError("Fail 1")
        
        def failing2(event):
            raise RuntimeError("Fail 2")
        
        def good(event):
            call_count.append(1)
        
        dispatcher.subscribe("test", failing1)
        dispatcher.subscribe("test", failing2)
        dispatcher.subscribe("test", good)
        
        dispatcher.emit(Event(type="test"))
        
        # Good callback should be called
        assert len(call_count) == 1
        
        dispatcher.clear()


class TestPanicManager:
    """Test panic manager."""

    def test_info_level(self):
        """Test INFO level panic."""
        manager = PanicManager()
        
        manager.info("Test info message")
        
        assert manager.level == PanicLevel.INFO
        assert len(manager.get_events()) == 1
        
        events = manager.get_events()
        assert events[0].level == PanicLevel.INFO
        
        manager.reset()

    def test_warning_level(self):
        """Test WARNING level panic."""
        manager = PanicManager()
        
        manager.warning("Test warning")
        
        assert manager.level == PanicLevel.WARNING
        assert len(manager.get_events()) == 1
        
        events = manager.get_events()
        assert events[0].level == PanicLevel.WARNING
        
        manager.reset()

    def test_error_level(self):
        """Test ERROR level panic."""
        manager = PanicManager()
        
        manager.error("Test error")
        
        assert manager.level == PanicLevel.ERROR
        assert len(manager.get_events()) == 1
        
        events = manager.get_events()
        assert events[0].level == PanicLevel.ERROR
        
        manager.reset()

    def test_critical_level(self):
        """Test CRITICAL level panic."""
        manager = PanicManager()
        
        manager.critical("Test critical", exception=ValueError("test"))
        
        assert manager.level == PanicLevel.CRITICAL
        assert len(manager.get_events()) == 1
        
        events = manager.get_events()
        assert events[0].level == PanicLevel.CRITICAL
        assert events[0].exception is not None
        
        manager.reset()

    def test_panic_triggers_shutdown(self):
        """Test PANIC level triggers shutdown handler."""
        manager = PanicManager()
        shutdown_called = []
        
        def shutdown_handler():
            shutdown_called.append(1)
        
        manager.set_shutdown_handler(shutdown_handler)
        
        # Trigger panic
        manager.panic("Test panic")
        
        assert manager.is_panic
        assert len(shutdown_called) == 1
        
        manager.reset()

    def test_panic_preserves_state(self):
        """Test panic preserves state snapshot."""
        manager = PanicManager()
        
        manager.panic("Test panic")
        
        snapshot = manager.get_snapshot()
        assert snapshot is not None
        
        manager.reset()

    def test_panic_subscription(self):
        """Test panic event subscription."""
        manager = PanicManager()
        
        received = []
        
        def panic_handler(event):
            received.append(event)
        
        manager.subscribe(PanicLevel.ERROR, panic_handler)
        
        manager.error("Test error")
        
        assert len(received) == 1
        assert received[0].level == PanicLevel.ERROR
        
        manager.reset()


class TestRecovery:
    """Test recovery mechanisms."""

    def test_kernel_survives_multiple_restarts(self):
        """Test kernel survives multiple start/stop cycles."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        
        for i in range(10):
            kernel.start()
            kernel.stop()
            assert kernel.state == KernelState.STOPPED
        
        kernel.shutdown()

    def test_kernel_survives_tick_errors(self):
        """Test kernel survives tick with registered errors."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        # Run multiple ticks
        for _ in range(100):
            kernel.tick()
        
        assert kernel.state == KernelState.RUNNING
        
        kernel.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
