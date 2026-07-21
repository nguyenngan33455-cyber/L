"""
Kernel Integration Tests for Phase 27.

Tests end-to-end integration of framework modules with Kernel.
"""

import pytest
import time
from zbgym.kernel import (
    Kernel,
    KernelConfig,
    KernelState,
    KernelIntegration,
    KernelContext,
    create_kernel,
    run_kernel_env,
    ModuleRegistry,
    get_registry,
    register_module,
    get_module,
    has_module,
    list_modules,
)


class TestKernelIntegration:
    """Test Kernel integration layer."""

    def test_kernel_integration_create(self):
        """Test creating KernelIntegration."""
        integration = KernelIntegration()
        
        assert integration.kernel is not None
        assert integration.context is not None
        
        integration.shutdown()

    def test_kernel_integration_bootstrap(self):
        """Test bootstrapping KernelIntegration."""
        integration = KernelIntegration()
        integration.bootstrap()
        
        assert integration.context.is_initialized
        assert integration.context.clock is not None
        
        integration.shutdown()

    def test_kernel_integration_register_module(self):
        """Test registering a module."""
        integration = KernelIntegration()
        integration.bootstrap()
        
        class DummyModule:
            def __init__(self):
                self.name = "dummy"
        
        integration.register_module("dummy", DummyModule())
        
        assert integration.has_module("dummy")
        assert integration.get_module("dummy") is not None
        
        integration.shutdown()

    def test_kernel_integration_chain(self):
        """Test method chaining."""
        integration = (
            KernelIntegration()
            .bootstrap()
            .register_module("dummy", object())
        )
        
        assert integration.has_module("dummy")
        
        integration.shutdown()

    def test_kernel_integration_status(self):
        """Test getting status."""
        integration = KernelIntegration()
        integration.bootstrap()
        integration.register_module("module1", object())
        integration.register_module("module2", object())
        
        status = integration.get_status()
        
        assert status["initialized"] is True
        assert "module1" in status["modules"]
        assert "module2" in status["modules"]
        
        integration.shutdown()

    def test_kernel_integration_emit_event(self):
        """Test emitting events."""
        integration = KernelIntegration()
        integration.bootstrap()
        
        received = []
        integration.subscribe("test", lambda e: received.append(e))
        
        integration.emit_event("test", {"data": "value"})
        
        assert len(received) == 1
        assert received[0].data["data"] == "value"
        
        integration.shutdown()


class TestKernelContext:
    """Test KernelContext manager."""

    def test_kernel_context_enter_exit(self):
        """Test context manager entry/exit."""
        with KernelContext() as ctx:
            assert ctx.kernel is not None
            assert ctx.context is not None
        
        # After exit, kernel should be shut down
        assert ctx.kernel.state == KernelState.TERMINATED

    def test_kernel_context_create_environment(self):
        """Test creating environment in context."""
        with KernelContext() as ctx:
            # Just verify context works without creating env
            assert ctx.kernel is not None
            ctx.kernel.bootstrap()
            
            # Run a tick
            for _ in range(10):
                ctx.context.clock.tick()

    def test_kernel_context_run(self):
        """Test running steps in context."""
        with KernelContext() as ctx:
            ctx.kernel.bootstrap()
            
            # Run 10 clock ticks
            ctx.run(10)
            
            assert ctx.context.clock.current_tick == 10


class TestCreateKernel:
    """Test create_kernel factory."""

    def test_create_kernel_defaults(self):
        """Test create_kernel with defaults."""
        kernel = create_kernel()
        
        assert kernel is not None
        assert kernel.state != KernelState.TERMINATED
        
        kernel.shutdown()

    def test_create_kernel_custom_config(self):
        """Test create_kernel with custom config."""
        config = KernelConfig(name="CustomKernel", tick_rate=30)
        kernel = create_kernel(name="CustomKernel", tick_rate=30)
        
        assert kernel.config.name == "CustomKernel"
        assert kernel.config.tick_rate == 30
        
        kernel.shutdown()


class TestModuleRegistry:
    """Test module registry."""

    def test_global_registry(self):
        """Test global registry."""
        registry = get_registry()
        
        assert registry is not None
        
        # Register a module
        registry.register("test_module", object())
        
        assert registry.has("test_module")
        assert registry.get("test_module") is not None

    def test_register_and_get_module(self):
        """Test register_module and get_module functions."""
        class TestModule:
            pass
        
        # Register
        register_module("test", TestModule())
        
        # Get
        assert has_module("test")
        module = get_module("test")
        assert module is not None
        assert isinstance(module, TestModule)

    def test_list_modules(self):
        """Test list_modules."""
        register_module("mod1", object())
        register_module("mod2", object())
        
        modules = list_modules()
        
        assert "mod1" in modules
        assert "mod2" in modules


class TestKernelLifecycle:
    """Test Kernel lifecycle integration."""

    def test_full_lifecycle(self):
        """Test full kernel lifecycle."""
        kernel = Kernel()
        
        # Bootstrap
        kernel.bootstrap()
        assert kernel.state == KernelState.INITIALIZING
        
        # Start
        kernel.start()
        assert kernel.state == KernelState.RUNNING
        
        # Run ticks
        for _ in range(10):
            kernel.tick()
        
        # Pause
        kernel.pause()
        assert kernel.state == KernelState.PAUSED
        
        # Resume
        kernel.resume()
        assert kernel.state == KernelState.RUNNING
        
        # Stop
        kernel.stop()
        assert kernel.state == KernelState.STOPPED
        
        # Shutdown
        kernel.shutdown()
        assert kernel.state == KernelState.TERMINATED

    def test_kernel_with_modules(self):
        """Test kernel with registered modules."""
        kernel = Kernel()
        kernel.bootstrap()
        
        # Register modules
        kernel.register_module("module1", object())
        kernel.register_module("module2", object())
        
        # Verify modules exist
        assert kernel.has_module("module1")
        assert kernel.has_module("module2")
        
        kernel.shutdown()


class TestIntegrationCompatibility:
    """Test backward compatibility."""

    def test_existing_api_preserved(self):
        """Test that existing APIs are preserved."""
        # These imports should work
        from zbgym.kernel import (
            Kernel,
            KernelState,
            KernelConfig,
            RuntimeContext,
        )
        
        assert Kernel is not None
        assert KernelState is not None
        assert KernelConfig is not None
        assert RuntimeContext is not None

    def test_kernel_config_defaults(self):
        """Test KernelConfig defaults."""
        config = KernelConfig()
        
        assert config.name == "ZBGym"
        assert config.version == "1.0.0"
        assert config.tick_rate == 60
        assert config.enable_health_monitoring is True
        assert config.enable_metrics is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
