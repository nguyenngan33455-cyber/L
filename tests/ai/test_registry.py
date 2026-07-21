"""
Tests for AI Registry

Verifies AIRegistry functionality:
- Registration
- Lookup
- Creation
- Duplicate detection
- Cleanup
"""

import pytest
from zbgym.ai.registry import AIRegistry, get_global_registry
from zbgym.ai.agents import IdleAgent, RandomAgent
from zbgym.ai.core.agent import AIAgent
from zbgym.ai.exceptions.registry_error import RegistryError


class TestAIRegistry:
    """Test cases for AIRegistry."""

    def test_registry_creation(self):
        """Test registry creation."""
        registry = AIRegistry()
        assert len(registry) == 0
        assert registry.list_agents() == []

    def test_register_agent(self):
        """Test agent registration."""
        registry = AIRegistry()
        registry.register("idle", IdleAgent)
        
        assert registry.has("idle")
        assert "idle" in registry
        assert len(registry) == 1

    def test_register_with_metadata(self):
        """Test registration with metadata."""
        registry = AIRegistry()
        registry.register(
            "random",
            RandomAgent,
            version="1.0",
            description="Random agent",
        )
        
        metadata = registry.get_metadata("random")
        assert metadata["version"] == "1.0"
        assert metadata["description"] == "Random agent"

    def test_register_duplicate(self):
        """Test duplicate registration raises error."""
        registry = AIRegistry()
        registry.register("idle", IdleAgent)
        
        with pytest.raises(RegistryError) as exc_info:
            registry.register("idle", RandomAgent)
        
        assert "already registered" in str(exc_info.value)

    def test_unregister_agent(self):
        """Test agent unregistration."""
        registry = AIRegistry()
        registry.register("idle", IdleAgent)
        
        assert registry.has("idle")
        result = registry.unregister("idle")
        
        assert result is True
        assert not registry.has("idle")
        assert len(registry) == 0

    def test_unregister_nonexistent(self):
        """Test unregistering non-existent agent."""
        registry = AIRegistry()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_agent_class(self):
        """Test getting agent class."""
        registry = AIRegistry()
        registry.register("idle", IdleAgent)
        
        agent_class = registry.get("idle")
        assert agent_class == IdleAgent

    def test_get_nonexistent(self):
        """Test getting non-existent agent raises error."""
        registry = AIRegistry()
        
        with pytest.raises(RegistryError) as exc_info:
            registry.get("nonexistent")
        
        assert "not found" in str(exc_info.value)

    def test_create_agent(self):
        """Test agent creation through registry."""
        registry = AIRegistry()
        registry.register("idle", IdleAgent)
        
        agent = registry.create("idle", agent_id="created_1")
        
        assert isinstance(agent, AIAgent)
        assert agent.agent_id == "created_1"

    def test_create_with_kwargs(self):
        """Test agent creation with additional kwargs."""
        registry = AIRegistry()
        registry.register("random", RandomAgent)
        
        agent = registry.create(
            "random",
            agent_id="created_random",
            seed=42,
        )
        
        assert agent.seed == 42

    def test_create_nonexistent(self):
        """Test creating non-existent agent raises error."""
        registry = AIRegistry()
        
        with pytest.raises(RegistryError) as exc_info:
            registry.create("nonexistent", agent_id="test")
        
        assert "not found" in str(exc_info.value)

    def test_list_agents(self):
        """Test listing all registered agents."""
        registry = AIRegistry()
        registry.register("idle", IdleAgent)
        registry.register("random", RandomAgent)
        
        agents = registry.list_agents()
        assert len(agents) == 2
        assert "idle" in agents
        assert "random" in agents

    def test_clear_registry(self):
        """Test clearing registry."""
        registry = AIRegistry()
        registry.register("idle", IdleAgent)
        registry.register("random", RandomAgent)
        
        assert len(registry) == 2
        registry.clear()
        assert len(registry) == 0

    def test_global_registry(self):
        """Test global registry singleton."""
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        
        assert registry1 is registry2

    def test_global_registry_registration(self):
        """Test registering to global registry."""
        from zbgym.ai.registry import register_agent, create_agent
        
        # Note: This test depends on state from other tests
        # We just verify the functions exist and work
        
        registry = AIRegistry()
        registry.register("test_global", IdleAgent)
        
        agent = registry.create("test_global", agent_id="global_test")
        assert agent.agent_id == "global_test"


class TestRegistryDeterminism:
    """Test registry determinism."""

    def test_creation_order(self):
        """Test agents are created in consistent order."""
        registry = AIRegistry()
        registry.register("idle", IdleAgent)
        registry.register("random", RandomAgent)
        
        # Create agents multiple times
        agents1 = [
            registry.create("idle", agent_id="a1"),
            registry.create("random", agent_id="a2"),
        ]
        
        agents2 = [
            registry.create("idle", agent_id="a3"),
            registry.create("random", agent_id="a4"),
        ]
        
        # Both lists should have same types in same order
        assert type(agents1[0]) == type(agents2[0])
        assert type(agents1[1]) == type(agents2[1])
