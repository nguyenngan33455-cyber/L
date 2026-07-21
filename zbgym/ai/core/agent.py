"""
AIAgent Base Interface

Defines the contract for all AI agents in the system.
Every agent must implement this interface.

The agent lifecycle:
    1. initialize() - Setup agent resources
    2. reset() - Reset to initial state
    3. observe() - Perceive the environment
    4. think() - Make decisions
    5. act() - Execute action
    6. update() - Update internal state
    7. shutdown() - Cleanup resources

Example:
    >>> class MyAgent(AIAgent):
    ...     def __init__(self, agent_id: str):
    ...         self.agent_id = agent_id
    ...     
    ...     def initialize(self) -> None:
    ...         pass
    ...     
    ...     def reset(self, seed: int | None = None) -> None:
    ...         pass
    ...     
    ...     def observe(self, game_state: GameState) -> PerceptionResult:
    ...         return PerceptionResult()
    ...     
    ...     def think(self, context: DecisionContext) -> ActionRequest:
    ...         return ActionRequest(ActionType.IDLE)
    ...     
    ...     def act(self, action: ActionRequest) -> ActionResult:
    ...         return ActionResult.success_result(action)
    ...     
    ...     def update(self, result: ActionResult) -> None:
    ...         pass
    ...     
    ...     def shutdown(self) -> None:
    ...         pass
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.interfaces import GameState, Vector2D
    from zbgym.ai.core.types import (
        ActionRequest,
        ActionResult,
        DecisionContext,
        PerceptionResult,
    )
    from zbgym.ai.config import AIConfig


class AIAgent(ABC):
    """
    Abstract base class for all AI agents.
    
    This interface defines the contract that all AI agents must implement.
    The simulator interacts with agents exclusively through these methods.
    
    Attributes:
        agent_id: Unique identifier for this agent
        
    Thread Safety:
        All methods should be thread-safe if the agent is used in
        multi-threaded environments.
    """
    
    def __init__(self, agent_id: str) -> None:
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        self.agent_id = agent_id
        self._initialized = False
        self._seed: int | None = None
    
    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized
    
    @property
    def seed(self) -> int | None:
        """Get the random seed used by this agent."""
        return self._seed
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize agent resources.
        
        Called once before the agent is used.
        Setup any required resources, load configurations, etc.
        
        Raises:
            AIError: If initialization fails
        """
        ...
    
    @abstractmethod
    def reset(self, seed: int | None = None) -> None:
        """
        Reset agent to initial state.
        
        Called at the start of each episode.
        Reset all internal state, memory, etc.
        
        Args:
            seed: Random seed for reproducibility
        """
        ...
    
    @abstractmethod
    def observe(self, game_state: GameState) -> PerceptionResult:
        """
        Perceive the environment.
        
        Process the game state and extract relevant information.
        This is the first step in each decision cycle.
        
        Args:
            game_state: Current game state snapshot
            
        Returns:
            PerceptionResult containing perceived information
        """
        ...
    
    @abstractmethod
    def think(self, context: DecisionContext) -> ActionRequest:
        """
        Make a decision based on context.
        
        This is the core decision-making step.
        Use perception, memory, and blackboard to decide what to do.
        
        Args:
            context: Decision context with all relevant information
            
        Returns:
            ActionRequest describing the desired action
        """
        ...
    
    @abstractmethod
    def act(self, action: ActionRequest) -> ActionResult:
        """
        Execute the action.
        
        Take the requested action and return the result.
        
        Args:
            action: The action to execute
            
        Returns:
            ActionResult describing what happened
        """
        ...
    
    @abstractmethod
    def update(self, result: ActionResult) -> None:
        """
        Update internal state based on action result.
        
        Learn from the action result, update memory, etc.
        
        Args:
            result: Result of the last action
        """
        ...
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Cleanup agent resources.
        
        Called when the agent is no longer needed.
        Release any held resources.
        """
        ...
    
    def get_state_dict(self) -> dict:
        """
        Get agent state for serialization.
        
        Returns:
            Dictionary containing agent state
        """
        return {
            "agent_id": self.agent_id,
            "initialized": self._initialized,
            "seed": self._seed,
        }
    
    def load_state_dict(self, state: dict) -> None:
        """
        Load agent state from dictionary.
        
        Args:
            state: State dictionary from get_state_dict()
        """
        self._initialized = state.get("initialized", False)
        self._seed = state.get("seed")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent_id='{self.agent_id}')"
