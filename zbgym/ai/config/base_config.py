"""
AI Configuration

Base configuration for AI agents and systems.
All AI configurations should inherit from this class.

Example:
    >>> config = AIConfig(
    ...     tick_rate=60.0,
    ...     vision_radius=500.0,
    ...     reaction_time=0.15,
    ...     seed=42,
    ... )
    >>> agent = MyAgent(config=config)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIConfig:
    """
    Base configuration for AI systems.
    
    Attributes:
        tick_rate: AI update frequency (Hz)
        vision_radius: Maximum perception distance
        reaction_time: Minimum time between decisions (seconds)
        decision_frequency: How often to make decisions (every N ticks)
        planning_frequency: How often to run planning (every N ticks)
        memory_size: Maximum memory entries
        seed: Random seed for determinism
        deterministic: Whether to use deterministic mode
        debug: Enable debug logging
    """
    
    # Timing
    tick_rate: float = 60.0
    reaction_time: float = 0.1  # seconds
    decision_frequency: int = 1  # Every tick
    planning_frequency: int = 10  # Every 10 ticks
    
    # Perception
    vision_radius: float = 500.0
    
    # Memory
    memory_size: int = 100
    
    # Determinism
    seed: int | None = None
    deterministic: bool = True
    
    # Debug
    debug: bool = False
    
    # Additional parameters
    extra: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.tick_rate <= 0:
            raise ValueError(f"tick_rate must be positive, got {self.tick_rate}")
        if self.vision_radius <= 0:
            raise ValueError(f"vision_radius must be positive, got {self.vision_radius}")
        if self.memory_size <= 0:
            raise ValueError(f"memory_size must be positive, got {self.memory_size}")
        if self.decision_frequency <= 0:
            raise ValueError(
                f"decision_frequency must be positive, got {self.decision_frequency}"
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key, default)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tick_rate": self.tick_rate,
            "reaction_time": self.reaction_time,
            "decision_frequency": self.decision_frequency,
            "planning_frequency": self.planning_frequency,
            "vision_radius": self.vision_radius,
            "memory_size": self.memory_size,
            "seed": self.seed,
            "deterministic": self.deterministic,
            "debug": self.debug,
            "extra": self.extra,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AIConfig:
        """Create from dictionary."""
        known_fields = {
            "tick_rate", "reaction_time", "decision_frequency",
            "planning_frequency", "vision_radius", "memory_size",
            "seed", "deterministic", "debug"
        }
        # Handle both nested and flat extra
        if "extra" in data:
            extra = dict(data["extra"]) if data["extra"] else {}
        else:
            extra = {k: v for k, v in data.items() if k not in known_fields}
        
        known = {k: v for k, v in data.items() if k in known_fields}
        known["extra"] = extra
        return cls(**known)
