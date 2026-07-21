"""
AI Perception Package

Provides perception systems for AI agents.
Perception processes game state into actionable information.

Components:
- Sensor: Base sensor interface
- PerceptionModule: Perception processing
- VisualPerception: Line-of-sight based perception
- AudioPerception: Sound-based perception
"""

from zbgym.ai.perception.sensor import Sensor, SensorResult
from zbgym.ai.perception.module import PerceptionModule

__all__ = ["Sensor", "SensorResult", "PerceptionModule"]
