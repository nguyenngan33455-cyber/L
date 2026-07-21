"""
Kernel Lifecycle Manager Tests for Phase 26.5 Validation.

Tests module lifecycle state transitions.
"""

import pytest
from zbgym.kernel import (
    LifecycleManager, ModuleState, LifecycleTransitionError,
    LifecycleCallbacks
)


class TestLifecycleManager:
    """Test lifecycle manager."""

    def test_discover_module(self):
        """Test module discovery."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        
        assert manager.get_state("test_module") == ModuleState.DISCOVERED

    def test_register_transition(self):
        """Test register transition."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        manager.register("test_module")
        
        assert manager.get_state("test_module") == ModuleState.REGISTERED

    def test_initialize_transition(self):
        """Test initialize transition."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        manager.register("test_module")
        manager.initialize("test_module")
        
        assert manager.get_state("test_module") == ModuleState.INITIALIZED

    def test_start_transition(self):
        """Test start transition."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        manager.register("test_module")
        manager.initialize("test_module")
        manager.start("test_module")
        
        assert manager.get_state("test_module") == ModuleState.STARTED

    def test_full_lifecycle(self):
        """Test full lifecycle."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        
        # Register -> Initialize -> Start -> Running -> Paused -> Stopped -> Shutdown -> Unloaded
        manager.register("test_module")
        assert manager.get_state("test_module") == ModuleState.REGISTERED
        
        manager.initialize("test_module")
        assert manager.get_state("test_module") == ModuleState.INITIALIZED
        
        manager.start("test_module")
        assert manager.get_state("test_module") == ModuleState.STARTED
        
        manager.set_running("test_module")
        assert manager.get_state("test_module") == ModuleState.RUNNING
        
        manager.pause("test_module")
        assert manager.get_state("test_module") == ModuleState.PAUSED
        
        manager.resume("test_module")
        assert manager.get_state("test_module") == ModuleState.RUNNING
        
        manager.stop("test_module")
        assert manager.get_state("test_module") == ModuleState.STOPPED
        
        manager.shutdown("test_module")
        assert manager.get_state("test_module") == ModuleState.SHUTDOWN


class TestInvalidTransitions:
    """Test invalid transition rejection."""

    def test_cannot_skip_register(self):
        """Test cannot skip register."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        
        with pytest.raises(LifecycleTransitionError):
            manager.initialize("test_module")

    def test_cannot_skip_initialize(self):
        """Test cannot skip initialize."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        manager.register("test_module")
        
        with pytest.raises(LifecycleTransitionError):
            manager.start("test_module")

    def test_cannot_shutdown_from_discovered(self):
        """Test cannot shutdown from discovered."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        
        with pytest.raises(LifecycleTransitionError):
            manager.shutdown("test_module")


class TestLifecycleCallbacks:
    """Test lifecycle callbacks."""

    def test_callbacks_called(self):
        """Test callbacks are called."""
        class TestCallbacks(LifecycleCallbacks):
            def __init__(self):
                self.calls = []
            
            def on_initializing(self):
                self.calls.append("initializing")
            
            def on_initialized(self):
                self.calls.append("initialized")
            
            def on_starting(self):
                self.calls.append("starting")
            
            def on_started(self):
                self.calls.append("started")
            
            def on_running(self):
                self.calls.append("running")
            
            def on_stopping(self):
                self.calls.append("stopping")
            
            def on_shutting_down(self):
                self.calls.append("shutting_down")
        
        callbacks = TestCallbacks()
        manager = LifecycleManager()
        
        manager.discover("test_module", object(), callbacks)
        manager.register("test_module")
        manager.initialize("test_module")
        manager.start("test_module")
        manager.set_running("test_module")
        manager.stop("test_module")
        manager.shutdown("test_module")
        
        assert "initializing" in callbacks.calls
        assert "initialized" in callbacks.calls
        assert "starting" in callbacks.calls
        assert "started" in callbacks.calls
        assert "running" in callbacks.calls
        assert "stopping" in callbacks.calls
        assert "shutting_down" in callbacks.calls


class TestLifecycleAPI:
    """Test lifecycle manager API."""

    def test_get_all_states(self):
        """Test getting all states."""
        manager = LifecycleManager()
        
        manager.discover("module1", object())
        manager.discover("module2", object())
        
        states = manager.get_all_states()
        
        assert "module1" in states
        assert "module2" in states

    def test_get_modules_in_state(self):
        """Test getting modules in specific state."""
        manager = LifecycleManager()
        
        manager.discover("module1", object())
        manager.discover("module2", object())
        manager.register("module1")
        
        discovered = manager.get_modules_in_state(ModuleState.DISCOVERED)
        registered = manager.get_modules_in_state(ModuleState.REGISTERED)
        
        assert "module2" in discovered
        assert "module1" in registered

    def test_get_instance(self):
        """Test getting module instance."""
        instance = object()
        manager = LifecycleManager()
        
        manager.discover("test_module", instance)
        
        assert manager.get_instance("test_module") is instance


class TestLifecycleStress:
    """Test lifecycle under stress."""

    def test_many_modules(self):
        """Test with many modules."""
        manager = LifecycleManager()
        
        # Create 100 modules
        for i in range(100):
            manager.discover(f"module_{i}", object())
        
        # Register all
        for i in range(100):
            manager.register(f"module_{i}")
        
        # Initialize all
        for i in range(100):
            manager.initialize(f"module_{i}")
        
        # Verify all in correct state
        for i in range(100):
            assert manager.get_state(f"module_{i}") == ModuleState.INITIALIZED

    def test_rapid_transitions(self):
        """Test rapid state transitions."""
        manager = LifecycleManager()
        
        manager.discover("test_module", object())
        
        # Rapid register/unregister
        for _ in range(100):
            manager.register("test_module")
            assert manager.get_state("test_module") == ModuleState.REGISTERED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
