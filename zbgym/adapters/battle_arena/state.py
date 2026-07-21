"""
BattleArena Game State Implementation

This module provides the BattleArenaGameState class that implements
the generic GameState interface for BattleArena.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from zbgym.interfaces import (
    GameState,
    Player,
    Team,
    GameMap,
    Zone,
    Vector2D,
    Health,
    Mana,
    Score,
    Experience,
    GameTime,
)


@dataclass(frozen=True)
class BattleArenaPlayer(Player):
    """
    BattleArena implementation of Player protocol.
    
    Immutable snapshot of a player's state at a point in time.
    
    Note: Uses 'pos' and 'vel' internal fields to avoid conflicts
    with the Player protocol properties.
    """
    
    id: str = ""
    pos: Vector2D = field(default_factory=Vector2D.zero)
    vel: Vector2D = field(default_factory=Vector2D.zero)
    is_alive: bool = True
    team_id: str | None = None
    _health_current: float = 100.0
    _health_max: float = 100.0
    _shield: float = 0.0
    _energy: float = 100.0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    damage_dealt: float = 0.0
    damage_taken: float = 0.0
    healing: float = 0.0
    ability_cooldowns: tuple[tuple[str, float], ...] = field(default_factory=tuple)
    
    @property
    def position(self) -> Vector2D:
        """Get position (Player protocol)."""
        return self.pos
    
    @property
    def velocity(self) -> Vector2D:
        """Get velocity (Player protocol)."""
        return self.vel
    
    @property
    def health(self) -> Health:
        """Get health state."""
        return Health(
            current=self._health_current,
            max=self._health_max,
            regen=0.0  # BattleArena doesn't track regen in state
        )
    
    @property
    def is_active(self) -> bool:
        """Player is active if alive."""
        return self.is_alive


@dataclass(frozen=True)
class BattleArenaTeam(Team):
    """
    BattleArena implementation of Team protocol.
    
    Immutable snapshot of a team's state.
    
    Note: Uses internal fields to avoid conflicts with Team protocol properties.
    """
    
    team_id: str = ""
    name: str = ""
    score: int = 0
    _player_ids: tuple[str, ...] = field(default_factory=tuple)
    
    @property
    def id(self) -> str:
        """Team ID (Team protocol)."""
        return self.team_id
    
    @property
    def player_ids(self) -> tuple[str, ...]:
        """Player IDs (Team protocol)."""
        return self._player_ids


@dataclass(frozen=True)
class BattleArenaZone(Zone):
    """
    BattleArena implementation of Zone protocol.
    
    Represents a circular zone in the arena.
    
    Note: Uses internal fields to avoid conflicts with Zone protocol.
    """
    
    zone_id: str = ""
    _center: Vector2D = field(default_factory=Vector2D.zero)
    _radius: float = 0.0
    _danger_level: float = 0.0  # 0.0 = safe, 1.0 = lethal
    
    @property
    def id(self) -> str:
        """Zone ID (Zone protocol)."""
        return self.zone_id
    
    @property
    def center(self) -> Vector2D:
        """Center (Zone protocol)."""
        return self._center
    
    @property
    def radius(self) -> float:
        """Radius (Zone protocol)."""
        return self._radius
    
    @property
    def danger_level(self) -> float:
        """Danger level (Zone protocol)."""
        return self._danger_level
    
    @property
    def zone_type(self) -> str:
        """Zone type: 'safe' or 'danger'."""
        return "safe" if self._danger_level < 0.5 else "danger"
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within zone."""
        return self._center.distance_to(Vector2D(x=x, y=y)) <= self._radius


@dataclass(frozen=True)
class BattleArenaMap(GameMap):
    """
    BattleArena implementation of GameMap protocol.
    
    Represents the arena map.
    """
    
    width: float = 2000.0
    height: float = 2000.0
    zones: tuple[BattleArenaZone, ...] = field(default_factory=tuple)
    
    def is_valid_position(self, x: float, y: float) -> bool:
        """Check if position is within map bounds."""
        return 0 <= x <= self.width and 0 <= y <= self.height
    
    def get_zone_at(self, x: float, y: float) -> Zone | None:
        """Get zone at given position."""
        for zone in self.zones:
            if zone.contains_point(x, y):
                return zone
        return None


@dataclass(frozen=True)
class BattleArenaGameState(GameState):
    """
    BattleArena implementation of GameState interface.
    
    Immutable snapshot of the entire BattleArena game state.
    This class provides a read-only view that can be used by
    generic observation and reward providers.
    
    Example:
        >>> state = BattleArenaGameState.from_battle_arena_state(arena_state)
        >>> players = state.get_players()
        >>> teams = state.get_teams()
    """
    
    _tick: int = 0
    _elapsed_time: float = 0.0
    _is_match_active: bool = True
    _match_duration: float = 600.0
    players: tuple[BattleArenaPlayer, ...] = field(default_factory=tuple)
    teams: tuple[BattleArenaTeam, ...] = field(default_factory=tuple)
    map: BattleArenaMap = field(default_factory=BattleArenaMap)
    
    # Additional metadata
    _metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    
    @property
    def tick(self) -> int:
        """Current game tick."""
        return self._tick
    
    @property
    def elapsed_time(self) -> float:
        """Elapsed time in seconds since game start."""
        return self._elapsed_time
    
    @property
    def is_match_active(self) -> bool:
        """Whether match is currently active."""
        return self._is_match_active
    
    @property
    def match_duration(self) -> float:
        """Total match duration in seconds (0 = unlimited)."""
        return self._match_duration
    
    def get_players(self) -> list[Player]:
        """Get all players in the game."""
        return list(self.players)
    
    def get_player(self, player_id: str) -> Player | None:
        """Get specific player by ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def get_teams(self) -> list[Team]:
        """Get all teams in the game."""
        return list(self.teams)
    
    def get_team(self, team_id: str) -> Team | None:
        """Get specific team by ID."""
        for team in self.teams:
            if team.id == team_id:
                return team
        return None
    
    def get_map(self) -> GameMap:
        """Get the game map."""
        return self.map
    
    def get_zones(self) -> list[Zone]:
        """Get all zones in the game."""
        return list(self.map.zones)
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "tick": self.tick,
            "elapsed_time": self.elapsed_time,
            "is_match_active": self.is_match_active,
            "match_duration": self.match_duration,
            "players": [
                {
                    "id": p.id,
                    "position": {"x": p.position.x, "y": p.position.y},
                    "velocity": {"x": p.velocity.x, "y": p.velocity.y},
                    "is_alive": p.is_alive,
                    "team_id": p.team_id,
                    "health": {"current": p._health_current, "max": p._health_max},
                    "kills": p.kills,
                    "deaths": p.deaths,
                    "assists": p.assists,
                }
                for p in self.players
            ],
            "teams": [
                {
                    "id": t.id,
                    "name": t.name,
                    "score": t.score,
                    "player_ids": list(t.player_ids),
                }
                for t in self.teams
            ],
            "map": {
                "width": self.map.width,
                "height": self.map.height,
            },
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BattleArenaGameState:
        """Deserialize state from dictionary."""
        players = []
        for p_data in data.get("players", []):
            player = BattleArenaPlayer(
                id=p_data["id"],
                pos=Vector2D(
                    x=p_data["position"]["x"],
                    y=p_data["position"]["y"]
                ),
                vel=Vector2D(
                    x=p_data["velocity"]["x"],
                    y=p_data["velocity"]["y"]
                ),
                is_alive=p_data["is_alive"],
                team_id=p_data.get("team_id"),
                _health_current=p_data["health"]["current"],
                _health_max=p_data["health"]["max"],
                _shield=0.0,
                _energy=100.0,
                kills=p_data.get("kills", 0),
                deaths=p_data.get("deaths", 0),
                assists=p_data.get("assists", 0),
            )
            players.append(player)
        
        teams = []
        for t_data in data.get("teams", []):
            team = BattleArenaTeam(
                team_id=t_data["id"],
                name=t_data["name"],
                score=t_data["score"],
                _player_ids=tuple(t_data.get("player_ids", [])),
            )
            teams.append(team)
        
        map_data = data.get("map", {})
        game_map = BattleArenaMap(
            width=map_data.get("width", 2000.0),
            height=map_data.get("height", 2000.0),
        )
        
        return cls(
            _tick=data.get("tick", 0),
            _elapsed_time=data.get("elapsed_time", 0.0),
            _is_match_active=data.get("is_match_active", True),
            _match_duration=data.get("match_duration", 600.0),
            players=tuple(players),
            teams=tuple(teams),
            map=game_map,
        )
