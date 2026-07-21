"""
Kernel Boot and Shutdown Tests for Phase 26.5 Validation.

Tests kernel bootstrap, initialization, and shutdown scenarios.
"""

import pytest
import sys
import time
from zbgym.kernel import (
    Kernel, KernelState, KernelConfig,
    RuntimeContext, Clock
)


class TestKernelBoot:
    """Test kernel boot scenarios."""

    def test_boot_once(self):
        """Test single boot cycle."""
        kernel = Kernel()
        kernel.bootstrap()
        assert kernel.state == KernelState.INITIALIZING
        kernel.shutdown()
        assert kernel.state == KernelState.TERMINATED

    def test_boot_multiple_times(self):
        """Test multiple boot cycles."""
        for i in range(10):
            kernel = Kernel()
            kernel.bootstrap()
            assert kernel.state == KernelState.INITIALIZING
            kernel.shutdown()
            assert kernel.state == KernelState.TERMINATED

    def test_boot_with_config(self):
        """Test boot with custom config."""
        config = KernelConfig(name="TestKernel", tick_rate=30)
        kernel = Kernel(config)
        assert kernel.config.name == "TestKernel"
        assert kernel.config.tick_rate == 30
        kernel.bootstrap()
        kernel.shutdown()

    def test_runtime_context_initialized(self):
        """Test RuntimeContext is initialized on boot."""
        kernel = Kernel()
        kernel.bootstrap()
        
        assert kernel.context.is_initialized
        assert kernel.context.clock is not None
        assert kernel.context.event_bus is not None
        assert kernel.context.state_store is not None
        assert kernel.context.health_monitor is not None
        assert kernel.context.metrics is not None
        
        kernel.shutdown()


class TestKernelShutdown:
    """Test kernel shutdown scenarios."""

    def test_shutdown_from_initializing(self):
        """Test shutdown from INITIALIZING state."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.shutdown()
        assert kernel.state == KernelState.TERMINATED

    def test_shutdown_idempotent(self):
        """Test multiple shutdowns don't crash."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.shutdown()
        kernel.shutdown()  # Should not crash
        assert kernel.state == KernelState.TERMINATED

    def test_shutdown_from_ready(self):
        """Test shutdown from READY state."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.shutdown()
        assert kernel.state == KernelState.TERMINATED


class TestKernelRestart:
    """Test kernel restart scenarios."""

    def test_start_stop_start(self):
        """Test stop then start sequence."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        assert kernel.state == KernelState.RUNNING
        kernel.stop()
        assert kernel.state == KernelState.STOPPED
        kernel.start()
        assert kernel.state == KernelState.RUNNING
        kernel.shutdown()

    def test_pause_resume(self):
        """Test pause and resume."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        assert kernel.state == KernelState.RUNNING
        kernel.pause()
        assert kernel.state == KernelState.PAUSED
        kernel.resume()
        assert kernel.state == KernelState.RUNNING
        kernel.shutdown()


class TestBootPerformance:
    """Test boot performance."""

    def test_boot_time(self):
        """Test boot completes within 100ms."""
        start = time.perf_counter()
        kernel = Kernel()
        kernel.bootstrap()
        kernel.shutdown()
        duration_ms = (time.perf_counter() - start) * 1000
        assert duration_ms < 100, f"Boot took {duration_ms:.2f}ms"

    def test_shutdown_time(self):
        """Test shutdown completes within 50ms."""
        kernel = Kernel()
        kernel.bootstrap()
        
        start = time.perf_counter()
        kernel.shutdown()
        duration_ms = (time.perf_counter() - start) * 1000
        assert duration_ms < 50, f"Shutdown took {duration_ms:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
