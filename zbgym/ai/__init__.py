"""
ZBGym AI Foundation Package

A generic, game-agnostic AI framework for ZBGym that provides
the foundation for intelligent NPCs, scripted bots, rule-based agents,
and future reinforcement learning agents.

Architecture:
    - core/         : Base interfaces and protocols
    - agents/       : Agent implementations
    - behaviors/    : Behavior definitions
    - planners/     : Planning systems
    - perception/   : Perception systems
    - targeting/    : Target selection
    - blackboard/   : Shared knowledge system
    - memory/       : Memory systems
    - registry/     : Agent registry
    - scheduler/    : AI execution scheduler
    - action_queue/ : Action queue with validation
    - events/       : AI lifecycle events
    - config/       : Configuration
    - exceptions/   : Custom exceptions

Example:
    >>> from zbgym.ai import AIAgent, AIScheduler, ActionQueue
    >>> from zbgym.ai.agents import RandomAgent
    >>> from zbgym.ai.registry import AIRegistry
    >>> 
    >>> # Create scheduler
    >>> scheduler = AIScheduler(tick_rate=60)
    >>> scheduler.attach_agent("bot_1", RandomAgent(agent_id="bot_1"))
    >>> 
    >>> # Create action queue
    >>> queue = ActionQueue()
    >>> 
    >>> # Game loop
    >>> decisions = scheduler.tick(game_state)
    >>> for agent_id, action in decisions.items():
    ...     queue.enqueue(agent_id, action)
"""

from zbgym.ai.core.agent import AIAgent
from zbgym.ai.core.controller import AIController
from zbgym.ai.core.types import (
    ActionRequest,
    ActionResult,
    ActionType,
    DecisionContext,
    PerceptionResult,
)
from zbgym.ai.blackboard.blackboard import Blackboard, BlackboardEntry
from zbgym.ai.memory.memory import Memory, MemoryEntry
from zbgym.ai.registry.registry import AIRegistry
from zbgym.ai.scheduler.scheduler import AIScheduler, AgentUpdateContext
from zbgym.ai.action_queue.queue import ActionQueue, QueuedAction
from zbgym.ai.events.types import AIAgentEvent, AIAgentEventType
from zbgym.ai.config import AIConfig, AgentConfig

__all__ = [
    # Core
    "AIAgent",
    "AIController",
    "ActionRequest",
    "ActionResult",
    "ActionType",
    "DecisionContext",
    "PerceptionResult",
    # Scheduler
    "AIScheduler",
    "AgentUpdateContext",
    # Action Queue
    "ActionQueue",
    "QueuedAction",
    # Events
    "AIAgentEvent",
    "AIAgentEventType",
    # Blackboard
    "Blackboard",
    "BlackboardEntry",
    # Memory
    "Memory",
    "MemoryEntry",
    # Registry
    "AIRegistry",
    # Config
    "AIConfig",
    "AgentConfig",
]

__version__ = "0.2.0"