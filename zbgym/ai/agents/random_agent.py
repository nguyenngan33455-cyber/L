"""
Random Agent

An AI agent that makes random decisions.
Useful for baseline testing and debugging.

Example:
    >>> agent = RandomAgent(agent_id="random_bot", seed=42)
    >>> agent.initialize()
    >>> 
    >>> for step in range(100):
    ...     perception = agent.observe(game_state)
    ...     action = agent.think(context)
    ...     result = agent.act(action)
    ...     agent.update(result)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zbgym.ai.agents.base_agent import BaseAgent
from zbgym.ai.core.types import (
    ActionRequest,
    ActionResult,
    ActionType,
    DecisionContext,
    PerceptionResult,
)

if TYPE_CHECKING:
    from zbgym.interfaces import GameState
    import numpy as np


class RandomAgent(BaseAgent):
    """
    Agent that makes random decisions.
    
    Selects actions uniformly at random from available actions.
    Fully deterministic with seed.
    
    Attributes:
        available_actions: List of actions to choose from
    """
    
    def __init__(
        self,
        agent_id: str,
        seed: int | None = None,
        available_actions: list[ActionType] | None = None,
    ) -> None:
        """
        Initialize random agent.
        
        Args:
            agent_id: Unique agent identifier
            seed: Random seed for determinism
            available_actions: Actions to choose from
        """
        from zbgym.ai.config.base_config import AIConfig
        
        # Store seed at agent level
        self._agent_seed = seed
        config = AIConfig(seed=seed)
        super().__init__(agent_id, config=config)
        
        # Default actions to choose from
        self.available_actions = available_actions or [
            ActionType.IDLE,
            ActionType.MOVE,
            ActionType.ATTACK,
        ]
    
    @property
    def seed(self) -> int | None:
        """Get the random seed."""
        return self._seed or self._agent_seed
    
    def think_impl(self, context: DecisionContext) -> ActionRequest:
        """
        Make a random decision.
        
        Returns:
            Random action request
        """
        if self._rng is None:
            return ActionRequest(ActionType.IDLE)
        
        # Choose random action
        action_type = self._rng.choice(self.available_actions)
        
        # Create action request
        request = ActionRequest(
            action_type=action_type,
            confidence=1.0,
        )
        
        # Add random target position for movement actions
        if action_type == ActionType.MOVE and context.agent_position is not None:
            try:
                import numpy as np
                offset = self._rng.uniform(-100, 100, size=2)
                # Use position values if available
                if hasattr(context.agent_position, 'x') and hasattr(context.agent_position, 'y'):
                    target_x = context.agent_position.x + offset[0]
                    target_y = context.agent_position.y + offset[1]
                    from zbgym.physics.vector import Vector2D
                    request.target_position = Vector2D(target_x, target_y)
            except (TypeError, AttributeError):
                # MagicMock or other mock objects - skip target position
                pass
        
        return request
    
    def get_state_dict(self) -> dict:
        """Get agent state."""
        state = super().get_state_dict()
        state["available_actions"] = [a.value for a in self.available_actions]
        return state
