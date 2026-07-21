"""
Adapter Factory

This module provides the AdapterFactory class for registering
and creating game adapters.
"""

from __future__ import annotations

from typing import Any, Callable

from zbgym.interfaces import GameAdapter


class AdapterFactory:
    """
    Factory for creating game adapters.
    
    This factory follows the registry pattern for pluggable adapters.
    New game adapters can be registered without modifying this class.
    
    Example:
        >>> from zbgym.adapters import AdapterFactory
        >>> 
        >>> # Create adapter
        >>> adapter = AdapterFactory.create('BattleArena-v1')
        >>> 
        >>> # Register new adapter
        >>> def create_moba_adapter(**kwargs):
        ...     return MOBAAttackAdapter(**kwargs)
        >>> 
        >>> AdapterFactory.register('MOBAAttack-v1', create_moba_adapter)
    """
    
    # Registry of adapter creators
    _adapters: dict[str, Callable[..., GameAdapter]] = {}
    
    @classmethod
    def register(
        cls,
        env_id: str,
        adapter_class: type[GameAdapter] | Callable[..., GameAdapter],
    ) -> None:
        """
        Register an adapter for an environment ID.
        
        Args:
            env_id: Environment ID (e.g., 'BattleArena-v1')
            adapter_class: Adapter class or factory function
            
        Example:
            >>> AdapterFactory.register('BattleArena-v1', BattleArenaAdapter)
            >>> AdapterFactory.register('Zooba-v1', ZoobaAdapter)
        """
        cls._adapters[env_id] = adapter_class
    
    @classmethod
    def create(cls, env_id: str, **kwargs) -> GameAdapter:
        """
        Create an adapter for the given environment.
        
        Args:
            env_id: Environment ID
            **kwargs: Arguments to pass to the adapter
            
        Returns:
            GameAdapter instance
            
        Raises:
            KeyError: If no adapter is registered for the env_id
            
        Example:
            >>> adapter = AdapterFactory.create('BattleArena-v1')
            >>> adapter = AdapterFactory.create('BattleArena-v1', render_mode='human')
        """
        if env_id not in cls._adapters:
            available = ", ".join(cls._adapters.keys()) or "none"
            raise KeyError(
                f"No adapter registered for '{env_id}'. "
                f"Available adapters: {available}"
            )
        
        adapter_class = cls._adapters[env_id]
        return adapter_class(**kwargs)
    
    @classmethod
    def list_adapters(cls) -> list[str]:
        """
        List all registered adapter environment IDs.
        
        Returns:
            List of environment IDs
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def is_registered(cls, env_id: str) -> bool:
        """
        Check if an adapter is registered for the given environment.
        
        Args:
            env_id: Environment ID
            
        Returns:
            True if registered, False otherwise
        """
        return env_id in cls._adapters
    
    @classmethod
    def unregister(cls, env_id: str) -> None:
        """
        Unregister an adapter.
        
        Args:
            env_id: Environment ID
            
        Raises:
            KeyError: If no adapter is registered for the env_id
        """
        if env_id not in cls._adapters:
            raise KeyError(f"No adapter registered for '{env_id}'")
        del cls._adapters[env_id]


# Register built-in adapters
def _register_builtin_adapters() -> None:
    """Register the built-in BattleArena adapter."""
    from zbgym.adapters.battle_arena import BattleArenaAdapter
    
    AdapterFactory.register("BattleArena-v1", BattleArenaAdapter)
    
    # ZoobaAdapter is the same as BattleArenaAdapter with default config
    AdapterFactory.register("Zooba-v1", BattleArenaAdapter)


# Register adapters on module import
_register_builtin_adapters()
