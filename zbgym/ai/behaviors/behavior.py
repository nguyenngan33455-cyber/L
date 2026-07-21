"""
AI Behavior Base

Base classes for behavior tree and FSM implementations.
This is a foundation for future behavior-based AI systems.

Example (future):
    >>> class AttackBehavior(Behavior):
    ...     def execute(self, context: DecisionContext) -> BehaviorStatus:
    ...         enemies = context.get_visible_enemies()
    ...         if enemies:
    ...             return BehaviorStatus.SUCCESS
    ...         return BehaviorStatus.FAILURE
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.ai.core.types import DecisionContext


class BehaviorStatus(Enum):
    """
    Status of a behavior execution.
    
    Attributes:
        SUCCESS: Behavior completed successfully
        FAILURE: Behavior failed
        RUNNING: Behavior is still running
        ERROR: An error occurred during execution
    """
    
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"
    ERROR = "error"


class Behavior(ABC):
    """
    Abstract base class for behaviors.
    
    Behaviors are the building blocks of behavior trees.
    Each behavior can succeed, fail, or continue running.
    
    Attributes:
        name: Behavior name
        parent: Parent behavior (if any)
    """
    
    def __init__(self, name: str = "Behavior") -> None:
        """
        Initialize behavior.
        
        Args:
            name: Behavior name
        """
        self.name = name
        self.parent: Behavior | None = None
        self._tick: int = 0
    
    @abstractmethod
    def execute(self, context: DecisionContext) -> BehaviorStatus:
        """
        Execute the behavior.
        
        Args:
            context: Decision context
            
        Returns:
            Behavior status
        """
        ...
    
    def tick(self, context: DecisionContext) -> BehaviorStatus:
        """
        Execute with tick tracking.
        
        Args:
            context: Decision context
            
        Returns:
            Behavior status
        """
        self._tick += 1
        return self.execute(context)
    
    def reset(self) -> None:
        """Reset behavior state."""
        self._tick = 0
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
