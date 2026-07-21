"""
BattleArena Adapter Implementation

This module provides the BattleArenaAdapter class that wraps
the BattleArena environment and exposes the generic GameAdapter interface.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import numpy as np

from zbgym.interfaces import (
    GameAdapter,
    GameEngine,
    GameState,
    ObservationProvider,
    RewardProvider,
)
from zbgym.adapters.battle_arena.state import BattleArenaGameState
from zbgym.adapters.battle_arena.mapper import BattleArenaStateMapper

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArena


class BattleArenaAdapter(GameAdapter):
    """
    Adapter for BattleArena environment.
    
    This adapter wraps the BattleArena environment and provides
    access to the generic GameState interface through the
    BattleArenaGameState class.
    
    The adapter does NOT contain any game logic - it only
    translates data between the BattleArena and the generic interface.
    
    Example:
        >>> from zbgym.adapters.battle_arena import BattleArenaAdapter
        >>> 
        >>> adapter = BattleArenaAdapter()
        >>> state = adapter.get_game_state()
        >>> 
        >>> # Use with generic interfaces
        >>> players = state.get_players()
        >>> for player in players:
        ...     print(f"{player.id}: {player.health.current}/{player.health.max}")
    """
    
    def __init__(
        self,
        config: Any | None = None,
        render_mode: str | None = None,
        obs_config: dict | None = None,
        reward_config: dict | None = None,
    ):
        """
        Initialize BattleArena adapter.
        
        Args:
            config: Environment configuration
            render_mode: Rendering mode
            obs_config: Observation configuration
            reward_config: Reward configuration
        """
        from zbgym.env.battle_arena import BattleArena
        
        # Create the internal BattleArena engine
        self._engine = BattleArena(
            config=config,
            render_mode=render_mode,
            obs_config=obs_config,
            reward_config=reward_config,
        )
        
        # Create the state mapper
        self._mapper = BattleArenaStateMapper()
        
        # Cache for last game state
        self._last_game_state: BattleArenaGameState | None = None
    
    @property
    def engine(self) -> GameEngine:
        """Get the underlying game engine."""
        return self._engine
    
    def get_game_state(self) -> GameState:
        """
        Get current game state as generic GameState.
        
        Returns:
            BattleArenaGameState instance
        """
        # Get raw state from engine
        arena_state = self._engine.get_state()
        
        # Map to generic state
        self._last_game_state = self._mapper.to_game_state(arena_state)
        
        return self._last_game_state
    
    def set_game_state(self, state: GameState) -> None:
        """
        Set game state from generic GameState.
        
        Note: This operation is not fully supported for BattleArena
        as BattleArenaState is mutable. This method will raise
        TypeError if the state type is incompatible.
        
        Args:
            state: GameState to restore
            
        Raises:
            TypeError: If state type is incompatible
        """
        if not isinstance(state, BattleArenaGameState):
            raise TypeError(
                f"Cannot convert {type(state).__name__} to BattleArenaState"
            )
        
        # For full implementation, would need to convert back
        # and set individual fields. This is a limitation of
        # BattleArena's mutable state design.
        raise NotImplementedError(
            "set_game_state is not fully supported for BattleArena. "
            "Use BattleArena.set_state() directly for state restoration."
        )
    
    def get_observation_provider(self) -> ObservationProvider | None:
        """
        Get the observation provider for this adapter.
        
        Returns:
            None - BattleArena uses internal observation system
        """
        # BattleArena has its own internal observation system
        # This adapter is primarily for state access
        return None
    
    def get_reward_provider(self) -> RewardProvider | None:
        """
        Get the reward provider for this adapter.
        
        Returns:
            None - BattleArena uses internal reward system
        """
        # BattleArena has its own internal reward system
        # This adapter is primarily for state access
        return None
    
    # Convenience methods for direct BattleArena access
    
    @property
    def action_space(self) -> Any:
        """Get the action space from the engine."""
        return self._engine.action_space
    
    @property
    def observation_space(self) -> Any:
        """Get the observation space from the engine."""
        return self._engine.observation_space
    
    def reset(self, seed: int | None = None) -> tuple[np.ndarray, dict]:
        """
        Reset the environment.
        
        Args:
            seed: Random seed
            
        Returns:
            Initial observation and info dict
        """
        return self._engine.reset(seed=seed)
    
    def step(self, action: Any) -> tuple[np.ndarray, float, bool, bool, dict]:
        """
        Execute one environment step.
        
        Args:
            action: Action to execute
            
        Returns:
            observation, reward, terminated, truncated, info
        """
        return self._engine.step(action)
    
    def close(self) -> None:
        """Close the adapter and release resources."""
        self._engine.close()
        self._last_game_state = None
    
    def __repr__(self) -> str:
        return f"BattleArenaAdapter(engine={self._engine!r})"
