"""
AI Perception Module

Combines multiple sensors into a perception system.
Processes game state through sensors to produce perception results.

Example:
    >>> from zbgym.ai.perception import PerceptionModule, Sensor
    >>> 
    >>> # Create module
    >>> module = PerceptionModule(vision_radius=500.0)
    >>> 
    >>> # Add sensors
    >>> module.add_sensor(EnemySensor())
    >>> module.add_sensor(ItemSensor())
    >>> 
    >>> # Process game state
    >>> result = module.perceive(game_state, agent_id)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zbgym.ai.perception.sensor import Sensor, SensorResult
from zbgym.ai.core.types import PerceptionResult, PerceptionResult as CorePerceptionResult

if TYPE_CHECKING:
    from zbgym.interfaces import GameState, Player, Vector2D


@dataclass
class PerceptionModule:
    """
    Perception processing module.
    
    Combines multiple sensors and processes game state
    into unified perception results.
    
    Attributes:
        vision_radius: Maximum perception distance
        sensors: List of active sensors
    """
    
    vision_radius: float = 500.0
    sensors: list[Sensor] = field(default_factory=list)
    
    def add_sensor(self, sensor: Sensor) -> None:
        """
        Add a sensor to the module.
        
        Args:
            sensor: Sensor to add
        """
        self.sensors.append(sensor)
    
    def remove_sensor(self, sensor: Sensor) -> bool:
        """
        Remove a sensor from the module.
        
        Args:
            sensor: Sensor to remove
            
        Returns:
            True if removed
        """
        if sensor in self.sensors:
            self.sensors.remove(sensor)
            return True
        return False
    
    def perceive(
        self,
        game_state: GameState,
        agent_id: str,
        agent_position: Vector2D | None = None,
    ) -> CorePerceptionResult:
        """
        Process game state through all sensors.
        
        Args:
            game_state: Current game state
            agent_id: Agent ID
            agent_position: Agent's current position
            
        Returns:
            Unified perception result
        """
        from zbgym.ai.core.types import DecisionContext
        
        # Create minimal context for sensors
        context = DecisionContext(
            game_state=game_state,
            perception=CorePerceptionResult(),
            agent_id=agent_id,
            agent_position=agent_position or (game_state.get_player(agent_id).position if game_state.get_player(agent_id) else None),
            tick=game_state.tick,
            elapsed_time=game_state.elapsed_time,
        )
        
        # Process through all sensors
        all_detected = []
        all_threats = []
        all_allies = []
        all_items = []
        
        for sensor in self.sensors:
            if not sensor.enabled:
                continue
            
            result = sensor.sense(context)
            all_detected.extend(result.detected)
            
            # Process sensor-specific data
            if hasattr(result, 'threats'):
                all_threats.extend(result.threats)
            if hasattr(result, 'allies'):
                all_allies.extend(result.allies)
            if hasattr(result, 'items'):
                all_items.extend(result.items)
        
        # Get visible players from game state
        visible_players = self._get_visible_players(
            game_state, agent_id, agent_position
        )
        
        return CorePerceptionResult(
            visible_players=tuple(visible_players),
            visible_positions=(),
            threats=tuple(set(all_threats)),
            allies=tuple(set(all_allies)),
            items=tuple(set(all_items)),
            nearest_enemy_distance=self._calc_nearest_distance(
                visible_players, agent_position, exclude_team=None
            ),
        )
    
    def _get_visible_players(
        self,
        game_state: GameState,
        agent_id: str,
        agent_position: Vector2D | None,
    ) -> list[Player]:
        """Get players within vision range."""
        if agent_position is None:
            return []
        
        visible = []
        agent = game_state.get_player(agent_id)
        agent_team = agent.team_id if agent else None
        
        for player in game_state.players:
            if player.id == agent_id:
                continue
            if not player.is_alive:
                continue
            if hasattr(player, 'position') and player.position:
                dist = agent_position.distance_to(player.position)
                if dist <= self.vision_radius:
                    visible.append(player)
        
        return visible
    
    def _calc_nearest_distance(
        self,
        players: list[Player],
        agent_position: Vector2D | None,
        exclude_team: str | None = None,
    ) -> float | None:
        """Calculate distance to nearest player."""
        if agent_position is None or not players:
            return None
        
        nearest_dist = float('inf')
        for player in players:
            if hasattr(player, 'position') and player.position:
                if exclude_team and hasattr(player, 'team_id') and player.team_id == exclude_team:
                    continue
                dist = agent_position.distance_to(player.position)
                if dist < nearest_dist:
                    nearest_dist = dist
        
        return nearest_dist if nearest_dist < float('inf') else None
    
    def reset(self) -> None:
        """Reset all sensors."""
        for sensor in self.sensors:
            sensor.reset()
