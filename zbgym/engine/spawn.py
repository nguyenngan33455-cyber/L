"""Spawn system for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from zbgym.engine.map import MapManager, SpawnPoint
    from zbgym.physics.vector import Vector2D
    from zbgym.engine.event_bus import EventBus


@dataclass
class SpawnConfig:
    """Configuration for spawn system."""

    respawn_time: float = 5.0
    spawn_protection_time: float = 2.0
    max_respawn_attempts: int = 10
    spawn_radius: float = 50.0
    prevent_spawn_kill: bool = True


class SpawnSystem:
    """
    Manages character spawning and respawning.

    Features:
    - Team-based spawn points
    - Respawn timers
    - Spawn protection
    - Spawn point selection
    """

    def __init__(
        self,
        config: SpawnConfig | None = None,
        map_manager: MapManager | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """
        Initialize spawn system.

        Args:
            config: Spawn configuration
            map_manager: Map manager for spawn points
            event_bus: Event bus for spawn events
        """
        self.config = config or SpawnConfig()
        self.map_manager = map_manager
        self.event_bus = event_bus

        # Spawn state
        self._pending_respawns: dict[str, float] = {}
        self._spawn_protections: dict[str, float] = {}
        self._used_spawn_points: set[str] = set()

    def request_spawn(
        self,
        character_id: str,
        team: str | None = None,
    ) -> bool:
        """
        Request spawn for a character.

        Args:
            character_id: ID of character to spawn
            team: Team to spawn for

        Returns:
            True if spawn was successful
        """
        if self.map_manager is None:
            return False

        spawn_point = self._select_spawn_point(team)
        if spawn_point is None:
            return False

        # Mark spawn point as used temporarily
        self._used_spawn_points.add(spawn_point.id)

        # Set respawn timer
        self._pending_respawns[character_id] = self.config.respawn_time

        # Set spawn protection
        self._spawn_protections[character_id] = (
            self.config.spawn_protection_time
        )

        # Emit spawn event
        if self.event_bus:
            self.event_bus.emit(
                "character_spawn",
                character_id=character_id,
                spawn_id=spawn_point.id,
                position=spawn_point.position.to_dict(),
                team=team,
            )

        return True

    def _select_spawn_point(
        self, team: str | None = None
    ) -> SpawnPoint | None:
        """Select an available spawn point."""
        if self.map_manager is None:
            return None

        map_data = self.map_manager.get_current_map()
        if map_data is None:
            return None

        # Get available spawn points
        available = [
            sp for sp in map_data.spawn_points
            if sp.id not in self._used_spawn_points
        ]

        if not available:
            # Reset if all used
            self._used_spawn_points.clear()
            available = map_data.spawn_points

        # Filter by team if specified
        if team:
            team_spawns = [sp for sp in available if sp.team == team]
            if team_spawns:
                available = team_spawns

        if not available:
            return None

        import random

        return random.choice(available)

    def update(self, dt: float) -> None:
        """Update spawn system."""
        # Update pending respawns
        for char_id in list(self._pending_respawns.keys()):
            self._pending_respawns[char_id] -= dt
            if self._pending_respawns[char_id] <= 0:
                del self._pending_respawns[char_id]

        # Update spawn protections
        for char_id in list(self._spawn_protections.keys()):
            self._spawn_protections[char_id] -= dt
            if self._spawn_protections[char_id] <= 0:
                del self._spawn_protections[char_id]

    def is_spawn_protected(self, character_id: str) -> bool:
        """Check if character has spawn protection."""
        return character_id in self._spawn_protections

    def get_respawn_time(self, character_id: str) -> float:
        """Get remaining respawn time for a character."""
        return self._pending_respawns.get(character_id, 0.0)

    def release_spawn_point(self, spawn_id: str) -> None:
        """Release a spawn point."""
        self._used_spawn_points.discard(spawn_id)

    def reset(self) -> None:
        """Reset spawn system state."""
        self._pending_respawns.clear()
        self._spawn_protections.clear()
        self._used_spawn_points.clear()
