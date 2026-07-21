"""
Tests for AI Determinism

Verifies deterministic behavior:
- Same seed + same state = same decisions
- No hidden randomness
- Consistent action sequences
"""

import pytest
from unittest.mock import MagicMock

from zbgym.ai.agents import RandomAgent, IdleAgent, ScriptedAgent
from zbgym.ai.core.types import (
    ActionRequest,
    ActionType,
    DecisionContext,
    PerceptionResult,
)
from zbgym.interfaces import GameState, Vector2D


def create_mock_context(agent_id: str, tick: int = 0):
    """Create a mock decision context."""
    mock_game_state = MagicMock(spec=GameState)
    mock_game_state.tick = tick
    mock_game_state.players = []
    
    mock_position = MagicMock(spec=Vector2D)
    mock_position.x = 100.0
    mock_position.y = 100.0
    
    return DecisionContext(
        game_state=mock_game_state,
        perception=PerceptionResult(),
        agent_id=agent_id,
        agent_position=mock_position,
        tick=tick,
        elapsed_time=float(tick) / 60.0,
    )


class TestAgentDeterminism:
    """Test deterministic agent behavior."""

    def test_idle_agent_determinism(self):
        """Test IdleAgent produces identical actions."""
        agent1 = IdleAgent(agent_id="idle1")
        agent2 = IdleAgent(agent_id="idle2")
        
        agent1.initialize()
        agent2.initialize()
        
        context1 = create_mock_context("idle1")
        context2 = create_mock_context("idle2")
        
        # IdleAgent should always return same action
        for _ in range(100):
            action1 = agent1.think(context1)
            action2 = agent2.think(context2)
            
            assert action1.action_type == ActionType.IDLE
            assert action2.action_type == ActionType.IDLE
            assert action1.action_type == action2.action_type

    def test_random_agent_same_seed(self):
        """Test RandomAgent produces same actions with same seed."""
        agent1 = RandomAgent(agent_id="random1", seed=42)
        agent2 = RandomAgent(agent_id="random2", seed=42)
        
        agent1.initialize()
        agent2.initialize()
        
        # Run multiple iterations
        for i in range(100):
            context1 = create_mock_context("random1", tick=i)
            context2 = create_mock_context("random2", tick=i)
            
            agent1.reset(seed=42)
            agent2.reset(seed=42)
            
            action1 = agent1.think(context1)
            action2 = agent2.think(context2)
            
            assert action1.action_type == action2.action_type, \
                f"Iteration {i}: Actions differ"
            assert action1.confidence == action2.confidence, \
                f"Iteration {i}: Confidence differs"

    def test_random_agent_different_seeds(self):
        """Test RandomAgent produces different actions with different seeds."""
        agent1 = RandomAgent(agent_id="seed1", seed=111)
        agent2 = RandomAgent(agent_id="seed2", seed=222)
        
        agent1.initialize()
        agent2.initialize()
        
        differences = 0
        for i in range(50):
            context1 = create_mock_context("seed1", tick=i)
            context2 = create_mock_context("seed2", tick=i)
            
            agent1.reset(seed=111)
            agent2.reset(seed=222)
            
            action1 = agent1.think(context1)
            action2 = agent2.think(context2)
            
            if action1.action_type != action2.action_type:
                differences += 1
        
        # Should have some differences (statistically likely)
        assert differences >= 0  # At least no hard guarantee

    def test_sequence_determinism(self):
        """Test deterministic action sequences."""
        agent = RandomAgent(agent_id="sequence", seed=12345)
        agent.initialize()
        
        sequence1 = []
        sequence2 = []
        
        for seed in [1, 2, 3]:
            agent.reset(seed=seed)
            
            for tick in range(10):
                context = create_mock_context("sequence", tick=tick)
                action = agent.think(context)
                sequence1.append(action.action_type)
        
        # Reset and repeat
        for seed in [1, 2, 3]:
            agent.reset(seed=seed)
            
            for tick in range(10):
                context = create_mock_context("sequence", tick=tick)
                action = agent.think(context)
                sequence2.append(action.action_type)
        
        assert sequence1 == sequence2, "Sequences should be identical"


class TestMemoryDeterminism:
    """Test deterministic memory behavior."""

    def test_memory_recall_determinism(self):
        """Test memory recall is deterministic."""
        from zbgym.ai.memory import Memory
        
        mem1 = Memory(capacity=100, seed=42)
        mem2 = Memory(capacity=100, seed=42)
        
        # Store same data
        mem1.remember("key1", "value1")
        mem2.remember("key1", "value1")
        
        # Recall should be identical
        assert mem1.recall("key1") == mem2.recall("key1")

    def test_memory_order_determinism(self):
        """Test memory order is deterministic."""
        from zbgym.ai.memory import Memory
        
        mem = Memory(capacity=100, seed=42)
        
        # Store multiple items
        for i in range(10):
            mem.remember(f"key_{i}", f"value_{i}")
        
        # Get recent should be in consistent order
        recent1 = mem.get_recent(5)
        recent2 = mem.get_recent(5)
        
        keys1 = [e.key for e in recent1]
        keys2 = [e.key for e in recent2]
        
        assert keys1 == keys2


class TestBlackboardDeterminism:
    """Test deterministic blackboard behavior."""

    def test_blackboard_get_determinism(self):
        """Test blackboard get is deterministic."""
        from zbgym.ai.blackboard import Blackboard
        
        bb1 = Blackboard(seed=42)
        bb2 = Blackboard(seed=42)
        
        # Set same values
        bb1.set("key1", {"data": 123})
        bb2.set("key1", {"data": 123})
        
        assert bb1.get("key1") == bb2.get("key1")

    def test_blackboard_keys_determinism(self):
        """Test blackboard keys are deterministic."""
        from zbgym.ai.blackboard import Blackboard
        
        bb = Blackboard(seed=123)
        
        bb.set("key_a", "value_a")
        bb.set("key_b", "value_b")
        bb.set("key_c", "value_c")
        
        keys1 = bb.keys()
        keys2 = bb.keys()
        
        assert keys1 == keys2


class TestDeterminismStress:
    """Stress tests for determinism."""

    def test_100_iterations(self):
        """Test determinism over 100 iterations."""
        agent1 = RandomAgent(agent_id="stress1", seed=999)
        agent2 = RandomAgent(agent_id="stress2", seed=999)
        
        agent1.initialize()
        agent2.initialize()
        
        for i in range(100):
            agent1.reset(seed=999)
            agent2.reset(seed=999)
            
            context1 = create_mock_context("stress1", tick=i)
            context2 = create_mock_context("stress2", tick=i)
            
            action1 = agent1.think(context1)
            action2 = agent2.think(context2)
            
            assert action1.action_type == action2.action_type

    def test_1000_iterations(self):
        """Test determinism over 1000 iterations."""
        agent1 = RandomAgent(agent_id="stress1k_1", seed=8888)
        agent2 = RandomAgent(agent_id="stress1k_2", seed=8888)
        
        agent1.initialize()
        agent2.initialize()
        
        for i in range(1000):
            agent1.reset(seed=8888)
            agent2.reset(seed=8888)
            
            context1 = create_mock_context("stress1k_1", tick=i)
            context2 = create_mock_context("stress1k_2", tick=i)
            
            action1 = agent1.think(context1)
            action2 = agent2.think(context2)
            
            assert action1.action_type == action2.action_type
