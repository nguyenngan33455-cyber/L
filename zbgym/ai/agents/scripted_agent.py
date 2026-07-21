"""
Scripted Agent

An AI agent that follows predefined scripts.
Actions are determined by scripts, not AI logic.

Example:
    >>> # Create patrol script
    >>> def patrol(context):
    ...     return ActionRequest(ActionType.PATROL, target_position=(100, 200))
    >>> 
    >>> # Create attack script
    >>> def attack(context):
    ...     enemies = context.get_visible_enemies()
    ...     if enemies:
    ...         return ActionRequest(ActionType.ATTACK, target_id=enemies[0].id)
    ...     return None
    >>> 
    >>> # Create scripted agent
    >>> agent = ScriptedAgent(
    ...     agent_id="bot_1",
    ...     scripts=[patrol, attack],
    ...     priority="first_match",
    ... )
"""

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from zbgym.ai.agents.base_agent import BaseAgent
from zbgym.ai.core.types import (
    ActionRequest,
    ActionType,
    DecisionContext,
)
from zbgym.ai.exceptions.agent_error import AgentError

if TYPE_CHECKING:
    from zbgym.interfaces import GameState


ScriptFunction = Callable[[DecisionContext], ActionRequest | None]


class ScriptedAgent(BaseAgent):
    """
    Agent that follows predefined scripts.
    
    Scripts are functions that take a DecisionContext and return
    an ActionRequest or None (to continue to next script).
    
    Attributes:
        scripts: List of script functions
        priority: How to handle multiple matches
            - "first_match": Return first non-None result
            - "highest_priority": Return action with highest priority
    """
    
    def __init__(
        self,
        agent_id: str,
        scripts: list[ScriptFunction] | None = None,
        priority: str = "first_match",
        seed: int | None = None,
    ) -> None:
        """
        Initialize scripted agent.
        
        Args:
            agent_id: Unique agent identifier
            scripts: List of script functions
            priority: Script execution priority
            seed: Random seed
        """
        from zbgym.ai.config.base_config import AIConfig
        
        config = AIConfig(seed=seed)
        super().__init__(agent_id, config=config)
        
        self.scripts = scripts or []
        self.priority = priority
        
        if priority not in ("first_match", "highest_priority"):
            raise AgentError(
                f"Invalid priority: {priority}",
                agent_id=agent_id,
            )
    
    def add_script(self, script: ScriptFunction) -> None:
        """Add a script to the agent."""
        self.scripts.append(script)
    
    def remove_script(self, script: ScriptFunction) -> bool:
        """Remove a script from the agent."""
        if script in self.scripts:
            self.scripts.remove(script)
            return True
        return False
    
    def think_impl(self, context: DecisionContext) -> ActionRequest:
        """
        Execute scripts and return action.
        
        Args:
            context: Decision context
            
        Returns:
            First matching action or idle
        """
        if not self.scripts:
            return ActionRequest(ActionType.IDLE)
        
        if self.priority == "first_match":
            for script in self.scripts:
                result = script(context)
                if result is not None:
                    return result
            return ActionRequest(ActionType.IDLE)
        
        elif self.priority == "highest_priority":
            best_action: ActionRequest | None = None
            best_priority = -1.0
            
            for script in self.scripts:
                result = script(context)
                if result is not None and result.priority > best_priority:
                    best_action = result
                    best_priority = result.priority
            
            if best_action is None:
                return ActionRequest(ActionType.IDLE)
            
            return best_action
        
        return ActionRequest(ActionType.IDLE)


# Predefined script helpers

def script_patrol(
    position: tuple[float, float] | None = None,
    radius: float = 50.0,
) -> ScriptFunction:
    """
    Create a patrol script.
    
    Args:
        position: Center position to patrol
        radius: Patrol radius
        
    Returns:
        Script function
    """
    def patrol(context: DecisionContext) -> ActionRequest | None:
        if context.agent_position is None:
            return None
        
        # Simple circular patrol - offset from current position
        import numpy as np
        
        if position is None:
            target = context.agent_position
        else:
            target = np.array(position) + np.array([
                np.cos(context.tick * 0.1) * radius,
                np.sin(context.tick * 0.1) * radius,
            ])
        
        return ActionRequest(
            action_type=ActionType.PATROL,
            target_position=target,
            priority=0.5,
        )
    
    return patrol


def script_attack_nearest(
    attack_range: float = 100.0,
) -> ScriptFunction:
    """
    Create an attack script targeting nearest enemy.
    
    Args:
        attack_range: Maximum attack range
        
    Returns:
        Script function
    """
    def attack(context: DecisionContext) -> ActionRequest | None:
        enemies = context.get_visible_enemies()
        
        if not enemies:
            return None
        
        # Find nearest enemy
        nearest = None
        nearest_dist = float('inf')
        
        for enemy in enemies:
            if hasattr(enemy, 'position') and enemy.position:
                dist = context.agent_position.distance_to(enemy.position)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = enemy
        
        if nearest is None:
            return None
        
        # Attack if in range
        if nearest_dist <= attack_range:
            return ActionRequest(
                action_type=ActionType.ATTACK,
                target_id=nearest.id,
                priority=0.8,
            )
        
        # Move toward enemy
        return ActionRequest(
            action_type=ActionType.MOVE,
            target_id=nearest.id,
            priority=0.7,
        )
    
    return attack


def script_flee_low_health(
    health_threshold: float = 0.3,
) -> ScriptFunction:
    """
    Create a flee script for low health.
    
    Args:
        health_threshold: Health percentage to flee at
        
    Returns:
        Script function
    """
    def flee(context: DecisionContext) -> ActionRequest | None:
        player = context.game_state.get_player(context.agent_id)
        
        if player is None:
            return None
        
        # Check health
        from zbgym.constants import MAX_HEALTH
        health_pct = player.health / MAX_HEALTH if MAX_HEALTH > 0 else 1.0
        
        if health_pct < health_threshold:
            # Flee from nearest enemy
            enemies = context.get_visible_enemies()
            if enemies:
                # Get direction away from enemies
                flee_dir = None
                for enemy in enemies:
                    if hasattr(enemy, 'position') and enemy.position:
                        dir_away = context.agent_position - enemy.position
                        if flee_dir is None:
                            flee_dir = dir_away
                        else:
                            flee_dir = flee_dir + dir_away
                
                if flee_dir is not None:
                    flee_dir = flee_dir / max(1, flee_dir.length)
                    target = context.agent_position + flee_dir * 100
                    
                    return ActionRequest(
                        action_type=ActionType.FLEE,
                        target_position=target,
                        priority=0.9,
                    )
        
        return None
    
    return flee
