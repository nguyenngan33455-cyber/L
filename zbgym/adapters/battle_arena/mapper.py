"""
BattleArena State Mapper

This module provides the BattleArenaStateMapper class that converts
BattleArenaState to BattleArenaGameState.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zbgym.adapters.battle_arena.state import (
    BattleArenaGameState,
    BattleArenaPlayer,
    BattleArenaTeam,
    BattleArenaZone,
    BattleArenaMap,
)
from zbgym.interfaces import Vector2D

if TYPE_CHECKING:
    from zbgym.env.battle_arena import BattleArenaState, CharacterState


class BattleArenaStateMapper:
    """
    Maps BattleArenaState to BattleArenaGameState.
    
    This mapper is deterministic - same input always produces same output.
    Thread-safe as all mapping operations are stateless.
    
    Example:
        >>> mapper = BattleArenaStateMapper()
        >>> game_state = mapper.to_game_state(arena_state)
    """
    
    def to_game_state(self, arena_state: BattleArenaState) -> BattleArenaGameState:
        """
        Convert BattleArenaState to BattleArenaGameState.
        
        Args:
            arena_state: The BattleArenaState to convert
            
        Returns:
            BattleArenaGameState instance
        """
        # Map players
        players = tuple(
            self._map_character(char_state)
            for char_state in arena_state.characters.values()
        )
        
        # Map teams
        teams = self._map_teams(arena_state, players)
        
        # Map zones
        zones = self._map_zones(arena_state)
        
        # Create map
        game_map = BattleArenaMap(
            width=2000.0,  # Default arena width
            height=2000.0,  # Default arena height
            zones=zones,
        )
        
        return BattleArenaGameState(
            _tick=arena_state.tick,
            _elapsed_time=arena_state.elapsed_time,
            _is_match_active=arena_state.match_active,
            _match_duration=arena_state.match_duration,
            players=players,
            teams=teams,
            map=game_map,
        )
    
    def _map_character(self, char_state: CharacterState) -> BattleArenaPlayer:
        """
        Map CharacterState to BattleArenaPlayer.
        
        Args:
            char_state: Source character state
            
        Returns:
            BattleArenaPlayer instance
        """
        # Get position - BattleArena uses physics.vector.Vector2D
        char_pos = char_state.position
        position = Vector2D(x=float(char_pos.x), y=float(char_pos.y))
        
        # Get velocity
        char_vel = char_state.velocity
        velocity = Vector2D(x=float(char_vel.x), y=float(char_vel.y))
        
        # Convert cooldowns to frozen tuple
        cooldowns = tuple(
            (key, float(value))
            for key, value in char_state.ability_cooldowns.items()
        )
        
        return BattleArenaPlayer(
            id=char_state.id,
            pos=position,
            vel=velocity,
            is_alive=char_state.is_alive,
            team_id=char_state.team if char_state.team != "none" else None,
            _health_current=char_state.health,
            _health_max=100.0,  # Default max health
            _shield=char_state.shield,
            _energy=char_state.energy,
            kills=char_state.kills,
            deaths=char_state.deaths,
            assists=char_state.assists,
            damage_dealt=char_state.damage_dealt,
            damage_taken=char_state.damage_taken,
            healing=char_state.healing,
            ability_cooldowns=cooldowns,
        )
    
    def _map_teams(
        self,
        arena_state: BattleArenaState,
        players: tuple[BattleArenaPlayer, ...]
    ) -> tuple[BattleArenaTeam, ...]:
        """
        Map teams from arena state and players.
        
        Args:
            arena_state: Source arena state
            players: Already mapped players
            
        Returns:
            Tuple of BattleArenaTeam
        """
        teams_dict: dict[str, list[str]] = {}
        
        # Group players by team
        for player in players:
            team_id = player.team_id or "none"
            if team_id not in teams_dict:
                teams_dict[team_id] = []
            teams_dict[team_id].append(player.id)
        
        # Get scores from arena state
        scores = arena_state.scores or {}
        
        # Create team objects
        teams = []
        for team_id, player_ids in teams_dict.items():
            team = BattleArenaTeam(
                team_id=team_id,
                name=self._get_team_name(team_id),
                score=scores.get(team_id, 0),
                _player_ids=tuple(player_ids),
            )
            teams.append(team)
        
        return tuple(teams)
    
    def _map_zones(self, arena_state: BattleArenaState) -> tuple[BattleArenaZone, ...]:
        """
        Map zones from arena state.
        
        Args:
            arena_state: Source arena state
            
        Returns:
            Tuple of BattleArenaZone
        """
        zones = []
        
        # Safe zone
        safe_center = arena_state.safe_zone_center
        safe_center_iv = Vector2D(
            x=float(safe_center.x),
            y=float(safe_center.y)
        )
        safe_zone = BattleArenaZone(
            zone_id="safe_zone",
            _center=safe_center_iv,
            _radius=float(arena_state.safe_zone_radius),
            _danger_level=0.0,  # Safe zone has no danger
        )
        zones.append(safe_zone)
        
        # Danger zone
        danger_zone = BattleArenaZone(
            zone_id="danger_zone",
            _center=safe_center_iv,  # Same center
            _radius=float(arena_state.danger_zone_radius),
            _danger_level=1.0,  # Full danger
        )
        zones.append(danger_zone)
        
        return tuple(zones)
    
    def _get_team_name(self, team_id: str) -> str:
        """Get display name for team."""
        team_names = {
            "red": "Red Team",
            "blue": "Blue Team",
            "green": "Green Team",
            "yellow": "Yellow Team",
            "none": "No Team",
        }
        return team_names.get(team_id, f"Team {team_id}")
