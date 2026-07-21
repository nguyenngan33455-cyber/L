"""
ZBGym AI Foundation Package

A generic, game-agnostic AI framework for ZBGym that provides
the foundation for intelligent NPCs, scripted bots, rule-based agents,
and future reinforcement learning agents.

Architecture:
    - core/        : Base interfaces and protocols
    - agents/      : Agent implementations
    - behaviors/   : Behavior definitions
    - planners/    : Planning systems
    - perception/   : Perception systems
    - targeting/   : Target selection
    - blackboard/  : Shared knowledge system
    - memory/      : Memory systems
    - registry/     : Agent registry
    - config/       : Configuration
    - exceptions/   : Custom exceptions

Example:
    >>> from zbgym.ai import AIAgent, AIController
    >>> from zbgym.ai.agents import RandomAgent
    >>> from zbgym.ai.registry import AIRegistry
    >>> 
    >>> # Create agent
    >>> agent = RandomAgent(agent_id="bot_1")
    >>> 
    >>> # Use with registry
    >>> registry = AIRegistry()
    >>> registry.register("random_bot", RandomAgent)
"""

from zbgym.ai.core.agent import AIAgent
from zbgym.ai.core.controller import AIController
from zbgym.ai.core.types import (
    ActionRequest,
    ActionResult,
    DecisionContext,
    PerceptionResult,
)
from zbgym.ai.blackboard.blackboard import Blackboard, BlackboardEntry
from zbgym.ai.memory.memory import Memory, MemoryEntry
from zbgym.ai.registry.registry import AIRegistry

__all__ = [
    # Core
    "AIAgent",
    "AIController",
    "ActionRequest",
    "ActionResult",
    "DecisionContext",
    "PerceptionResult",
    # Blackboard
    "Blackboard",
    "BlackboardEntry",
    # Memory
    "Memory",
    "MemoryEntry",
    # Registry
    "AIRegistry",
]

__version__ = "0.1.0"