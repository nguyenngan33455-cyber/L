"""
Tests for AI Configuration

Verifies AIConfig and AgentConfig:
- Validation
- Defaults
- Serialization
- Boundary values
"""

import pytest
from zbgym.ai.config import AIConfig, AgentConfig


class TestAIConfig:
    """Test cases for AIConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AIConfig()
        
        assert config.tick_rate == 60.0
        assert config.vision_radius == 500.0
        assert config.reaction_time == 0.1
        assert config.decision_frequency == 1
        assert config.planning_frequency == 10
        assert config.memory_size == 100
        assert config.seed is None
        assert config.deterministic is True
        assert config.debug is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = AIConfig(
            tick_rate=30.0,
            vision_radius=1000.0,
            seed=42,
            deterministic=True,
        )
        
        assert config.tick_rate == 30.0
        assert config.vision_radius == 1000.0
        assert config.seed == 42

    def test_invalid_tick_rate(self):
        """Test invalid tick rate raises error."""
        with pytest.raises(ValueError) as exc_info:
            AIConfig(tick_rate=0)
        assert "positive" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            AIConfig(tick_rate=-1)
        assert "positive" in str(exc_info.value)

    def test_invalid_vision_radius(self):
        """Test invalid vision radius raises error."""
        with pytest.raises(ValueError) as exc_info:
            AIConfig(vision_radius=0)
        assert "positive" in str(exc_info.value)

    def test_invalid_memory_size(self):
        """Test invalid memory size raises error."""
        with pytest.raises(ValueError) as exc_info:
            AIConfig(memory_size=0)
        assert "positive" in str(exc_info.value)

    def test_invalid_decision_frequency(self):
        """Test invalid decision frequency raises error."""
        with pytest.raises(ValueError) as exc_info:
            AIConfig(decision_frequency=0)
        assert "positive" in str(exc_info.value)

    def test_get_method(self):
        """Test get method for configuration values."""
        config = AIConfig(seed=42, tick_rate=30.0)
        
        assert config.get("seed") == 42
        assert config.get("tick_rate") == 30.0
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"

    def test_extra_parameters(self):
        """Test extra parameters."""
        config = AIConfig(extra={"custom": "value"})
        
        assert config.extra["custom"] == "value"
        assert config.get("custom") == "value"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = AIConfig(seed=42, tick_rate=30.0)
        data = config.to_dict()
        
        assert data["seed"] == 42
        assert data["tick_rate"] == 30.0
        assert "deterministic" in data
        assert "extra" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "seed": 123,
            "tick_rate": 45.0,
            "vision_radius": 800.0,
            "custom_param": "test",
        }
        
        config = AIConfig.from_dict(data)
        
        assert config.seed == 123
        assert config.tick_rate == 45.0
        assert config.vision_radius == 800.0
        assert config.extra["custom_param"] == "test"

    def test_roundtrip_serialization(self):
        """Test serialization roundtrip."""
        original = AIConfig(
            seed=999,
            tick_rate=120.0,
            vision_radius=750.0,
            decision_frequency=5,
            deterministic=False,
            extra={"key": "value"},
        )
        
        data = original.to_dict()
        restored = AIConfig.from_dict(data)
        
        assert restored.seed == original.seed
        assert restored.tick_rate == original.tick_rate
        assert restored.vision_radius == original.vision_radius
        assert restored.decision_frequency == original.decision_frequency
        assert restored.deterministic == original.deterministic
        assert restored.extra["key"] == "value"


class TestAgentConfig:
    """Test cases for AgentConfig."""

    def test_default_agent_config(self):
        """Test default agent configuration."""
        config = AgentConfig(agent_id="test")
        
        assert config.agent_id == "test"
        assert config.agent_type == "base"
        assert config.team_id is None
        assert config.spawn_position is None
        assert isinstance(config.ai_config, AIConfig)

    def test_custom_agent_config(self):
        """Test custom agent configuration."""
        config = AgentConfig(
            agent_id="custom_agent",
            agent_type="random",
            team_id="red",
            spawn_position=(100, 200),
        )
        
        assert config.agent_id == "custom_agent"
        assert config.agent_type == "random"
        assert config.team_id == "red"
        assert config.spawn_position == (100, 200)

    def test_agent_config_with_ai_config(self):
        """Test agent config with custom AI config."""
        ai_config = AIConfig(seed=42, vision_radius=1000.0)
        config = AgentConfig(
            agent_id="with_ai",
            ai_config=ai_config,
        )
        
        assert config.ai_config.seed == 42
        assert config.ai_config.vision_radius == 1000.0

    def test_empty_agent_id(self):
        """Test empty agent ID raises error."""
        with pytest.raises(ValueError) as exc_info:
            AgentConfig(agent_id="")
        assert "cannot be empty" in str(exc_info.value)

    def test_empty_agent_type(self):
        """Test empty agent type raises error."""
        with pytest.raises(ValueError) as exc_info:
            AgentConfig(agent_id="test", agent_type="")
        assert "cannot be empty" in str(exc_info.value)

    def test_personality(self):
        """Test personality parameters."""
        config = AgentConfig(
            agent_id="personality_test",
            personality={
                "aggression": 0.8,
                "caution": 0.3,
            },
        )
        
        assert config.personality["aggression"] == 0.8
        assert config.personality["caution"] == 0.3

    def test_agent_config_to_dict(self):
        """Test agent config serialization."""
        config = AgentConfig(
            agent_id="serialize_test",
            agent_type="rule_based",
            team_id="blue",
        )
        
        data = config.to_dict()
        
        assert data["agent_id"] == "serialize_test"
        assert data["agent_type"] == "rule_based"
        assert data["team_id"] == "blue"

    def test_agent_config_from_dict(self):
        """Test agent config deserialization."""
        data = {
            "agent_id": "deserialize_test",
            "agent_type": "random",
            "team_id": "green",
            "spawn_position": (50, 75),
        }
        
        config = AgentConfig.from_dict(data)
        
        assert config.agent_id == "deserialize_test"
        assert config.agent_type == "random"
        assert config.team_id == "green"
        assert config.spawn_position == (50, 75)


class TestConfigBoundary:
    """Test boundary values for configuration."""

    def test_minimum_tick_rate(self):
        """Test minimum valid tick rate."""
        config = AIConfig(tick_rate=0.001)
        assert config.tick_rate == 0.001

    def test_large_values(self):
        """Test large configuration values."""
        config = AIConfig(
            tick_rate=10000.0,
            vision_radius=100000.0,
            memory_size=1000000,
        )
        
        assert config.tick_rate == 10000.0
        assert config.vision_radius == 100000.0
        assert config.memory_size == 1000000

    def test_decimal_values(self):
        """Test decimal values."""
        config = AIConfig(
            reaction_time=0.001,
            vision_radius=0.5,
        )
        
        assert config.reaction_time == 0.001
        assert config.vision_radius == 0.5
