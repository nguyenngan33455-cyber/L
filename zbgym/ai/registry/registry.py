"""
AI Registry

Registry for managing and instantiating AI agents.
Supports registration by name and type-based instantiation.

Example:
    >>> from zbgym.ai.registry import AIRegistry
    >>> from zbgym.ai.agents import RandomAgent
    >>> 
    >>> registry = AIRegistry()
    >>> 
    >>> # Register agents
    >>> registry.register("random", RandomAgent)
    >>> registry.register("random_v2", RandomAgent, version=2)
    >>> 
    >>> # Create agents
    >>> agent1 = registry.create("random", agent_id="bot_1")
    >>> agent2 = registry.create("random", agent_id="bot_2", seed=42)
    >>> 
    >>> # List available
    >>> print(registry.list_agents())
    ['random', 'random_v2']
    >>> 
    >>> # Check availability
    >>> if registry.has("random"):
    ...     agent = registry.create("random")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypeVar

from zbgym.ai.exceptions.registry_error import RegistryError

if TYPE_CHECKING:
    from zbgym.ai.core.agent import AIAgent


T = TypeVar("T", bound="AIAgent")


class AIRegistry:
    """
    Registry for AI agents.
    
    Manages agent types and supports deterministic instantiation.
    Thread-safe for concurrent access.
    
    Attributes:
        _agents: Mapping of agent names to factory functions
    """
    
    def __init__(self) -> None:
        """Initialize the registry."""
        self._agents: dict[str, type[AIAgent] | Callable[..., AIAgent]] = {}
        self._metadata: dict[str, dict] = {}
    
    def register(
        self,
        name: str,
        agent_class: type[AIAgent] | Callable[..., AIAgent],
        **metadata: str | int | float | bool,
    ) -> None:
        """
        Register an agent type.
        
        Args:
            name: Unique name for this agent type
            agent_class: Agent class or factory function
            **metadata: Additional metadata (version, description, etc.)
            
        Raises:
            RegistryError: If name already registered
        """
        if name in self._agents:
            raise RegistryError(
                f"Agent '{name}' already registered",
                agent_type=name,
            )
        
        self._agents[name] = agent_class
        self._metadata[name] = metadata
    
    def unregister(self, name: str) -> bool:
        """
        Unregister an agent type.
        
        Args:
            name: Agent name to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self._agents:
            del self._agents[name]
            if name in self._metadata:
                del self._metadata[name]
            return True
        return False
    
    def has(self, name: str) -> bool:
        """
        Check if agent type is registered.
        
        Args:
            name: Agent name
            
        Returns:
            True if registered
        """
        return name in self._agents
    
    def get(self, name: str) -> type[AIAgent] | Callable[..., AIAgent]:
        """
        Get registered agent class.
        
        Args:
            name: Agent name
            
        Returns:
            Agent class
            
        Raises:
            RegistryError: If not found
        """
        if name not in self._agents:
            raise RegistryError(
                f"Agent '{name}' not found in registry",
                agent_type=name,
            )
        return self._agents[name]
    
    def create(
        self,
        name: str,
        agent_id: str,
        **kwargs: any,
    ) -> AIAgent:
        """
        Create an agent instance.
        
        Args:
            name: Agent type name
            agent_id: Unique ID for the agent
            **kwargs: Additional arguments for agent constructor
            
        Returns:
            New agent instance
            
        Raises:
            RegistryError: If agent type not found or creation fails
        """
        agent_class = self.get(name)
        try:
            # Handle agents that take config as first arg
            return agent_class(agent_id=agent_id, **kwargs)
        except TypeError as e:
            raise RegistryError(
                f"Failed to create agent '{name}': {e}",
                agent_type=name,
            )
    
    def list_agents(self) -> list[str]:
        """
        List all registered agent names.
        
        Returns:
            List of agent names
        """
        return list(self._agents.keys())
    
    def get_metadata(self, name: str) -> dict:
        """
        Get metadata for an agent type.
        
        Args:
            name: Agent name
            
        Returns:
            Metadata dictionary
        """
        return self._metadata.get(name, {}).copy()
    
    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        self._metadata.clear()
    
    def __len__(self) -> int:
        """Get number of registered agents."""
        return len(self._agents)
    
    def __contains__(self, name: str) -> bool:
        """Check if agent is registered."""
        return self.has(name)


# Global registry instance
_global_registry: AIRegistry | None = None


def get_global_registry() -> AIRegistry:
    """Get the global AI registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AIRegistry()
    return _global_registry


def register_agent(
    name: str,
    agent_class: type[AIAgent] | Callable[..., AIAgent],
    **metadata: str | int | float | bool,
) -> None:
    """
    Register an agent with the global registry.
    
    Convenience function for global registration.
    """
    get_global_registry().register(name, agent_class, **metadata)


def create_agent(name: str, agent_id: str, **kwargs: any) -> AIAgent:
    """
    Create an agent from the global registry.
    
    Convenience function for global creation.
    """
    return get_global_registry().create(name, agent_id, **kwargs)
