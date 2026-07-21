"""
AIController Interface

Manages AI agents and coordinates the decision pipeline.
The controller orchestrates the observation -> decision -> action cycle.

Decision Pipeline:
    GameState
        ↓
    observe() - Perception
        ↓
    think() - Decision Making
        ↓
    act() - Action Execution
        ↓
    update() - Learning/Feedback
        ↓
    GameState (next tick)

Example:
    >>> from zbgym.ai.core.controller import AIController
    >>> from zbgym.ai.agents import RandomAgent
    >>> 
    >>> controller = AIController(agent=RandomAgent("bot_1"))
    >>> controller.initialize()
    >>> 
    >>> for step in range(100):
    ...     controller.update(game_state)
    ...     action = controller.decide(game_state)
    ...     result = controller.execute(action)
    ... 
    >>> controller.shutdown()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.interfaces import GameState
    from zbgym.ai.core.agent import AIAgent
    from zbgym.ai.core.types import (
        ActionRequest,
        ActionResult,
        DecisionContext,
        PerceptionResult,
    )


class AIController(ABC):
    """
    Controller for managing AI agents.
    
    Coordinates the decision pipeline and manages agent lifecycle.
    Provides a high-level interface for interacting with AI agents.
    
    Attributes:
        agent: The AI agent being controlled
        
    Thread Safety:
        Implementations should be thread-safe if used in
        multi-threaded environments.
    """
    
    def __init__(self, agent: AIAgent) -> None:
        """
        Initialize the controller.
        
        Args:
            agent: The AI agent to control
        """
        self.agent = agent
        self._current_context: DecisionContext | None = None
        self._last_action: ActionRequest | None = None
        self._step_count: int = 0
    
    @property
    def agent_id(self) -> str:
        """Get the controlled agent's ID."""
        return self.agent.agent_id
    
    @property
    def step_count(self) -> int:
        """Get the number of steps executed."""
        return self._step_count
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the controller and agent.
        
        Must be called before any other operations.
        
        Raises:
            AIError: If initialization fails
        """
        ...
    
    @abstractmethod
    def reset(self, seed: int | None = None) -> None:
        """
        Reset for a new episode.
        
        Args:
            seed: Random seed for reproducibility
        """
        ...
    
    @abstractmethod
    def perceive(self, game_state: GameState) -> PerceptionResult:
        """
        Process game state through perception.
        
        Args:
            game_state: Current game state
            
        Returns:
            Perception result
        """
        ...
    
    @abstractmethod
    def decide(self, game_state: GameState) -> ActionRequest:
        """
        Make a decision based on game state.
        
        Complete pipeline: perceive -> think -> return action
        
        Args:
            game_state: Current game state
            
        Returns:
            Selected action
        """
        ...
    
    @abstractmethod
    def execute(self, action: ActionRequest) -> ActionResult:
        """
        Execute an action.
        
        Args:
            action: Action to execute
            
        Returns:
            Action result
        """
        ...
    
    @abstractmethod
    def update(self, game_state: GameState) -> ActionResult:
        """
        Update controller state.
        
        Complete pipeline: perceive -> think -> act -> update
        
        Args:
            game_state: Current game state
            
        Returns:
            Action result from execution
        """
        ...
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Shutdown the controller and agent.
        
        Release all resources.
        """
        ...
    
    def get_context(self) -> DecisionContext | None:
        """Get the current decision context."""
        return self._current_context
    
    def get_last_action(self) -> ActionRequest | None:
        """Get the last executed action."""
        return self._last_action
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent={self.agent!r})"
