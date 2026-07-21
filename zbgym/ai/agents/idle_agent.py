"""
Idle Agent

An AI agent that does nothing.
Useful for testing and as a fallback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zbgym.ai.agents.base_agent import BaseAgent
from zbgym.ai.core.types import (
    ActionRequest,
    ActionType,
    DecisionContext,
)

if TYPE_CHECKING:
    from zbgym.interfaces import GameState


class IdleAgent(BaseAgent):
    """
    Agent that always returns idle action.
    
    Useful for:
    - Baseline testing
    - Disabled AI
    - Placeholder agents
    """
    
    def think_impl(self, context: DecisionContext) -> ActionRequest:
        """Return idle action."""
        return ActionRequest(
            action_type=ActionType.IDLE,
            confidence=1.0,
        )
