"""
AI Sensor Base

Base interface for sensors that perceive the game state.
Sensors extract specific types of information from the environment.

Example:
    >>> class EnemySensor(Sensor):
    ...     def sense(self, context: DecisionContext) -> SensorResult:
    ...         enemies = context.game_state.get_enemies()
    ...         return SensorResult(
    ...             detected=enemies,
    ...             count=len(enemies),
    ...         )
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.ai.core.types import DecisionContext


@dataclass
class SensorResult:
    """
    Result from a sensor.
    
    Attributes:
        detected: List of detected entities/objects
        count: Number of detections
        metadata: Additional sensor data
    """
    
    detected: list = field(default_factory=list)
    count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __bool__(self) -> bool:
        """Return True if anything detected."""
        return self.count > 0


class Sensor(ABC):
    """
    Abstract base class for sensors.
    
    Sensors are pluggable components that extract specific
    information from the game state.
    
    Attributes:
        name: Sensor name
        enabled: Whether sensor is active
    """
    
    def __init__(self, name: str = "Sensor") -> None:
        """
        Initialize sensor.
        
        Args:
            name: Sensor name
        """
        self.name = name
        self.enabled = True
    
    @abstractmethod
    def sense(self, context: DecisionContext) -> SensorResult:
        """
        Perform sensing.
        
        Args:
            context: Current decision context
            
        Returns:
            Sensor result
        """
        ...
    
    def reset(self) -> None:
        """Reset sensor state."""
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
