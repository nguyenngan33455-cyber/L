"""
Tests for AI Types and Exceptions

Verifies:
- ActionRequest/ActionResult
- DecisionContext
- PerceptionResult
- Custom exceptions
"""

import pytest
from unittest.mock import MagicMock

from zbgym.ai.core.types import (
    ActionRequest,
    ActionResult,
    ActionType,
    DecisionContext,
    PerceptionResult,
)
from zbgym.ai.exceptions import (
    AIError,
    AgentError,
    DecisionError,
    RegistryError,
)
from zbgym.interfaces import GameState, Player, Vector2D


class TestActionRequest:
    """Test ActionRequest."""

    def test_action_request_creation(self):
        """Test ActionRequest creation."""
        req = ActionRequest(ActionType.MOVE)
        
        assert req.action_type == ActionType.MOVE
        assert req.target_id is None
        assert req.target_position is None
        assert req.parameters == {}
        assert req.priority == 1.0
        assert req.confidence == 1.0

    def test_action_request_full(self):
        """Test ActionRequest with all fields."""
        mock_pos = MagicMock(spec=Vector2D)
        
        req = ActionRequest(
            action_type=ActionType.ATTACK,
            target_id="enemy_1",
            target_position=mock_pos,
            parameters={"damage": 100},
            priority=0.8,
            confidence=0.9,
        )
        
        assert req.action_type == ActionType.ATTACK
        assert req.target_id == "enemy_1"
        assert req.target_position == mock_pos
        assert req.parameters["damage"] == 100
        assert req.priority == 0.8
        assert req.confidence == 0.9

    def test_invalid_action_type(self):
        """Test invalid action type raises error."""
        with pytest.raises(ValueError):
            ActionRequest(action_type="invalid")

    def test_invalid_priority(self):
        """Test invalid priority raises error."""
        with pytest.raises(ValueError):
            ActionRequest(ActionType.IDLE, priority=-0.1)
        
        with pytest.raises(ValueError):
            ActionRequest(ActionType.IDLE, priority=1.5)

    def test_invalid_confidence(self):
        """Test invalid confidence raises error."""
        with pytest.raises(ValueError):
            ActionRequest(ActionType.IDLE, confidence=-0.1)
        
        with pytest.raises(ValueError):
            ActionRequest(ActionType.IDLE, confidence=1.5)


class TestActionResult:
    """Test ActionResult."""

    def test_success_result(self):
        """Test successful action result."""
        req = ActionRequest(ActionType.MOVE)
        result = ActionResult.success_result(req, execution_time=0.1)
        
        assert result.success is True
        assert result.executed is True
        assert result.action_request == req
        assert result.execution_time == 0.1
        assert result.error_message is None

    def test_failure_result(self):
        """Test failed action result."""
        req = ActionRequest(ActionType.ATTACK)
        result = ActionResult.failure_result(req, "Out of range")
        
        assert result.success is False
        assert result.executed is False
        assert result.error_message == "Out of range"

    def test_result_properties(self):
        """Test result properties."""
        req = ActionRequest(ActionType.IDLE)
        result = ActionResult(
            success=True,
            action_request=req,
            executed=True,
            execution_time=0.05,
        )
        
        assert result.success
        assert result.executed


class TestPerceptionResult:
    """Test PerceptionResult."""

    def test_default_perception(self):
        """Test default perception result."""
        perc = PerceptionResult()
        
        assert perc.visible_players == ()
        assert perc.visible_positions == ()
        assert perc.threats == ()
        assert perc.allies == ()
        assert perc.projectiles == ()
        assert perc.items == ()

    def test_perception_with_data(self):
        """Test perception with data."""
        mock_player = MagicMock(spec=Player)
        mock_player.id = "player_1"
        
        perc = PerceptionResult(
            visible_players=(mock_player,),
            threats=("enemy_1",),
            nearest_enemy_distance=100.0,
        )
        
        assert len(perc.visible_players) == 1
        assert "enemy_1" in perc.threats
        assert perc.nearest_enemy_distance == 100.0


class TestDecisionContext:
    """Test DecisionContext."""

    def test_decision_context_creation(self):
        """Test DecisionContext creation."""
        mock_state = MagicMock(spec=GameState)
        perc = PerceptionResult()
        mock_pos = MagicMock(spec=Vector2D)
        
        ctx = DecisionContext(
            game_state=mock_state,
            perception=perc,
            agent_id="agent_1",
            agent_position=mock_pos,
            tick=100,
            elapsed_time=1.5,
        )
        
        assert ctx.game_state == mock_state
        assert ctx.perception == perc
        assert ctx.agent_id == "agent_1"
        assert ctx.tick == 100
        assert ctx.elapsed_time == 1.5

    def test_decision_context_defaults(self):
        """Test DecisionContext default values."""
        mock_state = MagicMock(spec=GameState)
        perc = PerceptionResult()
        mock_pos = MagicMock(spec=Vector2D)
        
        ctx = DecisionContext(
            game_state=mock_state,
            perception=perc,
            agent_id="agent_1",
            agent_position=mock_pos,
            tick=0,
            elapsed_time=0.0,
        )
        
        assert ctx.memory is None
        assert ctx.blackboard is None
        assert len(ctx.available_actions) == len(ActionType)


class TestActionType:
    """Test ActionType enum."""

    def test_action_types(self):
        """Test all action types exist."""
        expected_types = [
            "move", "attack", "use_skill", "use_item",
            "patrol", "defend", "flee", "idle", "custom"
        ]
        
        for action_type in expected_types:
            assert hasattr(ActionType, action_type.upper())
            assert ActionType[action_type.upper()].value == action_type

    def test_action_type_values(self):
        """Test action type values."""
        assert ActionType.MOVE.value == "move"
        assert ActionType.ATTACK.value == "attack"
        assert ActionType.IDLE.value == "idle"


class TestAIError:
    """Test AIError exception."""

    def test_ai_error_basic(self):
        """Test basic AIError."""
        error = AIError("Test error")
        
        assert error.message == "Test error"
        assert error.agent_id is None
        assert "Test error" in str(error)

    def test_ai_error_with_agent_id(self):
        """Test AIError with agent ID."""
        error = AIError("Error for agent", agent_id="agent_1")
        
        assert error.agent_id == "agent_1"
        assert "agent_1" in str(error)


class TestAgentError:
    """Test AgentError exception."""

    def test_agent_error(self):
        """Test AgentError."""
        error = AgentError(
            "Agent failed",
            agent_id="agent_1",
            operation="initialize",
        )
        
        assert error.agent_id == "agent_1"
        assert error.operation == "initialize"
        assert "initialize" in str(error)


class TestDecisionError:
    """Test DecisionError exception."""

    def test_decision_error(self):
        """Test DecisionError."""
        error = DecisionError(
            "Decision failed",
            agent_id="agent_1",
            context_info={"tick": 100},
        )
        
        assert error.agent_id == "agent_1"
        assert error.context_info["tick"] == 100


class TestRegistryError:
    """Test RegistryError exception."""

    def test_registry_error(self):
        """Test RegistryError."""
        error = RegistryError(
            "Agent not found",
            agent_type="random",
        )
        
        assert error.agent_type == "random"
        assert "not found" in str(error)


class TestExceptionHierarchy:
    """Test exception hierarchy."""

    def test_ai_error_is_base(self):
        """Test AIError is base for all."""
        assert issubclass(AgentError, AIError)
        assert issubclass(DecisionError, AIError)
        assert issubclass(RegistryError, AIError)

    def test_can_catch_base(self):
        """Test can catch all with base exception."""
        try:
            raise AgentError("test")
        except AIError as e:
            assert isinstance(e, AgentError)
