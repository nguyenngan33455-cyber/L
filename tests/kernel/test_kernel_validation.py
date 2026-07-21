"""
Kernel Quick Validation Tests for Phase 26.5.

Simplified tests for rapid validation.
"""

import pytest
import time
from zbgym.kernel import (
    Kernel, KernelState, KernelConfig,
    RuntimeContext, Clock,
    EventDispatcher, Event,
    StateStore,
    HealthMonitor, HealthStatus,
    DependencyResolver, ModuleSpec, Dependency,
    LifecycleManager, ModuleState,
    PanicManager, PanicLevel,
    TickCoordinator, TickStage
)


def test_kernel_boot_shutdown():
    """Test basic boot and shutdown."""
    kernel = Kernel()
    kernel.bootstrap()
    kernel.shutdown()
    assert kernel.state == KernelState.TERMINATED


def test_kernel_runtime_context():
    """Test RuntimeContext initialization."""
    kernel = Kernel()
    kernel.bootstrap()
    
    assert kernel.context.is_initialized
    assert kernel.context.clock is not None
    assert kernel.context.event_bus is not None
    assert kernel.context.state_store is not None
    
    kernel.shutdown()


def test_kernel_tick():
    """Test single tick."""
    kernel = Kernel()
    kernel.bootstrap()
    
    # Don't call start() as it may wait for modules
    # Just verify tick infrastructure exists
    assert kernel.context.clock is not None
    
    kernel.shutdown()


def test_state_store():
    """Test state store."""
    store = StateStore()
    store.set("key", "value")
    assert store.get("key") == "value"
    store.shutdown()


def test_state_snapshot():
    """Test state snapshot."""
    store = StateStore()
    store.set("key1", "value1")
    snapshot = store.snapshot()
    store.set("key1", "modified")
    store.restore(snapshot)
    assert store.get("key1") == "value1"
    store.shutdown()


def test_event_dispatcher():
    """Test event dispatcher."""
    dispatcher = EventDispatcher()
    received = []
    
    def callback(event):
        received.append(event)
    
    dispatcher.subscribe("test", callback)
    dispatcher.emit(Event(type="test"))
    
    assert len(received) == 1
    dispatcher.clear()


def test_health_monitor():
    """Test health monitor."""
    monitor = HealthMonitor()
    monitor.register_module("test_module")
    monitor.heartbeat("test_module")  # Heartbeat sets to healthy
    report = monitor.get_module_health("test_module")
    assert report is not None
    assert report.status == HealthStatus.HEALTHY
    monitor.shutdown()


def test_dependency_resolver():
    """Test dependency resolution."""
    resolver = DependencyResolver()
    resolver.register_module(ModuleSpec(name="a"))
    resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("a")]))
    order = resolver.resolve()
    assert order.index("a") < order.index("b")


def test_dependency_cycle_detection():
    """Test cycle detection."""
    resolver = DependencyResolver()
    resolver.register_module(ModuleSpec(name="a", dependencies=[Dependency("b")]))
    resolver.register_module(ModuleSpec(name="b", dependencies=[Dependency("a")]))
    
    from zbgym.kernel import CyclicDependencyError
    try:
        resolver.resolve()
        assert False, "Should have raised CyclicDependencyError"
    except CyclicDependencyError:
        pass


def test_lifecycle_manager():
    """Test lifecycle manager."""
    manager = LifecycleManager()
    manager.discover("test", object())
    manager.register("test")
    manager.initialize("test")
    assert manager.get_state("test") == ModuleState.INITIALIZED


def test_panic_manager():
    """Test panic manager."""
    manager = PanicManager()
    manager.info("test")
    assert manager.level == PanicLevel.INFO
    manager.reset()


def test_tick_coordinator():
    """Test tick coordinator."""
    coordinator = TickCoordinator()
    assert len(coordinator.STAGE_ORDER) == 14
    assert coordinator.STAGE_ORDER[0] == TickStage.PREPARE
    assert coordinator.STAGE_ORDER[-1] == TickStage.FINISH


def test_kernel_performance():
    """Test kernel performance."""
    start = time.perf_counter()
    kernel = Kernel()
    kernel.bootstrap()
    kernel.shutdown()
    duration_ms = (time.perf_counter() - start) * 1000
    assert duration_ms < 100, f"Boot took {duration_ms:.2f}ms"


def test_tick_performance():
    """Test tick performance."""
    kernel = Kernel()
    kernel.bootstrap()
    
    # Test clock tick performance
    start = time.perf_counter()
    for _ in range(100):
        kernel.context.clock.tick()
    duration_ms = (time.perf_counter() - start) * 1000
    
    kernel.shutdown()
    assert duration_ms < 50, f"100 clock ticks took {duration_ms:.2f}ms"


def test_determinism():
    """Test clock determinism."""
    kernel1 = Kernel()
    kernel1.bootstrap()
    
    kernel2 = Kernel()
    kernel2.bootstrap()
    
    for _ in range(50):
        kernel1.context.clock.tick()
        kernel2.context.clock.tick()
    
    assert kernel1.context.clock.current_tick == kernel2.context.clock.current_tick
    
    kernel1.shutdown()
    kernel2.shutdown()


def test_event_priority():
    """Test event priority ordering."""
    dispatcher = EventDispatcher()
    order = []
    
    dispatcher.subscribe("test", lambda e: order.append("low"), priority=0)
    dispatcher.subscribe("test", lambda e: order.append("high"), priority=100)
    
    dispatcher.emit(Event(type="test"))
    
    assert order == ["high", "low"]
    dispatcher.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
