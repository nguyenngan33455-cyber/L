"""
AI Core Types

Defines fundamental types used across the AI system.
These types are game-agnostic and depend only on zbgym.interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from enum import Enum

from zbgym.interfaces import GameState, Vector2D, Player


class ActionType(Enum):
    """Types of actions an AI can request."""
    
    MOVE = "move"
    ATTACK = "attack"
    USE_SKILL = "use_skill"
    USE_ITEM = "use_item"
    PATROL = "patrol"
    DEFEND = "defend"
    FLEE = "flee"
    IDLE = "idle"
    CUSTOM = "custom"


@dataclass
class ActionRequest:
    """
    Represents a requested action from an AI agent.
    
    This is the output of the AI decision process and the input
    to the action execution system.
    
    Attributes:
        action_type: Type of action to perform
        target_id: Optional target entity ID
        target_position: Optional target position
        parameters: Additional action parameters
        priority: Action priority (higher = more important)
        confidence: AI confidence in this action (0-1)
    """
    
    action_type: ActionType
    target_id: str | None = None
    target_position: Vector2D | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    priority: float = 1.0
    confidence: float = 1.0
    
    def __post_init__(self) -> None:
        """Validate action request."""
        if not isinstance(self.action_type, ActionType):
            raise ValueError(
                f"action_type must be ActionType, got {type(self.action_type)}"
            )
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError(f"priority must be in [0, 1], got {self.priority}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")


@dataclass
class ActionResult:
    """
    Represents the result of an action execution.
    
    Attributes:
        success: Whether the action was executed successfully
        action_request: The original action request
        executed: Whether the action was actually executed
        error_message: Error message if execution failed
        execution_time: Time taken to execute the action
    """
    
    success: bool
    action_request: ActionRequest
    executed: bool = False
    error_message: str | None = None
    execution_time: float = 0.0
    
    @classmethod
    def success_result(
        cls,
        action: ActionRequest,
        execution_time: float = 0.0
    ) -> ActionResult:
        """Create a successful action result."""
        return cls(
            success=True,
            action_request=action,
            executed=True,
            execution_time=execution_time,
        )
    
    @classmethod
    def failure_result(
        cls,
        action: ActionRequest,
        error: str
    ) -> ActionResult:
        """Create a failed action result."""
        return cls(
            success=False,
            action_request=action,
            executed=False,
            error_message=error,
        )


@dataclass
class PerceptionResult:
    """
    Result of the perception system.
    
    Contains all perceived entities and their properties.
    
    Attributes:
        visible_players: Players visible to the agent
        visible_positions: Notable positions
        threats: Identified threats
        allies: Known allies
        projectiles: Incoming projectiles
        items: Visible items
        map_info: Map information
    """
    
    visible_players: tuple[Player, ...] = field(default_factory=tuple)
    visible_positions: tuple[Vector2D, ...] = field(default_factory=tuple)
    threats: tuple[str, ...] = field(default_factory=tuple)  # Entity IDs
    allies: tuple[str, ...] = field(default_factory=tuple)  # Entity IDs
    projectiles: tuple[str, ...] = field(default_factory=tuple)  # Entity IDs
    items: tuple[str, ...] = field(default_factory=tuple)  # Entity IDs
    nearest_enemy_distance: float | None = None
    nearest_ally_distance: float | None = None
    time_in_perception: float = 0.0  # Time spent perceiving


@dataclass
class DecisionContext:
    """
    Context provided to the decision-making system.
    
    This encapsulates all information an AI needs to make decisions.
    
    Attributes:
        game_state: Current game state snapshot
        perception: Perception results
        agent_id: ID of the agent making the decision
        agent_position: Current position of the agent
        tick: Current game tick
        elapsed_time: Elapsed game time
        memory: Agent's memory
        blackboard: Shared knowledge
        available_actions: List of possible actions
    """
    
    game_state: GameState
    perception: PerceptionResult
    agent_id: str
    agent_position: Vector2D
    tick: int
    elapsed_time: float
    memory: Memory | None = None
    blackboard: Blackboard | None = None
    available_actions: tuple[ActionType, ...] = field(
        default_factory=lambda: tuple(ActionType)
    )
    
    def get_visible_enemies(self) -> list[Player]:
        """Get list of visible enemies."""
        enemies = []
        agent = self.game_state.get_player(self.agent_id)
        agent_team = agent.team_id if agent else None
        
        for player in self.perception.visible_players:
            if player.id != self.agent_id and player.team_id != agent_team:
                enemies.append(player)
        
        return enemies
    
    def get_visible_allies(self) -> list[Player]:
        """Get list of visible allies."""
        agent = self.game_state.get_player(self.agent_id)
        agent_team = agent.team_id if agent else None
        
        allies = []
        for player in self.perception.visible_players:
            if player.id != self.agent_id and player.team_id == agent_team:
                allies.append(player)
        
        return allies


# Forward reference to avoid circular import
class Memory:
    pass


class Blackboard:
    pass
