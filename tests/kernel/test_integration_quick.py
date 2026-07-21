"""
Quick Kernel Integration Tests for Phase 27.

Simplified tests for rapid validation.
"""

import pytest
from zbgym.kernel import (
    Kernel,
    KernelState,
    KernelConfig,
    KernelIntegration,
    KernelContext,
    ModuleRegistry,
    get_registry,
    register_module,
    get_module,
    has_module,
)


def test_kernel_create():
    """Test creating kernel."""
    kernel = Kernel()
    kernel.bootstrap()
    assert kernel.state == KernelState.INITIALIZING
    kernel.shutdown()
    assert kernel.state == KernelState.TERMINATED


def test_kernel_config_defaults():
    """Test KernelConfig defaults."""
    config = KernelConfig()
    assert config.name == "ZBGym"
    assert config.tick_rate == 60
    assert config.enable_health_monitoring is True


def test_kernel_integration():
    """Test KernelIntegration."""
    integration = KernelIntegration()
    integration.bootstrap()
    assert integration.context.is_initialized
    integration.shutdown()


def test_kernel_integration_register():
    """Test registering modules."""
    integration = KernelIntegration()
    integration.bootstrap()
    integration.register_module("test", object())
    assert integration.has_module("test")
    integration.shutdown()


def test_module_registry():
    """Test global registry."""
    registry = get_registry()
    registry.register("test_reg", object())
    assert registry.has("test_reg")
    assert registry.get("test_reg") is not None


def test_register_get_module():
    """Test register/get functions."""
    class TestMod:
        pass
    
    register_module("mod_test", TestMod())
    assert has_module("mod_test")
    mod = get_module("mod_test")
    assert isinstance(mod, TestMod)


def test_kernel_context():
    """Test KernelContext."""
    with KernelContext() as ctx:
        assert ctx.kernel is not None
        # Kernel is already bootstrapped in __enter__
        for _ in range(5):
            ctx.context.clock.tick()


def test_kernel_lifecycle():
    """Test kernel lifecycle."""
    kernel = Kernel()
    kernel.bootstrap()
    kernel.initialize_modules()
    # Note: start() requires tick_coordinator which needs a running scheduler
    # For now, test bootstrap and shutdown
    kernel.shutdown()
    assert kernel.state == KernelState.TERMINATED


def test_kernel_modules():
    """Test kernel with modules."""
    kernel = Kernel()
    kernel.bootstrap()
    kernel.register_module("mod1", object())
    kernel.register_module("mod2", object())
    assert kernel.has_module("mod1")
    assert kernel.has_module("mod2")
    kernel.shutdown()


def test_runtime_context_services():
    """Test RuntimeContext services."""
    kernel = Kernel()
    kernel.bootstrap()
    
    assert kernel.context.clock is not None
    assert kernel.context.event_bus is not None
    assert kernel.context.state_store is not None
    assert kernel.context.health_monitor is not None
    assert kernel.context.metrics is not None
    
    kernel.shutdown()


def test_event_emission():
    """Test event emission."""
    kernel = Kernel()
    kernel.bootstrap()
    
    received = []
    kernel.context.event_bus.subscribe("test", lambda e: received.append(e))
    kernel.context.event_bus.emit(kernel.context.event_bus.__class__.__name__, type="test")
    
    kernel.shutdown()


def test_state_store():
    """Test state store."""
    kernel = Kernel()
    kernel.bootstrap()
    
    kernel.context.state_store.set("key", "value")
    assert kernel.context.state_store.get("key") == "value"
    
    kernel.shutdown()


def test_health_monitor():
    """Test health monitor."""
    kernel = Kernel()
    kernel.bootstrap()
    
    kernel.context.health_monitor.register_module("test")
    kernel.context.health_monitor.heartbeat("test")
    report = kernel.context.health_monitor.get_module_health("test")
    assert report is not None
    
    kernel.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
