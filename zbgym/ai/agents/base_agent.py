"""
Base Agent Implementation

Provides a base class for AI agents with common functionality.
Agents can inherit from this to get default implementations.

Example:
    >>> class MyAgent(BaseAgent):
    ...     def think_impl(self, context: DecisionContext) -> ActionRequest:
    ...         # Custom decision logic
    ...         return ActionRequest(ActionType.IDLE)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zbgym.ai.core.agent import AIAgent
from zbgym.ai.core.types import (
    ActionRequest,
    ActionResult,
    ActionType,
    DecisionContext,
    PerceptionResult,
)
from zbgym.ai.memory.memory import Memory
from zbgym.ai.blackboard.blackboard import Blackboard
from zbgym.ai.config.base_config import AIConfig
from zbgym.ai.exceptions.agent_error import AgentError

if TYPE_CHECKING:
    from zbgym.interfaces import GameState
    import numpy as np


class BaseAgent(AIAgent):
    """
    Base implementation of AIAgent.
    
    Provides common functionality:
    - Memory management
    - Blackboard access
    - Configuration handling
    - Determinism support
    
    Subclasses should override the *_impl methods for custom behavior.
    """
    
    def __init__(
        self,
        agent_id: str,
        config: AIConfig | None = None,
        memory_capacity: int = 100,
    ) -> None:
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique agent identifier
            config: AI configuration
            memory_capacity: Maximum memory entries
        """
        super().__init__(agent_id)
        self.config = config or AIConfig()
        self._memory = Memory(capacity=memory_capacity, seed=self.config.seed)
        self._blackboard: Blackboard | None = None
        self._rng: np.random.Generator | None = None
        self._tick: int = 0
        self._elapsed_time: float = 0.0
    
    @property
    def memory(self) -> Memory:
        """Get agent's memory."""
        return self._memory
    
    @property
    def blackboard(self) -> Blackboard | None:
        """Get agent's blackboard."""
        return self._blackboard
    
    @blackboard.setter
    def blackboard(self, value: Blackboard) -> None:
        """Set agent's blackboard."""
        self._blackboard = value
    
    def initialize(self) -> None:
        """Initialize agent resources."""
        if self._initialized:
            return
        
        try:
            # Initialize RNG
            if self.config.deterministic and self.config.seed is not None:
                import numpy as np
                self._rng = np.random.default_rng(self.config.seed)
            elif not self.config.deterministic:
                import numpy as np
                self._rng = np.random.default_rng()
            
            # Initialize blackboard if not set
            if self._blackboard is None:
                self._blackboard = Blackboard(seed=self.config.seed)
            
            self._initialized = True
            
        except Exception as e:
            raise AgentError(
                f"Failed to initialize agent: {e}",
                agent_id=self.agent_id,
                operation="initialize",
            )
    
    def reset(self, seed: int | None = None) -> None:
        """Reset agent state."""
        if seed is not None:
            self._seed = seed
            self.config.seed = seed
            import numpy as np
            self._rng = np.random.default_rng(seed)
        
        self._memory.clear()
        self._tick = 0
        self._elapsed_time = 0.0
    
    def observe(self, game_state: GameState) -> PerceptionResult:
        """Process game state through perception."""
        from zbgym.ai.core.types import PerceptionResult
        
        # Store observation in memory
        self._memory.remember(
            key="last_observation",
            value={
                "tick": self._tick,
                "player_count": len(game_state.players),
            },
            importance=0.3,
        )
        
        return PerceptionResult()
    
    def think(self, context: DecisionContext) -> ActionRequest:
        """Make a decision."""
        return self.think_impl(context)
    
    def think_impl(self, context: DecisionContext) -> ActionRequest:
        """
        Override this method for custom decision logic.
        
        Default implementation returns idle action.
        """
        return ActionRequest(ActionType.IDLE)
    
    def act(self, action: ActionRequest) -> ActionResult:
        """Execute action."""
        return ActionResult.success_result(action)
    
    def update(self, result: ActionResult) -> None:
        """Update internal state based on result."""
        # Store action result in memory
        self._memory.remember(
            key="last_action_result",
            value={
                "success": result.success,
                "action_type": result.action_request.action_type.value,
            },
            importance=0.5,
        )
        
        # Update tick
        if hasattr(self, "config") and self.config.tick_rate > 0:
            self._elapsed_time += 1.0 / self.config.tick_rate
        self._tick += 1
    
    def shutdown(self) -> None:
        """Cleanup resources."""
        self._memory.clear_all()
        self._blackboard = None
        self._rng = None
        self._initialized = False
