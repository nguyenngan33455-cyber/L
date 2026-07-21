"""
Tests for AI Agent Lifecycle

Verifies the complete lifecycle of AIAgent implementations:
initialize() → reset() → observe() → think() → act() → update() → shutdown()

Test coverage:
- Lifecycle transitions
- Repeated initialization
- Repeated shutdown
- Reset behavior
- State management
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Any

from zbgym.ai.agents import RandomAgent, IdleAgent, ScriptedAgent
from zbgym.ai.core.agent import AIAgent
from zbgym.ai.core.types import (
    ActionRequest,
    ActionResult,
    ActionType,
    DecisionContext,
    PerceptionResult,
)
from zbgym.ai.exceptions.agent_error import AgentError
from zbgym.interfaces import GameState, Player, Team, Vector2D


class TestAIAgentLifecycle:
    """Test cases for AIAgent lifecycle."""

    def test_agent_creation(self):
        """Test agent can be created with ID."""
        agent = IdleAgent(agent_id="test_agent")
        assert agent.agent_id == "test_agent"
        assert not agent.is_initialized

    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = IdleAgent(agent_id="test_init")
        assert not agent.is_initialized
        
        agent.initialize()
        assert agent.is_initialized
        
        # Double init should be safe
        agent.initialize()
        assert agent.is_initialized

    def test_agent_reset(self):
        """Test agent reset."""
        agent = RandomAgent(agent_id="test_reset", seed=42)
        agent.initialize()
        
        # Reset with seed
        agent.reset(seed=123)
        assert agent.seed == 123
        
        # Reset without seed (should keep existing)
        agent.reset()
        assert agent.seed == 123

    def test_agent_shutdown(self):
        """Test agent shutdown."""
        agent = IdleAgent(agent_id="test_shutdown")
        agent.initialize()
        
        assert agent.is_initialized
        agent.shutdown()
        assert not agent.is_initialized
        
        # Double shutdown should be safe
        agent.shutdown()
        assert not agent.is_initialized

    def test_full_lifecycle(self):
        """Test complete lifecycle: init → reset → observe → think → act → update → shutdown."""
        agent = IdleAgent(agent_id="test_lifecycle")
        
        # Initialize
        agent.initialize()
        assert agent.is_initialized
        
        # Reset
        agent.reset(seed=42)
        
        # Create mock game state
        mock_game_state = MagicMock(spec=GameState)
        mock_game_state.tick = 0
        mock_game_state.players = []
        
        # Observe
        perception = agent.observe(mock_game_state)
        assert isinstance(perception, PerceptionResult)
        
        # Create decision context
        mock_position = MagicMock(spec=Vector2D)
        context = DecisionContext(
            game_state=mock_game_state,
            perception=perception,
            agent_id=agent.agent_id,
            agent_position=mock_position,
            tick=0,
            elapsed_time=0.0,
        )
        
        # Think
        action = agent.think(context)
        assert isinstance(action, ActionRequest)
        assert isinstance(action.action_type, ActionType)
        
        # Act
        result = agent.act(action)
        assert isinstance(result, ActionResult)
        assert result.success
        
        # Update
        agent.update(result)
        
        # Shutdown
        agent.shutdown()
        assert not agent.is_initialized

    def test_lifecycle_order_enforcement(self):
        """Test that lifecycle methods are called in order."""
        agent = IdleAgent(agent_id="test_order")
        
        # Should not fail even if not initialized
        # Methods should handle uninitialized state gracefully
        
        agent.reset()  # Should work even before init
        agent.initialize()
        agent.reset()
        agent.shutdown()

    def test_agent_repr(self):
        """Test agent string representation."""
        agent = IdleAgent(agent_id="test_repr")
        assert "test_repr" in repr(agent)
        assert "IdleAgent" in repr(agent)


class TestRandomAgent:
    """Test cases for RandomAgent."""

    def test_random_agent_creation(self):
        """Test RandomAgent creation."""
        agent = RandomAgent(agent_id="random_test", seed=42)
        assert agent.agent_id == "random_test"
        assert agent.seed == 42

    def test_random_agent_decisions(self):
        """Test RandomAgent produces decisions."""
        agent = RandomAgent(agent_id="random_decisions", seed=42)
        agent.initialize()
        agent.reset(seed=42)
        
        mock_game_state = MagicMock(spec=GameState)
        mock_game_state.tick = 0
        mock_game_state.players = []
        
        mock_position = MagicMock(spec=Vector2D)
        context = DecisionContext(
            game_state=mock_game_state,
            perception=PerceptionResult(),
            agent_id=agent.agent_id,
            agent_position=mock_position,
            tick=0,
            elapsed_time=0.0,
        )
        
        # Should produce valid action
        action = agent.think(context)
        assert action.action_type in [ActionType.IDLE, ActionType.MOVE, ActionType.ATTACK]
        assert 0.0 <= action.confidence <= 1.0

    def test_random_agent_determinism(self):
        """Test RandomAgent is deterministic with seed."""
        mock_game_state = MagicMock(spec=GameState)
        mock_game_state.tick = 0
        mock_game_state.players = []
        mock_position = MagicMock(spec=Vector2D)
        
        # Create two agents with same seed
        agent1 = RandomAgent(agent_id="det1", seed=12345)
        agent2 = RandomAgent(agent_id="det2", seed=12345)
        
        for agent in [agent1, agent2]:
            agent.initialize()
            agent.reset()
        
        context1 = DecisionContext(
            game_state=mock_game_state,
            perception=PerceptionResult(),
            agent_id="det1",
            agent_position=mock_position,
            tick=0,
            elapsed_time=0.0,
        )
        context2 = DecisionContext(
            game_state=mock_game_state,
            perception=PerceptionResult(),
            agent_id="det2",
            agent_position=mock_position,
            tick=0,
            elapsed_time=0.0,
        )
        
        # Should produce same action with same seed
        action1 = agent1.think(context1)
        action2 = agent2.think(context2)
        
        assert action1.action_type == action2.action_type


class TestIdleAgent:
    """Test cases for IdleAgent."""

    def test_idle_agent_always_idles(self):
        """Test IdleAgent always returns idle action."""
        agent = IdleAgent(agent_id="idle_test")
        agent.initialize()
        
        mock_game_state = MagicMock(spec=GameState)
        mock_position = MagicMock(spec=Vector2D)
        
        context = DecisionContext(
            game_state=mock_game_state,
            perception=PerceptionResult(),
            agent_id=agent.agent_id,
            agent_position=mock_position,
            tick=0,
            elapsed_time=0.0,
        )
        
        # Should always return idle
        action = agent.think(context)
        assert action.action_type == ActionType.IDLE
        assert action.confidence == 1.0


class TestScriptedAgent:
    """Test cases for ScriptedAgent."""

    def test_scripted_agent_creation(self):
        """Test ScriptedAgent creation."""
        def test_script(ctx):
            return ActionRequest(ActionType.ATTACK)
        
        agent = ScriptedAgent(
            agent_id="scripted_test",
            scripts=[test_script],
        )
        
        assert agent.agent_id == "scripted_test"
        assert len(agent.scripts) == 1

    def test_scripted_agent_script_execution(self):
        """Test ScriptedAgent executes scripts."""
        executed = []
        
        def test_script(ctx):
            executed.append(True)
            return ActionRequest(ActionType.MOVE)
        
        agent = ScriptedAgent(agent_id="exec_test", scripts=[test_script])
        agent.initialize()
        
        mock_game_state = MagicMock(spec=GameState)
        mock_position = MagicMock(spec=Vector2D)
        
        context = DecisionContext(
            game_state=mock_game_state,
            perception=PerceptionResult(),
            agent_id=agent.agent_id,
            agent_position=mock_position,
            tick=0,
            elapsed_time=0.0,
        )
        
        action = agent.think(context)
        assert len(executed) == 1
        assert action.action_type == ActionType.MOVE

    def test_scripted_agent_first_match(self):
        """Test ScriptedAgent with first_match priority."""
        def always_returns(ctx):
            return ActionRequest(ActionType.ATTACK)
        
        def never_returns(ctx):
            return None
        
        agent = ScriptedAgent(
            agent_id="first_match",
            scripts=[always_returns, never_returns],
            priority="first_match",
        )
        agent.initialize()
        
        mock_game_state = MagicMock(spec=GameState)
        mock_position = MagicMock(spec=Vector2D)
        
        context = DecisionContext(
            game_state=mock_game_state,
            perception=PerceptionResult(),
            agent_id=agent.agent_id,
            agent_position=mock_position,
            tick=0,
            elapsed_time=0.0,
        )
        
        action = agent.think(context)
        assert action.action_type == ActionType.ATTACK

    def test_scripted_agent_add_remove_scripts(self):
        """Test adding and removing scripts."""
        def script1(ctx):
            return ActionRequest(ActionType.IDLE)
        
        agent = ScriptedAgent(agent_id="add_remove", scripts=[script1])
        assert len(agent.scripts) == 1
        
        def script2(ctx):
            return ActionRequest(ActionType.MOVE)
        
        agent.add_script(script2)
        assert len(agent.scripts) == 2
        
        agent.remove_script(script1)
        assert len(agent.scripts) == 1
