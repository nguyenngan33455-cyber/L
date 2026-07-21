"""Main game engine for ZBGym."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.engine.event_bus import EventBus
    from zbgym.engine.tick_system import TickSystem

from zbgym.engine.event_bus import EventBus
from zbgym.engine.tick_system import TickSystem


@dataclass
class EngineConfig:
    """Configuration for the game engine."""

    tick_rate: int = 60
    max_frame_time: float = 0.1
    deterministic: bool = True
    debug: bool = False


class GameEngine:
    """
    Main game engine coordinating all subsystems.

    Manages:
    - Event bus for component communication
    - Tick system for deterministic updates
    - Entity management
    - Collision detection
    - Rendering
    """

    def __init__(self, config: EngineConfig | None = None) -> None:
        """
        Initialize game engine.

        Args:
            config: Engine configuration
        """
        self.config = config or EngineConfig()

        # Core subsystems
        self.event_bus: EventBus = EventBus()
        self.tick_system: TickSystem = TickSystem(
            tick_rate=self.config.tick_rate,
            event_bus=self.event_bus,
            max_frame_time=self.config.max_frame_time,
        )

        # State
        self._entities: dict[str, object] = {}
        self._running = False
        self._paused = False

    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._running

    @property
    def is_paused(self) -> bool:
        """Check if engine is paused."""
        return self._paused

    @property
    def current_tick(self) -> int:
        """Current tick number."""
        return self.tick_system.current_tick

    def register_entity(self, entity_id: str, entity: object) -> None:
        """
        Register an entity with the engine.

        Args:
            entity_id: Unique identifier for the entity
            entity: Entity object
        """
        self._entities[entity_id] = entity

    def unregister_entity(self, entity_id: str) -> bool:
        """
        Unregister an entity.

        Args:
            entity_id: Entity identifier

        Returns:
            True if entity was found and removed
        """
        if entity_id in self._entities:
            del self._entities[entity_id]
            return True
        return False

    def get_entity(self, entity_id: str) -> object | None:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_entities(self) -> dict[str, object]:
        """Get all registered entities."""
        return self._entities.copy()

    def start(self) -> None:
        """Start the engine."""
        self._running = True
        self.tick_system.start()

    def stop(self) -> None:
        """Stop the engine."""
        self._running = False
        self.tick_system.stop()

    def pause(self) -> None:
        """Pause the engine."""
        self._paused = True
        self.tick_system.pause()

    def resume(self) -> None:
        """Resume the engine."""
        self._paused = False
        self.tick_system.resume()

    def update(self) -> float:
        """
        Advance the engine by one tick.

        Returns:
            Delta time in seconds
        """
        return self.tick_system.tick()

    def reset(self) -> None:
        """Reset the engine to initial state."""
        self._entities.clear()
        self.tick_system.reset()
        self.event_bus.clear_history()
        self._running = False
        self._paused = False

    def get_stats(self) -> dict:
        """Get engine statistics."""
        return {
            "tick_system": self.tick_system.get_stats(),
            "num_entities": len(self._entities),
            "running": self._running,
            "paused": self._paused,
            "config": {
                "tick_rate": self.config.tick_rate,
                "deterministic": self.config.deterministic,
                "debug": self.config.debug,
            },
        }
