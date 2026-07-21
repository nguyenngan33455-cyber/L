"""
Agent Configuration

Configuration for specific agent types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from zbgym.ai.config.base_config import AIConfig


@dataclass
class AgentConfig:
    """
    Configuration for an AI agent.
    
    Attributes:
        agent_id: Unique identifier for this agent
        agent_type: Type of agent (e.g., "random", "rule_based")
        ai_config: Base AI configuration
        team_id: Team assignment (if applicable)
        spawn_position: Initial spawn position
        personality: Agent personality parameters
    """
    
    agent_id: str
    agent_type: str = "base"
    ai_config: AIConfig = field(default_factory=AIConfig)
    team_id: str | None = None
    spawn_position: tuple[float, float] | None = None
    personality: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.agent_id:
            raise ValueError("agent_id cannot be empty")
        if not self.agent_type:
            raise ValueError("agent_type cannot be empty")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "ai_config": self.ai_config.to_dict(),
            "team_id": self.team_id,
            "spawn_position": self.spawn_position,
            "personality": self.personality,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentConfig:
        """Create from dictionary."""
        ai_config_data = data.get("ai_config", {})
        ai_config = AIConfig.from_dict(ai_config_data) if ai_config_data else AIConfig()
        return cls(
            agent_id=data["agent_id"],
            agent_type=data.get("agent_type", "base"),
            ai_config=ai_config,
            team_id=data.get("team_id"),
            spawn_position=data.get("spawn_position"),
            personality=data.get("personality", {}),
        )
