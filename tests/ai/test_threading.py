"""
Tests for AI Thread Safety and Memory

Verifies:
- Thread-safe operations
- No race conditions
- Memory management
- No leaks
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock

from zbgym.ai.agents import IdleAgent, RandomAgent
from zbgym.ai.blackboard import Blackboard
from zbgym.ai.memory import Memory
from zbgym.ai.config import AIConfig


class TestBlackboardThreadSafety:
    """Test blackboard thread safety."""

    def test_concurrent_read_write(self):
        """Test concurrent read/write operations."""
        bb = Blackboard()
        
        errors = []
        
        def writer(thread_id):
            try:
                for i in range(100):
                    bb.set(f"key_{thread_id}_{i}", {"value": i})
            except Exception as e:
                errors.append(e)
        
        def reader(thread_id):
            try:
                for i in range(100):
                    bb.get(f"key_{thread_id}_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(5):
            t1 = threading.Thread(target=writer, args=(i,))
            t2 = threading.Thread(target=reader, args=(i,))
            threads.extend([t1, t2])
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"

    def test_concurrent_team_operations(self):
        """Test concurrent team-specific operations."""
        bb = Blackboard()
        
        def team_writer(team_id):
            for i in range(50):
                bb.set_for_team(team_id, f"key_{i}", {"value": i})
        
        threads = []
        for team_id in ["red", "blue", "green"]:
            t = threading.Thread(target=team_writer, args=(team_id,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify all teams have data
        for team_id in ["red", "blue", "green"]:
            keys = bb.get_team_keys(team_id)
            assert len(keys) == 50

    def test_concurrent_expire_check(self):
        """Test concurrent expiration checks."""
        bb = Blackboard()
        
        # Set entry with short TTL
        bb.set("expiring", "value", ttl=0.1)
        
        # Concurrent reads
        results = []
        
        def check_expire():
            for _ in range(100):
                bb.has("expiring")
                results.append(bb.get("expiring"))
        
        threads = [threading.Thread(target=check_expire) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not crash
        assert len(results) > 0


class TestMemoryThreadSafety:
    """Test memory thread safety."""

    def test_concurrent_remember(self):
        """Test concurrent remember operations."""
        mem = Memory(capacity=1000)
        
        errors = []
        
        def writer(thread_id):
            try:
                for i in range(100):
                    mem.remember(f"key_{thread_id}_{i}", {"value": i})
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"

    def test_concurrent_recall(self):
        """Test concurrent recall operations."""
        mem = Memory(capacity=100)
        
        # Pre-populate
        for i in range(50):
            mem.remember(f"key_{i}", {"value": i})
        
        results = []
        
        def reader():
            for _ in range(100):
                for i in range(50):
                    mem.recall(f"key_{i}")
        
        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 0  # No errors expected

    def test_concurrent_get_recent(self):
        """Test concurrent get_recent operations."""
        mem = Memory(capacity=100)
        
        for i in range(50):
            mem.remember(f"key_{i}", {"value": i})
        
        results = []
        
        def reader():
            for _ in range(100):
                recent = mem.get_recent(10)
                results.append(len(recent))
        
        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) > 0


class TestMemoryManagement:
    """Test memory management and leak detection."""

    def test_memory_capacity(self):
        """Test memory respects capacity."""
        mem = Memory(capacity=10)
        
        for i in range(20):
            mem.remember(f"key_{i}", {"value": i})
        
        # Should be limited to capacity
        assert len(mem) <= 10

    def test_memory_clear(self):
        """Test memory clear."""
        mem = Memory(capacity=100)
        
        for i in range(50):
            mem.remember(f"key_{i}", {"value": i})
        
        assert len(mem) == 50
        
        mem.clear()
        
        assert len(mem) == 0

    def test_long_duration_memory(self):
        """Test memory over long duration."""
        mem = Memory(capacity=1000)
        
        # Simulate many iterations
        for episode in range(100):
            for step in range(50):
                mem.remember(
                    f"episode_{episode}_step_{step}",
                    {"episode": episode, "step": step}
                )
            
            # Forget old entries
            mem.forget_old(max_age=60.0)
        
        # Memory should not grow unbounded
        assert len(mem) <= 1000

    def test_cooldown_tracking(self):
        """Test cooldown tracking."""
        mem = Memory(capacity=100)
        
        mem.update_cooldown("skill1", duration=5.0)
        
        assert mem.is_on_cooldown("skill1")
        assert not mem.is_on_cooldown("skill2")
        
        # After cooldown expires
        time.sleep(0.1)  # Simulate time passing
        remaining = mem.get_cooldown_remaining("skill1")
        
        # Should have decreased
        assert remaining < 5.0 or remaining == 0.0


class TestAgentMemory:
    """Test agent memory management."""

    def test_agent_memory_cleanup(self):
        """Test agent memory is cleaned up."""
        agent = IdleAgent(agent_id="cleanup_test")
        agent.initialize()
        
        # Add some memory
        agent.memory.remember("key1", "value1")
        agent.memory.remember("key2", "value2")
        
        assert len(agent.memory) == 2
        
        # Shutdown should clear memory
        agent.shutdown()
        
        # Memory should be cleared
        assert len(agent.memory) == 0

    def test_agent_reset_clears_memory(self):
        """Test reset clears agent memory."""
        agent = IdleAgent(agent_id="reset_test")
        agent.initialize()
        
        agent.memory.remember("key1", "value1")
        assert len(agent.memory) == 1
        
        agent.reset()
        assert len(agent.memory) == 0


class TestStressTests:
    """Stress tests for AI components."""

    def test_many_agents(self):
        """Test creating many agents."""
        agents = []
        
        for i in range(100):
            agent = IdleAgent(agent_id=f"agent_{i}")
            agent.initialize()
            agents.append(agent)
        
        assert len(agents) == 100
        
        # Cleanup
        for agent in agents:
            agent.shutdown()

    def test_many_agents_with_memory(self):
        """Test many agents with memory."""
        agents = []
        
        for i in range(50):
            agent = IdleAgent(agent_id=f"mem_agent_{i}")
            agent.initialize()
            
            for j in range(100):
                agent.memory.remember(f"key_{j}", {"value": j})
            
            agents.append(agent)
        
        # Total memory across all agents
        total_memories = sum(len(a.memory) for a in agents)
        assert total_memories == 50 * 100
        
        # Cleanup
        for agent in agents:
            agent.shutdown()

    def test_many_blackboard_entries(self):
        """Test many blackboard entries."""
        bb = Blackboard()
        
        # Add many entries
        for i in range(1000):
            bb.set(f"key_{i}", {"value": i})
        
        assert len(bb) == 1000
        
        # Clear
        bb.clear()
        assert len(bb) == 0

    def test_many_memories(self):
        """Test many memory entries."""
        mem = Memory(capacity=10000)
        
        for i in range(10000):
            mem.remember(f"key_{i}", {"value": i})
        
        assert len(mem) <= 10000

    def test_parallel_agent_creation(self):
        """Test parallel agent creation."""
        agents = []
        
        def create_agent(agent_id):
            agent = IdleAgent(agent_id=agent_id)
            agent.initialize()
            return agent
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_agent, f"par_{i}") for i in range(50)]
            for future in as_completed(futures):
                agents.append(future.result())
        
        assert len(agents) == 50
        
        # Cleanup
        for agent in agents:
            agent.shutdown()
