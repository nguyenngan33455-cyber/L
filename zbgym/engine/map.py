"""Map system for ZBGym."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.physics.vector import Vector2D


@dataclass
class SpawnPoint:
    """Spawn point for characters."""

    id: str
    position: Vector2D
    team: str = "none"
    facing_angle: float = 0.0


@dataclass
class Obstacle:
    """Map obstacle."""

    id: str
    position: Vector2D
    width: float
    height: float
    is_destructible: bool = False
    health: float = 100.0


@dataclass
class LootPoint:
    """Loot spawn point."""

    id: str
    position: Vector2D
    loot_table: str = "default"
    respawn_time: float = 30.0


@dataclass
class MapData:
    """Complete map definition."""

    id: str
    name: str
    width: float
    height: float

    spawn_points: list[SpawnPoint] = field(default_factory=list)
    obstacles: list[Obstacle] = field(default_factory=list)
    loot_points: list[LootPoint] = field(default_factory=list)

    safe_zone_center: Vector2D | None = None
    safe_zone_radius: float = 500.0

    navigation_graph: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def default_map(cls) -> MapData:
        """Create default battle arena map."""
        from zbgym.physics.vector import Vector2D

        return cls(
            id="default",
            name="Battle Arena",
            width=2000.0,
            height=1500.0,
            spawn_points=[
                SpawnPoint(id="sp_1", position=Vector2D(200, 750), team="red"),
                SpawnPoint(id="sp_2", position=Vector2D(1800, 750), team="blue"),
                SpawnPoint(id="sp_3", position=Vector2D(1000, 200), team="red"),
                SpawnPoint(id="sp_4", position=Vector2D(1000, 1300), team="blue"),
            ],
            obstacles=[
                Obstacle(id="obs_1", position=Vector2D(500, 750), width=100, height=300),
                Obstacle(id="obs_2", position=Vector2D(1500, 750), width=100, height=300),
                Obstacle(id="obs_3", position=Vector2D(1000, 500), width=200, height=100),
                Obstacle(id="obs_4", position=Vector2D(1000, 1000), width=200, height=100),
            ],
            safe_zone_center=Vector2D(1000, 750),
            safe_zone_radius=800.0,
        )


class MapManager:
    """Manages map loading and navigation with deterministic spawn selection."""

    def __init__(self, seed: int | None = None) -> None:
        self._maps: dict[str, MapData] = {}
        self._current_map: MapData | None = None
        self._rng = random.Random(seed)

        # Register default map
        self.register_map(MapData.default_map())

    def register_map(self, map_data: MapData) -> None:
        """Register a map."""
        self._maps[map_data.id] = map_data

    def load_map(self, map_id: str) -> MapData:
        """Load a map by ID."""
        if map_id not in self._maps:
            raise ValueError(f"Map '{map_id}' not found")
        self._current_map = self._maps[map_id]
        return self._current_map

    def get_current_map(self) -> MapData | None:
        """Get current map."""
        return self._current_map

    def get_spawn_point(self, team: str | None = None) -> SpawnPoint | None:
        """Get a spawn point for a team using deterministic RNG."""
        if self._current_map is None:
            return None

        candidates = self._current_map.spawn_points
        if team:
            team_spawns = [sp for sp in candidates if sp.team == team]
            if team_spawns:
                candidates = team_spawns

        if candidates:
            return self._rng.choice(candidates)
        return None

    def set_seed(self, seed: int) -> None:
        """Set RNG seed for deterministic spawn selection."""
        self._rng.seed(seed)

    def is_position_valid(self, position: Vector2D) -> bool:
        """Check if position is valid (within bounds)."""
        if self._current_map is None:
            return False

        return (
            0 <= position.x <= self._current_map.width
            and 0 <= position.y <= self._current_map.height
        )

    def is_line_of_sight_clear(self, start: Vector2D, end: Vector2D) -> bool:
        """Check if line of sight is clear between two points."""
        if self._current_map is None:
            return True

        for obstacle in self._current_map.obstacles:
            if self._line_intersects_rect(start, end, obstacle):
                return False

        return True

    def _line_intersects_rect(self, start: Vector2D, end: Vector2D, obstacle: Obstacle) -> bool:
        """Check if line intersects rectangle."""
        # Simple check using bounding box

        min_x = obstacle.position.x - obstacle.width / 2
        max_x = obstacle.position.x + obstacle.width / 2
        min_y = obstacle.position.y - obstacle.height / 2
        max_y = obstacle.position.y + obstacle.height / 2

        # Check if line segment intersects bounding box
        dx = end.x - start.x
        dy = end.y - start.y

        t_min = 0.0
        t_max = 1.0

        for axis in [
            (dx, min_x - start.x, max_x - start.x),
            (dy, min_y - start.y, max_y - start.y),
        ]:
            d, p1, p2 = axis
            if d != 0:
                t1 = p1 / d
                t2 = p2 / d
                t_min = max(t_min, min(t1, t2))
                t_max = min(t_max, max(t1, t2))

        return t_max >= t_min
