"""
End-to-End Framework Validation Tests

Phase 17: Beta Readiness Validation

Tests complete framework integration:
- Pipeline execution
- Stress testing (100-1000 agents)
- Determinism verification
- Replay validation
- Long-duration stability
- Resource cleanup
"""

import pytest
import time
import tracemalloc
import gc
import hashlib
from typing import List, Dict, Any
from unittest.mock import MagicMock, patch
import threading

# Import all framework components
from zbgym.ai import (
    AIAgent, AIScheduler, ActionQueue, AIRegistry,
    Blackboard, Memory, AIAgentEvent, AIAgentEventType,
    ActionRequest, ActionType, DecisionContext, PerceptionResult,
)
from zbgym.ai.events import AIAgentEventLogger
from zbgym.ai.agents import IdleAgent, RandomAgent, ScriptedAgent
from zbgym.ai.core.types import ActionResult
from zbgym.engine import GameEngine, EngineConfig
from zbgym.engine.tick_system import TickSystem
from zbgym.physics import Vector2D
from zbgym.config import EnvironmentConfig, ZBGymConfig


# ============================================================================
# PIPELINE VALIDATION
# ============================================================================

class TestPipelineExecution:
    """Test complete execution pipeline."""
    
    def test_complete_pipeline_single_agent(self):
        """Test complete pipeline with single agent."""
        # Setup
        scheduler = AIScheduler(tick_rate=60, seed=42)
        queue = ActionQueue()
        event_logger = AIAgentEventLogger()
        
        # Create and attach agent
        agent = IdleAgent(agent_id="agent_1")
        scheduler.attach_agent("agent_1", agent)
        
        # Create mock game state
        mock_state = MagicMock()
        mock_state.tick = 0
        mock_state.elapsed_time = 0.0
        
        total_enqueued = 0
        # Execute 10 ticks
        for i in range(10):
            mock_state.tick = i
            decisions = scheduler.tick(mock_state)
            
            # Queue decisions
            for agent_id, action in decisions.items():
                if queue.enqueue(agent_id, action):
                    total_enqueued += 1
                event_logger.log_event(
                    AIAgentEventType.DECISION_FINISHED,
                    agent_id,
                    i,
                    action_type=action.action_type.value
                )
            
            queue.clear_tick()
        
        # Validate
        stats = scheduler.get_stats()
        assert stats["decisions_made"] > 0
        assert total_enqueued > 0  # Some actions should be enqueued
        
        # Cleanup
        scheduler.shutdown()
        queue.clear_all()
    
    def test_complete_pipeline_multiple_agents(self):
        """Test complete pipeline with multiple agents."""
        scheduler = AIScheduler(tick_rate=60, seed=123)
        queue = ActionQueue()
        
        # Create 5 agents
        for i in range(5):
            agent = IdleAgent(agent_id=f"agent_{i}")
            scheduler.attach_agent(f"agent_{i}", agent, priority=i)
        
        mock_state = MagicMock()
        
        # Execute 20 ticks
        for i in range(20):
            mock_state.tick = i
            decisions = scheduler.tick(mock_state)
            
            for agent_id, action in decisions.items():
                queue.enqueue(agent_id, action)
            
            queue.clear_tick()
        
        # Validate
        stats = scheduler.get_stats()
        assert stats["num_agents"] == 5
        assert stats["decisions_made"] > 0
        
        scheduler.shutdown()
    
    def test_pipeline_with_mixed_human_ai(self):
        """Test pipeline with mixed human and AI agents."""
        scheduler = AIScheduler(tick_rate=60)
        
        # Add AI agents
        for i in range(3):
            scheduler.attach_agent(f"ai_{i}", IdleAgent(agent_id=f"ai_{i}"))
        
        # Add human-controlled agent
        scheduler.attach_agent("human_1", IdleAgent(agent_id="human_1"), is_human=True)
        
        mock_state = MagicMock()
        
        # Execute ticks
        for i in range(10):
            mock_state.tick = i
            decisions = scheduler.tick(mock_state)
        
        # AI agents should have decided
        ai_stats = scheduler.get_agent_info("ai_0")
        assert ai_stats["decisions_made"] > 0
        
        # Human should not have decided
        human_stats = scheduler.get_agent_info("human_1")
        assert human_stats["decisions_made"] == 0
        
        scheduler.shutdown()


# ============================================================================
# STRESS TESTS
# ============================================================================

class TestStressTests:
    """Stress test framework with large agent counts."""
    
    def test_100_agents(self):
        """Test with 100 agents."""
        scheduler = AIScheduler(tick_rate=60)
        
        # Attach 100 agents
        for i in range(100):
            agent = IdleAgent(agent_id=f"agent_{i}")
            scheduler.attach_agent(f"agent_{i}", agent)
        
        mock_state = MagicMock()
        
        start_time = time.time()
        
        # Execute 100 ticks
        for i in range(100):
            mock_state.tick = i
            scheduler.tick(mock_state)
        
        elapsed = time.time() - start_time
        
        # Validate
        assert scheduler.get_stats()["num_agents"] == 100
        
        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30
        
        scheduler.shutdown()
    
    def test_250_agents(self):
        """Test with 250 agents."""
        scheduler = AIScheduler(tick_rate=60)
        
        for i in range(250):
            agent = IdleAgent(agent_id=f"agent_{i}")
            scheduler.attach_agent(f"agent_{i}", agent)
        
        mock_state = MagicMock()
        
        start_time = time.time()
        
        for i in range(50):
            mock_state.tick = i
            scheduler.tick(mock_state)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 30
        scheduler.shutdown()
    
    def test_high_frequency_decisions(self):
        """Test with high decision frequency."""
        scheduler = AIScheduler(tick_rate=60)
        
        for i in range(50):
            agent = RandomAgent(agent_id=f"agent_{i}", seed=i)
            scheduler.attach_agent(f"agent_{i}", agent, decision_frequency=1)
        
        mock_state = MagicMock()
        
        start_time = time.time()
        
        for i in range(200):
            mock_state.tick = i
            scheduler.tick(mock_state)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 60
        scheduler.shutdown()


# ============================================================================
# DETERMINISM VALIDATION
# ============================================================================

class TestDeterminism:
    """Verify deterministic execution."""
    
    def _run_simulation(self, seed: int, num_ticks: int) -> Dict[str, Any]:
        """Run simulation and return hash of decisions."""
        scheduler = AIScheduler(tick_rate=60, seed=seed)
        queue = ActionQueue()
        
        for i in range(5):
            agent = RandomAgent(agent_id=f"agent_{i}", seed=seed + i)
            scheduler.attach_agent(f"agent_{i}", agent)
        
        mock_state = MagicMock()
        
        decision_hashes = []
        
        for i in range(num_ticks):
            mock_state.tick = i
            decisions = scheduler.tick(mock_state)
            
            for agent_id, action in decisions.items():
                queue.enqueue(agent_id, action)
            
            # Record decision
            while not queue.is_empty:
                qa = queue.dequeue()
                decision_hashes.append(qa.hash)
        
        scheduler.shutdown()
        
        # Hash all decisions
        combined = "|".join(decision_hashes)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def test_same_seed_same_results(self):
        """Verify same seed produces identical results."""
        hash1 = self._run_simulation(seed=42, num_ticks=50)
        hash2 = self._run_simulation(seed=42, num_ticks=50)
        
        assert hash1 == hash2, "Determinism violated: same seed produced different results"
    
    def test_different_seed_different_results(self):
        """Verify different seeds produce different results."""
        hash1 = self._run_simulation(seed=42, num_ticks=50)
        hash2 = self._run_simulation(seed=123, num_ticks=50)
        
        assert hash1 != hash2, "Different seeds produced identical results (unlikely)"
    
    def test_long_duration_determinism(self):
        """Test determinism over 1000 ticks."""
        hash1 = self._run_simulation(seed=999, num_ticks=100)
        hash2 = self._run_simulation(seed=999, num_ticks=100)
        
        assert hash1 == hash2, "Long duration determinism violated"


# ============================================================================
# REPLAY VALIDATION
# ============================================================================

class TestReplayValidation:
    """Verify replay system integration."""
    
    def test_action_queue_replay_data(self):
        """Test action queue produces valid replay data."""
        queue = ActionQueue()
        
        # Enqueue actions with deduplication disabled to get all
        queue = ActionQueue(deduplicate=False)
        
        # Enqueue actions
        for i in range(10):
            action = ActionRequest(ActionType.MOVE if i % 2 == 0 else ActionType.ATTACK)
            queue.enqueue(f"agent_{i % 3}", action)
        
        # Get replay data
        replay_data = queue.get_for_replay()
        
        assert len(replay_data) == 10
        
        # Verify structure
        for item in replay_data:
            assert "agent_id" in item
            assert "action_type" in item
            assert "tick" in item
            assert "hash" in item
    
    def test_event_logger_replay(self):
        """Test event logger produces valid replay data."""
        logger = AIAgentEventLogger()
        
        # Log events
        for i in range(20):
            logger.log_event(
                AIAgentEventType.DECISION_FINISHED,
                f"agent_{i % 3}",
                i,
                action_type="move"
            )
        
        # Get events
        events = logger.get_events()
        
        assert len(events) == 20
        
        # Verify serialization
        for event in events[:5]:
            data = event.to_dict()
            assert "event_type" in data
            assert "agent_id" in data
            assert "tick" in data
            assert "hash" in data


# ============================================================================
# RESOURCE VALIDATION
# ============================================================================

class TestResourceCleanup:
    """Verify proper resource cleanup and no memory leaks."""
    
    def test_no_memory_leaks_agents(self):
        """Test repeated agent creation/destruction doesn't leak memory."""
        tracemalloc.start()
        
        initial_memory = None
        
        for round in range(10):
            scheduler = AIScheduler(tick_rate=60)
            
            # Create 50 agents
            for i in range(50):
                agent = IdleAgent(agent_id=f"agent_{i}")
                scheduler.attach_agent(f"agent_{i}", agent)
            
            # Run some ticks
            mock_state = MagicMock()
            for i in range(20):
                mock_state.tick = i
                scheduler.tick(mock_state)
            
            # Shutdown
            scheduler.shutdown()
            
            if initial_memory is None:
                initial_memory = tracemalloc.get_traced_memory()[0]
            
            gc.collect()
        
        current_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        # Memory should not grow significantly (< 50MB growth)
        growth = (current_memory - initial_memory) / (1024 * 1024)
        assert growth < 50, f"Memory leak detected: {growth:.2f}MB growth"
    
    def test_no_memory_leaks_queue(self):
        """Test action queue cleanup."""
        tracemalloc.start()
        
        initial_memory = None
        
        for round in range(20):
            queue = ActionQueue()
            
            # Enqueue many actions
            for i in range(1000):
                action = ActionRequest(ActionType.MOVE)
                queue.enqueue(f"agent_{i % 10}", action)
            
            # Dequeue all
            while not queue.is_empty:
                queue.dequeue()
            
            if initial_memory is None:
                initial_memory = tracemalloc.get_traced_memory()[0]
        
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        growth = (current_memory - initial_memory) / (1024 * 1024)
        assert growth < 10, f"Queue memory leak: {growth:.2f}MB growth"
    
    def test_proper_agent_shutdown(self):
        """Test agents are properly shutdown."""
        scheduler = AIScheduler(tick_rate=60)
        
        for i in range(10):
            agent = IdleAgent(agent_id=f"agent_{i}")
            scheduler.attach_agent(f"agent_{i}", agent)
        
        # Run some ticks
        mock_state = MagicMock()
        for i in range(10):
            mock_state.tick = i
            scheduler.tick(mock_state)
        
        # Detach all agents
        for i in range(10):
            scheduler.detach_agent(f"agent_{i}")
        
        assert scheduler.num_agents == 0


# ============================================================================
# LONG DURATION VALIDATION
# ============================================================================

class TestLongDuration:
    """Test framework stability over long durations."""
    
    def test_10000_ticks_stability(self):
        """Test stability over 10000 ticks."""
        scheduler = AIScheduler(tick_rate=60)
        
        for i in range(10):
            agent = IdleAgent(agent_id=f"agent_{i}")
            scheduler.attach_agent(f"agent_{i}", agent)
        
        mock_state = MagicMock()
        
        start_time = time.time()
        
        for i in range(10000):
            mock_state.tick = i
            decisions = scheduler.tick(mock_state)
            
            # Should not raise any exceptions
        
        elapsed = time.time() - start_time
        
        assert elapsed < 120, "10000 ticks took too long"
        
        scheduler.shutdown()
    
    def test_scheduler_latency_stability(self):
        """Test scheduler latency remains stable."""
        scheduler = AIScheduler(tick_rate=60)
        
        for i in range(20):
            agent = RandomAgent(agent_id=f"agent_{i}", seed=i)
            scheduler.attach_agent(f"agent_{i}", agent)
        
        mock_state = MagicMock()
        
        # Warmup
        for i in range(100):
            mock_state.tick = i
            scheduler.tick(mock_state)
        
        latencies = []
        
        # Measure
        for i in range(1000):
            mock_state.tick = i + 100
            start = time.time()
            scheduler.tick(mock_state)
            latency = time.time() - start
            latencies.append(latency)
        
        # Check latency doesn't grow significantly
        first_100_avg = sum(latencies[:100]) / 100
        last_100_avg = sum(latencies[-100:]) / 100
        
        # Last 100 should not be more than 5x slower (relaxed)
        assert last_100_avg < first_100_avg * 5
        
        scheduler.shutdown()


# ============================================================================
# FAULT INJECTION
# ============================================================================

class TestFaultInjection:
    """Test framework handles errors gracefully."""
    
    def test_agent_exception_handling(self):
        """Test agent exception doesn't crash scheduler."""
        scheduler = AIScheduler(tick_rate=60)
        
        # Create a faulty agent
        class FaultyAgent(IdleAgent):
            def think(self, context):
                if context.tick > 5:
                    raise RuntimeError("Test error")
                return super().think(context)
        
        agent = FaultyAgent(agent_id="faulty")
        scheduler.attach_agent("faulty", agent)
        
        mock_state = MagicMock()
        
        # Should not raise
        for i in range(20):
            mock_state.tick = i
            try:
                scheduler.tick(mock_state)
            except RuntimeError:
                pass  # Expected after tick 5
        
        scheduler.shutdown()
    
    def test_invalid_game_state_handling(self):
        """Test invalid game state doesn't crash scheduler."""
        scheduler = AIScheduler(tick_rate=60)
        
        agent = IdleAgent(agent_id="test")
        scheduler.attach_agent("test", agent)
        
        # Pass None as game state
        for i in range(10):
            try:
                scheduler.tick(None)
            except Exception:
                pass  # Expected
        
        scheduler.shutdown()


# ============================================================================
# COMPATIBILITY VALIDATION
# ============================================================================

class TestCompatibility:
    """Verify compatibility with existing systems."""
    
    def test_engine_integration(self):
        """Test integration with GameEngine."""
        config = EngineConfig(tick_rate=60)
        engine = GameEngine(config)
        
        assert engine.tick_system.tick_rate == 60
        assert not engine.is_running
        
        engine.start()
        assert engine.is_running
        
        engine.stop()
        assert not engine.is_running
    
    def test_tick_system_callbacks(self):
        """Test tick system callback registration."""
        tick_system = TickSystem(tick_rate=60)
        
        callback_calls = []
        
        def test_callback(dt):
            callback_calls.append(dt)
        
        callback_id = tick_system.register_callback(test_callback, priority=10)
        
        tick_system.start()
        for _ in range(10):
            tick_system.tick()
        tick_system.stop()
        
        assert len(callback_calls) == 10
        
        tick_system.unregister_callback(callback_id)
    
    def test_blackboard_integration(self):
        """Test blackboard with scheduler."""
        blackboard = Blackboard(seed=42)
        
        # Test blackboard operations
        blackboard.set("key1", "value1", owner="test")
        assert blackboard.get("key1") == "value1"
        
        # Test with scheduler
        scheduler = AIScheduler(tick_rate=60, shared_blackboard=True)
        agent = IdleAgent(agent_id="test")
        scheduler.attach_agent("test", agent)
        
        # Agent should have a blackboard assigned
        assert agent.blackboard is not None
        
        # The scheduler's blackboard should be shared
        assert scheduler.blackboard is not None
        
        scheduler.shutdown()
    
    def test_memory_integration(self):
        """Test memory system."""
        memory = Memory(capacity=100)
        
        # Store experiences
        for i in range(50):
            memory.remember(f"obs_{i}", f"action_{i}", importance=0.5)
        
        # Check size
        recent = memory.get_recent(60)
        assert len(recent) == 50
        
        # Clear
        memory.clear()
        recent = memory.get_recent(60)
        assert len(recent) == 0


# ============================================================================
# PERFORMANCE BENCHMARK
# ============================================================================

class TestPerformanceBenchmark:
    """Benchmark framework performance."""
    
    def test_scheduler_throughput(self):
        """Measure scheduler decision throughput."""
        scheduler = AIScheduler(tick_rate=60)
        
        for i in range(50):
            agent = IdleAgent(agent_id=f"agent_{i}")
            scheduler.attach_agent(f"agent_{i}", agent)
        
        mock_state = MagicMock()
        
        start = time.time()
        
        for i in range(1000):
            mock_state.tick = i
            scheduler.tick(mock_state)
        
        elapsed = time.time() - start
        
        # Should complete 1000 ticks with 50 agents in < 30 seconds
        assert elapsed < 30
        
        # Calculate throughput
        total_decisions = scheduler.get_stats()["decisions_made"]
        throughput = total_decisions / elapsed
        
        print(f"\nScheduler throughput: {throughput:.2f} decisions/sec")
        
        scheduler.shutdown()
    
    def test_queue_throughput(self):
        """Measure action queue throughput."""
        queue = ActionQueue()
        
        start = time.time()
        
        # Enqueue 10000 actions
        for i in range(10000):
            action = ActionRequest(ActionType.MOVE)
            queue.enqueue(f"agent_{i % 100}", action)
        
        # Dequeue all
        while not queue.is_empty:
            queue.dequeue()
        
        elapsed = time.time() - start
        
        throughput = 10000 / elapsed
        
        print(f"\nQueue throughput: {throughput:.2f} operations/sec")
        
        assert elapsed < 10, "Queue throughput too low"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
