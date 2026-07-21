"""
AI Core Package

Provides base interfaces and protocols for the AI system.

Interfaces:
    - AIAgent: Base agent interface
    - AIController: Agent controller interface
    - DecisionModule: Decision-making interface
    - Sensor: Perception interface
    - Actuator: Action interface
"""

from zbgym.ai.core.agent import AIAgent
from zbgym.ai.core.controller import AIController
from zbgym.ai.core.decision import DecisionModule

__all__ = ["AIAgent", "AIController", "DecisionModule"]
