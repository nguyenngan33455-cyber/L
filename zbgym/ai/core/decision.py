"""
DecisionModule Interface

Base interface for decision-making systems.
Decision modules take a DecisionContext and produce ActionRequests.

Example:
    >>> class RandomDecisionModule(DecisionModule):
    ...     def __init__(self, seed: int | None = None):
    ...         self.seed = seed
    ...         self.rng = np.random.default_rng(seed)
    ...     
    ...     def decide(self, context: DecisionContext) -> ActionRequest:
    ...         actions = list(ActionType)[:3]  # MOVE, ATTACK, IDLE
    ...         action_type = self.rng.choice(actions)
    ...         return ActionRequest(action_type)
    ...     
    ...     def reset(self, seed: int | None = None) -> None:
    ...         self.rng = np.random.default_rng(seed)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.ai.core.types import ActionRequest, DecisionContext


class DecisionModule(ABC):
    """
    Abstract base for decision-making modules.
    
    Decision modules are pluggable components that can be replaced
    to change AI behavior without changing the agent.
    
    Attributes:
        name: Module name for identification
    """
    
    def __init__(self, name: str = "DecisionModule") -> None:
        """
        Initialize decision module.
        
        Args:
            name: Module name
        """
        self.name = name
        self._seed: int | None = None
    
    @abstractmethod
    def decide(self, context: DecisionContext) -> ActionRequest:
        """
        Make a decision based on context.
        
        Args:
            context: Decision context with all relevant information
            
        Returns:
            Selected action request
        """
        ...
    
    @abstractmethod
    def reset(self, seed: int | None = None) -> None:
        """
        Reset module state.
        
        Args:
            seed: Random seed for reproducibility
        """
        ...
    
    def get_state_dict(self) -> dict:
        """Get module state for serialization."""
        return {"name": self.name, "seed": self._seed}
    
    def load_state_dict(self, state: dict) -> None:
        """Load module state."""
        self._seed = state.get("seed")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
