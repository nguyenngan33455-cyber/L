"""
AI Planner Base

Base class for planning systems.
Planners generate plans to achieve goals.

Example (future):
    >>> class GOAPPlanner(Planner):
    ...     def create_plan(self, goals: list[Goal], state: WorldState) -> Plan:
    ...         # Implement GOAP planning
    ...         pass
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.ai.core.types import ActionRequest, DecisionContext


class Planner(ABC):
    """
    Abstract base class for AI planners.
    
    Planners generate sequences of actions to achieve goals.
    They can be simple (one-shot) or complex (hierarchical).
    
    Attributes:
        name: Planner name
    """
    
    def __init__(self, name: str = "Planner") -> None:
        """
        Initialize planner.
        
        Args:
            name: Planner name
        """
        self.name = name
        self._seed: int | None = None
    
    @abstractmethod
    def plan(self, context: DecisionContext) -> list[ActionRequest]:
        """
        Generate a plan.
        
        Args:
            context: Decision context with goals and state
            
        Returns:
            List of actions to execute
        """
        ...
    
    @abstractmethod
    def reset(self, seed: int | None = None) -> None:
        """
        Reset planner state.
        
        Args:
            seed: Random seed
        """
        ...
    
    def get_state_dict(self) -> dict:
        """Get planner state."""
        return {"name": self.name, "seed": self._seed}
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
