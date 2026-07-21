"""
Tests for AI Action Queue

Verifies:
- Enqueue/dequeue
- Priority ordering
- Deduplication
- Cancellation
- Replay serialization
"""

import pytest
from unittest.mock import MagicMock

from zbgym.ai.action_queue import ActionQueue, QueuedAction
from zbgym.ai.core.types import ActionRequest, ActionType
from zbgym.interfaces import GameState


class TestQueuedAction:
    """Test QueuedAction."""

    def test_queued_action_creation(self):
        """Test creating a queued action."""
        req = ActionRequest(ActionType.MOVE)
        queued = QueuedAction(
            agent_id="test",
            action=req,
            priority=1.0,
            tick=100,
        )
        
        assert queued.agent_id == "test"
        assert queued.action.action_type == ActionType.MOVE
        assert queued.priority == 1.0
        assert queued.tick == 100
        assert not queued.cancelled
        assert queued.hash  # Hash should be generated

    def test_queued_action_hash_deterministic(self):
        """Test hash is deterministic."""
        req = ActionRequest(ActionType.MOVE)
        
        q1 = QueuedAction("test", req, 1.0, 100)
        q2 = QueuedAction("test", req, 1.0, 100)
        
        assert q1.hash == q2.hash

    def test_queued_action_cancel(self):
        """Test cancelling a queued action."""
        req = ActionRequest(ActionType.MOVE)
        queued = QueuedAction("test", req, 1.0, 100)
        
        queued.cancel()
        assert queued.cancelled


class TestActionQueue:
    """Test ActionQueue."""

    def test_queue_creation(self):
        """Test creating an action queue."""
        queue = ActionQueue()
        
        assert queue.is_empty
        assert queue.size == 0
        assert queue.tick == 0

    def test_enqueue(self):
        """Test enqueueing an action."""
        queue = ActionQueue()
        req = ActionRequest(ActionType.MOVE)
        
        result = queue.enqueue("agent_1", req)
        
        assert result is True
        assert not queue.is_empty
        assert queue.size == 1

    def test_dequeue(self):
        """Test dequeuing an action."""
        queue = ActionQueue()
        req = ActionRequest(ActionType.MOVE)
        queue.enqueue("agent_1", req)
        
        queued = queue.dequeue()
        
        assert queued is not None
        assert queued.agent_id == "agent_1"
        assert queue.is_empty

    def test_dequeue_empty(self):
        """Test dequeuing from empty queue."""
        queue = ActionQueue()
        result = queue.dequeue()
        assert result is None

    def test_priority_ordering(self):
        """Test actions are ordered by priority."""
        queue = ActionQueue()
        
        queue.enqueue("low", ActionRequest(ActionType.IDLE), priority=0.2)
        queue.enqueue("high", ActionRequest(ActionType.ATTACK), priority=0.9)
        queue.enqueue("medium", ActionRequest(ActionType.MOVE), priority=0.5)
        
        # Should be: high, medium, low
        assert queue.dequeue().agent_id == "high"
        assert queue.dequeue().agent_id == "medium"
        assert queue.dequeue().agent_id == "low"

    def test_deduplication(self):
        """Test deduplication by agent+type."""
        queue = ActionQueue(deduplicate=True)
        
        req1 = ActionRequest(ActionType.MOVE)
        req2 = ActionRequest(ActionType.MOVE)  # Same type
        
        queue.enqueue("agent_1", req1, priority=0.8)
        result = queue.enqueue("agent_1", req2, priority=0.3)  # Lower priority
        
        assert result is False  # Should be dropped
        assert queue.size == 1
        
        # Higher priority should replace
        result = queue.enqueue("agent_1", req2, priority=0.9)
        assert result is True
        assert queue.size == 1

    def test_deduplication_disabled(self):
        """Test no deduplication when disabled."""
        queue = ActionQueue(deduplicate=False)
        
        req = ActionRequest(ActionType.MOVE)
        
        queue.enqueue("agent_1", req)
        result = queue.enqueue("agent_1", req)
        
        assert result is True
        assert queue.size == 2

    def test_cancel_agent(self):
        """Test cancelling all actions for an agent."""
        queue = ActionQueue()
        
        queue.enqueue("agent_1", ActionRequest(ActionType.MOVE))
        queue.enqueue("agent_1", ActionRequest(ActionType.ATTACK))
        queue.enqueue("agent_2", ActionRequest(ActionType.IDLE))
        
        count = queue.cancel_agent("agent_1")
        
        assert count == 2
        assert queue.size == 1
        assert queue.dequeue().agent_id == "agent_2"

    def test_cancel_action_type(self):
        """Test cancelling all actions of a type."""
        queue = ActionQueue()
        
        queue.enqueue("a1", ActionRequest(ActionType.MOVE))
        queue.enqueue("a2", ActionRequest(ActionType.ATTACK))
        queue.enqueue("a3", ActionRequest(ActionType.MOVE))
        
        count = queue.cancel_action_type(ActionType.MOVE)
        
        assert count == 2
        assert queue.size == 1

    def test_clear_tick(self):
        """Test clearing all actions for tick."""
        queue = ActionQueue()
        
        # Enqueue with tick 0
        queue.enqueue("a1", ActionRequest(ActionType.MOVE), tick=0)
        queue.enqueue("a2", ActionRequest(ActionType.MOVE), tick=0)
        
        # Advance tick to 1, which clears tick 0 actions
        cleared = queue.clear_tick()  # tick becomes 1, clears tick 0
        
        assert cleared == 2
        assert queue.size == 0
        assert queue.tick == 1
        
        # Enqueue with tick 1
        queue.enqueue("a3", ActionRequest(ActionType.MOVE), tick=1)
        
        # Advance to tick 2, which clears tick 1 actions
        cleared = queue.clear_tick()  # tick becomes 2, clears tick 1
        assert cleared == 1

    def test_clear_all(self):
        """Test clearing all actions."""
        queue = ActionQueue()
        
        for i in range(10):
            queue.enqueue(f"agent_{i}", ActionRequest(ActionType.MOVE))
        
        count = queue.clear_all()
        
        assert count == 10
        assert queue.is_empty

    def test_allow_idle(self):
        """Test idle action filtering."""
        queue_allow = ActionQueue(allow_idle=True)
        queue_block = ActionQueue(allow_idle=False)
        
        req = ActionRequest(ActionType.IDLE)
        
        result_allow = queue_allow.enqueue("test", req)
        result_block = queue_block.enqueue("test", req)
        
        assert result_allow is True
        assert result_block is False

    def test_peek(self):
        """Test peeking without removing."""
        queue = ActionQueue()
        
        queue.enqueue("a1", ActionRequest(ActionType.MOVE), priority=0.9)
        queue.enqueue("a2", ActionRequest(ActionType.ATTACK), priority=0.8)
        
        peeked = queue.peek()
        
        # Highest priority should be first
        assert peeked.agent_id == "a1"
        assert peeked.action.action_type == ActionType.MOVE
        assert queue.size == 2  # Not removed

    def test_get_for_replay(self):
        """Test getting actions for replay."""
        queue = ActionQueue()
        
        queue.enqueue("a1", ActionRequest(ActionType.MOVE), priority=0.9, tick=10)
        queue.enqueue("a2", ActionRequest(ActionType.ATTACK), priority=0.8, tick=10)
        
        replay_data = queue.get_for_replay()
        
        assert len(replay_data) == 2
        # First should be highest priority
        assert replay_data[0]["agent_id"] == "a1"
        assert replay_data[0]["tick"] == 10
        assert replay_data[0]["priority"] == 0.9

    def test_get_stats(self):
        """Test queue statistics."""
        queue = ActionQueue()
        
        for i in range(5):
            queue.enqueue(f"a{i}", ActionRequest(ActionType.MOVE))
        
        for _ in range(3):
            queue.dequeue()
        
        stats = queue.get_stats()
        
        assert stats["total_enqueued"] == 5
        assert stats["total_dequeued"] == 3
        assert stats["size"] == 2


class TestQueueDeterminism:
    """Test queue determinism."""

    def test_same_inputs_same_order(self):
        """Test same inputs produce same order."""
        queue1 = ActionQueue()
        queue2 = ActionQueue()
        
        actions = [
            ("agent_1", ActionType.MOVE, 5.0),
            ("agent_2", ActionType.ATTACK, 10.0),
            ("agent_3", ActionType.IDLE, 1.0),
        ]
        
        for agent_id, action_type, priority in actions:
            queue1.enqueue(agent_id, ActionRequest(action_type), priority=priority)
        
        for agent_id, action_type, priority in actions:
            queue2.enqueue(agent_id, ActionRequest(action_type), priority=priority)
        
        order1 = [queue1.dequeue().agent_id for _ in range(3)]
        order2 = [queue2.dequeue().agent_id for _ in range(3)]
        
        assert order1 == order2
