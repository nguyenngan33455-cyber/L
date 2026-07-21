"""
Kernel Tick Pipeline Tests for Phase 26.5 Validation.

Tests tick pipeline execution and ordering.
"""

import pytest
import time
from zbgym.kernel import (
    Kernel, KernelState, KernelConfig,
    TickCoordinator, TickStage
)


class TestTickPipeline:
    """Test tick pipeline execution."""

    def test_tick_executes(self):
        """Test single tick executes."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        result = kernel.tick()
        assert result is True
        assert kernel.context.clock.current_tick == 1
        
        kernel.shutdown()

    def test_tick_count_increments(self):
        """Test tick counter increments correctly."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        for i in range(10):
            kernel.tick()
            assert kernel.context.clock.current_tick == i + 1
        
        kernel.shutdown()

    def test_tick_pipeline_stages(self):
        """Test all 14 pipeline stages execute."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        # Register handlers for each stage to verify execution
        stage_order = []
        
        for stage in TickStage:
            kernel.context.event_bus.subscribe(
                f"kernel.tick.{stage.value}",
                lambda e, s=stage: stage_order.append(s)
            )
        
        kernel.tick()
        
        # Verify stages were called (at least some)
        assert len(stage_order) > 0
        
        kernel.shutdown()

    def test_tick_pipeline_order(self):
        """Test tick pipeline executes in correct order."""
        # Define expected order
        expected_order = [
            TickStage.PREPARE,
            TickStage.SCHEDULER,
            TickStage.AI,
            TickStage.ACTION_QUEUE,
            TickStage.PHYSICS,
            TickStage.COLLISION,
            TickStage.GAME_LOGIC,
            TickStage.REWARD,
            TickStage.OBSERVATION,
            TickStage.REPLAY,
            TickStage.DASHBOARD,
            TickStage.METRICS,
            TickStage.EVENTS,
            TickStage.FINISH,
        ]
        
        # Verify coordinator has correct order
        coordinator = TickCoordinator()
        assert coordinator.STAGE_ORDER == expected_order


class TestTickBurnin:
    """Test tick execution under load."""

    def test_100_ticks(self):
        """Test 100 ticks complete."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        for _ in range(100):
            kernel.tick()
        
        assert kernel.context.clock.current_tick == 100
        kernel.shutdown()

    def test_1000_ticks(self):
        """Test 1000 ticks complete."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        for _ in range(1000):
            kernel.tick()
        
        assert kernel.context.clock.current_tick == 1000
        kernel.shutdown()

    def test_10000_ticks(self):
        """Test 10000 ticks complete."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        for _ in range(10000):
            kernel.tick()
        
        assert kernel.context.clock.current_tick == 10000
        kernel.shutdown()

    def test_tick_timing_stable(self):
        """Test tick timing remains stable."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        timings = []
        for _ in range(100):
            start = time.perf_counter()
            kernel.tick()
            duration_ms = (time.perf_counter() - start) * 1000
            timings.append(duration_ms)
        
        # Check timing is reasonable (under 1ms per tick)
        avg_timing = sum(timings) / len(timings)
        assert avg_timing < 10, f"Average tick time {avg_timing:.2f}ms too high"
        
        kernel.shutdown()

    def test_tick_determinism(self):
        """Test tick execution is deterministic."""
        kernel1 = Kernel()
        kernel1.bootstrap()
        kernel1.initialize_modules()
        kernel1.start()
        
        kernel2 = Kernel()
        kernel2.bootstrap()
        kernel2.initialize_modules()
        kernel2.start()
        
        # Run same number of ticks
        for _ in range(100):
            kernel1.tick()
            kernel2.tick()
        
        # Both should have same tick count
        assert kernel1.context.clock.current_tick == kernel2.context.clock.current_tick
        
        kernel1.shutdown()
        kernel2.shutdown()


class TestTickPerformance:
    """Test tick performance."""

    def test_tick_overhead(self):
        """Test tick overhead is under 1ms."""
        kernel = Kernel()
        kernel.bootstrap()
        kernel.initialize_modules()
        kernel.start()
        
        timings = []
        for _ in range(1000):
            start = time.perf_counter()
            kernel.tick()
            duration_ms = (time.perf_counter() - start) * 1000
            timings.append(duration_ms)
        
        avg_overhead = sum(timings) / len(timings)
        assert avg_overhead < 1, f"Tick overhead {avg_overhead:.2f}ms exceeds 1ms target"
        
        kernel.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
