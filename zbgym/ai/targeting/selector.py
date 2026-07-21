"""
AI Target Selector

Base class for target selection strategies.
Target selectors choose the best target from available options.

Example:
    >>> selector = NearestTargeting()
    >>> target = selector.select_target(
    ...     candidates=enemies,
    ...     agent_position=pos,
    ...     blackboard=blackboard,
    ... )
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from zbgym.interfaces import Player, Vector2D
    from zbgym.ai.blackboard.blackboard import Blackboard
    from zbgym.ai.core.types import DecisionContext


T = TypeVar("T")


class TargetSelector(ABC, Generic[T]):
    """
    Abstract base class for target selection.
    
    Target selectors evaluate candidates and return the best target.
    They can be composed for complex selection logic.
    
    Attributes:
        name: Selector name
    """
    
    def __init__(self, name: str = "TargetSelector") -> None:
        """
        Initialize target selector.
        
        Args:
            name: Selector name
        """
        self.name = name
    
    @abstractmethod
    def select(
        self,
        candidates: list[T],
        agent_id: str,
        context: DecisionContext,
    ) -> T | None:
        """
        Select the best target from candidates.
        
        Args:
            candidates: List of possible targets
            agent_id: Agent ID making the selection
            context: Decision context
            
        Returns:
            Selected target or None
        """
        ...
    
    def score(self, target: T, context: DecisionContext) -> float:
        """
        Score a target for selection.
        
        Override this for custom scoring.
        
        Args:
            target: Target to score
            context: Decision context
            
        Returns:
            Score (higher is better)
        """
        return 1.0
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class NearestTargeting(TargetSelector["Player"]):
    """
    Select the nearest target.
    """
    
    def select(
        self,
        candidates: list["Player"],
        agent_id: str,
        context: DecisionContext,
    ) -> "Player | None":
        """Select nearest player."""
        if not candidates or context.agent_position is None:
            return None
        
        nearest = None
        nearest_dist = float('inf')
        
        for player in candidates:
            if hasattr(player, 'position') and player.position:
                dist = context.agent_position.distance_to(player.position)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = player
        
        return nearest


class LowestHealthTargeting(TargetSelector["Player"]):
    """
    Select the target with lowest health.
    """
    
    def select(
        self,
        candidates: list["Player"],
        agent_id: str,
        context: DecisionContext,
    ) -> "Player | None":
        """Select player with lowest health."""
        if not candidates:
            return None
        
        lowest = None
        lowest_hp = float('inf')
        
        for player in candidates:
            if hasattr(player, 'health'):
                if player.health < lowest_hp:
                    lowest_hp = player.health
                    lowest = player
        
        return lowest


class HighestHealthTargeting(TargetSelector["Player"]):
    """
    Select the target with highest health.
    """
    
    def select(
        self,
        candidates: list["Player"],
        agent_id: str,
        context: DecisionContext,
    ) -> "Player | None":
        """Select player with highest health."""
        if not candidates:
            return None
        
        highest = None
        highest_hp = 0.0
        
        for player in candidates:
            if hasattr(player, 'health'):
                if player.health > highest_hp:
                    highest_hp = player.health
                    highest = player
        
        return highest


class CompositeTargeting(TargetSelector["Player"]):
    """
    Combine multiple targeting strategies.
    
    Attributes:
        selectors: List of selectors to combine
        weights: Weights for each selector
    """
    
    def __init__(
        self,
        selectors: list[TargetSelector],
        weights: list[float] | None = None,
    ) -> None:
        """
        Initialize composite targeting.
        
        Args:
            selectors: Selectors to combine
            weights: Weights for each selector (default: equal)
        """
        super().__init__(name="Composite")
        self.selectors = selectors
        self.weights = weights or [1.0] * len(selectors)
    
    def select(
        self,
        candidates: list["Player"],
        agent_id: str,
        context: DecisionContext,
    ) -> "Player | None":
        """Select using weighted combination."""
        if not candidates:
            return None
        
        best_target = None
        best_score = -float('inf')
        
        for candidate in candidates:
            score = 0.0
            for selector, weight in zip(self.selectors, self.weights):
                score += selector.score(candidate, context) * weight
            
            if score > best_score:
                best_score = score
                best_target = candidate
        
        return best_target
