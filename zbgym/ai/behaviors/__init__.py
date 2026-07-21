"""
AI Behaviors Package

Provides behavior definitions and utilities.
This package is for future behavior tree and FSM implementations.

Planned components:
- BehaviorTree: Behavior tree structure
- BehaviorNode: Base behavior node
- CompositeNodes: Sequence, Selector, Parallel
- LeafNodes: Action, Condition, Decorator
- FSM: Finite State Machine
"""

from zbgym.ai.behaviors.behavior import Behavior, BehaviorStatus

__all__ = ["Behavior", "BehaviorStatus"]
